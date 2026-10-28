---
name: biotech-ticker-sentinel
description: Keeps a Google Sheet watchlist of biotech tickers that Wilson adds and removes by hand, and for every ticker on it reports (1) any new news or SEC filing, (2) the day's price move and the most likely reason for it, and (3) options IV, put and call skew and term structure read against the next catalyst, naming the specific put contract when a setup is worth selling premium into. Use when the user says create my watchlist, run the sentinel, check my watchlist, any news on my biotechs, why is TICKER moving, IV check or skew check, and for the scheduled daily run.
---

# Biotech Ticker Sentinel

Three jobs for each ticker on the watchlist, and nothing else:
1. **News**: is there any?
2. **Price**: how did it move, and why?
3. **IV**: is there skew or rich premium to take advantage of? If so, which contract?

No portfolio audits, no position management, no orders.

## Rules (override everything below)

- **Numbers come from a page you opened this run.** Write each as `value (source, time ET)`. If you couldn't get one, write `n/a`. Never estimate, and never reuse a number from memory.
- **Links**: only pages you opened this run.
- **"No news" needs proof.** List what you checked and the newest item on each, e.g. `SEC: 8-K 10/22 · IR: PR 10/14`. If a source failed to load, the status is `UNVERIFIED`, not `NO NEWS`.
- **Don't invent a reason for a move.** If nothing explains it, say `no identifiable catalyst`.
- **Read IV as the page shows it.** You can't calculate IV. Only divide, subtract and compare displayed numbers, and show the inputs to every ratio so Wilson can check them.
- **Times**: ET and Da Nang. Da Nang is ET+11 during US daylight time and ET+12 otherwise. US clocks change on the second Sunday of March and the first Sunday of November.
- **Read-only**: never place orders and never log into brokerage accounts.

## Fixed data sources (use the same ones every run so numbers compare)

| Data | Source | Fallback |
|---|---|---|
| Price, % change, volume, average volume, XBI | Yahoo Finance quote page (`finance.yahoo.com/quote/TICKER`) | Google Finance |
| Option chains: bid, ask, volume, open interest, IV per contract | Yahoo Finance options page (`finance.yahoo.com/quote/TICKER/options`, pick each expiry) | Nasdaq option chain (it has no IV, so skew is `n/a`) |
| IV30, IV Rank, IV Percentile, historical volatility | Barchart options overview for the ticker | `n/a`. Never derive these yourself. |
| Filings | SEC EDGAR company filings page | none: mark `UNVERIFIED` |
| Press releases | Company IR site | a news search |

**Is a contract's IV usable?** It needs all four of:
- a live bid and ask, both > 0
- a spread (ask − bid) no more than 35% of the mid ((bid + ask) ÷ 2)
- open interest ≥ 25, or volume today > 0
- for an at-the-money check, a put and call IV at the same strike within 20 vol points of each other

If the target strike fails, step one strike at a time toward at-the-money, staying within 10% of the target. If nothing passes, that reading is `n/a (chain too thin)`. A thin chain is useful information too: fills will be poor.

## The watchlist (Google Sheet)

**`create my watchlist [tickers]`** creates a Google Sheet named **Biotech Sentinel** with two tabs. If the sheet already exists, open it instead.

**Tab `Watchlist`**: Wilson adds and deletes rows by hand.

| Ticker | Added | Next catalyst | Catalyst date | Catalyst source | Notes |
|---|---|---|---|---|---|

- Monitor **every ticker listed**. Skip a row only if `Notes` contains the word `pause`.
- Never add or delete tickers yourself.
- You may fill `Next catalyst`, `Catalyst date` and `Catalyst source` when a filing, IR page or company presentation confirms them.
- For guidance like "Q4 2026", write the window as it was guided (e.g. `Q4 2026`).

**Tab `Log`**: you append one row per ticker per run.

| Run (ET) | Ticker | Close | % chg | XBI % chg | Volume | Avg vol | IV30 | IV Rank | IV Pctl | HV30 | Front ATM IV | Back ATM IV | Put ratio | Call ratio | Flags | News |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

- A ticker's most recent row is its **baseline**. With no row, the baseline is `none (first run)`.
- If the sheet can't be written, say so at the top of the report and carry on.

## Each run

**First, check that the market was open.** If the latest regular-session date on Yahoo isn't the most recent US trading day you expect, write `US market closed <date> (holiday)`. Then run news only and skip price and IV.

### 1. News (every ticker)
**Window**: since that ticker's last `Log` row. With no row, since the previous US close (4:00 PM ET); on a Monday, since Friday's close.

