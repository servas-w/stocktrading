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
- **Budget: ≤ 12 data calls** (≤ 14 with the overflow quote calls in 7 and 8; EOD may add call 13, so ≤ 15). The Drive upload doesn't count. Hitting it = stop and mark the rest UNVERIFIED.
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

## Data calls (≤ 12, or 13 at EOD; two parallel turns; calls 10 and 13 at EOD only)
**Turn 1 (parallel, 6):**
1. `get_portfolio` (5QR66081) → NAV, cash, buying power.
2. `get_option_orders` (5QR66081, `state: "filled"`, `created_at_gte: SESSION_START`) → fills of orders **created** this session. **Never pull all states**: cancelled orders were ~80% of the tokens in the first run.
3. `get_option_orders` (5QR66081, `state: "confirmed"`, `created_at_gte: SESSION_START`) → new working orders (GTCs, resting STOs).
4. `get_option_positions` (5QR66081, `nonzero: true`) → book. `pending_buy_quantity` > 0 on a short = a working BTC exists. `created_at` ≥ SESSION_START = a position opened this session.
5. `get_pnl_trade_history` (5QR66081, `span: "week"`; **`span: "month"` at EOD**, for the month-to-date close stats) → keep only rows dated in the session for the fills; at EOD keep the month-to-date rows for the close stats. **This catches GTCs created on earlier days that filled this session**: `created_at_gte` filters on when an order was created, so call 2 misses them, and they are exactly the 50% GTC buy-to-closes Rule 2 produces.
6. `get_equity_positions` (5QR66081) → held lots (quantity, average cost; negative quantity = short stock).

**Turn 2 (parallel, 5; up to 7 at EOD):**
7. `get_option_quotes` → every open short (velocity needs each mark) plus the session's fills (at EOD this includes every contract closed this session, for the hindsight mark); max 20 ids per call. If there are more than 20 shorts, make **one more call** for the next 20 (≤ 30 DTE first, then largest notional). Anything still unquoted is marked UNVERIFIED and printed as `n/q` in the Appendix.
8. `get_equity_quotes` → underlyings of every open short (defense 7% test, ITM test) plus every held lot (unrealized), plus at EOD the underlying of every contract closed this session (whether a defense trigger was hit when it closed); max 20 symbols per call, open-short underlyings first, then the largest lots. If there are more than 20 symbols, make **one more call** for the next 20; print the rest as `n/q`.
9. `get_equity_orders` (5QR66081, `state: "filled"`, `created_at_gte: SESSION_START`) → stock buys and sells this session (assigned shares dumped, adds to underwater lots, short stock).
10. **EOD only:** `get_banking_transactions` (last 7 days) → rows that move money between the Robinhood bank account and the brokerage, for the reports' QQQ benchmark (A8). The connector can't see external deposits or wires straight into the brokerage, so A8 always ends with `external deposits not visible to the connector`. Also add **QQQ and SPY** to call 8's symbol list.
11. `get_option_instruments` (ids of every option position from call 4, batched) → the **exact** strike, expiry and type of every line. Never print a strike worked out from a quote when this call returned it.
12. `get_equity_fundamentals` (every A3/A4 underlying missing from `universe.md`) → market cap and sector for the class auto rule.
13. **EOD only, and only if needed:** `get_option_orders` (5QR66081, `state: "filled"`, `created_at_gte` = session date − 120 days) → the opening fill (credit and date) of each contract closed this session. Skip it when the call-5 rows already carry the opening price and date. Match on symbol + strike + expiry + type; take the latest opening fill before the close. Any close still without opening data gets realized P&L only (from call 5), with velocity and return on risk printed `UNVERIFIED`. **Never pull all order states.**

**Fill reconciliation:** session fills = call 2 ∪ the closing rows from call 5 (dedupe on symbol + strike + expiry + qty + price; tag call-5-only rows "GTC fill, order created earlier"). New positions from call 4 with no matching opening fill = a resting STO created earlier that filled this session: list them as opening fills too. Call 5 shows realizing trades only, so this positions check is the only way to see those.

**Field notes:**
- **Tickers exactly as the API returns them.** Never normalize or "correct" a symbol (MRVI is not MRVL; the 4 Nov PDF printed MRVI as MRVL and showed a false −$18,193 loss).
- Strike, expiry and type come from call 11. Only if that call fails for a line: put = break_even + mark, call = break_even − mark, rounded to the nearest listed increment, and the row is tagged `strike inferred` (the reports never stage an order on it). Greeks null/zero on an ITM contract → treat Δ as −1.0 (puts) and say so.
- Credit per share = |position `average_price`| ÷ `trade_value_multiplier` (100). Sanity-check it against the mark; if the ratio is implausible (> 50× or < 0.02×), mark velocity UNVERIFIED for that short rather than guess.
- % captured = (credit − mark) ÷ credit. % of DTE elapsed = (today − position `created_at`) ÷ (expiry − position `created_at`).
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
MID and PRE runs skip this section: MID lists closes in the fills table only. EOD reviews **every close in the session**, using data already pulled (calls 2, 4, 5, 6, 7, 8, 9, 11), plus call 13 if needed.

