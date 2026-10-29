---
name: biotech-watchlist-sentinel
description: Monitors the biotech tickers on Wilson's Robinhood watchlist "Biotech Sentinel" (he adds and removes names by hand in the app). For each name it reports any new news or SEC filing, the day's price move and the most likely reason, and options IV, 25-delta put/call skew and term structure read against the next catalyst, naming the put contract when a setup is worth selling premium into. Emails a daily report, and an hourly breaking-news watch emails an alert when urgent news or a big move hits. Use when the user says create my sentinel watchlist, run the sentinel, sentinel, check my watchlist, news watch, why is TICKER moving, IV check or skew check on the watchlist, or set up the sentinel schedule. Not for underwriting a single trade (biotech-options-master-engine) or auditing the book (war room / book audits).
---

# Biotech Watchlist Sentinel

Three jobs for each ticker on the watchlist, and nothing else:
1. **News**: is there any?
2. **Price**: how did it move, and why?
3. **IV**: is there skew or rich premium to take advantage of? If so, which contract?

No portfolio audit, no position management. The war room and book-audit skills do that.

## Rules (override everything below)

- **Numbers come from a tool call made this run.** Write each as `value (source, time ET)`. If you didn't get it, write `n/a`. Never estimate, and never reuse a number from memory.
- **Links**: only URLs a tool returned this run.
- **"No news" needs proof.** Give the newest item per source, e.g. `SEC: 8-K 10/22 · IR: PR 10/14`. If a source failed, the status is `UNVERIFIED`, not `NO NEWS`.
- **Don't invent a reason for a move.** If nothing explains it, say `no identifiable catalyst`.
- **All math goes through `scripts/sentinel_calc.py`**: `price`, `overlay`, `skew`, `contract`, `assess`. Don't do arithmetic, delta picking, date counts or flag logic in your head. Pass JSON as the argument or on stdin.
- **Times**: ET and Da Nang. Da Nang is ET+11 during US daylight time and ET+12 otherwise.
- **Never place, modify, cancel or preview orders.** Read Robinhood account data only if needed, and you shouldn't need it.
- **The only writes allowed**:
  - creating and seeding the watchlist, when Wilson asks
  - emailing **wilsonhersandy@gmail.com**
  
  A scheduled run is pre-authorized for those emails; don't stop to ask.
- **No preamble.** Dry and direct.

## Watchlist (Robinhood)

**`create my sentinel watchlist [tickers]`**:
1. `get_watchlists`: if a list named **Biotech Sentinel** exists, use it.
2. If not, `create_watchlist` with that name, then `add_to_watchlist` for the tickers Wilson named.
3. After that, **never add or remove items yourself.** Wilson manages the list in the Robinhood app.

**Each run**: `get_watchlists` → `get_watchlist_items` for Biotech Sentinel. Monitor every stock on it.
- If the list is missing or empty, say so and stop. In a scheduled run, email a one-line notice instead.

## Memory (Gmail)

Every daily report email ends with a `BASELINE` block, one line per ticker (example values):
```
BASELINE XYZ | 2026-10-29 | close 6.10 | iv30 1.48 | ivp52 0.71 | put_ratio 1.22 | call_ratio 1.05 | term 0.84 | catalyst PDUFA 2026-12-03 (8-K 8/24) | last_news 8-K 10/22
```

- **At the start of each run**, read the latest one: `search_threads` with `subject:"Biotech Sentinel daily" newer_than:10d`, then `get_thread`.
  - Use those values for the "vs last run" changes and as the cached catalyst.
  - A ticker with no line has the baseline `none (first run)`.
- **Refresh the catalyst** when news changes it, on Mondays, or when the cached one is missing. Use the latest 8-K, 10-Q or IR deck, and the `search_trials` / `get_trial_details` (ClinicalTrials.gov) tools for trial timing. Write the source next to the date.

## Each run, for every ticker

**Market open?** If the latest daily bar (step 2) isn't from the most recent US trading day, write `US market closed <date>`, run news only, and still email.

### 1. News
**Window**: since the last daily report (from the baseline date). With no report, the last 24 hours; on a Monday, the last 72 hours.

**Check**:
1. **SEC**: `get_sec_filing_index` (symbol, since = window start). Note the form, and the item number for 8-Ks.
2. **Press releases and news**: a web search for the ticker plus the company name, and for the lead drug name, limited to the window. Open the company IR page if a search result points there. Use a news connector too if one is connected (e.g. Twelve Data `get_company_news`).
   - Don't use the Robinhood equity news feed.
3. **If a trial or FDA event is pending**: ClinicalTrials.gov changes, and FDA/AdComm notices from the web search.

**Status**:
- `NEW NEWS`: what, when (ET), link, and why it matters.
- `NO NEWS since <time>`: with the receipts.
- `UNVERIFIED (<source> failed)`.

