---
name: rh-daily-book-audit
description: Wilson's daily audit of the whole Robinhood book (account 5QR66081) against Playbook v2. Reads positions, working orders and today's fills, then checks every short leg for ITM/defense/21-DTE/50%-GTC actions, the 10% NAV cap (counting held shares), earnings before expiry, and any >=8% moves. Output is a concise chat report; email only if asked. Use when the user says "RH daily audit", "daily book audit", "audit my book", or "check my book". For the new-fills-only morning email use morning-trade-audit; for Axe/Wendy roleplay use the war room skill.
---

# RH daily book audit

Requires the **Robinhood** connector. Read-only: never place, modify or cancel orders. Account `5QR66081` only. If a result is too large, use code execution (jq/python) or read in chunks. Do not call `get_equity_news` (unreliable). Reply in chat, concise, no preamble; send an email (Gmail, to wilsonhersandy@gmail.com) only if Wilson asks.

**Step 1: Book**
- `get_portfolio` (NAV, cash, buying power), `get_equity_positions`, `get_option_positions` (nonzero, all pages), `get_option_orders` and `get_equity_orders` (working orders, plus fills from the last 3 days by `trade_date`).
- Strip trailing digits from adjusted chains (e.g. `SNDQ1` -> `SNDQ`). Group by ticker: shares, short/long legs, structure (put spread, covered call, calendar, naked).
- `get_option_instruments` (ids comma-separated, <=55 per call) for strike/type/expiry; `get_option_quotes` for delta, IV, mark; `get_equity_quotes` (<=20 symbols) for spot.

**Step 2: Per short leg**
Moneyness % (puts (S-K)/S, calls (K-S)/S; negative = ITM), delta, DTE, breakeven, mark vs credit (% of max profit captured), assignment notional, max loss for spreads.
Action flags (Playbook v2):
- **ITM** or **delta <= -0.30** or **spot within 7% of strike**: defense. Give hold / roll down-and-out for a credit / close / take assignment (effective basis).
- **<= 21 DTE and ITM/near**: gamma rule, act now.
- **>= 50% of credit captured**: velocity profit-take; check a GTC close is working (`get_option_orders` working). If not, say "no GTC resting".
- **Short < 30 DTE** opened without an OPP tag: note it.
- **Debit trades**: apply the 3:1 test (reward:risk).
- **Earnings before expiry** (`get_earnings_results`, mark unverified "tent."): flag.

**Step 3: Book-level**
- **10% NAV cap** per name: (short put assignment notional + held shares value) / NAV. List anything >= 8% and mark >10% red.
- Ticker with a short leg or short stock is always "watched"; short stock = unlimited risk, say so.
- **Move check**: for tickers with short legs/short stock, `get_equity_historicals` (interval day, ~6 calendar days, <=10 symbols per call); flag >= 8% close-to-close, cause "unknown" unless sourced. Sub-$10B names with short puts: `get_sec_filing_index` for 8-K/offering/13D.
- Cash %, buying power %, margin use.
- Today's fills: any second opening ticket on one name in a day (rule: one opening ticket per name per day); any put sold on an underwater held lot.

**Output (chat)**
1. One line: NAV, cash, BP, day change.
2. **Act today** (max 5, most urgent first): ticker, leg, why, suggested action.
3. Table of short legs, sorted by cushion: leg, spot, cushion %, delta, DTE, % captured, flag. Show flagged + cushion <= 10%; one line for the rest.
4. Cap table (names >= 8% NAV).
5. Earnings/catalysts inside expiry windows.
6. Footer: "Points to weigh, not orders."
