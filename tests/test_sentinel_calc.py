import importlib.util
import json
import math
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parent.parent / "skills/biotech-ticker-sentinel/scripts/sentinel_calc.py"
_spec = importlib.util.spec_from_file_location("sentinel_calc", _PATH)
calc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(calc)


def test_floor_counts_prefunded_and_debt_and_burn():
    out = calc.cash_floor({
        "cash": 100, "inflows_since": 10, "debt": 20, "current_liabilities": 5,
        "quarterly_burn": 18.2, "balance_sheet_date": "2026-06-30",
        "as_of": "2026-09-29", "expiry": "2026-12-29",
        "basic_shares_m": 40, "prefunded_warrants_m": 10,
    })
    assert out["economic_shares_m"] == 50
    assert out["gross_cash_per_share"] == 2.2
    # 91 days of burn at 0.2/day = 18.2
    assert out["net_cash_now"] == pytest.approx(110 - 25 - 18.2)
    assert out["net_cash_at_expiry"] == pytest.approx(110 - 25 - 36.4)


def test_floor_treasury_stock_only_counts_itm():
    out = calc.cash_floor({
        "cash": 50, "balance_sheet_date": "2026-06-30", "as_of": "2026-06-30",
        "basic_shares_m": 10, "reference_price": 4.0,
        "dilutive": [{"qty_m": 2, "strike": 2.0}, {"qty_m": 5, "strike": 8.0}],
    })
    # 2M options at $2 with stock at $4: 2 - 2*2/4 = 1M net new shares
    assert out["fully_diluted_shares_m"] == 11


def test_event_move_from_term_structure():
    out = calc.event_move({"spot": 3.0, "pre_iv": 1.0, "post_iv": 2.0, "post_dte": 36.5})
    std = math.sqrt((4 - 1) * 0.1)
    assert out["event_std_move_pct"] == round(std * 100, 1)
    assert out["expected_abs_move_pct"] == round(std * calc.ABS_MOVE_FACTOR * 100, 1)
    assert out["term_structure_inverted"] is True


def test_event_move_no_premium_and_straddle():
    out = calc.event_move({"spot": 2.0, "pre_iv": 1.5, "post_iv": 1.2, "post_dte": 30, "straddle": 0.5})
    assert out["event_std_move_pct"] == 0.0
    assert out["straddle_move_pct"] == 25.0
    assert (out["straddle_low"], out["straddle_high"]) == (1.5, 2.5)


def test_event_move_requires_inputs():
    with pytest.raises(ValueError):
        calc.event_move({"spot": 1.0})


def test_leg_alarms_and_exposure():
    out = calc.leg({"spot": 2.6, "strike": 2.5, "credit": 0.40, "qty": 10, "dte": 18,
                    "mark": 0.15, "delta": -0.32, "nav": 50000, "held_shares": 1000})
    assert out["breakeven"] == 2.1
    assert out["max_loss"] == pytest.approx(2100)
    assert out["captured_pct"] == 62.5
    assert set(out["alarms"]) >= {"within 7% of strike", "delta <= -0.30",
                                  "<= 21 DTE near the money", ">= 50% captured: velocity take-profit"}
    assert out["name_exposure_pct_nav"] == pytest.approx((2600 + 2100) / 500, abs=0.01)


def test_leg_spread_and_stale_mark():
    out = calc.leg({"spot": 1.8, "strike": 2.0, "long_strike": 1.0, "credit": 0.3,
                    "qty": 2, "dte": 40, "mark": 0.1})
    assert out["max_loss"] == pytest.approx(140)
    assert "ITM" in out["alarms"]
    assert "mark below intrinsic: quote stale or unfillable" in out["alarms"]


def test_cli_roundtrip(capsys):
    assert calc.main(["x", "leg", json.dumps({"spot": 5, "strike": 3, "credit": 0.2, "qty": 1, "dte": 70})]) == 0
    assert json.loads(capsys.readouterr().out)["alarms"] == []
    assert calc.main(["x", "nope"]) == 2


def test_event_move_down_level_is_log_and_never_negative():
    out = calc.event_move({"spot": 2.0, "pre_iv": 1.0, "post_iv": 5.0, "post_dte": 60})
    assert out["expected_abs_move_pct"] > 100
    assert 0 < out["expected_down_level"] < 2.0


