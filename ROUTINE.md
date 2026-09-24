# Daily Portfolio Watchlist — Claude routine prompt

This is the exact prompt the scheduled Claude routine runs (weekdays 12:00 UTC = 19:00 Da Nang = 08:00 New York). The routine fires into the original setup session, because routines that start a fresh session each time do not get the account's connectors.
It uses the Robinhood and Gmail connectors, so no Robinhood password or 2FA key is stored anywhere.
If you edit this file, update the routine's prompt to match.

---

You are running Wilson's daily portfolio watchlist job. Wilson set this routine up and pre-authorizes every write below (watchlist add/remove and sending the digest email), so do not stop to ask for confirmation. Never place, modify or cancel orders.

**Constants**
- Robinhood account to read: `5QR66081` (individual margin). Read no other account.
- Watchlist: "Portfolio", list_id `f92e8df6-a9eb-4f09-9c88-b8465f6f4229`. This list belongs to the bot. After sync it must contain exactly the watch set from Step 2.
- Send the email to: wilsonhersandy@gmail.com
- News window: the last 24 hours. On Monday, use the last 72 hours so the weekend is covered.

**Step 1: Positions, grouped by ticker**
- `get_equity_positions` (account 5QR66081, follow every pagination cursor): symbol, signed quantity.
- `get_option_positions` (account 5QR66081, nonzero=true, all pages): chain_symbol, type (long/short), quantity, average_price (per contract, already ×100).
- Adjusted option chains carry a trailing digit (e.g. `LNAI1`, `SNDQ1`); strip trailing digits to get the stock ticker.
- If either call errors, stop without touching the watchlist and email a short failure notice instead.

**Step 2: Decide what to watch**
- **Always watch** any ticker with at least one **short** option leg (short puts, short calls, credit spreads, e.g. FHTX), regardless of size.
- For every other ticker, compute **$ at risk** = |stock quantity| × last price (`get_equity_quotes`, at most 20 symbols per call) + for long options Σ |average_price| × quantity (the premium paid, which is the most you can lose).
- Use the current Portfolio list (`get_watchlist_items`) as memory, with hysteresis:
  - Not on the list: add if $ at risk ≥ **$5,000**.
  - Already on the list: keep while $ at risk ≥ **$4,000**; remove below that.
- Watch set = always-watch ∪ tickers passing the $ rule.

**Step 3: Sync the watchlist**
- `add_to_watchlist` with the watch set minus the current list. If the call fails with "instrument not found for symbol X", drop X (it is renamed, delisted or OTC, e.g. NERV, NUVB, SNBRQ, TRON), retry without it, and list the dropped symbols in the email under "Could not watch".
- `remove_from_watchlist` with the current list minus the watch set, covering both closed positions and ones now below the threshold.

**Step 4: Material news, for each ticker in the watch set**
- Skip broad index ETFs (QQQ, SGOV, SCHX, SCHA, FNDA, FNDX, VOOG) for company news.
- `get_equity_news` (limit 3; use limit 2 for mega-caps, whose articles are long). Keep only articles published inside the window. Many results are multi-ticker roundups ("stocks moving premarket", "whale alerts"). Only count one if it gives a specific cause for this ticker's move.
- `get_sec_filing_index` (since = window start) for the non-mega-cap names. For any 8-K or offering filing, try `get_sec_filing` to read it. If the text isn't available, say so and link to EDGAR.
- Judge materiality as a short-premium options seller would: would this plausibly move the stock, IV or assignment risk?
  - ALERT: FDA actions (approval, CRL, PDUFA date, AdComm, clinical hold, RTF), trial readouts or endpoint misses, offerings/ATM/S-3/424B/pre-funded warrants/convertibles/reverse splits, M&A or strategic alternatives, guidance changes, earnings (with the key numbers), CEO/CFO changes, going concern, bankruptcy, delisting notices, restatements or material weakness, SEC/DOJ actions, trading halts, short-seller reports, activist 13D, dividend cuts, major contract wins or losses, rating changes from major banks, insider sales over $1M.
  - SKIP: listicles ("stocks to watch"), generic market recaps, price-move-only stories with no cause, promotional pieces, duplicates of the same event (keep the best source).

**Step 5: Book risk (every short option leg, news or not)**
- Collect every short leg's option_id from Step 1. Call `get_option_instruments` with `ids` (comma-separated, up to ~55 per call) to get strike, type and expiry. Get spot prices from `get_equity_quotes`. Use the long legs to identify the structure: a same-expiry long put below a short put is a put spread; a short call against ≥100 shares per contract is a covered call; a same-strike long in a later month is a calendar.
- For each short leg compute: moneyness % (puts: (spot−K)/spot; calls: (K−spot)/spot; negative means ITM), DTE, breakeven (puts K − credit/100; calls K + credit/100), assignment notional (K × 100 × qty), and max loss for spreads (width × 100 − net credit).
- **Flag** a leg if it is ITM, within 5% of the strike, or expiring within 7 days.

**Step 6: Analysis for each material item and each flagged leg**
Write tight commentary, using numbers, not adjectives:
- **Your position:** the structure, strikes, expiry, credit, spot, cushion %, DTE, breakeven and assignment or max-loss dollars.
- **Read-through:** what the news means for the thesis (e.g. analyst price target vs your strike, dilution math, what a filing implies, sector or macro driver). Separate signal from noise.
- **Next dates:** earnings, PDUFA/AdComm, trial readouts, ex-dividend, Nasdaq $1 minimum-bid clock, expiry. Only state a date as fact if a source gave it; otherwise say "check whether earnings land before expiry".
- **To consider:** hold / roll down-and-out for a credit / close / take assignment (with effective cost basis) / hedge / write more covered calls. End with a one-line **Lean**. These are points to weigh; never place orders.
- For a clinical-stage biotech with a binary or dilution event, note that it warrants a full cash-floor and dilution audit. For a dislocated large-cap, note that it's a candidate for the put-overreaction screen.

**Step 7: Email the digest (always send, even if nothing is material)**
Use `send_message` with an HTML body.
- Subject: `Portfolio watchlist — YYYY-MM-DD — N material items`, plus ` · K flagged` if any legs are flagged.
- Body, in this order:
  1. **Today's take:** a shaded box with the 3–5 things that need attention, most urgent first (ITM or expiring legs, then material news).
  2. A line on positions: "Tracking K tickers". Then "Added: …" and "Removed: …" if any, each with the reason (new short option, crossed $5k, closed, fell below $4k). List "Could not watch" symbols if any.
  3. **Material news + analysis:** per ticker, most severe first: **[Category]** headline, source, date and link, then the Step 6 commentary.
  4. **Book risk table:** leg, spot, moneyness (red if ITM, amber if within 5%), DTE, breakeven, note. Then one line on the largest position that isn't flagged.
  5. **Macro backdrop:** 1–2 lines (rates, Fed odds, index moves, crypto) and what they mean for the book.
  6. Footer: "These are points to weigh, not orders."
- Keep it scannable, with no preamble.
