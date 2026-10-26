---
name: rh-pretrade-check
description: Wilson's pre-trade check for a trade he is CONSIDERING (not yet placed) on Robinhood account 5QR66081. Takes a pasted trade (e.g. "sell 5 FHTX Jan 2 put spread 4/3 for 0.45") and returns the same trade card as the daily audit - Playbook v2 grade, Shkreli-style forensic read, bear case, kill-shot, stress, and before/after portfolio composition including 10% NAV cap and sleep-at-night score - then saves a PDF (WarRoom_<date>_6-PRETRADE-<TICKER>.pdf) and logs his thesis to the journal in the Drive folder Robinhood Portfolio Review. Use when the user says "RH pretrade", "pre-trade check", "check this trade before I place it", or pastes a fully specified proposed option order (ticker, strikes, expiry and price). For underwriting a ticker from scratch ("should I sell puts on X?", a bare ticker) use large-cap-put-overreaction or biotech-options-master-engine. Never places orders.
---

# RH pre-trade check

Requires the **Robinhood** and **Google Drive** connectors. Read-only on Robinhood: never place, modify, cancel or even preview orders. Account `5QR66081` only. Do not call `get_equity_news`. Chat reply plus a PDF saved to Drive (see below), no preamble.

**Input**: ticker, structure, strikes, expiry, qty, limit price. If any is missing, ask once, in one line. Quantity default: 1.

**Definitions**
- **% NAV of a name** = held shares at market + option notional. Short put or put spread notional = short strike x 100 x qty (show spread max loss separately). Naked short call = spot x 100 x qty; covered call adds nothing beyond the shares. Long options = premium paid.
- **Grade (Playbook v2)**: **A** = 60-90 DTE, |delta| <= 0.20, no unstructured event before expiry, all rule checks pass. **B** = |delta| 0.20-0.25, or DTE 31-59 or 91-180, or an earnings/binary event before expiry with structure around it. **C** = |delta| >= 0.25, ITM, <= 30 DTE, unstructured binary before expiry, or any hard-rule breach (one opening ticket per name per day, puts on an underwater lot, name > 10% NAV after the trade, debit trade under 3:1, < 30 DTE short without an OPP tag).
- **Stock replacement (SR)**: sub-$5 biotech put sold at |delta| >= 0.40 is a deliberate stock-replacement trade, not a C. Skip the delta/DTE bands; grade it **SR-pass** if effective entry (strike - credit) <= cash per share (Floor A), else **SR-fail**. The other rule checks still apply.
- **IV gate**: Robinhood has no IV Rank. Report current IV and write "IVR unverified: check IBKR IV percentile (52w >= 60, 26w >= 50) or Barchart IVR >= 50" unless Wilson supplied it or an IBKR connector is authenticated. Defined-risk spreads may use the spread exception. Unverified is a flag, not a grade change; a verified fail is a hard-rule breach.
- **Danger leg**: short leg ITM, |delta| >= 0.30 (puts or calls), or spot within 7% of the short strike.
- **-20% stress**: shock each underlying by -20% x beta (beta 1.0 for index/large-cap, 1.5 for biotech, AI-semis and crypto unless fundamentals give one; state the assumption). Option loss = value at the shocked spot (intrinsic as a floor) - current mark, capped at max loss; shares lose shares x shock. Sum, as % NAV.

**Step 1: Live data** - `get_option_chains` / `get_option_instruments` to find the contract(s), `get_option_quotes` (bid/ask, delta, IV, OI), `get_equity_quotes`, `get_equity_fundamentals`, `get_earnings_results`, `get_equity_historicals` (day, ~10 days, >= 8% moves), `get_sec_filing_index` for sub-$10B names. Check whether the limit price is inside the bid/ask (flag a fill-unlikely or giving-away price). `get_equity_orders`/`get_option_orders` for a same-name opening ticket today (rule: one opening ticket per name per day) and any resting order on the name.

**Step 2: Trade card** - credit, cushion %, delta, IV (+ IV gate status), DTE, breakeven, assignment notional, max loss, ROC and annualized ROC, % NAV.
- **Grade** per the definitions (A/B/C or SR-pass/SR-fail), listing each failed rule check.
- **Shkreli-style forensic read**: follow the cash (biotech: cash/share vs strike, runway, dilution, Floor A/B; large-cap: owner FCF, debt, what the sell-off priced in). What is the market afraid of, and does this strike get paid for it?
- **Bear case** (one line), **kill-shot** (exact trigger to close), **stress** at -10 / -20 / -35% vs premium, **better version** (one alternative strike/expiry/structure if it grades B, C or SR-fail).

