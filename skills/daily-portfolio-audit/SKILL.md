---
name: "daily-portfolio-audit"
description: "Lean twice-daily audit (midday during the US session, and after the close) of Robinhood trades, the open option book and held stock lots, written as a 1-2 page PDF plus a data appendix, uploaded to the Google Drive folder Robinhood Portfolio Review for Gemini's daily stock report. Optional third run: a pre-market snapshot. Use when the user says audit my portfolio, audit, midday audit, daily audit, pre-market snapshot, run daily war room audit, run daily audit -> Drive PDF, yesterday's trades audit or similar. Audits against the War Room Playbook v2.5: velocity profit-take, OPP tagging for shorts under 30 DTE, ITM-at-21-DTE action, defense at delta -0.30 or spot within 7% of strike, one opening ticket per name per day, 10% NAV cap counting held shares, held-lot discipline, IV gate. Not for underwriting new tickers."
---

# Daily Portfolio Audit (lean, Playbook v2.5)

Goal: the War Room's compliance check at about a third of the compute. Pull only what the rules need, never full order history. The rule numbers below are Playbook v2.5 (R1–R12, confirmed by Wilson 5 Nov 2026; full text in the market-alpha-reports skill's `references/playbook.md`), extending the v2 rules in the Stock Trading project instructions (the canonical copy). When this file disagrees with them, the project instructions win; flag this file for an update.

## Rules
- **Read-only.** Never place, cancel or replace orders. Stage tickets only: `STAGE: BTC <qty> <TICKER> <EXP> <STRIKE>P @ <= $x GTC - reason (Rule #)` or `STAGE: CANCEL STO ... - reason (Rule #)`.
- **Robinhood MCP only** for data. No Gmail/Drive search for confirmations.
- **Mask accounts:** main book ••6081 (account_number 5QR66081). Shadow Delta ••1686 was empty on 2026-09-29; skip it unless the user asks.
- **Budget: ≤ 12 data calls** (≤ 14 with the overflow quote calls in 7 and 8). The Drive upload doesn't count. Hitting it = stop and mark the rest UNVERIFIED.
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

## Data calls (≤ 12; two parallel turns, call 10 at EOD only)
**Turn 1 (parallel, 6):**
1. `get_portfolio` (5QR66081) → NAV, cash, buying power.
2. `get_option_orders` (5QR66081, `state: "filled"`, `created_at_gte: SESSION_START`) → fills of orders **created** this session. **Never pull all states**: cancelled orders were ~80% of the tokens in the first run.
3. `get_option_orders` (5QR66081, `state: "confirmed"`, `created_at_gte: SESSION_START`) → new working orders (GTCs, resting STOs).
4. `get_option_positions` (5QR66081, `nonzero: true`) → book. `pending_buy_quantity` > 0 on a short = a working BTC exists. `created_at` ≥ SESSION_START = a position opened this session.
5. `get_pnl_trade_history` (5QR66081, `span: "week"`) → keep only rows dated in the session. **This catches GTCs created on earlier days that filled this session**: `created_at_gte` filters on when an order was created, so call 2 misses them, and they are exactly the 50% GTC buy-to-closes Rule 2 produces.
6. `get_equity_positions` (5QR66081) → held lots (quantity, average cost; negative quantity = short stock).

**Turn 2 (parallel, 5; 6 at EOD):**
7. `get_option_quotes` → every open short (velocity needs each mark) plus the session's fills; max 20 ids per call. If there are more than 20 shorts, make **one more call** for the next 20 (≤ 30 DTE first, then largest notional). Anything still unquoted is marked UNVERIFIED and printed as `n/q` in the Appendix.
8. `get_equity_quotes` → underlyings of every open short (defense 7% test, ITM test) plus every held lot (unrealized); max 20 symbols per call, open-short underlyings first, then the largest lots. If there are more than 20 symbols, make **one more call** for the next 20; print the rest as `n/q`.
9. `get_equity_orders` (5QR66081, `state: "filled"`, `created_at_gte: SESSION_START`) → stock buys and sells this session (assigned shares dumped, adds to underwater lots, short stock).
10. **EOD only:** `get_banking_transactions` (last 7 days) → rows that move money between the Robinhood bank account and the brokerage, for the reports' QQQ benchmark (A8). The connector can't see external deposits or wires straight into the brokerage, so A8 always ends with `external deposits not visible to the connector`. Also add **QQQ and SPY** to call 8's symbol list.
11. `get_option_instruments` (ids of every option position from call 4, batched) → the **exact** strike, expiry and type of every line. Never print a strike worked out from a quote when this call returned it.
12. `get_equity_fundamentals` (every A3/A4 underlying missing from `universe.md`) → market cap and sector for the class auto rule.

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

## PDF (narrative ≤ 2 pages, then the Appendix)
- reportlab Platypus, **built-in Helvetica only, ASCII text** (write "Delta", "<=", "->"; no TTF embedding). Keeps the file small (~10 KB narrative, ~25 KB with the Appendix) so the base64 upload stays small.
- Sections: 1 Snapshot card (session, NAV, BP, cash %, fills count and net credit, open shorts, no-GTC count, largest name % NAV incl. shares, held-lot unrealized) · 2 Fills table (tag GTC fills from earlier orders) · 3 Breach table by priority, with the rule # on every row · 4 Concentration (top 5, puts + shares) · 5 Held lots (top 5 by unrealized loss) · 6 Commentary: one Wendy observation + one question, one Axe point + ≤ 4 staged tickets · 7 War Room Contract · 8 UNVERIFIED list.
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
- Filename: `WarRoom_<SESSION_DATE>_<n>-<TYPE>-<HHMM>.pdf` where TYPE is PRE, MID or EOD and HHMM is the run time in ET (e.g. `WarRoom_2026-11-04_2-EOD-1655.pdf`), in `/mnt/user-data/outputs/`. A re-run gets a new HHMM, so two files never share a name; the Gemini reports find their feed by the TYPE token and take the latest HHMM.

## Upload
- `base64 -w0 <pdf>` once, then the `create_file` tool the Drive search returned, with `title` = filename, `base64Content`, `contentMimeType: "application/pdf"`, `disableConversionToGoogleType: true`, **`parentId: "1kchKBFGOQov1A6EZNxkgdD0qyzlTKttW"`** (folder "Robinhood Portfolio Review").
- Don't render preview images unless the layout changed.

## Chat reply
≤ 120 words: Drive link, net cash flow, top 3 breaches with rule #, count of staged tickets. No tables.

## Model
Sonnet for the routine run. Opus when the user asks for a full debrief or the book has an unusual event (assignment, gap through a strike, margin call).
