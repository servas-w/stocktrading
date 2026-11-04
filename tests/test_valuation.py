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
    assert h["val_core_eps_f1"] == 11.26    # consensus F1 19.80 minus FY-to-date marks after tax
    assert h["val_fair"] == 220.33          # v1 gave 306.53 off mark-inflated F1 EPS
    assert h["val_pe_range"] == [225.73, 243.64]
    assert h["val_soft_floor"] == 101.01    # maintenance = run-rate D&A $33.5B, not TTM $28.0B
    assert "net cash 11.36/sh" in out and "median x normalized FCF" in out
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


def _leveraged(int_exp=None, pretax=800):
    q = lambda e: {"end": e, "rev": 5000, "op_inc": 1000, "ni": 600, "eps": 1.5, "pretax": pretax, "tax": 168,
                   **({} if int_exp is None else {"int_exp": int_exp})}
    return {"ticker": "LEV", "asof": "2026-11-03", "spot": 60, "shares": 400, "fy_end": "2025-12-31", "cash": 500,
            "debt": 20000, "sbc_ttm": 100, "cf_mode": "ytd",
            "cf_q": [{"end": "2026-09-30", "ocf": 3000, "capex": -600, "da": 450}, {"end": "2026-06-30", "ocf": 2000, "capex": -400, "da": 300},
                     {"end": "2026-03-31", "ocf": 1000, "capex": -200, "da": 150}, {"end": "2025-12-31", "ocf": 4000, "capex": -800, "da": 600},
                     {"end": "2025-09-30", "ocf": 3000, "capex": -600, "da": 450}],
            "is_q": [q("2026-09-30"), q("2026-06-30"), q("2026-03-31"), q("2025-12-31")],
            "eps_f1": 6.0, "eps_f2": 6.6, "beta": 1.0, "peers": [{"t": "A", "pe_f1": 15, "ps": 2, "chg12w": 0}], "rf": 0.045}


def test_interest_expense_is_not_a_one_off():
    # interest unknown: a net non-op expense is treated as recurring, not stripped
    _, h = run(_leveraged())
    assert h["val_nonop_flag"] is False and h["val_soft_floor"] is None
    # interest known and it explains the gap: clean
    _, h = run(_leveraged(int_exp=200))
    assert h["val_nonop_flag"] is False and h["val_core_eps"] == 6.32
    # a one-off loss on top of interest still gets flagged
    _, h = run(_leveraged(int_exp=200, pretax=600))
    assert h["val_nonop_flag"] is True


def test_gemini_skill_copies_match_claude():
    gem = ROOT / "skills" / "stock-valuation-engine-gemini"
    claude = ROOT / "skills" / "stock-valuation-engine"
    for rel in ("scripts/valuation.py", "references/method.md"):
        assert (gem / rel).read_bytes() == (claude / rel).read_bytes(), f"{rel} drifted: copy it again"
    assert (gem / "references/test-case-goog.json").read_bytes() == GOOG.read_bytes()
    for rel in ():
        assert (gem / rel).read_bytes() == (claude / rel).read_bytes(), f"{rel} drifted: copy it again"


def test_forward_core_eps_falls_back_to_growth_scaling():
    x = json.loads(GOOG.read_text())
    x.pop("eps_f1")
    out, h = run(x)
    assert "core TTM x (1 +27% op-income growth)^(3/12)" in out
    assert h["val_core_eps_f1"] == 11.15


def test_ppe_life_raises_maintenance_capex():
    x = json.loads(GOOG.read_text())
    x["ppe_net"], x["ppe_life"] = 372827, 8
    out, h = run(x)
    assert "maintenance capex = net PP&E / 8y" in out
    assert h["val_soft_floor"] < 101.01


def test_capex_surge_with_positive_owner_fcf_shows_normalized_lens():
    x = _leveraged(int_exp=200)
    for r in x["cf_q"]:
        r["capex"] = -r["da"] * 3          # capex 3x D&A, owner FCF still positive
    out, h = run(x)
    assert "SURGE > 2x" in out and h["val_soft_floor"] is not None
    assert not h["val_verdict"].startswith("CAPEX-CYCLE")   # owner FCF > 0: normal verdict ladder
