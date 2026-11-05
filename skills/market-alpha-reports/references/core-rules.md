# Core rules (shared by every mode and both platforms)

The platform `SKILL.md` defines the **book source** (positions, cash, NAV, fills, orders, transfers) and the **quote source** (prices for held names). Layout is in `report-layout.md`, writing style in `style.md`, rules and terms in `playbook.md` (v2.5, R1–R12).

## 1. Clock and DST
- US daylight time runs from the second Sunday of March to the first Sunday of November: ET = ICT − 11h. Otherwise ET = ICT − 12h. Work it out from the session date; never hard-code a date.
- Times print as `HH:MM ET / HH:MM ICT`. Check US market holidays and half-days first.

## 2. Book (the anti-fabrication rules)
- Positions, quantities, strikes, expiries, cost basis, cash and NAV come **only** from the book source. Never from an earlier report, memory or a search result. Accounts: only those the book source returns.
- **Check figure:** the book source prints `CHECK: <N> short option lines · <M> stock lines · $<X> short-put notional`. Copy it exactly into the header and into A1. Count the short option lines you actually listed in A1; the count must equal N. If the book source has no CHECK line, compute it from the positions table and label it `CHECK (computed)`.
- **Feed-row rule:** every position mentioned in Sections 1–3 must exist in the book source's positions table with the same ticker, type, strike, expiry and quantity. In the Section 3 order table, copy that row into the **feed row** column. No matching row → the item is removed, not guessed.
- **Ticker discipline:** copy tickers exactly as the book source prints them. Never "correct" a ticker (MRVI is not MRVL).
- **Full trigger scan** over every short line and every stock line: R2, R3, R4, R5, R6, R7, R9, R10, R11, R12 (`playbook.md`). Print `Trigger scan: N lines checked · K hits` in A1. Every hit goes into Book Triggers, even if the book source's own summary didn't mention it.

## 3. Concentration (R5, v2.5 max-loss method)
Per underlying:
1. **Pair hedges:** match each short put with long puts on the same underlying at the same or lower strike that expire **on or after** the short. Highest long strike first, quantity for quantity. A pair counts its **width**: (short strike − long strike) × 100 × qty. A same-strike calendar counts 0.
2. **Unpaired short puts:** strike × 100 × qty. Long puts that expire **before** the short don't pair; flag `hedge expires first`.
3. **Shares:** long shares × spot. Short stock is measured under R11, not here.
4. **% NAV** = (1 + 2 + 3) ÷ NAV. Amber ≥ 8%, red > 10%. BIO/SC sleeve = sum over BIO/SC names, cap 25%.
5. Show **collateral tied up** (gross strike × 100 × qty before pairing) in its own column: hedged calendars can carry no risk and still lock up buying power, which is an R2 dead-collateral problem.

Worked examples (book of 4 Nov 2026, NAV ≈ $350K):
- **ACRS:** 233 short Nov $3P + 238 long Dec $3P → all pair at the same strike → R5 $0; collateral $69,900 → close the dead pennies (R2).
- **CMPX:** 251 short Nov $1P + 207 long Dec $1P → 44 unpaired × $100 = $4,400 = 1.3%.
- **CAPR:** 153 short Dec $2P; the Nov 27 longs expire first → 153 × $200 = $30,600 = 8.7%, amber.
- **META:** 570/420 put spread + 24 shares → width $15,000 + shares ≈ $15,100 = ≈ 8.6%, amber.

## 4. Repeat triggers
- Each Handoff carries `TRIGGERS:`. Still open → copy forward, count + 1. Cleared → mark `cleared` once, then drop.
- Count ≥ 3 → `REPEAT ×n`. Only count ≥ 3 may carry the label. Repeats lead Section 1's top items and Section 3's order table.
- `Repeat triggers: n` = open TRIGGERS lines with count ≥ 3 in **this** report's Handoff.

## 5. Number discipline
- **Source-or-N/A:** every market number needs a source page and the time it shows. None → `N/A`. Never a plausible, implied or derived value.
- **Every "why" needs a source.** If no source states the cause of a move: `cause unconfirmed`.
- **Dates on results:** a page dated before the session window is context, not a current mark. Gamma, IVR, Greeks and stress not refreshed this run get `STALE (as of …)`.
- **Published closes:** set by the first AH (Mon–Thu) or WKND (Fri) report for that session. Every later report takes "prior close" from the latest `PUBLISHED CLOSES`. A fresh source that disagrees: keep the published number, add `(source now shows X)`.
- **Continuity:** a benchmark moving > 2%, or a held name > 5%, vs the published close with no cited catalyst → search again. Still unresolved → benchmark: `UNVERIFIED`, out of Section 1. Held name: stays in, tagged `UNVERIFIED — check broker before acting`, never used as an order limit.
- **✓✓** only when two independent pages agree (stock ±0.5%, index ±0.1%, yield ±2 bp, FX ±0.1%, commodity ±0.5%, BTC ±0.5%, VIX ±0.2).
- **Calendar dates:** company IR, exchange, SEC or an official calendar of any age, or news ≤ 30 days old. Conflict → `date unconfirmed — check before expiry`.
- **One value per item:** the same number everywhere. Section 1 copies values from the section that calculated them; never recompute.
- **Claims about earlier reports** ("first time", "nobody caught it") only with evidence from the Handoff history.