**Check**:
1. **SEC EDGAR**: the form type, and the item number for 8-Ks.
2. **The company's IR press releases.**
3. **A news search** for the ticker and its lead drug, limited to the window.
4. **If a clinical or FDA event is pending**: FDA/AdComm notices, ClinicalTrials.gov changes and medical-meeting abstracts.

**Status**:
- `NEW NEWS`: what, when (ET), link, and one line on why it matters.
- `NO NEWS since <time>`: with the receipts.
- `UNVERIFIED (<source> failed)`.

**Mark 🔴 (urgent)** for:
- an offering, ATM sale or new shelf (S-3, 424B5)
- FDA approval, a CRL or a PDUFA date change
- a clinical hold
- topline trial data
- partnership or M&A news
- debt trouble, restructuring or going-concern language
- a 13D
- an insider buying or selling on the open market (Form 4; ignore 10b5-1 sales and tax withholding)

**Catalyst**: if news changes the next catalyst or its date, update the `Watchlist` row and say so.

### 2. Price move and why
- **Get**: close, % change, intraday range, volume vs average volume, any after-hours move, and XBI's % change.
- **Excess move** = the stock's % change − XBI's % change.
- **Explain the move by weighing these. Don't just stop at the first one that fits**:
  - **Sector**: an excess move under 3 points means **"moved with biotech"**. That's the main reason, even when there's minor news, unless a 🔴 item landed.
  - **Company news** from step 1 that came out at or just before the move.
  - **Peer read-across**: a competitor's data or FDA decision on the same target or disease, the same day.
  - **Financing**: an S-3, 424B5 or ATM filing in the last 30 days (from the EDGAR check), or the price falling toward a recent offering price.
  - **Options or positioning**: contract volume above its open interest on the Yahoo chain, or an options-expiry Friday.
  - **Catalyst drift**: days to the next catalyst from the `Watchlist` tab. A run-up into a catalyst, or de-risking selling ahead of it.
- **Give a primary reason and a confidence level**:
  - **high**: dated news lines up with the move
  - **medium**: a plausible cause, no direct link
  - **low**
- If nothing fits: `no identifiable catalyst`. Add the volume context; a big move on below-average volume is usually thin and technical.
- **Big move**: ±8% or more, or volume 3× average or more. These go to the top of the report.

### 3. Options IV

**Pick the expiries**:
- **Front**: the nearest expiry with at least 7 days left.
- **Back**: the expiry closest to 75 days (allow 60–90). This is the month Wilson sells.

**Measure**:
- **From Barchart**: IV30, IV Rank, IV Percentile and HV30. **Vol premium** = IV30 ÷ HV30.
  - Note: right after a gap, HV30 is inflated for about a month, which makes this ratio understate how rich the options are.
- **ATM IV** (front and back): the average of the put and call IV at the strike nearest the price.
- **Skew, measured in the back month, as ratios rather than vol points** (so names at 60% and 200% IV compare):
  - **Put ratio** = IV of the put near 75% of the price ÷ back ATM IV.
  - **Call ratio** = IV of the call near 125% of the price ÷ back ATM IV.
  - **Shape**:
    - `put skew`: put ratio > call ratio by 0.05 or more
    - `call skew`: call ratio > put ratio by 0.05 or more. The market is pricing upside, which is common before a binary event.
    - otherwise `flat`.
- **Term ratio** = front ATM IV ÷ back ATM IV.
- **Catalyst placement**: compare the `Catalyst date` with both expiries.
  - A decision date on a weekend or holiday can land on the trading day before, so treat that expiry as carrying the event.
  - A window like "Q4" counts as inside any expiry it overlaps.
- **Changes**: compare each number with the baseline row.

**Flags.** These are setups worth looking at, not trades. Read term structure against where the catalyst falls:

