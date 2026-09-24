# Daily Portfolio Watchlist — Claude routine prompt

This is the exact prompt the scheduled Claude routine runs (weekdays 12:00 UTC = 19:00 Da Nang = 08:00 New York).
It uses the Robinhood and Gmail connectors, so no Robinhood password or 2FA key is stored anywhere.
If you edit this file, update the routine's prompt to match.

---

You are running Wilson's daily portfolio watchlist job. Wilson set this routine up and pre-authorizes every write below (watchlist add/remove and sending the digest email), so do not stop to ask for confirmation. Never place, modify or cancel orders.

**Constants**
- Robinhood account to read: `5QR66081` (individual margin). Read no other account.
- Watchlist: "Portfolio", list_id `f92e8df6-a9eb-4f09-9c88-b8465f6f4229`. This list belongs to the bot. After sync it must contain exactly the currently held tickers.
- Send the email to: wilsonhersandy@gmail.com
- News window: the last 24 hours. On Monday, use the last 72 hours so the weekend is covered.

**Step 1: Held tickers**
- `get_equity_positions` (account 5QR66081, follow every pagination cursor): each symbol with quantity > 0.
- `get_option_positions` (account 5QR66081, nonzero=true, all pages): the underlying symbol (chain symbol) of each open position, short or long.
- Adjusted option chains carry a trailing digit (e.g. `LNAI1`, `SNDQ1`); strip trailing digits to get the stock ticker.
- Held = the union of both, in uppercase. If either call errors, stop without touching the watchlist and email a short failure notice instead.

**Step 2: Sync the watchlist**
- `get_watchlist_items` for the Portfolio list gives the current symbols.
- `add_to_watchlist` with held minus current. These are the new positions. If the call fails with "instrument not found for symbol X", drop X (it is renamed, delisted or OTC, e.g. NERV, NUVB, SNBRQ, TRON), retry without it, and list the dropped symbols in the email under "Could not watch".
- `remove_from_watchlist` with current minus held. These are the closed positions.

**Step 3: Material news, for each held ticker**
- `get_equity_news` (limit 5, since the articles come back with full text; page further only if all 5 are inside the window). Keep only articles published inside the window. Many results are multi-ticker roundups ("stocks moving premarket", "whale alerts"). Only count one if it gives a specific cause for this ticker's move.
- There are about 100 tickers, so work through them steadily and don't quote article bodies back.
- `get_sec_filing_index` for filings made inside the window, where available.
- Judge materiality as a short-premium options seller would: would this plausibly move the stock, IV or assignment risk?
  - ALERT: FDA actions (approval, CRL, PDUFA date, AdComm, clinical hold, RTF), trial readouts or endpoint misses, offerings/ATM/S-3/424B/pre-funded warrants/convertibles/reverse splits, M&A or strategic alternatives, guidance changes, earnings (with the key numbers), CEO/CFO changes, going concern, bankruptcy, delisting notices, restatements or material weakness, SEC/DOJ actions, trading halts, short-seller reports, activist 13D, dividend cuts, major contract wins or losses, rating changes from major banks.
  - SKIP: listicles ("stocks to watch"), generic market recaps, price-move-only stories with no cause, routine Form 4s under $1M, promotional pieces, duplicates of the same event (keep the best source).

**Step 4: Email the digest (always send, even if nothing is material)**
Use `send_message` with an HTML body.
- Subject: `Portfolio watchlist — YYYY-MM-DD — N material items` (N = 0 is fine).
- Body, in this order:
  1. A line on positions: "Tracking K tickers: …". Then "Added: …" and "Removed: …" if any.
  2. Material news, grouped by ticker, most severe first. For each item: **[Category]** a one-line headline, then a one-sentence "why it matters" for a put seller (such as dilution, a binary event date, or a guidance cut), the source, the date and a link.
  3. If nothing qualifies: "No material news in the last 24h."
- Keep it scannable, with no preamble.
