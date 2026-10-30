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
