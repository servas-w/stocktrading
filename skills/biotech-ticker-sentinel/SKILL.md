---
name: biotech-ticker-sentinel
description: Keeps a Google Sheet watchlist of biotech tickers that Wilson adds and removes by hand, and for every active ticker reports (1) any new news or SEC filing, (2) the day's price move and the most likely reason for it, and (3) options IV, put skew and term structure, flagging setups worth selling premium into. Use when the user says create my watchlist, set up the sentinel, run the sentinel, check my watchlist, any news on my biotechs, why is TICKER moving, or check IV/skew on my watchlist, and for the scheduled daily run.
---

# Biotech Ticker Sentinel

Three jobs for each ticker on the watchlist, and nothing else:
1. **News**: is there any?
2. **Price**: how did it move today, and why?
3. **IV**: is there skew or rich premium to take advantage of?

No portfolio audits, no position management, no orders.

## Rules (override everything below)

- **Numbers come from a source you actually opened this run.** Write each as `value (source, time ET)`. If you couldn't get a number, write `n/a`. Never estimate, never reuse a number from memory.
- **Links**: only pages you actually opened this run.
- **"No news" needs proof.** List what you checked and the newest item you saw on each, e.g. `SEC: 8-K 10/22 · IR: PR 10/14`. If a source wouldn't load, the status is `UNVERIFIED`, not `NO NEWS`.
- **Don't invent a reason for a move.** If nothing explains it, say `no identifiable catalyst` and give the context: sector, volume, options activity.
- **Times**: show ET and Da Nang time. Da Nang is ET+11 while the US is on daylight time and ET+12 otherwise (US clocks change on the first Sunday of November and the second Sunday of March).
- **Read-only**: never trade or place orders, and never touch Wilson's brokerage accounts.

## The watchlist (Google Sheet)

**"Create my watchlist"** creates a Google Sheet named **Biotech Sentinel** with two tabs. If one already exists, open it instead of making a second.

**Tab `Watchlist`** is what Wilson edits by hand:

| Ticker | Active | Added | Next catalyst | Catalyst date | Notes |
|---|---|---|---|---|---|

- Seed it with any tickers Wilson names. `Active` = `Y` or `N`.
- **Each run, read this tab first.** Monitor only rows with `Active = Y`. Never add, remove or pause tickers yourself, even if a name looks dead.
- You may fill or update `Next catalyst` and `Catalyst date` when a source confirms them. Write the source in `Notes`, e.g. `PDUFA per 8-K 8/24`.

**Tab `Log`** is written by you; one row per ticker per run:

| Run (ET) | Ticker | Close | % chg | Volume | Avg vol (30d) | IV30 | IV Rank | IV Pctl | HV30 | Put skew (pts) | Term (front−back pts) | News? | Flags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

- The previous row for a ticker is its **baseline**, used for "vs last run" changes.
- No previous row means the baseline is `none (first run)`.
- If you can't write to the sheet, say so at the top of the report and carry on.

## Each run, for every active ticker

### 1. News
**Window**: since that ticker's last `Log` row. With no row, since the previous US close (4:00 PM ET); on a Monday, since Friday's close.

**Check**:
1. **SEC EDGAR** filings for the company. Note the form type, and the item number for 8-Ks.
2. **The company's investor-relations press releases.**
3. **A news search** for the ticker and its lead drug, limited to the window.
4. **If a clinical or FDA event is pending**: FDA/AdComm notices, ClinicalTrials.gov changes and medical-meeting abstracts.

**Status**:
- `NEW NEWS`: what, when (ET), link, and one line on why it matters to the stock.
- `NO NEWS since <time>`: list the receipts.
- `UNVERIFIED (<source> failed)`.

**Mark 🔴 (urgent)** for:
- an offering, ATM sale or new shelf (S-3, 424B5)
- FDA approval, a CRL or a PDUFA date change
- a clinical hold
- topline trial data
- partnership or M&A news
- debt trouble, restructuring or going-concern language
- a 13D
- an insider buying or selling on the open market (Form 4; ignore planned 10b5-1 sales and tax withholding)

### 2. Price move and why
- **Get**: the last close (or the live price, labeled live), % change, intraday high/low, today's volume vs the 30-day average, and any pre/after-hours move.
- **Explain the move in this order. Stop at the first that fits, and say how confident you are**:
  1. **Company news** from step 1.
  2. **Peer or read-across news**: a competitor's data or FDA decision on the same target or disease.
  3. **Sector**: compare with XBI that day. If the stock moved with XBI, say so.
  4. **Financing pressure**: a recent shelf or ATM, a cash runway under 12 months, or a price falling toward a recent offering price.
  5. **Options or positioning**: an unusual call or put volume spike, high short interest, an options-expiry day, or a run-up into a known catalyst.
  6. Otherwise: `no identifiable catalyst`, with the volume context. Below-average volume on a big move usually means a thin, technical move.
