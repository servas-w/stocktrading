---
name: "daily-portfolio-audit"
description: "Lean twice-daily audit (midday during the US session, and after the close) of Robinhood trades, the open option book and held stock lots, written as a 1-2 page PDF plus a data appendix, uploaded to the Google Drive folder Robinhood Portfolio Review for Gemini's daily stock report. Optional third run: a pre-market snapshot. Use when the user says audit my portfolio, audit, midday audit, daily audit, pre-market snapshot, run daily war room audit, run daily audit -> Drive PDF, yesterday's trades audit or similar. Audits against the War Room Playbook v2.5: velocity profit-take, OPP tagging for shorts under 30 DTE, ITM-at-21-DTE action, defense at delta -0.30 or spot within 7% of strike, one opening ticket per name per day, 10% NAV cap counting held shares, held-lot discipline, IV gate. The EOD run also reviews every trade closed that session (realized P&L, velocity, return on risk, combined roll scoring, process grade) and comments on each in chat. Not for underwriting new tickers."
---

# Daily Portfolio Audit (lean, Playbook v2.5)

Goal: the War Room's compliance check at about a third of the compute. Pull only what the rules need, never full order history. The rule numbers below are Playbook v2.5 (R1–R12, confirmed by Wilson 5 Nov 2026; full text in the market-alpha-reports skill's `references/playbook.md`), extending the v2 rules in the Stock Trading project instructions (the canonical copy). When this file disagrees with them, the project instructions win; flag this file for an update.

## Rules
- **Read-only.** Never place, cancel or replace orders. Stage tickets only: `STAGE: BTC <qty> <TICKER> <EXP> <STRIKE>P @ <= $x GTC - reason (Rule #)` or `STAGE: CANCEL STO ... - reason (Rule #)`.
- **Robinhood MCP only** for data. No Gmail/Drive search for confirmations.
- **Mask accounts:** main book ••6081 (account_number 5QR66081). Shadow Delta ••1686 was empty on 2026-09-29; skip it unless the user asks.
- **Budget: ≤ 12 data calls** (≤ 14 with the overflow quote calls in 7 and 8; EOD may add call 13, plus 13b on an expiration day, so ≤ 16). The Drive upload doesn't count. Hitting it = stop and mark the rest UNVERIFIED.
- **One run per chat.** Start a new chat for every run (two per day).

## Two runs a day, plus an optional pre-market snapshot (pick the mode from the Da Nang clock)
The user is in Da Nang (UTC+7) and runs this twice a day. Label every file by the **US session date** it covers, so the names sort in time order and Gemini's "most recent file" is always the latest look at the book.

| Run | Da Nang time | US time | Mode | Covers | File suffix |
|---|---|---|---|---|---|
| Midday | ~00:00 (23:00 in US daylight time) | 12:00 ET year-round, so the file is in Drive before Gemini's MID report at 12:30 ET | **MID** | today's session so far | `_1-MID` |
| Morning | ~09:00 | after the close | **EOD** | the full previous session (Monday covers Friday) | `_2-EOD` |
| Evening (optional) | ~20:45 (19:45 in US daylight time) | 08:45 ET | **PRE** | pre-market marks for today's session | `_0-PRE` |

- EOD: `SESSION_START` = 00:00 ET on the session date: session date + `T04:00:00Z` in US daylight time, `T05:00:00Z` in standard time.
- MID: `SESSION_START` = session date + `T13:30:00Z` (09:30 ET open; `T14:30:00Z` after DST ends). Marks are live, not closing. Add an "Afternoon watch" line: shorts within 7% of strike or at Δ ≤ -0.30, ITM shorts ≤ 21 DTE, and working orders still unfilled.
- PRE: only calls 1, 4, 6, 7 and 8 (plus overflow). The PDF is the Snapshot card and the Appendix, with no breach commentary. It exists so the Gemini pre-market report has real pre-market quotes for held names.
- Order within a session: PRE (optional), then MID, then EOD about 9 hours later. EOD leads with what changed since that session's MID file; don't repeat its commentary.

