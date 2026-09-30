---
name: portfolio-watchlist-digest
description: Wilson's daily Robinhood portfolio job. Reads account 5QR66081, syncs the "Portfolio" watchlist (all short-option and short-stock tickers plus positions at risk ≥ $5k), computes book risk on every short option leg, checks SEC filings and big price moves for the names that matter, and emails an HTML digest to wilsonhersandy@gmail.com. Use when the user says "run the daily digest", "watchlist digest", "portfolio watchlist", "daily run" or "run my portfolio job". Needs the Robinhood and Gmail connectors enabled in this chat.
---

# Portfolio watchlist digest

Requires the **Robinhood** and **Gmail** connectors. If either is missing, say so and stop.
If a tool result is too large to read, use code execution (jq/python) if available; otherwise page through it in chunks. Keep the chat reply to 2-3 lines (adds/removes, N material items, K flagged legs, email sent); the email is the deliverable.

Run Wilson's portfolio watchlist job. Invoking this skill pre-authorizes every write below (watchlist add/remove and sending the digest email), so do not stop to ask for confirmation. Never place, modify or cancel orders.

**Constants**
- Robinhood account to read: `5QR66081` (individual margin). Read no other account.
- Watchlist: "Portfolio", list_id `f92e8df6-a9eb-4f09-9c88-b8465f6f4229`. This list belongs to the bot. After sync it must contain exactly the watch set from Step 2.
- Send the email to: wilsonhersandy@gmail.com
- Window: the last 24 hours. On Monday (or when run after a weekend), use the last 72 hours.

**Step 1: Positions, grouped by ticker**
- `get_equity_positions` (account 5QR66081, follow every pagination cursor): symbol, signed quantity.
- `get_option_positions` (account 5QR66081, nonzero=true, all pages): chain_symbol, type (long/short), quantity, average_price (per contract, already ×100).
- Adjusted option chains carry a trailing digit (e.g. `LNAI1`, `SNDQ1`); strip trailing digits to get the stock ticker.
- If either call errors, stop without touching the watchlist and email a short failure notice instead.

**Step 2: Decide what to watch**
- **Always watch** any ticker with at least one **short** option leg (short puts, short calls, credit spreads, e.g. FHTX) **or a short stock position** (unlimited risk, e.g. KOD), regardless of size.
- For every other ticker, compute **$ at risk** = |stock quantity| × last price (`get_equity_quotes`, at most 20 symbols per call) + for long options Σ |average_price| × quantity (the premium paid, which is the most you can lose).
- Use the current Portfolio list (`get_watchlist_items`) as memory, with hysteresis:
  - Not on the list: add if $ at risk ≥ **$5,000**.
  - Already on the list: keep while $ at risk ≥ **$4,000**; remove below that.
- Watch set = always-watch ∪ tickers passing the $ rule.

**Step 3: Sync the watchlist**
- `add_to_watchlist` with the watch set minus the current list. If the call fails with "instrument not found for symbol X", drop X (it is renamed, delisted or OTC, e.g. NERV, NUVB, SNBRQ, TRON), retry without it, and list the dropped symbols in the email under "Could not watch".
- `remove_from_watchlist` with the current list minus the watch set, covering both closed positions and ones now below the threshold.

**Step 4: Book risk (every short option leg, news or not)**
- Collect every short leg's option_id from Step 1. Call `get_option_instruments` with `ids` (comma-separated, up to ~55 per call) to get strike, type and expiry. Get spot prices from `get_equity_quotes`. Use the long legs to identify the structure: a same-expiry long put below a short put is a put spread; a short call against ≥100 shares per contract is a covered call; a same-strike long in a later month is a calendar.
- For each short leg compute: moneyness % (puts: (spot−K)/spot; calls: (K−spot)/spot; negative means ITM), DTE, breakeven (puts K − credit/100; calls K + credit/100), assignment notional (K × 100 × qty), and max loss for spreads (width × 100 − net credit).
- **Flag** a leg if it is ITM, within 5% of the strike, or expiring within 7 days.

