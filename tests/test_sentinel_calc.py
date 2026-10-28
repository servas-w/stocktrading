import importlib.util
import json
import math
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parent.parent / "skills/biotech-ticker-sentinel/scripts/sentinel_calc.py"
_spec = importlib.util.spec_from_file_location("sentinel_calc", _PATH)
calc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(calc)


# iv30

def test_iv30_interpolates_total_variance_and_reports_change():
    out = calc.iv30({"points": [{"dte": 51, "iv": 1.6}, {"dte": 23, "iv": 1.9}], "baseline_iv30": 1.7})
    w = 1.9**2 * 23 + (1.6**2 * 51 - 1.9**2 * 23) * 7 / 28
    assert out["iv30"] == round(math.sqrt(w / 30), 4)
    assert out["change_pts"] == round((out["iv30"] - 1.7) * 100, 1)


def test_iv30_flat_outside_range_still_reports_change():
    out = calc.iv30({"points": [{"dte": 40, "iv": 1.2}, {"dte": 70, "iv": 1.0}], "baseline_iv30": 1.0})
    assert out["iv30"] == 1.2
    assert "flat" in out["note"]
    assert out["change_pts"] == 20.0


def test_iv30_needs_two_points():
    with pytest.raises(ValueError):
        calc.iv30({"points": [{"dte": 30, "iv": 1.0}]})


# overlay

def test_overlay_weekend_pdufa():
    out = calc.overlay({"as_of": "2026-10-28", "event_date": "2026-11-22",
                        "expiries": ["2026-12-18", "2026-11-13", "2026-11-20"]})
    status = {e["expiry"]: e["status"] for e in out["expiries"]}
    assert status == {"2026-11-13": "before", "2026-11-20": "ambiguous", "2026-12-18": "carries"}
    assert out["pre_event_expiry"] == "2026-11-13"
    assert out["post_event_expiry"] == "2026-12-18"
    assert "2026-11-20" in out["note"]


def test_overlay_holiday_and_open_window():
    out = calc.overlay({"as_of": "2026-11-01", "event_date": "2026-11-26", "holidays": ["2026-11-26"],
                        "expiries": ["2026-11-25", "2026-11-27"]})
    assert [e["status"] for e in out["expiries"]] == ["ambiguous", "carries"]
    out = calc.overlay({"as_of": "2026-10-28", "window_start": "2026-10-01", "window_end": "2026-12-31",
                        "expiries": ["2026-11-20", "2027-01-15"]})
    assert [e["status"] for e in out["expiries"]] == ["in_window", "carries"]
    assert out["pre_event_expiry"] is None


# event_move

def test_event_move_from_term_structure_in_log_space():
    out = calc.event_move({"spot": 3.0, "pre_iv": 1.0, "post_iv": 2.0, "post_dte": 36.5})
    std = math.sqrt((4 - 1) * 0.1)
    assert out["event_std_move_pct"] == round(std * 100, 1)
    assert out["expected_down_level"] == round(3.0 * math.exp(-std * calc.ABS_MOVE_FACTOR), 3)
    big = calc.event_move({"spot": 2.0, "pre_iv": 1.0, "post_iv": 5.0, "post_dte": 60})
    assert big["expected_abs_move_pct"] > 100 and big["expected_down_level"] > 0


def test_event_move_failure_case_catches_what_average_move_misses():
    out = calc.event_move({"spot": 6.1, "pre_iv": 1.0, "post_iv": 2.0, "post_dte": 51,
                           "strike": 3.5, "credit": 0.35, "qty": 10, "fail_level": 2.4})
    assert out["move_test"] == "strike outside expected move"
    assert out["if_event_fails"] == {"stock_at": 2.4, "short_put": "ITM", "loss": pytest.approx(750.0)}


def test_event_move_failure_loss_capped_for_spread_and_zero_when_otm():
    out = calc.event_move({"spot": 5, "straddle": 2, "strike": 4, "long_strike": 3, "credit": 0.3,
                           "qty": 2, "fail_level": 1})
    assert out["if_event_fails"]["loss"] == pytest.approx(140.0)
    assert out["down_level_source"].startswith("straddle")
    out = calc.event_move({"spot": 5, "straddle": 1, "strike": 2, "credit": 0.1, "fail_level": 2.5})
    assert out["if_event_fails"] == {"stock_at": 2.5, "short_put": "OTM", "loss": 0.0}


