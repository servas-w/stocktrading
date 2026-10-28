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