**Mark 🔴 (urgent)** for:
- an offering, ATM sale or shelf (S-3, 424B5)
- FDA approval, a CRL or a PDUFA date change
- a clinical hold
- topline data
- partnership or M&A news
- debt trouble, restructuring or going-concern language
- a 13D
- an insider buying or selling on the open market (Form 4; ignore 10b5-1 sales and tax withholding)

### 2. Price move and why
- **Get the bars**: `get_equity_historicals` (symbols = ticker and XBI, `interval: day`, start ~50 days back), plus `get_equity_quotes` for after-hours. Run `price` with the last 31+ bars and XBI's % change. It returns the % change, volume vs average, HV30, the excess move vs XBI, `moved_with_biotech` and `big_move`.
- **Explain the move by weighing these. Don't just stop at the first one that fits**:
  - **Sector**: `moved_with_biotech` is the main reason, unless a 🔴 item landed.
  - **Company news** from step 1, timed at or just before the move.
  - **Peer read-across**: a competitor's same-day data or FDA decision on the same target or disease.
  - **Financing**: an S-3, 424B5 or ATM in the last 30 days, or the price falling toward a recent offering price.
  - **Options or positioning**: contract volume above open interest in the chain from step 3, or an options-expiry Friday.
  - **Catalyst drift**: from `overlay`'s `trading_days_to_event`. A run-up into the catalyst, or de-risking ahead of it.
- **Give a primary reason and a confidence level**:
  - **high**: dated news lines up with the move
  - **medium**: plausible
  - **low**
- If nothing fits: `no identifiable catalyst`, with the volume context.