def test_event_move_no_premium_and_requires_inputs():
    out = calc.event_move({"spot": 2.0, "pre_iv": 1.5, "post_iv": 1.2, "post_dte": 30})
    assert out["event_std_move_pct"] == 0.0
    with pytest.raises(ValueError):
        calc.event_move({"spot": 1.0})


# position

def test_position_short_put_flags_and_delta_sign_proof():
    for delta in (-0.32, 0.32):
        out = calc.position({"spot": 2.6, "as_of": "2026-10-28", "legs": [
            {"strike": 2.5, "credit": 0.40, "qty": 10, "expiry": "2026-11-13", "mark": 0.15, "delta": delta}]})
        lg = out["legs"][0]
        assert lg["dte"] == 16 and lg["breakeven"] == 2.1 and lg["captured_pct"] == 62.5
        assert set(lg["flags"]) == {"within 7% of strike", "delta >= 0.30",
                                    "<= 21 DTE near the money", ">= 50% captured"}


def test_position_spread_intrinsic_capped_and_long_put_hedge():
    out = calc.position({"spot": 0.8, "legs": [
        {"strike": 2.0, "long_strike": 1.0, "credit": 0.3, "qty": 2, "dte": 51, "mark": 1.0},
        {"type": "long_put", "strike": 1.0, "cost": 0.10, "qty": 3, "dte": 80, "mark": 0.35}]})
    short, long_ = out["legs"]
    assert short["max_loss"] == pytest.approx(140)
    assert "mark below intrinsic: quote stale" not in short["flags"]
    assert long_["pnl"] == pytest.approx(75.0)
    assert long_["flags"] == ["hedge worth >= 2x cost: consider monetizing"]
    assert out["hedge_ratio"] == 1.5


def test_position_stock_flags():
    out = calc.position({"spot": 5.75, "held_shares": -100, "avg_cost": 5.0,
                         "legs": [{"strike": 4, "credit": 0.5, "qty": 1, "dte": 60}]})
    assert out["stock"]["flag"].startswith("short stock up >= 15%")
    assert out["stock"]["pnl_pct"] == -15.0
    assert "Anti-CAPR" in out["flag"]
    out = calc.position({"spot": 4.0, "held_shares": 100, "avg_cost": 5.0})
    assert "underwater" in out["stock"]["flag"]
    assert out["legs"] == []


# floor

def test_floor_matches_audit_convention_and_net_of_debt():
    out = calc.floor({
        "cash": 100, "inflows_since": 10, "debt": 20, "quarterly_burn": 18.2,
        "balance_sheet_date": "2026-06-30", "as_of": "2026-09-29", "expiry": "2026-12-29",
        "basic_shares_m": 40, "prefunded_warrants_m": 10,
    })
    assert out["fd_shares_m"] == 50
    assert out["cash_now"] == pytest.approx(110 - 18.2)
    assert out["cash_per_share"] == round((110 - 18.2) / 50, 3)
    assert out["net_of_debt_per_share"] == round((110 - 18.2 - 20) / 50, 3)
    assert out["cash_per_share_at_expiry"] == round((110 - 36.4) / 50, 3)


def test_floor_treasury_stock_and_warnings():
    out = calc.floor({"cash": 50, "balance_sheet_date": "2026-06-30", "as_of": "2026-06-30",
                      "basic_shares_m": 10, "reference_price": 4.0,
                      "dilutive": [{"qty_m": 2, "strike": 2.0}, {"qty_m": 5, "strike": 8.0}]})
    assert out["fd_shares_m"] == 11
    out = calc.floor({"cash": 10, "balance_sheet_date": "2026-03-31", "as_of": "2026-10-28",
                      "basic_shares_m": 5, "dilutive": [{"qty_m": 1, "strike": 1}]})
    assert len(out["warnings"]) == 2


def test_cli_roundtrip(capsys):
    assert calc.main(["x", "event-move", json.dumps({"spot": 2, "straddle": 0.5})]) == 0
    assert json.loads(capsys.readouterr().out)["straddle_move_pct"] == 25.0
    assert calc.main(["x", "book"]) == 2
