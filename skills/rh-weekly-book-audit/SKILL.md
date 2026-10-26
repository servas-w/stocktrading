---
name: rh-weekly-book-audit
description: Wilson's weekly review of the whole Robinhood book (account 5QR66081) against Playbook v2. Covers realized P&L and closed trades for the week, win rate and premium captured, open-book risk (concentration vs the 10% NAV cap, expiry ladder, assignment calendar, earnings clustering, theta, net delta/beta), rule-compliance scorecard, held-lot review, and next week's action list. Use when the user says "RH weekly audit", "weekly book audit", "weekly review of my portfolio" or "weekend review". For the daily check use rh-daily-book-audit.
---

# RH weekly book audit

Requires the **Robinhood** connector. Read-only: never place, modify or cancel orders. Account `5QR66081` only. If a result is too large, use code execution (jq/python) or read in chunks. Do not call `get_equity_news`. Reply in chat, concise, no preamble; email (Gmail, wilsonhersandy@gmail.com) only if asked.

**Window** = last 7 calendar days to the most recent close (use `trade_date`). Run on weekends or Monday for a clean week.

**Step 1: Performance**
- `get_realized_pnl` and `get_pnl_trade_history` for the window (fallback: `get_option_orders` / `get_equity_orders` filled, group closes with their opens). `get_portfolio` for NAV change vs 7 days ago.
- Report: realized P&L, # closed trades, win rate, avg win vs avg loss, premium collected (opens) vs premium kept (closes), best and worst trade, and anything closed at a loss below the 50% profit-take level or held past 21 DTE.

**Step 2: Open book** (same data pulls as the daily audit: positions, instruments, quotes, greeks)
- Per-name table: structure, strikes, expiry, DTE, cushion %, delta, % of credit captured, max loss, assignment notional, % NAV (assignment notional + held shares).
- **10% NAV cap** violations and names within 2 pts of it.
- **Expiry ladder**: premium, assignment notional and max loss by week/month; anything <= 21 DTE.
- **Assignment calendar**: legs ITM or within 7% of strike, effective basis if assigned, cash/BP needed vs available.
- **Earnings/binary clustering**: `get_earnings_results` for every name with a leg; list those inside expiry windows (mark unverified "tent.") and the total notional exposed to the same week.
- **Greeks**: net delta ($), theta/day, vega; sector or theme clustering (e.g. biotech, AI, crypto).
- **Short stock** and any ticker with unlimited risk called out.
- **Move check** on short-leg tickers: `get_equity_historicals` (day, ~10 calendar days, <=10 symbols per call); flag any >= 8% close-to-close move this week. Cause "unknown" unless sourced.

**Step 3: Rule scorecard** (pass/fail with counts)
IV gate (IVR >= 50 or spread exception) at entry where known; 60-90 DTE; defense triggers acted on; one opening ticket per name per day; OPP tag on shorts < 30 DTE; no puts on underwater held lots; 3:1 on debit trades; GTC profit-takes resting; 10% cap. Pull repeated breaches into a **pattern to watch** (one or two lines).

**Step 4: Held lots**
`get_equity_positions` plus `get_equity_tax_lots` if useful: unrealized P&L per lot, lots > 20% underwater, covered-call coverage, and whether short puts sit on underwater lots.

**Output (chat)**
1. Scorecard line: week P&L, NAV change, win rate, cap breaches, rule score.
2. **Top 5 actions for next week**, ordered by urgency.
3. Performance table (closed trades).
4. Open-book risk table + expiry ladder + earnings clusters.
5. Rule scorecard + pattern to watch.
6. Footer: "Points to weigh, not orders."
