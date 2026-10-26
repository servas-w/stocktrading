---
name: rh-weekly-book-audit
description: Wilson's weekly review of the positions he OPENED over the past week on Robinhood account 5QR66081, with blunt Shkreli-style forensic commentary on the new trades and on how portfolio composition drifted. Grades every new position against Playbook v2, shows cohort stats and the week's total realized P&L, reviews held lots, awards trade of the week and trade to regret, compares start vs end of week composition, and sets next week's actions. Use when the user says "RH weekly audit", "weekly book audit", "weekly review of my new positions" or "weekend review". For the daily version use rh-daily-book-audit.
---

# RH weekly book audit

Requires the **Robinhood** connector. Read-only on Robinhood: never place, modify or cancel orders. Account `5QR66081` only. If a result is too large, use code execution (jq/python) or read in chunks. Do not call `get_equity_news`. Reply in chat, no preamble. Email (Gmail, wilsonhersandy@gmail.com) only if asked.

**Scope = positions opened in the last 7 calendar days** to the latest close (match `trade_date`). Rolls count as close + new open. Realized P&L and held lots cover the whole book, not just the week's opens.

**Definitions (use everywhere below)**
- **% NAV of a name** = held shares at market + option notional. Short put or put spread notional = short strike x 100 x qty (show spread max loss separately). Naked short call = spot x 100 x qty; covered call adds nothing beyond the shares. Long options = premium paid.
- **Grade (Playbook v2)**: **A** = 60-90 DTE, |delta| <= 0.20, no unstructured event before expiry, all rule checks pass. **B** = |delta| 0.20-0.25, or DTE 31-59 or 91-180, or an earnings/binary event before expiry with structure around it. **C** = |delta| >= 0.25, ITM, <= 30 DTE, unstructured binary before expiry, or any hard-rule breach (one opening ticket per name per day, puts on an underwater lot, name > 10% NAV after the trade, debit trade under 3:1, < 30 DTE short without an OPP tag). Grade at entry.
- **Stock replacement (SR)**: sub-$5 biotech put sold at |delta| >= 0.40 is a deliberate stock-replacement trade, not a C. Skip the delta/DTE bands; grade it **SR-pass** if effective entry (strike - credit) <= cash per share (Floor A), else **SR-fail**. The other rule checks still apply.
- **IV gate**: Robinhood has no IV Rank. Report IV at entry and write "IVR unverified: check IBKR IV percentile (52w >= 60, 26w >= 50) or Barchart IVR >= 50" unless Wilson supplied it or an IBKR connector is authenticated. Defined-risk spreads may use the spread exception. Unverified is a flag, not a grade change; a verified fail is a hard-rule breach.
- **Danger leg**: short leg ITM, |delta| >= 0.30 (puts or calls), or spot within 7% of the short strike.
- **Velocity profit-take**: short leg whose % of credit captured is well ahead of % of DTE elapsed (e.g. >= 50% captured in the first third of its life) -> flag "take it". Separately, >= 50% captured with no GTC close resting -> flag.
- **Market stress**: shock each underlying by the market move x beta (beta 1.0 for index/large-cap, 1.5 for biotech, AI-semis and crypto unless fundamentals give one; state the assumption). Option loss = value at the shocked spot (intrinsic as a floor) - current mark, capped at max loss; shares lose shares x shock. Sum, as % NAV.

**Step 1: Opens of the week**
- `get_option_orders` and `get_equity_orders` (state=filled, all pages). Filter on `updated_at` >= 30 days ago if the tool supports it, else `created_at` >= 30 days ago, so older GTC fills are caught and the prior week (days 8-14) is available for comparison. Keep opening executions by `trade_date`; group multi-leg orders into positions and positions by ticker. Note which are still open, closed (use `get_pnl_trade_history`) or rolled.
- **Assignments/exercises**: they are not filled orders. A held lot that grew with no matching buy, or a short option gone at/after expiry with no closing fill, is an assignment. Count it as a new held lot (entry = strike; effective = strike - original credit).
- **Week P&L**: `get_realized_pnl` (and `get_pnl_trade_history`) for the 7-day window across the whole book. This is `week_pnl` on the scoreboard. Do the same for the prior 7 days for the trend arrow.
- No opens: say so, show week P&L, held lots and composition only.

**Step 2: Data**
Per new position: `get_option_instruments`, `get_option_quotes` (greeks, mark now vs credit), `get_equity_quotes`, `get_equity_fundamentals`, `get_earnings_results`, `get_equity_historicals` (day, ~10 days: >= 8% moves, plus move since entry), `get_sec_filing_index` for sub-$10B names. Cause of moves "unknown" unless sourced.