### 3. Options IV
1. **IBKR**: `search_contracts` (the ticker's stock) → `get_price_snapshot` with `implied_vol_underlying`, `implied_volatility_percentile`, `historical_vol`. Response keys use hyphens.
   - This gives IV30, IVP 52w/26w and HV30. If IBKR fails, use `hv30_from_bars` from `price` and write IVP as `n/a`.
2. **Robinhood chains**: `get_option_chains` → expirations.
   - **Front** = the nearest expiry with at least 7 days left. **Back** = the expiry closest to 75 days (60–90).
   - For each, `get_option_instruments` (puts and calls, strikes from about 50% to 150% of spot), then `get_option_quotes` in batches of 20 or fewer.
   - Map each quote to `{type, strike, bid, ask, iv, delta, oi, volume}`.
3. **Run `skew`** with spot, front and back. It returns ATM IVs, the 25-delta put and call ratios vs back ATM IV, the shape and the term ratio. Unusable quotes are dropped and thin chains come back `n/a`.
4. **Run `overlay`** with the cached catalyst, the front and back expiries, and the holidays below.
   - Use `event_date` for a dated event, and `window_start`/`window_end` for guidance like "Q4 2026".
5. **Run `assess`** with:
   - IVP52, IVP26, IV30, HV30
   - the put and call ratios and shape
   - the baseline put ratio
   - the term ratio
   - the front and back status from overlay
   - `trading_days_to_event`, and `event_dated` (overlay's `dated` field)
   
   Then report the flags it returns.
6. **If `needs_contract`**: run `contract` with spot, DTE and the puts of the flag's expiry (front for `EVENT IN FRONT`, back otherwise). Report its line, then one line on the trap: a catalyst inside the expiry, a recent financing, or a thin chain.

**What the flags mean for a put seller**:

| Flag | Meaning |
|---|---|
| `RICH PREMIUM` | IVP52 ≥ 60, IVP26 ≥ 50 and IV/HV ≥ 1.3. Your IBKR gate for selling puts is met. |
| `RICH PUTS` | Out-of-the-money puts carry extra crash premium. Favors deep out-of-the-money puts or wide bull put spreads. |
| `PUTS NOT PAID` | Flat or call skew. The market prices upside, so deep puts aren't paid for the gap risk. |
| `EVENT IN FRONT` | The front holds the event in fewer days, so it's inverted. A front short put sells that premium. A short-front / long-back calendar sells the front's bigger post-event crush, with the back as partial protection. Risk: a gap through the strike. |
| `EVENT IN BACK` | Only the back month holds the event. **Selling a back-month put sells the event.** A short-front / long-back calendar here is *long* the event: a hedge, not a harvest. |
| `UNEXPLAINED INVERSION` | The front is rich with no known catalyst. Look for an unannounced offering, leak or rumor. Treat it as a warning. |
| `IV CRUSH WATCH` | A dated catalyst within 5 trading days. Selling now sells the binary event at peak premium; waiting means cheaper premium once the outcome is known. |
| `CHEAP` | IVP52 < 25. No premium edge. |

**US market holidays** for `overlay` (re-check against the NYSE calendar each January):
- **2026**: Nov 26, Dec 25.
- **2027**: Jan 1, Jan 18, Feb 15, Mar 26, May 31, Jun 18, Jul 5, Sep 6, Nov 25, Dec 24.

## Daily report (chat, plus an email when scheduled)

**Subject**: `Biotech Sentinel daily · YYYY-MM-DD · <n> flags · <n> 🔴`. The body is plain text:

1. 🔴 items and big moves first.
2. **One block per ticker**, every ticker every time (example values):
   ```
   XYZ  NO NEWS since 10/28 4:00 PM ET (SEC: 8-K 10/22 · Web: nothing new)
        $6.10 −4.2% · XBI −0.6% (excess −3.6) · vol 1.8× avg · Why: de-risking ahead of PDUFA 12/03 (medium)
        IV30 148% (+9) · IVP52 71 / IVP26 60 · IV/HV 1.6 · Put 1.22 · Call 1.05 · put skew · Term 0.84
        Catalyst after front (11/20), before back (1/15) → EVENT IN BACK · RICH PREMIUM · RICH PUTS
        Contract: Jan 15 (78d) $4P · 0.50/0.60/0.55 · 34% OTM · OI 1,240 · Δ −0.18 · BE 3.45 · ROC 15.9% · ann. 75%
        Trap: selling this sells the PDUFA outcome.
   ```
3. **Setups**: the flagged tickers, best first.
4. **Sources**: the links used.
5. **The `BASELINE` block** (the next run's memory).
6. The footer: `Sentinel report. Not advice. Nothing was traded.`

A quiet ticker gets its block only.

## Breaking-news watch (hourly, email only when urgent)

`news watch`, or the hourly schedule:
1. Read the watchlist.
2. For each ticker, run **step 1 only** for the **last 90 minutes**, plus a `get_equity_quotes` check of the move vs the previous close.
3. **Alert if** there's a 🔴 item, or a move of ±8% or more vs the previous close (then say `no identifiable catalyst yet` if there's no news).
4. **Dedupe**: `search_threads` with `subject:"SENTINEL ALERT" newer_than:3d`, then `get_thread` for the candidates. Every alert body carries a line `ITEM: <ticker> <form or headline> <date>`. Skip any item already sent.
   - A follow-up (e.g. the 424B5 pricing after the S-3) is a new item.
5. **Email** wilsonhersandy@gmail.com:
   - **Subject**: `🔴 SENTINEL ALERT · TICKER · <what happened> · <time ET>`
   - **Body**, 10 lines or fewer, plain text:
     - what happened, with the link
     - the time in ET and Da Nang
     - the price and % vs the previous close, and the session (pre-market, regular or after-hours)
     - front ATM IV from one `get_option_quotes` call, if it's quick, vs the baseline
     - what it changes about the catalyst or any financing overhang
     - the `ITEM:` line
     - the footer
   - Several tickers in one run go in one email.
6. **Nothing urgent**: no email and no chat output beyond `watch: nothing new`.

## Schedule

`set up the sentinel schedule` creates two scheduled tasks that run this skill. Following Wilson's existing routines, have them **fire into this session**, so the Robinhood, IBKR and Gmail connectors stay attached.

| Task | Cron (UTC) | Da Nang | What |
|---|---|---|---|
| Sentinel daily | `31 21 * * 1-5` | 4:31 AM Tue–Sat | Full run, emails the daily report. That's after the US close in both seasons (4:31 PM ET in winter, 5:31 PM ET in summer). |
| Sentinel news watch | `7 12-23 * * 1-5` | hourly 7 PM–6 AM | Breaking-news watch (US pre-market to after-hours) |

**Prompts**:
- Daily: `Run the biotech-watchlist-sentinel skill: full daily run on the Biotech Sentinel watchlist and email the report.`
- Watch: `Run the biotech-watchlist-sentinel skill: news watch. Email only if something urgent.`

If the platform's minimum interval is longer than hourly, use every 2 hours.

## Commands
- `create my sentinel watchlist [tickers]`
- `run the sentinel`: full run. Chat only, unless it's the scheduled run or Wilson says "email it".
- `check TICKER`: one ticker, on the list or not. Don't add it.
- `why is TICKER moving`: steps 1–2.
- `IV check` / `skew check`: step 3 for the whole list.
- `news watch`
- `test alert`: send one alert email marked TEST.
- `set up the sentinel schedule`

## Thresholds (in `scripts/sentinel_calc.py`; change them there)
- **Big move**: ±8%, or 3× average volume.
- **Moved with biotech**: an excess move under 3 points.
- **Usable quote**: a bid and ask, spread ≤ 35% of mid, OI ≥ 25 or volume > 0.
- **ATM**: put and call IV within 20 points.
- **Wings**: 25 delta ± 0.10.
- **Rich premium**: IVP52 ≥ 0.60, IVP26 ≥ 0.50, IV/HV ≥ 1.3.
- **Rich puts**: put ratio ≥ 1.15, or +0.10 vs baseline.
- **Puts not paid**: put ratio ≤ 1.00, or call skew.
- **Skew shape**: a gap of 0.05 or more.
- **Inversion**: term ratio ≥ 1.20.
- **IV crush watch**: a dated catalyst ≤ 5 trading days away.
- **Cheap**: IVP52 < 0.25.
- **Contract search**: 25–35% out of the money, highest OI.