| Flag | When | Meaning for a put seller |
|---|---|---|
| `RICH PREMIUM` | IV Rank ≥ 50 and vol premium ≥ 1.3 | Options are expensive versus their own history and how much the stock really moves. Your gate for selling puts is met. |
| `RICH PUTS` | Put ratio ≥ 1.15, or up ≥ 0.10 vs baseline | Out-of-the-money puts carry extra crash premium. Favors deep out-of-the-money puts or wide bull put spreads. |
| `PUTS NOT PAID` | Put ratio ≤ 1.00, or shape is `call skew` | The market prices upside, not a crash. Deep puts aren't paid for the gap risk. Don't sell puts for "skew" here. |
| `EVENT IN FRONT` | Catalyst on or before the front expiry, and term ratio ≥ 1.20 | Both expiries hold the event, but the front holds it in fewer days, so its IV is concentrated. A front-month short put sells that premium outright. A short-front / long-back put calendar sells the front's bigger post-event crush, with the back month as partial protection. Risk: a gap through the strike. |
| `EVENT IN BACK` | Catalyst after the front expiry but on or before the back | Only the back month holds the event. Its IV includes event premium; the front is clean. **Selling a back-month put means selling the event.** A short-front / long-back calendar here is *long* the event: a hedge, not a premium harvest. |
| `UNEXPLAINED INVERSION` | Term ratio ≥ 1.20 and no catalyst before the back expiry | Someone is paying up for near-term protection. Look for an unannounced event: an offering, data leak or rumor. Treat it as a warning, not an opportunity. |
| `IV CRUSH WATCH` | Catalyst within 5 trading days | IV collapses after the event. Selling now means selling into the binary event at peak premium. Waiting means cheaper premium once the outcome is known. |
| `CHEAP` | IV Rank < 25 | No premium edge. Say so plainly. |

**Name a contract for every sell-side flag** (`RICH PREMIUM`, `RICH PUTS`, `EVENT IN FRONT`, `EVENT IN BACK`). Use the expiry the flag is about, and the put 25–35% below the price that passes the "usable IV" test. Show:

`Expiry (DTE) · Strike · Bid/Ask/Mid · % OTM · OI · IV · Breakeven = strike − mid · Return on capital = mid ÷ (strike − mid) · Annualized = ROC × 365 ÷ DTE · Catalyst inside expiry: yes/no`

Then add one line on what would make it a trap: a catalyst inside the expiry, a recent or pending financing, or a thin chain. Underwriting the trade is Wilson's call.

## Report

**Order**:
1. 🔴 items and big moves.
2. One block per ticker, every ticker every time. The numbers and ticker below are made-up:
   ```
   XYZ  NO NEWS since 10/27 4:00 PM ET (SEC: 8-K 10/22 · IR: PR 10/20 · News: nothing new)
        $6.10 −4.2% · XBI −0.6% (excess −3.6) · vol 1.8× avg · Why: de-risking ahead of PDUFA 12/03 (medium)
        IV30 148% (+9 vs 10/27) · IVR 71 · IV/HV 1.6 · Put 1.22 · Call 1.05 · put skew · Term 0.84
        Catalyst between front (11/20) and back (1/15) → EVENT IN BACK · RICH PREMIUM · RICH PUTS
        Contract: Jan 15 (79d) $4P · 0.50/0.60/0.55 · 34% OTM · OI 1,240 · IV 162% · BE 3.45 · ROC 16% · ann. 74% · catalyst inside: YES
        Trap: selling this sells the PDUFA outcome.
   ```
3. **Setups**: flagged tickers, best first, with contract lines.
4. **Sources**: the links used.

A ticker with no news, no big move and no flags gets its block and nothing else.

**Delivery**:
- Post the report in the chat.
- Append the `Log` rows.
- On a scheduled run with any 🔴 item or big move, send a notification.

**Schedule**: 4:30 AM Da Nang, Tuesday to Saturday. That's always after the US close: 4:30 PM ET in US winter, 5:30 PM ET in summer.

## Commands
- `create my watchlist [tickers]`: create or open the sheet and seed it.
- `run the sentinel`: the full run on every listed ticker.
- `check TICKER`: one ticker now, on the list or not. Don't add it.
- `why is TICKER moving`: news and price only.
- `IV check` / `skew check`: step 3 only, for every listed ticker.

## Thresholds (starting values; Wilson tunes them)
- **Big move**: ±8%, or 3× average volume.
- **Moved with biotech**: excess move under 3 points.
- **RICH PREMIUM**: IV Rank ≥ 50 and IV30/HV30 ≥ 1.3.
- **RICH PUTS**: put ratio ≥ 1.15, or +0.10 vs baseline.
- **PUTS NOT PAID**: put ratio ≤ 1.00, or `call skew`.
- **Skew shape**: a difference of 0.05 or more between the put and call ratios.
- **Term inversion**: front ÷ back ≥ 1.20.
- **IV CRUSH WATCH**: catalyst within 5 trading days.
- **CHEAP**: IV Rank under 25.
- **Usable contract**: spread ≤ 35% of mid, OI ≥ 25 or volume > 0, put/call IV within 20 points at-the-money.
- **Contract search**: 25–35% out of the money, back expiry 60–90 days.