**Step 3: Portfolio impact** - `get_portfolio`, `get_equity_positions`, `get_option_positions` (nonzero, all pages; strip trailing digits). Show **before -> after**: % NAV by name and theme with concentration meters, net delta, theta/day, cash/BP, earnings-week stacking, and **sleep-at-night score** before -> after (start 10; -1 per name > 8% NAV (-2 if > 10%); -1 per danger leg, -1 more if that leg is also <= 21 DTE; -1 open short stock or naked call; -1 if the -20% stress costs > 5% NAV; -1 if cash+BP < 20% NAV; -1 if > 40% NAV in one theme; floor 0).

**Step 4: Verdict + journal** - one line: **GO / TRIM SIZE / WAIT / PASS** with the reason, and the max qty that keeps the name <= 10% NAV (using the notional definition above). Ask Wilson for a one-line thesis if he hasn't given one. Add the trade to the journal (below) with `status: considered`; the daily/weekly audits match it to the fill later. Do not log if he says pass.

**Save to Drive (required)**
Every run saves its report as a PDF in the Google Drive folder **Robinhood Portfolio Review** (folder id `1kchKBFGOQov1A6EZNxkgdD0qyzlTKttW`; never another folder, never a subfolder). The folder feeds Wilson's other stock market reports, so the name must match exactly:
- Name: `WarRoom_<YYYY-MM-DD>_6-PRETRADE-<TICKER>.pdf` (date = the session the trade is meant for: today's if the market is open or opens later today in New York, else the next session). Title: `RH pre-trade check - <TICKER> <structure>`.
- Date = the **US session date (New York)**, never the Da Nang date. If a file with that exact name already exists (`search_files` with `parentId = '1kchKBFGOQov1A6EZNxkgdD0qyzlTKttW' and title = '<name>'`), add `-v2`, `-v3` ... before `.pdf`; never create two files with the same name.
- Render the PDF with code execution (1-3 pages, tables for the cards and composition), then `create_file` with `parentId` = the folder id, `contentMimeType` `application/pdf`, `base64Content`, and `disableConversionToGoogleType: true`. If a PDF can't be rendered, say so; do not upload a Google Doc in its place.
- PDF header, same as the other WarRoom reports: line 1 `<report title> - US session YYYY-MM-DD`; line 2 `Account ...6081 | Run: <UTC time> (<Da Nang time>) | Read-only: no orders placed, modified or cancelled.` Last section **UNVERIFIED**: everything not pulled or not sourced (IVR, tentative earnings dates, stale quotes, bad greeks).
- End the chat reply with the file name and link. If the Drive connector is off, say so in one line and give the chat report only.

**Journal + scoreboard (same Drive folder)**
The Drive connector cannot edit a file's content, so these are snapshot files, like `WarRoom_metrics_<date>.csv`: read the newest, add to it, save a new file. Never try to edit in place.
- **Journal**: newest file named `WarRoom_journal_<YYYY-MM-DD>*.md` in the folder (`search_files` with `parentId = '1kchKBFGOQov1A6EZNxkgdD0qyzlTKttW' and title contains 'WarRoom_journal_'`, pick the latest date/version). One line per trade: `date | ticker | structure | strikes | expiry | qty | price | grade | thesis | kill-shot | status`.
- **Scoreboard**: newest `WarRoom_scoreboard_<YYYY-MM-DD>*.csv`, header `date,type,trades,avg_grade,premium_sold,pct_captured,cap_breaches,rule_score,sleep_score,top_theme_pct,week_pnl`.
- To write: copy the newest file's full content, apply the change, `create_file` `WarRoom_<journal|scoreboard>_<session date>.<md|csv>` (add `-v2`... if that name exists) with `contentMimeType` `text/markdown` or `text/csv` and `disableConversionToGoogleType: true`. If none exists yet, start one with just the header.

Footer: "Points to weigh, not orders." Tone: dry, sharp, a bit irreverent; roast the trade, not the person.
