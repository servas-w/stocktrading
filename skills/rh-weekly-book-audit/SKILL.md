---
name: rh-weekly-book-audit
description: Wilson's weekly review of the positions he OPENED over the past week on Robinhood account 5QR66081, with blunt Shkreli-style forensic commentary on the new trades and on how portfolio composition drifted. Grades every new position against Playbook v2, shows cohort stats, awards trade of the week and trade to regret, compares start vs end of week composition, and sets next week's actions. Use when the user says "RH weekly audit", "weekly book audit", "weekly review of my new positions" or "weekend review". For the daily version use rh-daily-book-audit.
---

# RH weekly book audit

Requires the **Robinhood** connector. Read-only: never place, modify or cancel orders. Account `5QR66081` only. If a result is too large, use code execution (jq/python) or read in chunks. Do not call `get_equity_news`. Reply in chat, no preamble. Email (Gmail, wilsonhersandy@gmail.com) only if asked.

**Scope = positions opened in the last 7 calendar days** to the latest close (match `trade_date`). Rolls count as close + new open.

**Step 1: Opens of the week**
- `get_option_orders` and `get_equity_orders` (state=filled, last 10 days, all pages) -> opening executions in the window; group multi-leg orders into positions and group positions by ticker. Note which are still open, closed (use `get_pnl_trade_history` / `get_realized_pnl`) or rolled.
- No opens: say so, show composition only.

**Step 2: Data**
Per new position: `get_option_instruments`, `get_option_quotes` (greeks, mark now vs credit), `get_equity_quotes`, `get_equity_fundamentals`, `get_earnings_results`, `get_equity_historicals` (day, ~10 days: >= 8% moves, plus move since entry), `get_sec_filing_index` for sub-$10B names. Cause of moves "unknown" unless sourced.

**Step 3: Each new position (compact card)**
Credit, cushion at entry vs now, delta, DTE, % of credit captured so far, P&L now/realized, assignment notional, % NAV.
- **Grade A/B/C** (Playbook v2: A fits all rules; B event before expiry or DTE slightly off 60-90; C delta >= 0.25, ITM, <= 30 DTE, unstructured binary, sub-$5 biotech at >= 0.40 delta). Rule checks: IV gate, one ticket per name per day, OPP tag < 30 DTE, no puts on underwater lots, 3:1 on debits, GTC profit-take resting, 10% NAV cap.
- **Shkreli-style forensic one-liner**: follow the cash (biotech: cash/share vs strike, runway, dilution; large-cap: owner FCF, debt, what's priced in). Did the thesis hold up this week? Was the premium worth the tail?
- **Kill-shot** (what would make you close) and **verdict** (keep / manage / close, would you re-enter Y/N).

**Step 4: Cohort stats for the week's opens**
# trades, avg grade, avg DTE and delta at entry, avg annualized ROC, total premium sold, total notional, win rate on closed ones, avg % captured, best and worst. Compare to last week if prior data is evident from orders (trend arrows up/down).

**Step 5: Portfolio composition, start of week vs now**
`get_portfolio`, `get_equity_positions`, `get_option_positions` (nonzero, all pages; strip trailing digits). Use `get_equity_historicals` and order history to estimate the start-of-week book.
- % NAV by name and theme, net delta $, theta/day, vega, cash/BP %, **drift** (what grew, what shrank).
- 10% NAV cap (counting held shares): amber >= 8%, red > 10%.
- **Expiry ladder** (notional and premium by week/month), **earnings clusters** (notional exposed per week), **stress table** (book P&L at -5% / -10% / -20% broad market, with beta assumptions stated).
- Short stock, unlimited-risk and < 21 DTE legs called out.

**Step 6: Behavior scorecard**
Pass/fail counts on each Playbook rule across the week's opens. Name one **pattern to watch** (the repeated breach) and one **habit to keep**.

**Bear case on the biggest position (30 seconds)**: take the largest name by % NAV (notional + shares). In 5 lines: the strongest case against it, the numbers behind it (cash, burn, FCF, debt, dilution, catalyst dates), the price at which the thesis breaks, what you'd do at that price, and what would change your mind. Use `get_equity_fundamentals`, `get_financials`, `get_earnings_results`, `get_sec_filing_index`; mark anything unsourced as unknown.

**Journal + scoreboard (Google Drive, optional)**
Append-only, one small file per entry. The Drive connector's `update_file` changes metadata only, never content, so never edit an existing file: write a new one.
- **Folders**: `search_files` with `title = 'RH Trade Journal' and mimeType = 'application/vnd.google-apps.folder'` (same for **"RH Audit Scoreboard"**); if missing, `create_file` with `contentMimeType: application/vnd.google-apps.folder`. Keep both folder ids.
- **Read the journal**: for each new position, `search_files` with `parentId = '<journal folder id>' and title contains '<TICKER>'`, then `read_file_content` each hit. Entry titles are `YYYY-MM-DD TICKER EXPIRY STRIKES STRUCTURE` (expiry `YYYY-MM-DD`, strikes like `4-3`); match by ticker + expiry + strikes, and if several match, the newest date wins. Show **"Your thesis"** (the line you wrote) next to the outcome, and say whether the thesis held, was wrong, or was never written (then ask for a one-liner and offer to log it).
- **Write a journal entry** (a thesis given now, or a considered trade now filled): `create_file` in the journal folder with `parentId`, the title above, `contentMimeType: text/plain`, `disableConversionToGoogleType: true`, and `textContent` = `date | ticker | structure | strikes | expiry | qty | price | grade | thesis | kill-shot | status: filled`.
- **Scoreboard**: after the audit, `create_file` in the scoreboard folder (same settings) titled `YYYY-MM-DD weekly` with `textContent` = the header `date,type,trades,avg_grade,premium_sold,pct_captured,cap_breaches,rule_score,sleep_score,top_theme_pct,week_pnl` plus one row. For last week's score and the trend, `search_files` with `parentId = '<scoreboard folder id>'`, sort by title (ISO date first, so newest last) and `read_file_content` the last 4-8.
If Drive is off, skip silently and print the row at the end of the reply instead.

**Sleep-at-night score (0-10, 10 = sleeps fine)**: start at 10. Subtract: 1 per name over 8% NAV (2 if over 10%), 1 per short leg ITM or within 7% of strike, 1 per short leg <= 21 DTE and near the money, 1 if net short-stock/unlimited risk is open, 1 if a -20% market day costs > 5% NAV, 1 if cash+BP < 20% NAV, 1 if > 40% NAV sits in one theme. Floor 0. Show the score with the 2-3 biggest deductions and the single fix that adds the most points.

**Output (chat), in this order**
1. Headline, one punchy line: week grade, trades opened, premium sold, biggest concentration.
2. **Awards**: Trade of the Week, Trade to Regret, Best Discipline, Biggest Tail Risk.
3. Trade cards, sorted worst grade first, each with **your thesis (from journal)**.
4. Cohort stats table with arrows vs last week.
5. Composition start -> now with concentration meters (e.g. biotech ████████░░ 38%), drift, ladder, earnings clusters, stress, **Sleep-at-night X/10** vs last week's score from the scoreboard.
6. Scorecard + pattern to watch + habit to keep + **30-second bear case** on the biggest position + **scoreboard trend** (last 4-8 rows: grade, sleep score, P&L, cap breaches, with arrows).
7. **Next week: 5 actions**, urgent first.
8. Footer: "Points to weigh, not orders."

Tone: dry, sharp, a bit irreverent; Shkreli-style forensic bluntness; roast the trade, not the person; no hype or filler; numbers beat adjectives.
