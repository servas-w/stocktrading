---
name: biotech-ticker-sentinel
description: Monitors only the biotech tickers Wilson names (default list in references/watchlist.md, e.g. CAPR, ACRS, MGNX, CMPX) and reports, per name, whether there is new news or a new filing (with proof of what was checked), how options IV moved against the last report, what catalyst is coming and which expiries it hits, and what that means for his position on that name. Use when the user says sentinel, run the sentinel, SENT: TICKER, monitor TICKER, watch these names, any news on TICKER, or how's IV on TICKER. Not a portfolio audit; the Claude War Room / book-audit skills do that.
---

# Biotech Ticker Sentinel

**One job: watch the names Wilson tells you to watch, and say what changed.** Nothing else. No whole-portfolio audit, no NAV maths, no trade ideas on names he didn't list.

**Which names**:
- If the message names tickers (`SENT: FHTX`, `monitor CAPR ACRS`), watch exactly those.
- Otherwise use the default list in `references/watchlist.md`.
- If he says add or drop a name, do it for this run and remind him to update the default list.

## Rules that override everything

1. **No made-up numbers.** Every figure gets a source and time (`RH 10:42 ET`, `10-Q 9/30/26`). If you didn't fetch it this run, write `n/a`.
2. **No made-up links.** Use only URLs a tool returned this run.
3. **"No news" needs proof.** For each source, show the newest item you found and its date (e.g. `SEC: latest 8-K 10/22`). If a source failed, the status is `UNVERIFIED`, not `NO NEW NEWS`.
4. **No mental math.** Use `scripts/sentinel_calc.py` for IV interpolation, dates, event moves, cushions and floors. In a Python sandbox, `import sys; sys.path.insert(0, 'scripts'); import sentinel_calc as c` and call `c.iv30({...})`, `c.overlay({...})`, `c.event_move({...})`, `c.position({...})` or `c.floor({...})`. From a shell, run `python3 scripts/sentinel_calc.py <command> '<json>'`. If neither works, show the formula and inputs.
5. **Times in ET and Da Nang.** Use a real time zone for ET (America/New_York). Da Nang is ET+11 until Nov 1, 2026, then ET+12. Outside US market hours, label quotes `stale (after hours)`.
6. **Read-only.** Mask the account (`••••6081`). Never use Gmail for positions. Never place, change or cancel orders.

## Per name, every run

### 1. News: did anything happen?
**Window**: since the last Sentinel report. If none can be found, since the prior 4:00 PM ET close; on Mondays, since Friday's close.

**Sources**:
- (a) SEC filings: Robinhood `get_sec_filing_index`, or EDGAR.
- (b) Company IR press releases.
- (c) A web/news search for the ticker and its lead drug.
- (d) For a pending clinical or FDA event: ClinicalTrials.gov last-update date, and FDA/AdComm notices.

Write one of three statuses:
- `NEW NEWS / FILING`: what it is, the ET time, the link, and one line on why it matters.
- `NO NEW NEWS since <time>`: list the newest item found per source.
- `UNVERIFIED (<source> failed)`.

**Mark 🔴 (urgent)** for any of these:
- offering, ATM use or shelf (S-3/424B5)
- FDA action, CRL, PDUFA date change or clinical hold
- topline data
- debt default, restructuring or going-concern language
- a 13D
- an insider buying or selling on the open market (Form 4; ignore 10b5-1 sales and tax withholding)

### 2. IV: did the options market react?
- Pull ATM put IV for the expiries around 30 days (`get_option_chains` → `get_option_instruments` → `get_option_quotes`, using mids). Run `iv30` with the last report's IV30 as `baseline_iv30`.
- **Use the IV30 change, not the front month.** The front month changes contract as it rolls, which makes the change meaningless.
- Also show IV at each strike you hold, against the last report.
- **IV Rank/Percentile** only if a source publishes it (IBKR, or Barchart if Wilson supplies it); otherwise write `IVR unverified`.
- **Open interest** updates overnight, so compare it to the previous day only.
- Ignore quotes whose bid-ask spread is wider than 30% of the mid, and strikes priced under $0.10.
- **Name the driver**: a run-up into the event, a post-event crush, OPEX pinning, offering fear, or `no clear driver`. Don't invent one.

