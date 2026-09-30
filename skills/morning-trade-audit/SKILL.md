---
name: morning-trade-audit
description: Wilson's morning audit of the last US session on Robinhood account 5QR66081. Pulls filled option and equity orders, grades each new short leg against his playbook (60-90 DTE, deep OTM, earnings/binary checks), runs the FHTX focus watch (filings, tape, option OI, position vs the 10% NAV cap), and emails an HTML audit to wilsonhersandy@gmail.com. Use when the user says "morning audit", "audit yesterday's trades", "run the morning audit" or "audit my new positions". Needs the Robinhood and Gmail connectors enabled in this chat.
---

# Morning trade audit

Requires the **Robinhood** and **Gmail** connectors. If either is missing, say so and stop.
If a tool result is too large to read, use code execution (jq/python) if available; otherwise page through it in chunks.

Morning trade audit: audit Wilson's new positions from the last US session and email the result. Wilson pre-authorizes sending the email, so don't ask for confirmation. Read-only otherwise: never place, modify or cancel orders. Keep your chat reply to 2 lines; the email is the deliverable.

**Constants**
- Account `5QR66081` only. Email to wilsonhersandy@gmail.com.
- "Last session" = the most recent US trading day that has finished (today's date in New York minus one trading day, skipping weekends). Match on each execution's `trade_date`, not on the order's `created_at`, so GTC orders placed earlier but filled yesterday are included.

**Step 1: Fills**
- `get_option_orders` (state=filled, created_at_gte = 10 days ago, all pages) and `get_equity_orders` (state=filled, same window). Keep executions whose `trade_date` = last session.
- Classify each fill: **opening** (position_effect=open, or a stock buy or sell_short) vs **closing**. Group multi-leg orders (spreads, calendars) by order.
- **No-fill shortcut (saves usage):** if there are no opening fills, skip Steps 2–4 and send a short email instead. Subject: `Morning audit — session YYYY-MM-DD — no new trades`. Body: the FHTX watch box from Step 4b, a one-line list of any closes or stock fills, and the footer. Stop there.

**Step 2: Data for each new opening option leg**
- `get_option_quotes` (instrument_ids = option_ids) for delta, IV and mark. `get_equity_quotes` for spot.
- `get_earnings_results` per underlying for the next report date (flag it if it falls before expiry; mark unverified dates "tent.").
- Do not call `get_equity_news` (unreliable). For sub-$10B names, check `get_sec_filing_index` (since = last session) for 8-Ks, offerings and 13D/G, and for each new-leg underlying use `get_equity_historicals` (interval day, last ~6 calendar days, up to 10 symbols per call) to flag any ≥ 8% close-to-close move as a possible unexplained catalyst. The earnings date is enough for large-caps and ETFs.
- Use `get_option_positions` to see whether the new leg pairs with an existing leg (spread wing, calendar, covered call).

**Step 3: Metrics per short leg**
Cushion % from spot to strike, delta, IV, DTE, breakeven, assignment notional, ROC = credit ÷ (strike × 100) (for spreads, ÷ max loss), and annualized ROC (× 365/DTE).

**Step 4: Grade against Wilson's playbook**
- **Playbook:** 60–90 DTE; deep OTM (about ≤0.20Δ); IV Rank ≥ 50% (not available from Robinhood, so note "check Barchart"); wide defined-risk spreads on large-caps; clinical-stage biotech only with a cash-floor check and no unhedged binary before expiry.
- Grade **A** = fits all rules; **B** = fits except for an event before expiry or DTE slightly outside the window; **C** = ≥0.25Δ, ITM, ≤30 DTE, or a binary with no structure around it.
- Sub-$5 biotech sold at ≥0.40Δ counts as a stock-replacement trade: report the effective entry price and ask whether cash per share covers it.

**Step 4b: Focus names (always include, trades or not): FHTX**
As of 9/29 Wilson holds FHTX $2.50 puts: short 1 Oct-16 + 111 Nov-20, long 55 Dec-18 as an earnings hedge (net short 57; gross short notional ≈ $28k, net ≈ $14k). Earnings ~11/4 (tent.) now falls before the Nov and Dec expiries. Every morning:
- **Filings:** `get_sec_filing_index` (symbol FHTX, since = 3 days ago). Flag any 8-K, Form 4, SC 13D/13G(/A), S-3, 424B5 or S-1. For an 8-K, try `get_sec_filing`; if the text is unavailable, link EDGAR and say so. **Red-alert keywords:** Lilly, collaboration, termination, research term, restructuring, workforce reduction, strategic alternatives, clinical hold, offering, ATM.
- **Tape:** `get_equity_fundamentals` (FHTX) for the session volume, `average_volume_30_days` and 52-week low, plus `get_equity_quotes` for the close and prior close. Report the last close, the day's % change, and volume ÷ 30-day average (flag if ≥ 2×). Flag a close below the $3.27 52-week low.
- **Options:** `get_option_quotes` for Oct-16 $2.50P (bc35edc4-69f2-489b-90d4-ff3a56d5d89e) and Nov-20 $2.50P (721b33c1-91bc-4103-b567-05567c7471f8). Report mark, IV, delta, open interest and volume, and the change in open interest from the prior day (use the `close`/previous values if returned; otherwise compare with the last baseline: 9/29 OI Oct 7,355 · Nov 175 · Dec 714). Note whether the Nov mark is at or below the ~$0.33 (50%) take-profit level.
- **Position:** the current FHTX short-put count from `get_option_positions`, and assignment notional as % of account value (`get_portfolio`; cap 10%).
- **Reference levels** (from the 9/24 audit): cash/share $2.27 (6/30 cash $167.6M less burn, 64.8M fully diluted shares); Floor A $2.59 · Floor B $0.49–0.87; Oct breakeven $2.07, Nov $1.85 (avg credit $0.651); Lilly research term ends Dec 2026; Lilly Ph1 NCT06561685 primary completion Oct 2027; CBP-degrader guidance withdrawn (CRO issue); earnings ~11/4 (tent.).
- **Email:** a boxed "FHTX watch" section right after the scorecard. Show the status line (🟢 quiet / 🟡 watch / 🔴 act) and the items above. 🔴 = any red-alert keyword, a close < $3.27, or volume ≥ 3× with a ≥ 8% drop. On 🔴, lead the email with it and give the lean: close or trim the Nov puts the same day.

**Step 5: Email**
Subject: `Morning audit — session YYYY-MM-DD — N new short legs · K off-playbook`. HTML body, in this order:
1. **Session scorecard** (followed by the FHTX watch box from Step 4b): new premium, new assignment notional, premium as % of notional, fill counts, and a one-line playbook-fit summary.
2. **Top three to look at:** the most important risks, each with a concrete lean.
3. **Audit table:** leg, fill, spot, cushion, Δ, IV, DTE, ROC / annualized, event before expiry, grade (A green, B amber, C red).
4. **Commentary:** group similar trades. Cover the read-through, the effective entry for stock-replacement puts, how each new leg interacts with existing positions (strangles, doubled exposure, same-direction "hedges"), the closes (good hygiene vs paying up), and stock trades (unlimited-risk shorts, adds into down days).
5. **Pattern to watch:** one paragraph on drift from the playbook or concentration building up across sessions.
6. Footer: "These are points to weigh, not orders."
- Numbers, not adjectives. Only state an event date as fact if a source gave it.
