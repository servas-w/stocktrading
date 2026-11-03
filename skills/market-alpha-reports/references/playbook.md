# Playbook v2 reference (rules, gates and terms)

This is the only place the reports take rule definitions from. Cite a rule by **name and number**, for example `R3 ITM ≤ 21 DTE`. If another installed skill numbers a rule differently, use this file and add `(see playbook.md)`.

Items marked **CONFIRM** were reconciled from sources that disagree (your report skills, the rh-* audit skills and past reports). They are working defaults until Wilson confirms them.

## Entry rules (new short premium)
| # | Rule | Gate |
|---|---|---|
| R1 | IV gate | Sell naked premium only when IV Rank ≥ 50. Defined-risk spreads are exempt from the gate (spread exception). If IVR can't be sourced, print `IVR unverified` and grade the entry B at best. |
| — | DTE and delta window **(CONFIRM)** | Ideal: 60–90 DTE at Δ 0.10–0.20 (grade A). 45–59 DTE is allowed (grade B). Δ ≥ 0.25, ITM at entry, or an unstructured binary event before expiry is grade C. |
| — | Under-30-DTE shorts | Allowed since 2 Oct, but each one is tagged `OPP` (opportunistic) and needs a written exit. Not a breach on its own. |
| — | One opening ticket per name per day | Several fills of one order count as one ticket. A second opening ticket on the same name the same day is a pacing breach. |
| — | Sub-$5 biotech | Selling at Δ ≥ 0.40 is stock replacement: grade C unless the cash floor (Floor A/B) is at or above the strike. |
| — | No LEAPS shorts | No short puts expiring in 2028 or later. |
| — | Debit trades | Need 3:1 reward-to-risk at entry. No directional long calls or puts into a binary print. |

## Management rules (open positions)
| # | Rule | Trigger → required action |
|---|---|---|
| R2 | Velocity profit-take / dead collateral | Rest a 50% GTC buy-to-close at fill. A short at ≥ 80% captured, or marked ≤ $0.05, is **dead collateral**: close it this session. |
| R3 | ITM at ≤ 21 DTE | Close it, or roll 30–60 days for a net credit, **this session**. |
| R4 | Defense | Spot within 7% of strike, or Δ ≤ −0.30: defend (roll out/down for a credit, or close). **Never add new shorts on a tested name**: no new opening sale on a name that has a short line ITM, within 7%, or at Δ ≤ −0.30. |
| R5 | Concentration | Single name ≤ 10% NAV, counting held shares (amber ≥ 8%, red > 10%), using the method in `core-rules.md`. Biotech sleeve ≤ 25% NAV. |
| R6 | Held-lot freeze | No covered calls below cost basis, and no new short puts on a name whose held lot is underwater. |
| R7 | Held-lot plan | Every flagged held lot needs a written plan within 7 days of first being flagged. Cancel resting sell-to-open orders on underwater lots. After 7 days with no plan: `Rule 7 deadline passed`. |
| R8 | Short stock | Hard buy-to-cover stop at +15% from entry. No new short stock on sub-$5 clinical biotech. |
| R9 | **(CONFIRM: number unused in the sources)** | — |
| R10 | Lottery longs | Long options at ≤ $0.10 need a stated purpose (a hedge or parachute wing). Opening more than 5 per day is a breach. |

Rule numbers: past reports used `Rule 2` for both dead collateral and ITM, and `Rule 4` for both defense and pacing. The table above is the single numbering from now on **(CONFIRM)**.

## Book limits
- Dry-powder floor: cash plus cash-like holdings (SGOV, STRC) of 15–20% of NAV.
- Stress limit: the S1–S5 scenario loss should stay ≤ 20% NAV. A breach goes in the Bottom Line.
- Short Bench sizing: 2% of NAV at risk per idea.

## Terms used in the templates
- **HARVEST / HOLD:** HARVEST is a short at ≥ 50% captured or dead collateral (close it now). HOLD is below target; show it if it's within 10% of target.
- **Harvest board / Missed harvest:** the HARVEST rows with a buy-to-close price. Missed harvest = HARVEST rows still open at the close, with the $ total.
- **Tripwire top 5 / Tripwire Map:** the 5 short lines (Map: all lines) with the smallest cushion, showing strike, spot, cushion %, Δ and DTE.
- **Book Map:** every position grouped by theme, with % NAV from `core-rules.md`.
- **Book Triggers:** the full list of R2/R3/R4/R5/R6/R7/R8 hits from the full trigger scan.
- **Greeks line:** net delta $, theta $/day, vega $/vol point, from the book source.
- **Floor A / Floor B:** biotech cash floor per share (A: net cash ÷ fully diluted shares; B: A plus a risk-weighted pipeline value).
- **Parachute wing:** a cheap long put below a short put that caps the crash loss.
- **Cross-Asset Dashboard:** equity index futures or cash, yields (2Y/10Y/30Y), DXY, EUR/USD, USD/JPY, Brent, WTI (contract month), gold, BTC, IG/HY credit, VIX. Every row shows its clock time.
- **Strategic Themes Desk (CONFIRM: use `apply-market-report-standards` if installed):** four standing desks: (1) AI capex & semis, (2) energy & geopolitics, (3) rates, Fed & liquidity, (4) biotech & FDA. "Full" means all four; "brief" means only desks with new facts.
- **Three-layer unbundling:** split a geopolitical or commodity story into the financial/clearing layer, the physical supply layer and the route/logistics layer.
- **Source-or-N/A:** if no source gives the number, print N/A. **Anti-synthesis:** never combine numbers from different times or sources into one claim.
- **Short Bench lanes:** Hedge (index/sector ETFs that offset the book's main theme) and Alpha (single names). **Multiple-expansion gate:** an Alpha short needs a rally driven by multiple expansion, not by earnings or fundamentals. **Rolling Over scan:** large-caps that closed below their 50-day average with relative strength falling for 2 or more weeks.
- **No-tickers line:** `No tickers meet the underwriting gates today.` **None line:** `Active Position Movers (≥ 5%): None — all held positions within ±5% <window>.`
- **Scenario Map:** base, bull and bear cases with probabilities and the level that confirms each. **Indicators & Warning Signs:** the 3–5 observable signals that would change the posture. **Decision Gates:** if-then rules with levels.
- **Shkreli Read:** a blunt, numbers-first comment of at most 3 sentences under a table, tied to a book exposure or a trigger level. **Bracket tags:** `[Guidance ≠ Realized Cash Flow]`, `[Aggregate ≠ Breadth]`, `[Price ≠ Proof]`, `[Contracted ≠ Energized]`, `[Plan ≠ Realized Output]`, `[Trial Design ≠ Clinical Efficacy]`.
