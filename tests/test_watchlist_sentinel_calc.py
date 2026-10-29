import importlib.util
import json
import math
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parent.parent / "skills/biotech-watchlist-sentinel/scripts/sentinel_calc.py"
_spec = importlib.util.spec_from_file_location("watchlist_sentinel_calc", _PATH)
calc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(calc)


def q(kind, strike, iv, delta, bid=0.50, ask=0.60, oi=100, volume=0):
    return {"type": kind, "strike": strike, "iv": iv, "delta": delta,
            "bid": bid, "ask": ask, "oi": oi, "volume": volume}


# price

def test_price_move_volume_hv_and_excess():
    bars = [{"close": 10 * (1.01 if i % 2 else 0.99), "volume": 1000} for i in range(30)]
    bars.append({"close": bars[-1]["close"] * 0.9, "volume": 4000})
    out = calc.price({"bars": bars, "xbi_change_pct": -1.0})
    assert out["change_pct"] == -10.0
    assert out["volume_x_avg"] == 4.0
    assert out["excess_vs_xbi_pts"] == -9.0 and out["moved_with_biotech"] is False
    assert out["big_move"] is True
    assert out["hv30_from_bars"] > 0


def test_price_with_sector():
    out = calc.price({"bars": [{"close": 10, "volume": 1}, {"close": 9.8, "volume": 1}], "xbi_change_pct": -1.5})
    assert out["moved_with_biotech"] is True and out["big_move"] is False


# overlay

def test_overlay_weekend_pdufa_counts_friday_expiry():
    out = calc.overlay({"as_of": "2026-10-29", "event_date": "2026-11-22",
                        "expiries": ["2026-11-13", "2026-11-20", "2026-12-18"]})
    assert [e["status"] for e in out["expiries"]] == ["before", "carries", "carries"]
    assert "2026-11-20" in out["note"]
    assert out["trading_days_to_event"] == 16 and out["dated"] is True


def test_overlay_window_and_holiday_trading_days():
    out = calc.overlay({"as_of": "2026-11-23", "event_date": "2026-11-27", "holidays": ["2026-11-26"],
                        "expiries": ["2026-11-27"]})
    assert out["trading_days_to_event"] == 3
    out = calc.overlay({"as_of": "2026-10-29", "window_start": "2026-10-01", "window_end": "2026-12-31",
                        "expiries": ["2026-11-20", "2027-01-15"]})
    assert [e["status"] for e in out["expiries"]] == ["in_window", "carries"]
    assert out["dated"] is False and out["trading_days_to_event"] == 0


# skew

def test_skew_ratios_shape_and_term():
    front = [q("put", 6, 1.80, -0.48), q("call", 6, 1.76, 0.52)]
    back = [q("put", 6, 1.20, -0.45), q("call", 6, 1.24, 0.55),
            q("put", 4.5, 1.50, -0.24), q("put", 4, 1.60, -0.15),
            q("call", 8, 1.30, 0.26)]
    out = calc.skew({"spot": 6.1, "front": front, "back": back})
    assert out["front_atm_iv"] == 1.78 and out["back_atm_iv"] == 1.22
    assert out["put_25d"]["strike"] == 4.5
    assert out["put_ratio"] == round(1.50 / 1.22, 3)
    assert out["call_ratio"] == round(1.30 / 1.22, 3)
    assert out["shape"] == "put skew"
    assert out["term_ratio"] == round(1.78 / 1.22, 3)


def test_skew_ignores_unusable_quotes():
    back = [q("put", 6, 1.2, -0.45), q("call", 6, 1.2, 0.55),
            q("put", 4.5, 3.0, -0.25, bid=0.05, ask=0.40),   # spread too wide
            q("call", 8, 1.3, 0.25, oi=0, volume=0)]          # no interest
    out = calc.skew({"spot": 6.1, "front": [], "back": back})
    assert out["put_ratio"] is None and out["call_ratio"] is None
    assert "chain too thin" in out["n/a"]


# contract

def test_contract_picks_usable_put_in_band_and_computes_roc():
    puts = [q("put", 4, 1.62, -0.18, bid=0.50, ask=0.60, oi=1240),
            q("put", 4.5, 1.55, -0.24, bid=0.70, ask=0.80, oi=300),
            q("put", 3, 1.9, -0.08, bid=0.05, ask=0.30, oi=5000)]
    out = calc.contract({"spot": 6.10, "dte": 79, "puts": puts})["contract"]
    assert out["strike"] == 4 and out["otm_pct"] == 34.4
    assert out["breakeven"] == 3.45
    assert out["roc_pct"] == round(0.55 / 3.45 * 100, 1)
    assert out["annualized_pct"] == round(0.55 / 3.45 * 365 / 79 * 100, 1)


def test_contract_none_when_thin():
    out = calc.contract({"spot": 6.1, "dte": 79, "puts": [q("put", 4, 1.6, -0.2, bid=0, ask=0.5)]})
    assert out["contract"] is None and "too thin" in out["note"]


# assess

def test_assess_event_in_back_rich_premium_and_puts():
    out = calc.assess({"ivp52": 0.71, "ivp26": 0.6, "iv30": 1.48, "hv30": 0.9,
                       "put_ratio": 1.22, "call_ratio": 1.05, "shape": "put skew",
                       "term_ratio": 0.84, "front_status": "before", "back_status": "carries",
                       "trading_days_to_event": 25})
    assert out["flags"] == ["RICH PREMIUM", "RICH PUTS", "EVENT IN BACK"]
    assert out["needs_contract"] is True


def test_assess_event_in_front_crush_and_unexplained():
    out = calc.assess({"term_ratio": 1.5, "front_status": "carries", "back_status": "carries",
                       "trading_days_to_event": 3})
    assert out["flags"] == ["EVENT IN FRONT", "IV CRUSH WATCH"]
    out = calc.assess({"term_ratio": 1.3, "front_status": None, "back_status": None})
    assert out["flags"] == ["UNEXPLAINED INVERSION"] and out["needs_contract"] is False


def test_assess_puts_not_paid_cheap_and_open_window_no_crush():
    out = calc.assess({"ivp52": 0.2, "put_ratio": 0.98, "shape": "call skew",
                       "front_status": "in_window", "back_status": "carries", "term_ratio": 1.0,
                       "trading_days_to_event": 0, "event_dated": False})
    assert out["flags"] == ["CHEAP", "PUTS NOT PAID"]


def test_cli_roundtrip(capsys):
    assert calc.main(["x", "overlay", json.dumps({"as_of": "2026-10-29", "event_date": "2026-11-02",
                                                   "expiries": ["2026-11-20"]})]) == 0
    assert json.loads(capsys.readouterr().out)["expiries"][0]["status"] == "carries"
    assert calc.main(["x", "nope"]) == 2