**1. Find and classify each close.**
| Type | How to detect it |
|---|---|
| **Profit-take** | BTC filled below the opening credit. Tag `GTC` if the order was created before the session (call-5-only row) |
| **Defense close** | BTC filled at or above the opening credit, or any BTC on a name whose R3/R4 trigger was hit |
| **Roll** | A close plus an opening fill on the **same underlying in the same session** (one multi-leg order, or two tickets). Score both legs as **one combined trade**, not as a close and a new position |
| **Dead penny** | BTC at ≤ $0.05 |
| **Expired** | A call-5 expiration row, or a short whose expiry was the session date that is now missing from call 4 with no BTC. Realized = full credit |
| **Assigned** | A call-5 assignment row, or new shares in call 6 (qty = 100 × contracts, average cost ≈ strike) on a name where a short put was open. If neither shows, print `expiries/assignments UNVERIFIED` |
| **Stock exit** | A shares sale from call 9. Compare it with the lot's average cost |
| **Long close** | STC of a long option (wing, LOTTO or debit spread). Realized = proceeds − debit |

**2. Metrics for each close** (credit and close price per share; qty = contracts):
- **Realized $** = (credit − close) × 100 × qty. Prefer call 5's realized figure; if the two differ by more than $1, print both.
- **% of credit kept** = (credit − close) ÷ credit.
- **Days held** (at least 1) and **planned DTE**, both counted from the opening fill date. **Velocity** = % of credit kept ÷ % of DTE elapsed.
- **Return on risk (RoR)** = realized ÷ max loss at entry. Max loss for a put = (strike − credit) × 100 × qty; for a spread = (width − credit) × 100 × qty. **Annualized** = RoR × 365 ÷ days held.
- **Remaining reward/risk at close** = close ÷ (strike − close), or close ÷ (width − close) for a spread. This is what was given up versus what was still at risk. Under 5% means the close is justified on reward/risk alone, whatever happens next.
- **Price improvement** = limit − average fill price, when the order shows both.
- **Hindsight** = mark now (call 7) − close price, × 100 × qty. Tag it `noise, not graded` and never use it in the grade.
- **Roll (combined):** net roll credit = new credit − close debit. Print old → new strike and expiry, days added, and **combined P&L** = realized on the old leg + net roll credit. RoR uses the max loss of the new leg.

**3. Process grade.** The grade scores whether the rules were followed, never the P&L. Print the outcome next to it separately: **Win**, **Scratch** (|realized| < 10% of credit) or **Loss**.
| Grade | When |
|---|---|
| **A** | Rule-driven: an R2 profit-take (≥ 50%, or velocity met), an R4 defense close or R3 ITM-at-21-DTE close within 1 session of the trigger, a dead-penny cleanup, a roll down and/or out for a net credit whose new leg passes R4, R5 and R9, or an expiry where a working BTC sat unfilled |
| **B** | The right action but late: ≥ 80% captured or mark ≤ $0.05 before closing (held past target); a defense or ITM close in the 2nd session after the trigger (the MID file flagged it); an expiry or assignment with no working BTC (R2 miss, survived pin risk); an LC/MC assignment at a strike inside the R7 limits |
| **C** | Discretionary: a close under 25% captured with no rule trigger (premature exit); a roll for a net debit; a roll whose new leg breaks R5, R9 or OPP limits; a stock sale at a loss with no written exit level |
| **D** | A rule breach on the exit: a loss close with **no defense trigger hit** (panic exit); a close after a trigger was ignored for ≥ 3 sessions; dumping assigned shares within ≤ 5 sessions (R7); a same-session open and close of a contract ≤ $0.20 (R10); closing a wing while its short stays open; a BIO/SC assignment above Floor B (R7) |
If a rule input is missing (Floor B stale, trigger history not visible), give the grade with `?` and list it under UNVERIFIED.

**4. Verdict line** (one per close, ≤ 40 words, used in both the PDF and the chat):
`<TICKER> <STRIKE><P/C> <EXP> <type>: <+/-$realized> (<% kept>) in <days>/<planned DTE>d, vel <x.x>x, RoR <y>% (<z>% ann.), R/R left <w>%. Process <grade>, <outcome>. <one-line why, citing the rule #>.`
Example: `AAPL 180P 16Jan27 profit-take: +$412 (64%) in 19/75d, vel 3.4x, RoR 2.3% (44% ann.), R/R left 4%. Process A, Win. GTC 50% filled (R2).`
A roll line uses `<old> -> <new>`, the net roll credit and the combined P&L.

**5. Month-to-date close stats** (from the call-5 month rows; no extra call): realized $, number of closes, win rate, average win vs average loss, profit factor (gross wins ÷ gross losses), and average days held where call 5 shows the opening date. Also the session's grade mix (e.g. `3A 1B 0C 1D`).

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
  - **A9 Closes (EOD):** ticker · contract (or shares) · type · qty · open date · credit or debit · close price · realized $ · % kept · days held · planned DTE · velocity · RoR % · ann. RoR % · R/R left % · hindsight $ · process grade · outcome · roll link (the new contract for a roll). Then one line: `MTD: <n> closes · $<realized> · win <w>% · avg win $<a> / avg loss $<b> · PF <p>`. `none` if nothing closed.
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
