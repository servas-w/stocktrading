# Report layout (all four modes)

Every report has the same four sections in the same order. Section 2 is the main body (about 60% of the reading words). The mode file says what goes into each slot for that mode.

## Header (2 lines)
`<Report name> · <session date> · Ref <PM|MD|AH|WK>-<date>`
`Runner: <Claude|Gemini> · Updated HH:MM ET / HH:MM ICT (vN) · Feed: <feed name, run time> · Check: <check figure>`

## Section 1 — Summary (≤ 7 lines, ≤ 120 words)
- **Market:** one sentence.
- **Book:** NAV, change vs QQQ (AH/WKND), cash vs floor, number of positions needing action.
- **Yesterday / this morning:** execution in one line (`X of Y actions done`) plus the biggest slip.
- **Top 3–5 items** with 🔴/🟡 markers, one line each, repeat triggers first (`REPEAT ×n`).
- `STALE FEED (<age>)` goes on the first line when it applies.

## Section 2 — Market & your book (main body)
Each item follows the template in `style.md`. Slots, in order:
- **2.1 Story of the day:** the one driver, why it happened, 3–5 sentences. Add the chapter for each running story (AI capex, oil/geopolitics, Fed path, biotech funding, crypto, China) only when something new happened.
- **2.2 Movers that matter:** three groups, in this order: (a) your names, (b) names that move your names (peers, suppliers, customers, sympathy), (c) the market's biggest movers. Table: ticker · move (1-day, 5-day) · why (cause tag) · your exposure. Then items for the 3–5 that matter most. A big move with `no news` is flagged.
- **2.3 Themes & read-throughs:** one line per theme you hold: direction, driver, your names, net effect on the book.
- **2.4 Your book today:** what made and lost money (top 3 each, and why); benchmark line (AH/WKND); positions that got more dangerous; expected move vs cushion for upcoming events; expiry and assignment exposure vs buying power; short-squeeze watch on short stock; liquidity warnings (zero bid, wide spread); red flags (S-3/ATM, reverse split, delisting, bankruptcy tickers, insider selling, analyst cuts).
- **2.5 What to watch:** next 24 hours and the week, filtered to your book (earnings of held names and peers, macro data, Fed, FDA dates, expiries, ex-dividend dates on covered calls); if-then lines; the top 3 risks to the book with their early-warning sign.
- **2.6 Opportunities (PRE, AH, WKND):** dislocated large caps and premium that got rich, each labelled `candidate — run LC/BIO underwriting first`. Never an order.

## Section 3 — Action plan (≤ 500 words)
- **Order table** (≤ 8 rows; more go to the Appendix): `🔴/🟡 · ticker · contract · side · qty · limit · rule · feed row`. Repeat triggers first. The **feed row** column copies the matching line from the book source exactly (ticker · type · strike · expiry · qty). An order without a matching feed row is dropped.
- **Do not do:** the 2–4 things to avoid today (adds on tested names, new shorts into earnings, scalping…).
- **If-then gates:** 3–5 lines with levels or times.

## Section 4 — Appendix (not counted in the word caps)
- **A1 Book:** feed line, check-figure line, reconcile line (Claude), trigger scan line, Book Triggers (full), R5 concentration table (max-loss method), held-lot table, tripwire map.
- **A2 Market data:** cross-asset dashboard, 11-sector table, Mag 7 table, bands and volatility, gamma (or N/A/STALE).
- **A3 Benchmark & scorecard** (AH line; WKND full tables).
- **A4 Journal rows** (AH/WKND).
- **A5 Source notes** (every Section 1–3 number: value · what · link · page time) and the Integrity line.
- **A6 War Room Handoff** in a ```text code block.

## Word caps for the reading sections (Sections 1–3)
| Mode | Section 1 | Section 2 | Section 3 | Total |
|---|---|---|---|---|
| PRE | 120 | 1,200 | 500 | 1,820 |
| MID | 120 | 1,000 | 400 | 1,520 |
| AH | 120 | 1,500 | 500 | 2,120 |
| WKND | 150 | 2,500 | 500 | 3,150 |
