# Core rules (shared by every mode and both platforms)

The platform `SKILL.md` defines two sources:
- **book source:** positions, cash, NAV, fills, orders and Greeks.
- **quote source:** prices for held names.

Everything else is defined here. Rule names and terms come from `playbook.md`.

## 1. Clock and DST
- US daylight time runs from the second Sunday of March to the first Sunday of November. During it, ET = ICT − 11h; otherwise ET = ICT − 12h. Work out which applies from the session date. Never hard-code a date.
- Print every time as `HH:MM ET / HH:MM ICT`. Check for US market holidays and half-days before writing.

## 2. Book
- Positions, quantities, strikes, cost basis, cash and NAV come only from the book source. Never take them from an earlier report, from memory or from a search result.
- Show only the accounts the book source returns. Never infer another account's positions.
- First line of Section 7: `Book feed: <source> (as of <time>) · NAV $X · short option lines N · stock lines M`.
- **Full trigger scan:** check every short line against R2 (velocity, ≥ 80% captured or mark ≤ $0.05, no working buy-to-close), R3 (ITM at ≤ 21 DTE; OPP tags), R4 (LC/MC: within 7% of strike or Δ ≤ −0.30; BIO/SC: Floor B rule; adds in defense; one ticket per name) and R6 (earnings before expiry). Check every name against R5, every held lot against R7, every short stock line against R8, and every opening fill against R9. Every hit goes into Book Triggers, even if the book source's own summary doesn't mention it. Print `Trigger scan: N lines checked · K hits`.

## 3. Concentration (R5): the official test plus a net-of-hedge column
**R5 test (official, matches the WarRoom PDF):** per name, % NAV = (short-put strike × 100 × qty + shares held × spot) ÷ NAV. Same-name long puts are **not netted**. Amber ≥ 8%, red > 10%. BIO/SC sleeve = BIO/SC put notional + BIO/SC shares, cap 25% of NAV. This number decides R5 breaches.

**Net-of-hedge column (information only, never used for R5):** shows the risk that remains after hedges, so the fix can be sized:
1. Pair each short put with long puts on the same underlying, at the same or a lower strike, that expire **on or after** the short put. Take the highest long strike first, quantity for quantity. Exposure = (short strike − long strike) × 100 × paired qty. A same-strike calendar nets to 0.
2. Unpaired short puts count at strike × 100 × qty. Long puts that expire **before** the short put don't pair; flag them `hedge expires first`.
3. Add shares × spot. Short calls covered by shares add nothing. A naked short call is flagged `unlimited`.

Worked examples (book of late Oct 2026, NAV ≈ $343K):
- **ACRS:** 233 short Nov $3P (+ 237 long Dec $3P) → R5 = $69,900 = 20.4% NAV, **red**. Net of hedge: $0, because the calendar covers it. The cheapest cure is closing the dead pennies (R2) for about $0.05.
- **CMPX:** 251 short Nov $1P (+ 207 long Dec $1P) → R5 = $25,100 = 7.3%, below amber. Net of hedge: 44 × $100 = $4,400 = 1.3%.
- **CAPR:** 283 short Dec $2P (+ long Nov 27 $2P) → R5 = $56,600 = 16.5%, **red**. Net of hedge: the same, `hedge expires first`.

## 4. Repeat triggers
- Each Handoff carries `TRIGGERS:` (see §9). When a trigger is still open, copy it forward and add 1 to its count. When it's cleared, mark it `cleared` once, then drop it.
- A count ≥ 3 makes it a repeat. **Only** a trigger with count ≥ 3 may carry the `REPEAT` label; a count of 1–2 is never labelled REPEAT.
- **Bottom Line order:** the `Action:` list starts with REPEAT triggers (highest count first, then by risk removed), then the rest by risk removed. If there are more than 5 repeats, the 5 with the highest risk come first and the others stay in the full order table.
- `Repeat triggers: n` in the Scorecard = the number of `TRIGGERS:` lines in **this** report's Handoff with count ≥ 3 and status open. Count them from the Handoff you actually wrote.

