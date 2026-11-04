"""Regression tests for the VALU v2 calculator (skills/stock-valuation-engine/scripts/valuation.py)."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CALC = ROOT / "skills" / "stock-valuation-engine" / "scripts" / "valuation.py"
GOOG = ROOT / "tests" / "fixtures" / "valu_goog_2026-11-03.json"


def run(payload):
    arg = payload if isinstance(payload, str) else json.dumps(payload)
    out = subprocess.run([sys.executable, str(CALC), "valu", arg], capture_output=True, text=True, check=True).stdout
    line = next(l for l in out.splitlines() if l.startswith("VALU_HANDOFF "))
    return out, json.loads(line[len("VALU_HANDOFF "):])


def test_goog_core_eps_and_capex_cycle():
    out, h = run(str(GOOG))
    assert h["val_nonop_flag"] is True
    assert h["val_core_eps"] == 10.52
    assert h["val_fair"] == 214.47          # v1 gave 306.53 off mark-inflated F1 EPS
    assert h["val_soft_floor"] == 105.26
    assert h["val_floor"] is None           # soft floor never becomes the hard floor
    assert h["val_verdict"].startswith("CAPEX-CYCLE")
    assert "EPS leg dropped" in out


def test_goog_without_new_inputs_matches_v1():
    x = json.loads(GOOG.read_text())
    for r in x["cf_q"]:
        r.pop("da")
    for r in x["is_q"]:
        r.pop("pretax", None)
        r.pop("tax", None)
    _, h = run(x)
    assert h["val_fair"] == 306.53
    assert h["val_verdict"] == "SPECULATIVE"
    assert h["val_soft_floor"] is None and h["val_nonop_flag"] is False


def test_clean_name_unchanged():
    x = {"ticker": "XYZ", "asof": "2026-10-23", "spot": 268.54, "shares": 389.2, "fy_end": "2025-11-30",
         "cash": 5639, "debt": 6363, "sbc_ttm": 2071, "cf_mode": "ytd",
         "cf_q": [{"end": "2026-08-31", "ocf": 7646, "capex": -180}, {"end": "2026-05-31", "ocf": 5123, "capex": -95},
                  {"end": "2026-02-28", "ocf": 2958, "capex": -37}, {"end": "2025-11-30", "ocf": 10031, "capex": -179},
                  {"end": "2025-08-31", "ocf": 6871, "capex": -145}],
         "eps_f1": 24.47, "eps_f2": 27.7, "beta": 1.42,
         "peers": [{"t": "INTU", "pe_f1": 14.28, "ps": 4.18, "peg": 1.09, "chg4w": 17.02, "chg12w": 0.74}], "rf": 0.045}
    _, h = run(x)
    assert h["val_floor"] == 272.95 and h["val_fair"] == 390.56 and h["val_verdict"] == "AT FLOOR"
