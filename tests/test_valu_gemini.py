import importlib.util
import json
import re
from pathlib import Path

import pytest

_DIR = Path(__file__).resolve().parent.parent / "skills/valu-gemini"
_spec = importlib.util.spec_from_file_location("valu_gemini", _DIR / "scripts/valuation.py")
calc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(calc)


def _example():
    md = (_DIR / "SKILL.md").read_text()
    return json.loads(re.search(r"```json\n(.*?)\n```", md, re.S).group(1))


def _handoff(out: str) -> dict:
    return json.loads(out.split("VALU_HANDOFF ", 1)[1])


def test_skill_example_runs_and_uses_direct_sp_move(capsys):
    calc.valu(_example())
    out = capsys.readouterr().out
    assert "S&P +6.0%" in out  # s_chg12w taken as given, not backed out of a relative change
    assert "discrete quarters summed" in out
    h = _handoff(out)
    assert h["val_floor"] is not None and h["val_fair"] is not None
    assert h["val_implied_g"] == pytest.approx(calc.implied_g(8515, 104521.9 + 6363 - 5639, h["val_r"]), abs=0.002)


def test_relative_change_fallback_matches_direct(capsys):
    x = _example()
    t12, s12 = x["t_chg12w"] / 100, x["s_chg12w"] / 100
    x.pop("s_chg12w")
    x["t_rel12w"] = ((1 + t12) / (1 + s12) - 1) * 100
    calc.valu(x)
    assert "S&P +6.0%" in capsys.readouterr().out


def test_financial_gives_no_floor(capsys):
    x = _example()
    x["financial"] = True
    calc.valu(x)
    assert _handoff(capsys.readouterr().out)["val_floor"] is None


def test_no_owner_cash_is_speculative(capsys):
    x = _example()
    x["sbc_ttm"] = 50000
    calc.valu(x)
    assert _handoff(capsys.readouterr().out)["val_verdict"] == "SPECULATIVE"


def test_fallback_table_matches_calculator():
    rows = [ln for ln in (_DIR / "references/dcf_table.md").read_text().splitlines() if re.match(r"\| [+-]\d", ln)]
    header = next(ln for ln in (_DIR / "references/dcf_table.md").read_text().splitlines() if ln.startswith("| g"))
    rs = [float(c.strip().rstrip("%")) / 100 for c in header.split("|")[2:-1]]
    for ln in rows:
        cells = [c.strip() for c in ln.split("|")[1:-1]]
        g = float(cells[0].rstrip("%")) / 100
        for r, cell in zip(rs, cells[1:]):
            assert float(cell) == pytest.approx(calc.dcf_ev(1.0, g, r), abs=0.051)


# web-format inputs (the audit's blind spot)

def test_web_formats_parse():
    assert [calc.f(v) for v in ["10,031", "(85)", "$268.54", "389.20M", "1.2B", "500K", "-3.18%", "−0.5", "n/a"]] == \
        [10031, -85, 268.54, 389.2, 1200, 0.5, -3.18, -0.5, None]
    assert [str(calc.d(v)) for v in ["Aug 31, 2026", "8/31/2026", "2026-08-31", "Oct 1, 2021", "2021-12"]] == \
        ["2026-08-31", "2026-08-31", "2026-08-31", "2021-10-01", "2021-12-01"]


def test_skill_example_in_web_format_has_no_warnings(capsys):
    calc.valu(_example())
    out = capsys.readouterr().out
    assert "INPUT WARNINGS" not in out
    assert "OCF $10.81B" in out
    assert _handoff(out)["input_warnings"] == 0


def test_unreadable_newest_quarter_refuses_instead_of_shifting(capsys):
    x = _example()
    x["cf_q"][0]["end"] = "Q3 FY26"  # unparseable label
    calc.valu(x)
    out = capsys.readouterr().out
    assert "INPUT WARNINGS: cash-flow row unreadable" in out
    h = _handoff(out)
    assert h["val_verdict"] == "INCOMPLETE" and h["input_warnings"] == 1


def test_peer_next_fy_pe_uses_eps_f2(capsys):
    x = _example()
    calc.valu(x)
    out = capsys.readouterr().out
    assert "fwd P/E (next FY)" in out
    assert f"fwd P/E {12.61 * x['eps_f2']:,.2f}" in out


def test_thousands_units_match_millions(capsys):
    x = _example()
    calc.valu(x)
    base = _handoff(capsys.readouterr().out)
    y = json.loads(json.dumps(x))
    y["statement_units"] = "thousands"
    for k in ("cash", "debt", "sbc_ttm"):
        y[k] = calc.f(y[k]) * 1000
    for key, fields in (("cf_q", ("ocf", "capex")), ("annual", ("ocf", "capex")), ("is_q", ("rev", "op_inc", "ni"))):
        for r in y[key]:
            for fl in fields:
                r[fl] = calc.f(r[fl]) * 1000
    calc.valu(y)
    other = _handoff(capsys.readouterr().out)
    assert other["val_floor"] == base["val_floor"] and other["val_fair"] == base["val_fair"]


def test_month_name_bars_feed_history(capsys):
    x = _example()
    months = [f"{m} 1, {y}" for y in (2024, 2025) for m in
              ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")]
    x["px_m"] = {"t": months + ["Mar 14, 2025 Dividend"], "l": [400 + i for i in range(24)] + [""]}
    x["annual"] = [{"end": "Nov 30, 2025", "ocf": "10,031", "capex": "(179)"},
                   {"end": "Nov 30, 2024", "ocf": "8,056", "capex": "(183)"}]
    calc.valu(x)
    out = capsys.readouterr().out
    assert "Own history (2 FY)" in out
    assert "monthly bar unreadable" in out  # the dividend row is reported, not used