## 5. Number discipline
- **Source-or-N/A:** every market number needs a source page and the time shown on that page. If none is found, print `N/A`. Never fill a gap with a plausible, "implied" or derived value (for example "SPX ~7,618 implied").
- **Dates on results:** a page dated before the session window is context, not a current mark. Tag it `(as of <date>)`. Gamma levels, IVR, Greeks and stress results not refreshed this run get `STALE (as of …)`.
- **Published closes:** a session's close is set by the first AH (Mon–Thu) or WKND (Fri) report for that session and listed in its `PUBLISHED CLOSES:`. Every later report takes "prior close" from the **latest** AH/WKND Handoff, whatever its own prior report was. If a fresh source disagrees, keep the published number and add `(source now shows X)`.
- **Continuity check:**
  - **Benchmarks** (index, FX, commodity, BTC) moving more than 2% versus the published close with no cited catalyst: search again. If it still doesn't reconcile, print `UNVERIFIED` and leave it out of Key levels and the bands.
  - **Held names** moving more than 5% with no cited catalyst: re-check against the quote source. If it still doesn't reconcile, **keep it** in the Bottom Line and triggers as `UNVERIFIED — check broker before acting`. Never set an order limit from an unverified price.
- **✓✓** only when two independent pages agree: stock ±0.5%, index/ETF ±0.1%, yield ±2 bp, FX ±0.1%, commodity ±0.5%, BTC ±0.5%, VIX ±0.2 pt. Two pages fed by the same syndicated feed count as one. Otherwise use `✓`.
- **Links:** each link opens the page that shows the number. Never link a generic quote page for a pre-market or after-hours mark it doesn't display, and never link an article about something else.
- **Calendar dates** (earnings, PDUFA, data releases): accept company investor relations, the exchange or SEC, or an official calendar of any age, or news ≤ 30 days old. If sources conflict, print `date unconfirmed — check before expiry`.
- **One value per item:** a ticker has the same price, strike and quantity in every section. Section 7 is the reference. Every number in the Bottom Line and Key Judgments (bands, % NAV, counts, closes) must equal the number in the section where it is calculated. Write the section first, then copy the value into the Bottom Line; never recompute it there.
- **Claims about earlier reports** ("first time", "no prior report caught it", "new") are allowed only if the TRIGGERS history in the previous Handoff, or a report you actually opened this run, shows it. Otherwise leave the claim out.
- **Top event coverage:** if the day's top event is an earnings release or a single stock, that stock's close, extended-hours mark and guidance must be pulled, or printed N/A with the reason. Every Mag 7 row needs a close and a day change.

## 6. Formulas (show inputs; use code execution where available)
- **Bands:**
  - SPX daily 1σ = spot × (VIX1D ÷ 100) ÷ √252 (use VIX if VIX1D is missing).
  - NDX daily 1σ = spot × (VXN ÷ 100) ÷ √252, labelled `30-day IV basis`.
  - Weekly 1σ = spot × (VIX or VXN ÷ 100) × √(5/252).
  - 2σ = 2 × 1σ. Centre the bands on the stated reference spot (the published close unless the text says otherwise).
- **Cushion % (puts)** = (spot − strike) ÷ spot; negative means ITM. **Calls:** (strike − spot) ÷ spot.
- **% captured** = (open credit − mark) ÷ open credit.
- **Collateral:** naked = strike × 100 × qty; spread max loss = width × 100 × qty − credit.
- **ROC:** naked = credit ÷ (strike × 100 × qty); spread = credit ÷ max loss. Annualized = ROC × 365 ÷ DTE at entry.
- **Breakeven (put)** = strike − credit per share.
- **Journal (WKND, AH):**
  - Win rate = winners ÷ closed trades. Average win, average loss.
  - Expectancy = win rate × average win − (1 − win rate) × average loss.
  - Average % captured on winners. Average days held.
  - Rule adherence % = closed trades with no rule broken ÷ closed trades.
  - Cost of Indiscipline = sum of P&L on trades that broke a rule, plus open marks on rule-breaking positions opened this period.
  - Under 10 closed trades in a setup: `n<10: no verdict`.