def test_event_move_verdicts():
    base = {"spot": 3.0, "pre_iv": 1.0, "post_iv": 2.0, "post_dte": 36.5}
    down = calc.event_move(base)["expected_down_level"]
    assert calc.event_move({**base, "strike": down - 0.1, "credit": 0.2})["verdict"] == "PAID"
    assert calc.event_move({**base, "strike": down + 0.1, "credit": 0.2})["verdict"] == "THIN"
    assert calc.event_move({**base, "strike": down + 0.5, "credit": 0.2})["verdict"] == "UNPAID"


def test_event_move_straddle_fallback_sets_level_and_post_expiry_dates():
    out = calc.event_move({"spot": 2.0, "straddle": 2.5, "strike": 1.0})
    assert out["straddle_low"] == 0.0
    assert out["strike_inside_expected_down_move"] is True
    a = calc.event_move({"spot": 3, "pre_iv": 1, "post_iv": 2, "post_dte": 36.5})
    b = calc.event_move({"spot": 3, "pre_iv": 1, "post_iv": 2, "as_of": "2026-01-01", "post_expiry": "2026-02-06"})
    assert a["event_std_move_pct"] == pytest.approx(b["event_std_move_pct"], abs=0.5)


def test_overlay_weekend_pdufa():
    out = calc.overlay({"as_of": "2026-10-28", "event_date": "2026-11-22",
                        "expiries": ["2026-12-18", "2026-11-13", "2026-11-20"]})
    status = {e["expiry"]: e["status"] for e in out["expiries"]}
    assert status == {"2026-11-13": "before", "2026-11-20": "ambiguous", "2026-12-18": "carries"}
    assert out["pre_event_expiry"] == "2026-11-13"
    assert out["post_event_expiry"] == "2026-12-18"
    assert "2026-11-20" in out["note"]


def test_overlay_open_window():
    out = calc.overlay({"as_of": "2026-10-28", "window_start": "2026-10-01", "window_end": "2026-12-31",
                        "expiries": ["2026-11-20", "2027-01-15"]})
    assert [e["status"] for e in out["expiries"]] == ["in_window", "carries"]
    assert out["pre_event_expiry"] is None


def test_leg_spread_intrinsic_capped_at_width_and_expiry_dte():
    out = calc.leg({"spot": 0.8, "strike": 2.0, "long_strike": 1.0, "credit": 0.3, "qty": 1,
                    "as_of": "2026-10-28", "expiry": "2026-12-18", "mark": 0.95})
    assert out["intrinsic"] == 1.0
    assert out["dte"] == 51
    assert "mark below intrinsic: quote stale or unfillable" in out["alarms"]
    out = calc.leg({"spot": 0.8, "strike": 2.0, "long_strike": 1.0, "credit": 0.3, "qty": 1, "dte": 51, "mark": 1.0})
    assert "mark below intrinsic: quote stale or unfillable" not in out["alarms"]


def test_book_counts_every_leg_and_shares_once():
    out = calc.book({"nav": 20000, "positions": [
        {"ticker": "AAA", "spot": 3.0, "held_shares": 100, "legs": [
            {"strike": 2.0, "credit": 0.2, "qty": 5, "dte": 60},
            {"strike": 2.5, "long_strike": 1.5, "credit": 0.3, "qty": 2, "dte": 80}]},
        {"ticker": "BBB", "spot": 5.0, "held_shares": -200, "legs": [
            {"strike": 4.0, "credit": 0.5, "qty": 1, "dte": 70}]},
    ]})
    aaa = next(r for r in out["names"] if r["ticker"] == "AAA")
    assert aaa["exposure"] == pytest.approx(300 + 900 + 140)
    assert aaa["name_alarms"] == []
    bbb = next(r for r in out["names"] if r["ticker"] == "BBB")
    assert "Anti-CAPR: short stock against short puts" in bbb["name_alarms"]
    assert out["names"][0]["ticker"] == "AAA"


def test_floor_warns_on_ignored_dilution_and_stale_balance_sheet():
    out = calc.cash_floor({"cash": 10, "balance_sheet_date": "2026-03-31", "as_of": "2026-10-28",
                           "basic_shares_m": 5, "dilutive": [{"qty_m": 1, "strike": 1}]})
    assert len(out["warnings"]) == 2