- **Big-move flag**: a move of ±8% or more, or volume of 3× average or more. Put these at the top of the report.

### 3. Options IV: is there something to take advantage of?
**Where to get the data**:
- A connected market-data or brokerage tool, if Spark has one.
- Otherwise, browse a public options page (Barchart's options overview for IV, IV Rank, IV Percentile and historical volatility; Yahoo Finance or Nasdaq for the chain).
- Use bid-ask mids. Skip a quote if its spread is more than 30% of the mid, its open interest is under 50, or it's priced under $0.10.

**Measure**, for each ticker:
- **IV30, IV Rank and IV Percentile**: from the page, never calculated by you.
- **Volatility premium**: IV30 ÷ historical volatility (30-day).
- **Put skew**: the IV of the put about 25–30% out of the money (or about 25 delta), minus the at-the-money IV, in the 60–90-days-to-expiry month. Report it in vol points.
- **Term structure**: the front-month (≤ 45 days) at-the-money IV minus the 60–120-day at-the-money IV.
  - Positive means inverted: the front is richer.
  - Note whether a catalyst falls between the two expiries.
- **Changes**: compare each figure with the baseline row.

**Setup flags.** These are not trades; they're things worth looking at:

| Flag | When | What it means |
|---|---|---|
| `RICH PREMIUM` | IV Rank ≥ 50 **and** IV30/HV30 ≥ 1.3 | Options are expensive versus both their own history and how much the stock actually moves. This is your gate for selling puts. |
| `STEEP PUT SKEW` | Put skew ≥ 15 pts, or up ≥ 10 pts vs baseline | Out-of-the-money puts are unusually rich. Favors selling deep out-of-the-money puts or wide bull put spreads. |
| `INVERTED TERM` | Front exceeds back by ≥ 10 pts | Premium is concentrated in the front month. If a catalyst explains it, it's event premium: selling the front month means selling the event. A front-short / back-long put calendar harvests it with the back month as protection. If no catalyst explains it, say "unexplained" and check for an offering or news. |
| `IV CRUSH WATCH` | A catalyst is within 5 trading days and IV is elevated | Premium will collapse after the event. Note it as an opportunity if it's held, and as a trap if he'd be selling into it. |
| `CHEAP` | IV Rank < 25 | No premium edge. Say so plainly. |

**For every flag**, give:
- the numbers behind it
- the expiry and strike area it points to
- the catalyst it overlaps (from the `Watchlist` tab), and whether that catalyst falls before or after the expiry. A decision date on a weekend can land on the Friday before.
- one line on what would make it a trap: a catalyst inside the expiry, a cash runway under 12 months, or an offering risk

Leave the actual underwriting to Wilson.

## Report

**Order**:
1. The 🔴 items and big moves.
2. One block per active ticker, every ticker every time. The numbers below are made-up examples:
   ```
   XYZ   NO NEWS since 10/27 4:00 PM ET (SEC: 8-K 10/22 · IR: PR 10/20 · News: nothing new)
         $6.10 −4.2% · vol 1.8× avg · XBI −0.6% · Why: drift into PDUFA, no news (medium confidence)
         IV30 148% (+9 vs 10/27) · IVR 71 · IV/HV 1.6 · Put skew +18 pts · Term +22 pts (PDUFA falls between the two expiries)
         Flags: RICH PREMIUM · STEEP PUT SKEW · INVERTED TERM (event premium)
   ```
3. **Setups**: the flagged tickers with the detail above, best first.
4. **Sources**: the links you used.

If a ticker had no news, a small move and no flags, its block is all it gets.

**Delivery**:
- Post the report in the chat.
- Append the `Log` rows.
- On a scheduled run where any ticker has a 🔴 item or a big move, send it as a notification.

**Suggested schedule**: **4:30 AM Da Nang time, Tuesday to Saturday** (the morning after each US session). That is always after the US close: 4:30 PM ET from November to March, 5:30 PM ET during US daylight time. Optionally add a pre-market run at 8:30 PM Da Nang (8:30 AM ET in winter, 9:30 AM ET in summer).

## Commands

- `create my watchlist [tickers]`: create (or open) the Biotech Sentinel sheet and seed it.
- `run the sentinel`: the full run on every active ticker.
- `check TICKER`: one ticker now, whether or not it's on the sheet. Don't add it.
- `why is TICKER moving`: steps 1 and 2 only.
- `IV check`: step 3 only, for every active ticker.

## Thresholds (Wilson can change these)
- big move: ±8% or 3× volume
- `RICH PREMIUM`: IVR ≥ 50 and IV/HV ≥ 1.3
- `STEEP PUT SKEW`: ≥ 15 pts, or +10 vs baseline
- `INVERTED TERM`: ≥ 10 pts
- `IV CRUSH WATCH`: catalyst ≤ 5 trading days away
- `CHEAP`: IVR < 25
- skip quotes with a spread over 30% of mid, OI under 50, or a price under $0.10