### 3. Catalyst: what's coming, and which expiries does it hit?
- Take the next event from `references/watchlist.md` and confirm it against the company's latest 8-K, 10-Q or IR page.
- Run `overlay` with every listed expiry, weeklies included, plus market holidays (2026: Nov 26, Dec 25).
- **Reading the overlay status**:
  - `ambiguous` (weekend/holiday decision date) and `in_window` (open-ended guidance like "4Q26") count as carrying the event.
  - `before` still faces early-action risk.
- Run `event_move` with the pre-event IV, the post-event IV and the post-event expiry. Then add, for each short put that carries the event:
  - `strike`, `credit` and `qty`
  - **`fail_level`**: where the stock likely trades if the event fails. Use cash per share from `floor`, unless a better analog (a past CRL or failed readout) is cited.
- **Report**:
  - the implied move %
  - `move_test`
  - `if_event_fails` (whether the put ends in or out of the money, and the $ loss)
- The failure case is the one that matters for a binary, because the average move understates it.

### 4. Your position on this name
- Pull only this ticker from Robinhood: `get_option_positions` (non-zero, all pages) → `get_option_instruments`, then `get_option_quotes`, `get_equity_positions` and resting `get_option_orders`.
- Run `position`. Include long puts as `type: long_put` (for example, calendar back-month hedges).
- **Report**:
  - each leg: breakeven, cushion, % captured, DTE, flags
  - the hedge ratio
  - any stock flags (Anti-CAPR, 15% short stop, underwater lot)
  - stale resting orders: a buy-to-close below intrinsic, or far from the mid
- **No position**: write `no position` and skip this step.

### 5. Cash floor: only when it changed
- Rerun `floor` only if a 10-Q/10-K, a financing, a cash event (asset sale, milestone) or debt news landed in the window, or Wilson asks. Otherwise repeat the last report's floor with its filing date.
- Q3 10-Qs land in early-to-mid November, so expect a refresh then.
- **Inputs**:
  - cash, equivalents and marketable securities
  - cash inflows since the quarter end
  - operating cash burn (not net loss)
  - debt at principal plus exit fees
- **Shares**: basic, pre-funded warrants, shares issued since, convertibles, and options/warrants counted by treasury-stock method at the short strike.
- `cash_per_share` matches the convention of the other audits; `net_of_debt_per_share` is the stricter view.

## Output

- **Top of every output: the banner.** One block per name, each name every time. The values below are made-up examples, never real data:
  ```
  CMPX · NO NEW NEWS since 10/27 16:00 ET (SEC: 8-K 10/22 · IR: PR 10/14 · Web: nothing new) · 🔴 none
  IV30 165% (+11 vs 10/27) · $1P IV 182% (+9) · IVR unverified · OI $1P +2.1k · Driver: no clear driver
  Next: full COMPANION-002 data, date TBD → in_window for Nov/Dec · Position: 10x Jan $1P, cushion 38%, no flags
  ```
- **Then, only for names with something to say**: the news detail, the catalyst/expiry table, the position table and the floor. If nothing happened, say `Nothing changed` and stop.
- **Staged order**, only when news or a flag calls for one: ticker, action, qty, limit, time-in-force, and a one-line reason. End with `Proposal only. Nothing was placed.`
- **Delivery**:
  - **Scheduled daily run**: a Google Doc with the banner, the details and the baseline block. Post the link plus the banner in chat.
  - **Any 🔴 item, a ±8% move or a ±15-point IV30 move**: a chat flash of 12 lines or fewer, banner first.
- **Baseline block** (the last thing in every report), one line per name (example values):
  ```
  BASELINE CMPX | 2026-10-28 16:05 ET | spot 1.42 | iv30 1.65 | strikeIV 1.00P=1.82 | OI 1.00P=12400 | cash/sh 0.61 (10-Q 6/30) | last news 8-K 10/22
  ```
  The next run reads this from the previous report (the Doc or the chat). If it can't find one, the baseline is `none (first report)`.

## Thresholds (defaults; change them to suit)
These are alarm levels, not trading rules:
- defense: spot within 7% of strike, or |delta| ≥ 0.30
- ≤ 21 DTE with a cushion of 20% or less
- buy back at a mark of $0.05 or less
- flag profit-taking at 50% captured
- flash: a ±8% move or a ±15-point IV30 move
- ignore quotes with a bid-ask spread over 30% of the mid
- the catalyst sheet goes stale after 14 days