## 6. Formulas (show inputs in the Appendix; use code execution)
- **Bands:** SPX daily 1σ = spot × (VIX1D ÷ 100) ÷ √252 (VIX if VIX1D missing); NDX uses VXN; weekly = × √(5/252); 2σ = 2 × 1σ.
- **Cushion (puts)** = (spot − strike) ÷ spot; negative = ITM. **% captured** = (credit − mark) ÷ credit.
- **Expected move** into an event = front ATM straddle ÷ spot, or a sourced implied move. `inside expected move` when cushion < expected move.
- **Collateral:** naked = strike × 100 × qty; spread max loss = width × 100 × qty − credit. **ROC:** naked = credit ÷ (strike × 100 × qty); spread = credit ÷ max loss; annualized × 365 ÷ DTE.
- **Assignment exposure** = Σ strike × 100 × qty over ITM shorts expiring in the next 10 trading days; compare with buying power (`× BP`).
- **Day P&L attribution:** per position, change in mark × 100 × qty (options) or change in price × shares (stock); rank the top 3 gains and losses; group by theme.
- **Stress line:** SPX −2% ≈ Σ(Δ × 100 × qty × spot × −2% × β) using the deltas in the book source; label `approx., delta-only`. If deltas are missing: N/A.
- **Journal analytics:** win rate, average win/loss, expectancy = win rate × avg win − (1 − win rate) × avg loss, average % captured, days held, rule adherence %, Cost of Indiscipline. Under 10 closed trades in a group: `n<10: no verdict`.

## 7. Benchmark & strategy scorecard
- **Benchmarks:** QQQ, SPY and the CBOE PUT index (S&P put-write). Use published closes; PUT index N/A if not sourced. Price return unless a total-return source is cited.
- **Book return is time-weighted:** daily r = (NAV_t − NAV_{t−1} − net deposits_t) ÷ NAV_{t−1}; period return = Π(1 + r) − 1. Net deposits come from the book source's transfers table; if transfers are missing, print `deposits UNVERIFIED` next to the return.
- **NAV history:** every AH and WKND Handoff carries `NAV:` lines (date · NAV · net deposits). WKND rebuilds week, month and YTD from them. Missing days → say which.
- **Also show:** max drawdown of the NAV series and the leverage line (short-put max loss ÷ NAV) so a return is never read without its risk.
- **Strategy scorecard (WKND, full; AH, one line):** group by journal setup tag (`playbook.md`). Per group: realized P&L, open P&L, win rate, average % captured, capital used, return on capital, verdict 🟢 keep / 🟡 fix / 🔴 stop with one plain sentence. Plus the **money map:** top 3 sources of profit and of loss this month by position.

## 8. Execution scorecard
| Mode | Tape grade | Execution grade |
|---|---|---|
| PRE | none. `Carry-in: N actions staged for today from <Ref>; overnight fills: …` | none |
| MID | PRE posture + prior AH/WKND next-session scenario vs cash prices since 09:30 ET | `X of Y PRE actions done` |
| AH | MID afternoon call + today's scenarios vs the close | `X of Y actions done today` |
| WKND | last weekend's posture vs the week | `X of Y actions done this week` |

HIT / PARTIAL / MISS / NOT TESTABLE; never HIT on a pre-market or after-hours mark. Execution matches Handoff ACTIONS against fills and working orders. The grade line goes in Section 1; the detail goes in A1.

## 9. War Room Handoff (A6, inside a ```text code block, one item per line)
```text
WAR ROOM HANDOFF — <Ref> — <session date> — Runner: <Claude|Gemini>
FEED: <book source name> as of <time>
CHECK: <N> short option lines · <M> stock lines · $<X> short-put notional
ACTIONS (for <session date>):
A1 · TICKER · contract · side · qty · limit · rule
TRIGGERS:
TICKER contract · rule · first flagged <date> · count n · open|cleared
PUBLISHED CLOSES (<session date>):   (AH and WKND)
SPX … · NDX … · DJI … · RUT … · QQQ … · SPY … · PUT … · 10Y … · DXY … · Brent … · WTI … · Gold … · BTC … · VIX …
held: TICKER $x · …
NAV:   (AH and WKND; last 10 sessions)
<date> · <NAV> · <net deposits>
HELD MOVERS (≥ 5%): … or None
```

## 10. Source notes and integrity
- A5 lists every number used in Sections 1–3 as `value · what · link · time on page`. A number without a line can't appear in Sections 1–3.
- Then the Integrity line from `integrity.md`.

## 11. Runner and save
**One runner per mode** (change here if Wilson changes the split):

| Mode | Runner |
|---|---|
| PRE | Claude |
| MID | Gemini |
| AH | Claude |
| WKND | Claude |

- The header shows the runner. A scheduled run for the other runner's mode stops: `<mode> belongs to <runner>; not written`. Run it only if Wilson asks directly in the conversation, and never replace a doc whose header shows the other runner.
- **Doc title:** exactly `YYYY-MM-DD — <Report name>` with an em dash (—). Search `Market Reports` for that exact title; one doc per mode per day; re-runs are `(vN)`.
- Native Docs headings, bold and tables. No markdown symbols inside table cells. The Handoff in a code block.
- Read back the first 1,000 characters; literal `#`, `**`, backslashes or backticks, or a doc under 2 KB, means the save failed. Plain-text fallback: CAPITAL headings, `Label: value` lines, table rows as ` · `-separated lines.
- Never leave an empty, duplicate, draft or test doc in `Market Reports`.

## 12. Trade Journal rows (AH and WKND)
- One row per fill. Columns in the sheet's order. **Dates as text** `YYYY-MM-DD` (prefix with an apostrophe if the tool would turn it into a number, e.g. `'2026-11-04`); never a serial number like 46329.
- Setup tag from `playbook.md` (LC · BIO-A · BIO-B · BIO-C · WHEEL-CC · SHORT-STOCK · LOTTO · SCALP · INDEX · OTHER).
- Rule check column: `Y` or `N (R#: reason)` using v2.5 numbers.
