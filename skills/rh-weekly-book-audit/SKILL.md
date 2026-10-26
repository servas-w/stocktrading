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

**Output (chat), in this order**
1. Headline, one punchy line: week grade, trades opened, premium sold, biggest concentration.
2. **Awards**: Trade of the Week, Trade to Regret, Best Discipline, Biggest Tail Risk.
3. Trade cards, sorted worst grade first.
4. Cohort stats table with arrows vs last week.
5. Composition start -> now with concentration meters (e.g. biotech ████████░░ 38%), drift, ladder, earnings clusters, stress.
6. Scorecard + pattern to watch + habit to keep.
7. **Next week: 5 actions**, urgent first.
8. Footer: "Points to weigh, not orders."

Tone: dry, sharp, a bit irreverent; Shkreli-style forensic bluntness; roast the trade, not the person; no hype or filler; numbers beat adjectives.