**Step 5: Material events, for the scope only (saves usage; no news feed)**
- Robinhood's news feed (`get_equity_news`) is unreliable, so **do not call it**. Material events come from SEC filings and price moves.
- **Scope** = tickers added in Step 3 · tickers with a flagged leg · tickers whose nearest short leg has a cushion ≤ 20% or ≤ 21 DTE · FHTX (always) · stock-only positions with ≥ $15k at risk. Skip every other ticker and broad index ETFs (QQQ, SGOV, SCHX, SCHA, FNDA, FNDX, VOOG). On Mondays, widen the scope to the whole watch set.
- `get_sec_filing_index` (since = window start) only for sub-$10B names in scope that have short puts or a short stock position. For any 8-K or offering filing, try `get_sec_filing` to read it. If the text isn't available, say so and link to EDGAR. Retry a throttled call once.
- **Price-move check:** quotes carry only one close, so they can't show a close-to-close move before the open. For the in-scope tickers with short puts, short calls or short stock, call `get_equity_historicals` (interval day, start ≈ 6 calendar days back, up to 10 symbols per call) and compare the last two daily closes. Flag any move ≥ 8% (also compare the overnight/pre-market last price with the last close for a second flag). Say the cause is unknown; do not guess one.
- Judge materiality as a short-premium options seller would: would this plausibly move the stock, IV or assignment risk?
  - ALERT: 8-K items (FDA/clinical, financing, M&A, strategic alternatives, CEO/CFO change, going concern, bankruptcy, delisting notice, restatement), offerings/ATM/S-3/424B, activist 13D/13G, Form 4 insider sales over $1M, earnings with the key numbers, and ≥ 8% price moves.
  - SKIP: routine 10-Q/10-K, small Form 4s, duplicates.

**Step 6: Analysis for each material item and each flagged leg**
Write tight commentary, using numbers, not adjectives:
- **Your position:** the structure, strikes, expiry, credit, spot, cushion %, DTE, breakeven and assignment or max-loss dollars.
- **Read-through:** what the filing or price move means for the thesis (e.g. dilution math, what a filing implies, sector or macro driver). Separate signal from noise.
- **Next dates:** earnings, PDUFA/AdComm, trial readouts, ex-dividend, Nasdaq $1 minimum-bid clock, expiry. Only state a date as fact if a source gave it; otherwise say "check whether earnings land before expiry".
- **To consider:** hold / roll down-and-out for a credit / close / take assignment (with effective cost basis) / hedge / write more covered calls. End with a one-line **Lean**. These are points to weigh; never place orders.
- For a clinical-stage biotech with a binary or dilution event, note that it warrants a full cash-floor and dilution audit. For a dislocated large-cap, note that it's a candidate for the put-overreaction screen.

**Step 7: Email the digest (always send, even if nothing is material)**
Use `send_message` with an HTML body.
- Subject: `Portfolio watchlist — YYYY-MM-DD — N material items`, plus ` · K flagged` if any legs are flagged.
- Body, in this order:
  1. **Today's take:** a shaded box with the 3–5 things that need attention, most urgent first (ITM or expiring legs, then material news).
  2. A line on positions: "Tracking K tickers". Then "Added: …" and "Removed: …" if any, each with the reason (new short option, crossed $5k, closed, fell below $4k). List "Could not watch" symbols if any.
  3. **Material events + analysis:** per ticker, most severe first: **[Category]** filing or move, source, date and link, then the Step 6 commentary. End the section with one grey line listing the tickers checked with nothing material. No news headlines are pulled; don't apologise for it in the email.
  4. **Book risk table:** leg, spot, moneyness (red if ITM, amber if within 5%), DTE, breakeven, note. **Mondays: every short leg. Other days: only flagged legs and legs with a cushion ≤ 10%**, followed by one line "N other legs, all >10% OTM". Then one line on the largest position that isn't flagged.
  5. **Macro backdrop:** 1–2 lines from quotes only (QQQ, IBIT/BTC, NVDA moves vs the prior close) and what they mean for the book. Don't cite rates or Fed odds unless a source gave them.
  6. Footer: "These are points to weigh, not orders."
- Keep it scannable, with no preamble.