**Step 3: Each new position (compact card)**
Credit, cushion at entry vs now, delta, DTE, IV gate status, % of credit captured so far, P&L now/realized, assignment notional, % NAV.
- **Grade** per the definitions (A/B/C or SR-pass/SR-fail), listing each failed rule check plus: GTC profit-take resting, velocity profit-take due.
- **Shkreli-style forensic one-liner**: follow the cash (biotech: cash/share vs strike, runway, dilution; large-cap: owner FCF, debt, what's priced in). Did the thesis hold up this week? Was the premium worth the tail?
- **Kill-shot** (what would make you close) and **verdict** (keep / manage / close, would you re-enter Y/N).

**Step 4: Cohort stats for the week's opens**
# trades, avg grade, avg DTE and delta at entry, avg annualized ROC, total premium sold, total notional, win rate on closed ones, avg % captured, best and worst, plus the week's total realized P&L (whole book). Compute the same for the prior week's opens (days 8-14) and show trend arrows up/down.

**Step 5: Portfolio composition, start of week vs now**
`get_portfolio`, `get_equity_positions`, `get_option_positions` (nonzero, all pages; strip trailing digits). **Start of week** = current book minus the week's opens, with the week's closes added back; price shares with `get_equity_historicals` and options with `get_option_historicals` at the start-of-week close (credit at entry if no history).
- % NAV by name and theme, net delta $, theta/day, vega, cash/BP %, **drift** (what grew, what shrank).
- 10% NAV cap: amber >= 8%, red > 10%.
- **Expiry ladder** (notional and premium by week/month), **earnings clusters** (notional exposed per week), **stress table** (book P&L at -5% / -10% / -20% broad market, beta assumptions stated).
- Danger legs, short stock, naked calls/unlimited risk, < 21 DTE legs and velocity profit-takes called out.

**Step 6: Held-lot review**
Every held stock lot (including new assignments): shares, cost basis, effective basis after premiums, mark, unrealized P&L $ and %, % NAV, covered calls against it, days held. Flag: underwater lots with puts open or added on the name (breach), lots > 10% NAV, lots with no call written and no plan. One line each on keep / write calls / cut.

**Step 7: Behavior scorecard**
Pass/fail counts on each Playbook rule across the week's opens. Name one **pattern to watch** (the repeated breach) and one **habit to keep**.

**Bear case on the biggest position (30 seconds)**: take the largest name by % NAV. In 5 lines: the strongest case against it, the numbers behind it (cash, burn, FCF, debt, dilution, catalyst dates), the price at which the thesis breaks, what you'd do at that price, and what would change your mind. Use `get_equity_fundamentals`, `get_financials`, `get_earnings_results`, `get_sec_filing_index`; mark anything unsourced as unknown.

**Journal + scoreboard (Google Drive, optional)**
If the Google Drive connector is on, `search_files` for **"RH Trade Journal"** and **"RH Audit Scoreboard"** (create each with `create_file` if missing; journal = markdown, scoreboard = CSV with header `date,type,trades,avg_grade,premium_sold,pct_captured,cap_breaches,rule_score,sleep_score,top_theme_pct,week_pnl`). `read_file_content` the journal and match entries by ticker/strike/expiry to each new position: show **"Your thesis"** (the line you wrote) next to the outcome, and say whether the thesis held, was wrong, or was never written (then ask for a one-liner and offer to log it). After the audit, append one row to the scoreboard (read, add row, `update_file`). If Drive is off, skip silently and print the row at the end of the reply instead.

**Sleep-at-night score (0-10, 10 = sleeps fine)**: start at 10. Subtract: 1 per name over 8% NAV (2 if over 10%); 1 per danger leg, plus 1 more if that leg is also <= 21 DTE (each leg counted once otherwise); 1 if short stock or a naked call is open; 1 if the -20% stress costs > 5% NAV; 1 if cash+BP < 20% NAV; 1 if > 40% NAV sits in one theme. Floor 0. Show the score with the 2-3 biggest deductions and the single fix that adds the most points.

**Output (chat), in this order**
1. Headline, one punchy line: week grade, trades opened, premium sold, week P&L, biggest concentration.
2. **Awards**: Trade of the Week, Trade to Regret, Best Discipline, Biggest Tail Risk.
3. Trade cards, sorted worst grade first, each with **your thesis (from journal)**.
4. Cohort stats table with arrows vs last week.
5. Composition start -> now with concentration meters (e.g. biotech ████████░░ 38%), drift, ladder, earnings clusters, stress, **Sleep-at-night X/10** vs last week's score from the scoreboard.
6. Held-lot review.
7. Scorecard + pattern to watch + habit to keep + **30-second bear case** on the biggest position + **scoreboard trend** (last 4-8 rows: grade, sleep score, P&L, cap breaches, with arrows).
8. **Next week: 5 actions**, urgent first.
9. Footer: "Points to weigh, not orders."

Tone: dry, sharp, a bit irreverent; Shkreli-style forensic bluntness; roast the trade, not the person; no hype or filler; numbers beat adjectives.
