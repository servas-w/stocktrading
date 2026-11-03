# Playbook v2 reference (rules, gates and terms)

This is the only place the reports take rule definitions from. The rule numbers follow the official Playbook v2 numbering in the Stock Trading project instructions (as used by `daily-portfolio-audit`). If the project instructions change, update this file. Cite a rule by **number and name**, for example `R3 Time`. LC/MC rules apply to large- and mid-caps; BIO/SC rules apply to biotech and small-caps. Each name's class comes from the CLASS column in the WarRoom PDF appendix. If a name is missing from it, apply the LC rules and tag it `class? UNVERIFIED`.

Confirmed by Wilson on 3 Nov 2026: a 60–90 DTE entry window for LC/MC, and the defaults below.

## The rules
| # | Rule | Gate → required action |
|---|---|---|
| R1 | IV gate | Sell naked premium only when IV Rank ≥ 50. Defined-risk spreads are exempt (spread exception). If IVR can't be sourced, print `IVR unverified`. |
| R2 | Profit take | Rest a 50% GTC buy-to-close at fill. **Velocity:** % captured ≥ 2 × % of time elapsed **and** ≥ 25% → take the profit. **Dead pennies:** mark ≤ $0.05 or ≥ 80% captured, still open → close this session. A short with no working buy-to-close is flagged. |
| R3 | Time | ITM short at ≤ 21 DTE → act within 1 session (close, or roll 30–60 days for a net credit); `2nd session` if it was already flagged. Shorts opened under 30 DTE are allowed but tagged **OPP**. Non-OPP LC/MC shorts at ≤ 21 DTE and under 80% captured → close or roll. |
| R4 | Defense + one ticket | **LC/MC:** Δ ≤ −0.30 or spot within 7% of strike → defend. **BIO/SC:** strike above Floor B with spot within 15% of strike → defend (if Floor B is missing or stale, flag at 15% with `Floor B UNVERIFIED`). **No adding in defense:** no opening fill or working sell-to-open on a triggered name. **One opening ticket per name per session.** |
| R5 | Concentration | Per name: short-put strike × 100 × qty **+ shares held × spot**, ÷ NAV ≤ 10% (amber ≥ 8%, red > 10%). Same-name long puts are shown but **not netted**. BIO/SC sleeve (BIO/SC put notional + shares) ≤ 25% of NAV. |
| R6 | Earnings | Check whether earnings land before expiry for every short. If the date isn't sourced: `earnings date UNVERIFIED — check before expiry`. |
| R7 | Held lots | **Underwater thresholds:** lots more than 15% below cost (BIO/SC) or 25% (LC/MC) → no new puts and no working sell-to-open on that name. Covered calls only at or above basis. Lots more than 25% below cost need a written plan (exit level, or calls at/above basis) within 7 days of first being flagged, otherwise `Rule 7 deadline passed`. Never dump assigned shares within 5 sessions of assignment. A BIO/SC short in expiry week with strike above Floor B is flagged. |
| R8 | Short stock | Hard buy-to-cover stop at +15% from entry. No new short stock on sub-$5 clinical biotech. Short stock over 2% of NAV is flagged. |
| R9 | Style (entry window) | **LC/MC: 60–90 DTE, \|Δ\| ≤ 0.20 at entry. BIO/SC: 30–90 DTE.** OPP shorts are exempt from the window. Scalp cap: OPP shorts at ≤ 7 DTE plus other scalps ≤ 1% of NAV at risk (at risk per put = (strike − credit) × 100 × qty, or spread width − credit). |
| R10 | Lottery longs | Long options at ≤ $0.10 need a stated purpose (a hedge or parachute wing). Opening more than 5 per day is a breach. |

## Other entry standards (not numbered)
- **Grades:** A = fits every rule. B = an event before expiry, or DTE outside the R9 window but ≥ 30. C = Δ ≥ 0.25, ITM at entry, an unstructured binary, or a sub-$5 biotech sold at Δ ≥ 0.40 (stock replacement) without the cash floor at or above the strike.
- No short puts expiring in 2028 or later (no LEAPS shorts).
- Debit trades need 3:1 reward-to-risk at entry. No directional long calls or puts into a binary print.

## Book limits
- Dry-powder floor: cash plus cash-like holdings (SGOV, STRC) of 15–20% of NAV.
- Stress limit: the S1–S5 scenario loss should stay ≤ 20% NAV. A breach goes in the Bottom Line.
- Short Bench sizing: 2% of NAV at risk per idea.

## Terms used in the templates
- **HARVEST / HOLD:** HARVEST is a short that meets R2 velocity, is ≥ 50% captured, or is a dead penny (close it now). HOLD is below target; show it if it's within 10% of target.
- **Harvest board / Missed harvest:** the HARVEST rows with a buy-to-close price. Missed harvest = HARVEST rows still open at the close, with the $ total.
- **Tripwire top 5 / Tripwire Map:** the 5 short lines (Map: all lines) with the smallest cushion, showing strike, spot, cushion %, Δ and DTE.
- **Book Map:** every position grouped by theme, with R5 % NAV (gross) and the net-of-hedge column from `core-rules.md`.
- **Book Triggers:** the full list of R2/R3/R4/R5/R6/R7/R8/R9 hits from the full trigger scan.
- **Greeks line:** net delta $, theta $/day, vega $/vol point, from the book source.
- **Floor A / Floor B:** biotech cash floor per share (A: net cash ÷ fully diluted shares; B: A plus a risk-weighted pipeline value).
- **Parachute wing:** a cheap long put below a short put that caps the crash loss.
- **Cross-Asset Dashboard:** equity index futures or cash, yields (2Y/10Y/30Y), DXY, EUR/USD, USD/JPY, Brent, WTI (contract month), gold, BTC, IG/HY credit, VIX. Every row shows its clock time.
- **Strategic Themes Desk:** four standing desks: (1) AI capex & semis, (2) energy & geopolitics, (3) rates, Fed & liquidity, (4) biotech & FDA. "Full" means all four; "brief" means only desks with new facts.
- **Three-layer unbundling:** split a geopolitical or commodity story into the financial/clearing layer, the physical supply layer and the route/logistics layer.
- **Source-or-N/A:** if no source gives the number, print N/A. **Anti-synthesis:** never combine numbers from different times or sources into one claim.
- **Short Bench lanes:** Hedge (index/sector ETFs that offset the book's main theme) and Alpha (single names). **Multiple-expansion gate:** an Alpha short needs a rally driven by multiple expansion, not by earnings or fundamentals. **Rolling Over scan:** large-caps that closed below their 50-day average with relative strength falling for 2 or more weeks.
- **No-tickers line:** `No tickers meet the underwriting gates today.` **None line:** `Active Position Movers (≥ 5%): None — all held positions within ±5% <window>.`
- **Scenario Map:** base, bull and bear cases with probabilities and the level that confirms each. **Indicators & Warning Signs:** the 3–5 observable signals that would change the posture. **Decision Gates:** if-then rules with levels.
- **Shkreli Read:** a blunt, numbers-first comment of at most 3 sentences under a table, tied to a book exposure or a trigger level. **Bracket tags:** `[Guidance ≠ Realized Cash Flow]`, `[Aggregate ≠ Breadth]`, `[Price ≠ Proof]`, `[Contracted ≠ Energized]`, `[Plan ≠ Realized Output]`, `[Trial Design ≠ Clinical Efficacy]`.