## Tool loading (`limit` ≤ 3; search by bare tool name, since server prefixes vary by install)
- `tool_search "get_portfolio get_equity_positions"`
- `tool_search "get_option_positions get_option_orders"`
- `tool_search "get_option_quotes get_equity_quotes"`
- `tool_search "get_pnl_trade_history get_equity_orders"`
- `tool_search "get_option_instruments get_equity_fundamentals"`
- `tool_search "get_banking_transactions"` (EOD only)
- `tool_search "Google Drive create_file upload"`, then call **whichever `create_file` the search returns** (the prefix differs by install; never type a full tool name from memory)

## Data calls (≤ 12; two parallel turns, then at EOD a third; calls 10, 13 and 13b at EOD only)
**Turn 1 (parallel, 6):**
1. `get_portfolio` (5QR66081) → NAV, cash, buying power.
2. `get_option_orders` (5QR66081, `state: "filled"`, **`updated_at_gte: SESSION_START`**) → every option order that filled this session, **including GTCs created on earlier days** (verified 18 Nov 2026: a GTC BTC created 16 Nov showed up when it filled on 18 Nov). Keep only executions with `trade_date` = session date. Each leg carries `option_id`, `strike_price`, `expiration_date`, `option_type`, `side` and `position_effect` (open/close); each order carries `opening_strategy` / `closing_strategy`, `time_in_force` and `created_at`. A filled order with `created_at` < SESSION_START = `GTC fill, order created earlier`. **Never pull all states**: cancelled orders were ~80% of the tokens in the first run.
3. `get_option_orders` (5QR66081, `state: "confirmed"`, `created_at_gte: SESSION_START`) → new working orders (GTCs, resting STOs).
4. `get_option_positions` (5QR66081, `nonzero: true`) → book. `pending_buy_quantity` > 0 on a short = a working BTC exists. `opened_at` ≥ SESSION_START = a position opened this session (the field is `opened_at`; positions have no `created_at`).
5. `get_pnl_trade_history` (5QR66081, `span: "week"`; **`span: "month"` at EOD**, for the month-to-date close stats) → realized gain per closing trade. **Rows carry only `timestamp`, `symbol` (the underlying), `side`, `quantity`, `price` and `realized_gain`: no strike, expiry, option type or asset class** (verified 18 Nov 2026). Option rows price per contract (`-125` = $1.25); stock rows price per share; a negative-quantity `buy` at a stock-level price is a short-stock cover; a multi-leg close is one row with an empty `side` and the net price. Tie each row to its order by symbol + timestamp (within 2 s of the order's last execution) + |qty|; a row with no option order behind it is a stock trade (call 9). At EOD keep only rows with `timestamp` ≥ the 1st of the month for the stats; if `next_cursor` is not empty, fetch **one** more page at most and, if it's still not empty, label the stats `MTD (partial, from <oldest date>)`.
6. `get_equity_positions` (5QR66081) → held lots (quantity, average cost; negative quantity = short stock).

**Turn 2 (parallel, 5; up to 7 at EOD):**
7. `get_option_quotes` → every open short (velocity needs each mark) plus the session's fills (at EOD this includes every contract closed this session, for the hindsight mark); max 20 ids per call. If there are more than 20 shorts, make **one more call** for the next 20 (≤ 30 DTE first, then largest notional). Anything still unquoted is marked UNVERIFIED and printed as `n/q` in the Appendix.
8. `get_equity_quotes` → underlyings of every open short (defense 7% test, ITM test) plus every held lot (unrealized), plus at EOD the underlying of every contract closed this session (whether a defense trigger was hit when it closed); max 20 symbols per call, open-short underlyings first, then the largest lots. If there are more than 20 symbols, make **one more call** for the next 20; print the rest as `n/q`.
9. `get_equity_orders` (5QR66081, `state: "filled"`, `created_at_gte: SESSION_START`) → stock buys and sells this session (assigned shares dumped, adds to underwater lots, short stock).
10. **EOD only:** `get_banking_transactions` (last 7 days) → rows that move money between the Robinhood bank account and the brokerage, for the reports' QQQ benchmark (A8). The connector can't see external deposits or wires straight into the brokerage, so A8 always ends with `external deposits not visible to the connector`. Also add **QQQ and SPY** to call 8's symbol list.
11. `get_option_instruments` (ids of every option position from call 4, batched) → the **exact** strike, expiry and type of every line. Never print a strike worked out from a quote when this call returned it.
12. `get_equity_fundamentals` (every A3/A4 underlying missing from `universe.md`) → market cap and sector for the class auto rule.
**Turn 3 (EOD only, after turn 1; parallel, 1–2):**
13. `get_option_positions` (5QR66081, **`option_ids`** = every `option_id` on a close leg in call 2; leave out `nonzero`) → the closed positions, which keep **`average_price`** (opening credit × 100, negative for a short) and **`opened_at`** (verified 18 Nov 2026 on three closed shorts). This gives the credit and opening date for velocity and return on risk. Skip it if nothing closed.
13b. **Expiration days only** (the session date is an option expiry, normally a Friday): `get_option_positions` (5QR66081, `expiration_date: SESSION_DATE`, leave out `nonzero`) → every contract that expired today. Quantity 0 with no close leg in call 2 = **expired or assigned**; a non-zero `pending_expiration_quantity` or `pending_assignment_quantity` = not processed yet, print `pending`.

**Fill reconciliation:** session fills = call 2 (it already includes GTCs created earlier). Use call 5 only for realized gain, tied to orders as described under call 5. New positions from call 4 with no matching opening fill = a resting STO created earlier that filled this session: list them as opening fills too.

**Field notes:**
- **Tickers exactly as the API returns them.** Never normalize or "correct" a symbol (MRVI is not MRVL; the 4 Nov PDF printed MRVI as MRVL and showed a false −$18,193 loss).
- Strike, expiry and type come from call 11. Only if that call fails for a line: put = break_even + mark, call = break_even − mark, rounded to the nearest listed increment, and the row is tagged `strike inferred` (the reports never stage an order on it). Greeks null/zero on an ITM contract → treat Δ as −1.0 (puts) and say so.
- Credit per share = |position `average_price`| ÷ `trade_value_multiplier` (100). Sanity-check it against the mark; if the ratio is implausible (> 50× or < 0.02×), mark velocity UNVERIFIED for that short rather than guess.
- % captured = (credit − mark) ÷ credit. % of DTE elapsed = (today − position `opened_at`) ÷ (expiry − position `opened_at`).
- **Class per name** comes from the project file `universe.md`: BIO/SC (biotech, small-cap) or LC/MC (large-cap, mid-cap). BIO names get the biotech rules (Rules 4, 5 sleeve, 7 at 15%); LC/MC get the large-cap rules (Rule 7 at 25%). Floor B comes from `floors.md` (stale after 90 days → UNVERIFIED). A name missing from universe.md (or universe.md unreachable, as in cloud runs) → **auto rule** from call 12: market cap < $2B, or a biotech/pharma name < $10B → BIO/SC; otherwise LC/MC; tag `class (auto)` and print the line to add (`TICKER | class`). No market cap either → LC rules, `class? UNVERIFIED`.
- **OPP** = a short opened with < 30 DTE. It's allowed (Rule 3) but tagged OPP on every table. OPP is exempt from the Rule 9 DTE window, still answers to Rules 1, 4, 5 and 7, and an OPP at ≤ 7 DTE counts toward the Rule 9 scalp cap (≤ 1% of NAV at risk across all scalps). At-risk per OPP put = (strike − credit) × 100 × qty, or the spread width minus credit for a spread.

## Checks (Playbook v2.5 rule numbers; report in this priority order)
| Priority | Rule | Check | Breach |
|---|---|---|---|
| 1 | **3 Time** | ITM short at ≤ 21 DTE (put: spot < strike) | Any; "act within 1 session" (if the MID file already flagged it, EOD says "2nd session") |
| 2 | **4 Defense** | LC/MC short put: Δ ≤ −0.30 **or** spot within 7% of strike. BIO/SC: strike > Floor B (floors.md) with spot within 15% of strike; Floor B missing or stale → spot within 15% flagged, "Floor B UNVERIFIED" | Trigger hit; plus any opening fill or working STO this session on a triggered name ("add in defense") |
| 3 | **5 Concentration** | Per name, v2.5 max loss: defined-risk spread = width × 100 × qty (pair a short put with a same-name long put at a lower or equal strike expiring on or after it); unpaired short put = strike × 100 × qty; **+ long shares × spot**; ÷ NAV. If a long leg's strike or expiry isn't known, count the short gross and mark `pairing UNVERIFIED` | Name > 10% of NAV; BIO sleeve (sum of the same max-loss figure over BIO/SC names) > 25% |
| 4 | **7 Held lots** | Each lot's spot vs average cost, threshold by universe.md class | Opening fill or working STO on a name > 15% under cost (BIO/SC) or > 25% (LC/MC); lots > 25% under cost listed with "plan? (written exit level or calls at/above basis)"; a BIO/SC short at or below expiry week with strike > Floor B (no assignment above Floor B); stock sold this session on a lot acquired ≤ 5 sessions ago (assigned shares dumped) if the acquisition date is visible, else UNVERIFIED |
| 5 | **2 Profit take** | Each short with a mark | No working BTC (`pending_buy_quantity` 0); velocity met (% captured ≥ 2 × % elapsed and ≥ 25%) but still open; mark ≤ $0.05 or ≥ 80% captured still open (dead pennies) |
| 6 | **3 Time / 9 Style** | Every opening fill and working STO | < 30 DTE → tag **OPP** (not a breach) and check it against Rules 1/4/5/7 like any short. Non-OPP: LC/MC outside 60–90 DTE (confirmed by Wilson 3 Nov 2026) or \|Δ\| > 0.20 at entry; BIO/SC outside 30–90 DTE. Scalp cap: OPP at ≤ 7 DTE plus other scalps > 1% of NAV at risk. Open non-OPP LC/MC shorts ≤ 21 DTE under 80% captured (close or roll) |
| 7 | **4 One ticket** | Opening orders (fills + working) per underlying this session | > 1 opening ticket on a name |
| 8 | **11 Short stock** | Negative equity quantity, entry vs spot | Spot ≥ entry × 1.15 (stop hit); any short line > 2% of NAV; new short into earnings or on sub-$5 clinical biotech |
| 9 | **12 Dry powder** | Cash + SGOV + STRC vs NAV | Below 15% of NAV |
| 10 | **10 Lottery / 8 Structure** | Long options ≤ $0.10 opened this session, each tagged WING (hedges a short on the same name) or LOTTO; long puts whose paired short is gone (orphan wings); any short expiring 2028+ | > 3 LOTTO opening tickets; any same-session open and close of a contract ≤ $0.20 (penny scalping); orphan wing held > 5 sessions; any LEAPS short or working LEAPS STO. Monthly LOTTO spend (≤ 0.25% NAV) is checked by the weekend report |
| — | **1 IV gate / 6 Earnings** | Not pulled in lean mode. R6 note: BIO/SC Mode A/B premium into a catalyst is allowed | UNVERIFIED |

## Close review (EOD only)
MID and PRE runs skip this section: MID lists closes in the fills table only. EOD reviews **every close in the session**, using data already pulled (calls 2, 4, 5, 6, 7, 8, 9, 11) plus calls 13 and 13b.

**1. Find, group and classify each close.** A close is an option leg with `position_effect: close` in call 2, a contract from call 13b that went to zero with no close leg, or a stock row in call 5 / call 9. **Group** every close of the same contract (or the same stock line) in the session into one entry: three 1-lot sells of the same put are one close of 3.
| Type | How to detect it |
|---|---|
| **Profit-take** | Short closed (`closing_strategy` short_put / short_call / a credit spread) below the opening credit. Tag `GTC` if the order's `created_at` < SESSION_START |
| **Loss close** | Short closed at or above the opening credit |
| **Roll** | A short closed **and** a short of the same option type opened on the same underlying in the same session, with the new expiry on or after the old one: either one multi-leg order (a close leg and an open leg) or two tickets. Score both legs as **one combined trade**. Long-leg churn (long closed, long reopened) and new structures on the same name (e.g. a calendar) are **not** rolls |
| **Dead penny** | Short closed at ≤ $0.05 |
| **Expired** | From call 13b: quantity 0 and no close leg. Realized = full credit (short) or full debit lost (long) |
| **Assigned** | From call 13b, with new shares in call 6 (qty = 100 × contracts, average cost ≈ strike) or a call-5 share row at 16:00 ET on that name. If 13b shows `pending`, print `assignment pending` |
| **Long close** | Long option sold to close (`closing_strategy` long_put / long_call): tag WING (a short on the same name stays open or closed in the same order) or LOTTO |
| **Short cover** | A call-5 row with negative quantity and side `buy` at a stock-level price (short stock bought back, R11) |
| **Stock exit** | A long share sale from call 5 / call 9 |

**2. Metrics for each close** (credit and close price per share; qty = contracts):
- **Credit** = |call-13 `average_price`| ÷ 100. Cross-check it against call 5: credit ≈ close + realized ÷ (100 × qty). If the two differ by more than $0.02, print both and tag `credit?`.
- **Realized $** = call 5 `realized_gain` (summed over the grouped rows). If no call-5 row matches, use (credit − close) × 100 × qty and tag `calc`.
- **% of credit kept** = (credit − close) ÷ credit.
- **Days held** (at least 1) = session date − `opened_at`; **planned DTE** = expiry − `opened_at`. **Velocity** = % of credit kept ÷ (days held ÷ planned DTE).
- **Return on risk (RoR)** = realized ÷ max loss at entry. Max loss for a put = (strike − credit) × 100 × qty; for a spread = (width − credit) × 100 × qty. **Annualized** = RoR × 365 ÷ days held, printed only when days held ≥ 7 (shorter holds print `n/m`).
- **Remaining reward/risk at close** = close ÷ (strike − close), or close ÷ (width − close) for a spread. This is what was given up versus what was still at risk. Under 5% means the close is justified on reward/risk alone, whatever happens next.
- **Price improvement** = limit − average fill price, when the order shows both.
- **Hindsight** = mark now (call 7) − close price, × 100 × qty. Tag it `noise, not graded` and never use it in the grade.
- **Roll (combined):** net roll credit = new credit − close debit. Print old → new strike and expiry, days added, and **combined P&L** = realized on the old leg + net roll credit. RoR uses the max loss of the new leg.
- **Short cover / stock exit:** realized $ and % vs entry (from call 5), days held when the lot's opening date is visible, else `n/a`.
- **Trigger at close:** R3/R4 are tested with the EOD spot (call 8) and the closed contract's EOD Delta (call 7), not the price at the moment of the close. Say so whenever the grade depends on it.

**3. Process grade.** The grade scores whether the rules were followed, never the P&L. Print the outcome next to it separately: **Win**, **Scratch** (|realized| < 10% of credit, or < $10 for a long or stock close) or **Loss**.
| Grade | When |
|---|---|
| **A** | Rule-driven. Shorts: a GTC fill at the R2 target (limit at ≥ 50% captured and ≤ 80%), a manual close with velocity met (≥ 2× and ≥ 25%), an R4 defense or R3 ITM-at-21-DTE close, a roll for a net credit whose new leg passes R4, R5 and R9, or an expiry while a working BTC sat unfilled. Longs: a WING closed together with (or after) its short, or a LOTTO sold at ≥ 2× its debit. Short covers: a cover at or before the R11 stop (entry × 1.15) |
| **B** | Right action, late or loose: a close at > 80% captured or a dead-penny buyback **without** a GTC at the R2 target (held past target), including a GTC whose limit was set above 80% captured; an expiry or assignment with no working BTC (R2 miss, survived pin risk); an LC/MC assignment inside the R7 limits; a short cover after spot went past the R11 stop |
| **C** | Discretionary: a short closed under 25% captured with no rule trigger (premature exit); a roll for a net debit; a roll whose new leg breaks R5, R9 or OPP limits; a LOTTO or long sold at a loss; a stock sale at a loss with no written exit level |
| **D** | A rule breach on the exit: dumping assigned shares within ≤ 5 sessions (R7); any contract ≤ $0.20 both opened and closed this session (R10 penny scalping); closing a WING while its short stays open (creates a naked short); a BIO/SC assignment above Floor B (R7) |
| **D?** | A short closed at a loss with **no R3/R4 trigger at EOD** (possible panic exit). Never assert panic: the trigger may have hit intraday, or the close may have been for an earnings or catalyst date (R6, not pulled in lean mode). Print `D?` and make it the Wendy question: "what was the trigger?" |
If a rule input is missing (Floor B stale, R11 entry not visible), add `?` to the grade and list it under UNVERIFIED. Facts the lean run can't see (whether the MID file flagged a trigger, how many sessions a trigger was ignored) never change a grade; they go in the commentary as a question.

**4. Verdict line** (one per close, ≤ 40 words, used in both the PDF and the chat):
`<TICKER> <STRIKE><P/C> <EXP> <type>: <+/-$realized> (<% kept>) in <days>/<planned DTE>d, vel <x.x>x, RoR <y>% (<z>% ann.), R/R left <w>%. Process <grade>, <outcome>. <one-line why, citing the rule #>.`
Example (the numbers are consistent): `AAPL 180P 16Jan27 profit-take: +$412 (64%) in 19/75d, vel 2.5x, RoR 2.4% (46% ann.), R/R left 1.3%. Process A, Win. GTC 50% filled (R2).` That's a credit of $6.44 closed at $2.32: 0.64 ÷ (19 ÷ 75) = 2.5; 412 ÷ ((180 − 6.44) × 100) = 2.4%; 2.32 ÷ (180 − 2.32) = 1.3%.
A roll line uses `<old> -> <new>`, the net roll credit and the combined P&L. A short-cover or stock line uses `<TICKER> <shares> sh <type>: <+/-$realized> (<% vs entry>). Process <grade>, <outcome>. <why>.`

**5. Month-to-date close stats** (from the call-5 rows dated this month; no extra call unless the second page is needed): realized $, number of closes, win rate, average win vs average loss, profit factor (gross wins ÷ gross losses), split options vs stock. Also the session's grade mix (e.g. `3A 1B 0C 1D 1D?`).

## PDF (narrative ≤ 2 pages, then the Appendix)
- reportlab Platypus, **built-in Helvetica only, ASCII text** (write "Delta", "<=", "->"; no TTF embedding). Keeps the file small (~10 KB narrative, ~25 KB with the Appendix) so the base64 upload stays small.
- Sections: 1 Snapshot card (session, NAV, BP, cash %, fills count and net credit, open shorts, no-GTC count, largest name % NAV incl. shares, held-lot unrealized; at EOD also session realized $ and the grade mix) · 2 Fills table (tag GTC fills from earlier orders) · **2b Closes (EOD only): one verdict line per close, then the month-to-date stats line** · 3 Breach table by priority, with the rule # on every row · 4 Concentration (top 5, puts + shares) · 5 Held lots (top 5 by unrealized loss) · 6 Commentary: one Wendy observation + one question (at EOD, if any close graded C or D, the Wendy observation is about that close), one Axe point + ≤ 4 staged tickets · 7 War Room Contract · 8 UNVERIFIED list.
- **Appendix: data for the Gemini market reports** (always included, on its own pages after the narrative; 7 pt Helvetica, ASCII, plain tables, one row per line, no merged cells, no wrapping inside a cell; it uses data already pulled, so it adds no calls). Gemini can't reach Robinhood, so this is its only view of the book. Print every row, not just flagged ones:
  - **A1 Header:** account · run type (PRE/MID/EOD) · run time `HH:MM ET / HH:MM ICT` · session date.
  - **CHECK line** (its own line, exactly this format; the reports copy it): `CHECK: <N> short option lines · <M> stock lines · $<X> short-put notional`. N must equal the number of short rows printed in A4.
  - **A2 Snapshot:** NAV · cash · buying power · options value long/short · short put notional · net delta $ · theta $/day · vega $/pt (`n/a` where not pulled).
  - **A3 Stock positions (every line):** ticker · class (universe.md, or `auto`) · qty (negative = short) · average cost · spot · quote time · unrealized $ · unrealized %.
  - **A4 Option positions (every line):** ticker · class · Floor B (floors.md, or `n/a`) · type · strike · expiry · qty (negative = short) · credit or debit per share · mark · Delta · DTE · cushion % · % captured · working BTC (Y/N). Unquoted lines print `n/q`; strikes from a quote print `strike inferred`.
  - **A5 Quotes:** every underlying in A3/A4: last · prior close · pre-market or after-hours mark if the quote has one · quote time.
  - **A6 Fills this session** (MID/EOD): time · ticker · contract or shares · side · qty · price · open/close · `GTC fill, order created earlier` tag.
  - **A7 Working orders:** ticker · contract · side · qty · limit · time in force · created time.
  - **A8 Transfers (EOD):** date · type (deposit / withdrawal) · amount, from call 10; `none` if there were none.
  - **A9 Closes (EOD):** ticker · contract (or shares) · type · qty · open date · credit or debit · close price · realized $ · % kept · days held · planned DTE · velocity · RoR % · ann. RoR % · R/R left % · hindsight $ · process grade · outcome · roll link (the new contract for a roll). Then one line: `MTD: <n> closes · $<realized> · win <w>% · avg win $<a> / avg loss $<b> · PF <p>` (or `MTD (partial, from <date>)`). `none` if nothing closed.
- Filename: `WarRoom_<SESSION_DATE>_<n>-<TYPE>-<HHMM>.pdf` where TYPE is PRE, MID or EOD and HHMM is the run time in ET (e.g. `WarRoom_2026-11-04_2-EOD-1655.pdf`), in `/mnt/user-data/outputs/`. A re-run gets a new HHMM, so two files never share a name; the Gemini reports find their feed by the TYPE token and take the latest HHMM.

## Upload
- `base64 -w0 <pdf>` once, then the `create_file` tool the Drive search returned, with `title` = filename, `base64Content`, `contentMimeType: "application/pdf"`, `disableConversionToGoogleType: true`, **`parentId: "1kchKBFGOQov1A6EZNxkgdD0qyzlTKttW"`** (folder "Robinhood Portfolio Review").
- Don't render preview images unless the layout changed.

## Chat reply
≤ 120 words: Drive link, net cash flow, top 3 breaches with rule #, count of staged tickets. No tables.

**EOD adds a "Closed today" block, which doesn't count toward the 120 words:**
- One verdict line per close (section 4 format), ordered by |realized $|, D and C grades first. Show at most 8; past that, add `+<n> more in the PDF (A9)`.
- Under each C or D, one sentence of commentary: what the rule called for and what the better exit would have been (e.g. "R4 trigger wasn't hit (Delta -0.18, spot 14% above strike): the GTC at 50% was the plan").
- Then one line: session realized $ · grade mix · the MTD stats line.
- Nothing closed → `Closed today: none`.

## Model
Sonnet for the routine run. Opus when the user asks for a full debrief or the book has an unusual event (assignment, gap through a strike, margin call).
