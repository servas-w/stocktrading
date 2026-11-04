# VALU v2 for Gemini

The same valuation method and output card as the Claude skill in [`../stock-valuation-engine`](../stock-valuation-engine/SKILL.md), so a Gemini run and a Claude run on the same ticker can be compared line for line.

## Set up the Gem
1. In Gemini, go to **Gems → New Gem**, name it **VALU**.
2. Paste the whole of [`GEM-INSTRUCTIONS.md`](GEM-INSTRUCTIONS.md) into **Instructions**.
3. Under **Knowledge**, upload:
   - [`../stock-valuation-engine/scripts/valuation.py`](../stock-valuation-engine/scripts/valuation.py) (the calculator; Gemini runs it when code execution is available)
   - [`../stock-valuation-engine/references/method.md`](../stock-valuation-engine/references/method.md) (why each rule exists, including the GOOG lessons)
   - [`../stock-valuation-engine/SKILL.md`](../stock-valuation-engine/SKILL.md) (the calculator's JSON input keys)
4. Run `VALU: TICKER` or `VALU DEEP: TICKER`.

## What changed from the old Gemini VALU (GOOG, Nov 3 2026 run)
| Old Gemini behaviour | v2 rule |
|---|---|
| Subtracted SBC from NOPAT ("33.7–35x core owner NOPAT") | Rule 1: SBC is subtracted from cash flow only (correct: 25.7–26.8x) |
| Hand-typed FCF paths (−$50B → +$178B), ~90% of value in terminal value | Rule 3: one fixed DCF shape, g and r set by rule |
| Base case left out $135B of private stakes; normalized case added them; then blended the two | Rule 5: one asset base for every scenario |
| Numbers sourced from blogs (money365, geminiq, convexityos) | Rule 7: primary sources only for numbers |
| Options gate and a $195P suggestion above its own $194.15 cap | Valuation only; LC owns strikes |
| ~1,800 words | Card ≤ 350 words; DEEP appendix ≤ 400 |

Kept from Gemini: the normalized (capex-adjusted) lens. v2 formalizes it as maintenance capex = D&A and a no-growth EPV soft floor.

GOOG with v2 (Nov 3 2026, spot $272.75): CAPEX-CYCLE (RICH vs peers), fair $214.47, soft floor $105.26, price implies 16.1% normalized growth for 5 years.