## 7. Scorecard: each report grades what can actually be tested
| Mode | Tape grade | Execution grade |
|---|---|---|
| PRE | none (the session hasn't opened). Print `Carry-in: N actions staged for today from <Ref>; overnight fills: <list or none>` | none |
| MID | PRE posture, levels and Scenario Map, **and** the prior AH/WKND next-session Scenario Map, against cash-session prices since 09:30 ET | `Execution: X of Y PRE actions done` |
| AH | the MID afternoon call and today's Scenario Maps against the close | `Execution: X of Y actions done today` (PRE + MID) |
| WKND | last weekend's posture and Scenario Map against the week | `Execution: X of Y actions done this week` |

- Tape grades: `HIT | PARTIAL | MISS | NOT TESTABLE`. A pre-market or after-hours mark never counts as a HIT.
- Execution matches the Handoff `ACTIONS:` ids against the fills and working orders in the book source. Name each missed action.
- Every mode also prints `Repeat triggers: n`.

## 8. Length and brevity
- **Word caps** (excluding the verbatim feed): PRE 3,500 · MID 3,000 · AH 4,000 · WKND 6,000. Over budget, trim tables first, then Reads. Never cut Book Triggers or the order table.
- **Bottom Line:** keep Posture / Book / Key levels / Top event / Action. `Action:` holds 5 orders at most, ranked by risk removed (REPEAT items first). Format each as `ticker · contract · side · qty · limit · rule`. The full order list goes in the mode's checklist or gameplan section.
- **Shkreli Read:** 3 sentences at most, naming a book exposure or a trigger level; otherwise leave it out.
- **Unchanged section:** one line, `No change since <Ref> — <key number>`.
- **Tables:** 10 rows at most. **Exempt:** the 11-sector leaderboard, the Cross-Asset Dashboard, the WKND Tripwire Map, staged order tables and Book Triggers. Held-name tables otherwise show only rows that are triggered or have moved ±5%, plus a one-line summary of the rest.
- **Formatting:** no backticks around numbers, tickers or times. Bold only labels and the Bottom Line. Link a ticker on its first mention only. No decorative emoji. State each number once and refer back with `(see §7)`.
- **Tables:** no `**`, `*`, backticks or links inside table cells. Google Docs bolds the header row by itself, so markdown inside cells shows as literal symbols. Put emphasis in the text around the table instead.
- **Line-by-line blocks** (the War Room Handoff, any verbatim feed text): put them inside a fenced code block (three backticks plus `text`). Single line breaks collapse into one paragraph outside a code block (tested 3 Nov 2026).

## 9. War Room Handoff (closes every report; the next report reads it)
```text
WAR ROOM HANDOFF — <Ref> — <session date>
FEED: <book source> as of <time>
ACTIONS (for <session date>):
A1 · TICKER · contract · side · qty · limit · rule
A2 · TICKER · contract · side · qty · limit · rule
TRIGGERS:
TICKER contract · rule · first flagged <date> · count n · open
TICKER contract · rule · first flagged <date> · count n · cleared
PUBLISHED CLOSES (<session date>):   (AH and WKND only)
SPX … · NDX … · DJI … · RUT … · 10Y … · DXY … · Brent … · WTI … · Gold … · BTC … · VIX …
held: TICKER $x · TICKER $x · …
HELD MOVERS (≥ 5%): … or None
```
Write it inside a fenced code block (` ```text ` … ` ``` `), one item per line, so the line breaks survive the conversion to a Google Doc. Each ACTIONS item and each TRIGGERS item gets its own line.

## 10. Source Notes and Integrity
- **Provenance:** Works Cited must list every number used in the Bottom Line and Key Judgments as `value · what it is · source link · time shown on page`. Anything without a line here can't appear in those two sections.
- Then print the Integrity line from `integrity.md`.

## 11. Save
**One runner per mode.** Each mode has exactly one runner. Change this table if Wilson changes the split:

| Mode | Runner | Why |
|---|---|---|
| PRE | Claude | sets the day's orders; needs the live book and pre-market quotes |
| MID | Gemini | refresh of an existing plan; reads the MID WarRoom PDF |
| AH | Claude | publishes the closes every later report reuses |
| WKND | Claude | stress test, journal and repeat-trigger history |

- The second header line of every report includes `Runner: Claude` or `Runner: Gemini`.
- If you are asked to run a mode that belongs to the other runner, run it only if the user explicitly asked in this conversation. A scheduled run of the wrong runner stops and replies `<mode> belongs to <runner>; not written`.
- Never replace or trash a doc whose header shows the other runner. If one already exists for the same mode and day, stop and reply with its link.

1. Search `Market Reports` for the exact doc title. If it exists, update it in place and set the header to `Updated HH:MM ET / HH:MM ICT (vN)`. Never create a second doc with a time suffix.
2. Write with native Docs headings, bold and tables.
3. Read back the first 1,000 characters. If you see literal `#`, `**`, backslashes or backticks, or the doc is under 2 KB, the save failed.
4. **Fallback** when the save tool only takes plain text: no markdown symbols at all. Put section headings in CAPITALS on their own line, write label lines as `Label: value`, and write tables one row per line with ` · ` between cells. Verify again.
5. Never leave an empty, duplicate or test doc in `Market Reports`.
