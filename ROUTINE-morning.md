# Morning Trade Audit — Claude routine prompt

Runs Tue–Sat at 02:00 UTC (09:00 Da Nang), after the US close, and audits the fills from the last US session.
It fires into the original setup session, which holds the Robinhood and Gmail connectors.
If you edit this file, update the routine's prompt to match.

---

Morning trade audit: audit Wilson's new positions from the last US session and email the result. Wilson pre-authorizes sending the email, so don't ask for confirmation. Read-only otherwise: never place, modify or cancel orders. Keep your chat reply to 2 lines; the email is the deliverable. Large tool results get saved to files; parse them with jq rather than reading them in full.

**Constants**
- Account `5QR66081` only. Email to wilsonhersandy@gmail.com.
- "Last session" = the most recent US trading day that has finished (today's date in New York minus one trading day, skipping weekends). Match on each execution's `trade_date`, not on the order's `created_at`, so GTC orders placed earlier but filled yesterday are included.

**Step 1: Fills**
- `get_option_orders` (state=filled, created_at_gte = 10 days ago, all pages) and `get_equity_orders` (state=filled, same window). Keep executions whose `trade_date` = last session.
- Classify each fill: **opening** (position_effect=open, or a stock buy or sell_short) vs **closing**. Group multi-leg orders (spreads, calendars) by order.
- If there are no fills, send a one-line email ("No trades in session YYYY-MM-DD") and stop.

**Step 2: Data for each new opening option leg**
- `get_option_quotes` (instrument_ids = option_ids) for delta, IV and mark. `get_equity_quotes` for spot.
- `get_earnings_results` per underlying for the next report date (flag it if it falls before expiry; mark unverified dates "tent.").
- Check the last 30 days of `get_equity_news` (limit 3) for known catalysts before expiry (PDUFA, AdComm, trial readouts, offerings).
- Use `get_option_positions` to see whether the new leg pairs with an existing leg (spread wing, calendar, covered call).

**Step 3: Metrics per short leg**
Cushion % from spot to strike, delta, IV, DTE, breakeven, assignment notional, ROC = credit ÷ (strike × 100) (for spreads, ÷ max loss), and annualized ROC (× 365/DTE).

**Step 4: Grade against Wilson's playbook**
- **Playbook:** 60–90 DTE; deep OTM (about ≤0.20Δ); IV Rank ≥ 50% (not available from Robinhood, so note "check Barchart"); wide defined-risk spreads on large-caps; clinical-stage biotech only with a cash-floor check and no unhedged binary before expiry.
- Grade **A** = fits all rules; **B** = fits except for an event before expiry or DTE slightly outside the window; **C** = ≥0.25Δ, ITM, ≤30 DTE, or a binary with no structure around it.
- Sub-$5 biotech sold at ≥0.40Δ counts as a stock-replacement trade: report the effective entry price and ask whether cash per share covers it.

**Step 5: Email**
Subject: `Morning audit — session YYYY-MM-DD — N new short legs · K off-playbook`. HTML body, in this order:
1. **Session scorecard:** new premium, new assignment notional, premium as % of notional, fill counts, and a one-line playbook-fit summary.
2. **Top three to look at:** the most important risks, each with a concrete lean.
3. **Audit table:** leg, fill, spot, cushion, Δ, IV, DTE, ROC / annualized, event before expiry, grade (A green, B amber, C red).
4. **Commentary:** group similar trades. Cover the read-through, the effective entry for stock-replacement puts, how each new leg interacts with existing positions (strangles, doubled exposure, same-direction "hedges"), the closes (good hygiene vs paying up), and stock trades (unlimited-risk shorts, adds into down days).
5. **Pattern to watch:** one paragraph on drift from the playbook or concentration building up across sessions.
6. Footer: "These are points to weigh, not orders."
- Numbers, not adjectives. Only state an event date as fact if a source gave it.
