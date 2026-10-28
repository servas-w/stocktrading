---
name: biotech-ticker-sentinel
description: Daily monitor and breaking-news flash for Wilson's biotech watchlist (CAPR, ACRS, MGNX, CMPX) or any single biotech ticker. Opens with a verified per-ticker news status (NEW NEWS / NO NEW NEWS / UNVERIFIED) and an IV-movement line against a logged baseline, then reconciles live Robinhood short puts, held shares and resting orders against Playbook v2, overlays every leg on the catalyst calendar with the market-implied event move, and recomputes cash floors from SEC filings with a bundled calculator. Use when the user says sentinel, run the sentinel, SENT: TICKER, biotech watchlist check, any news on CAPR/ACRS/MGNX/CMPX, how's IV on my biotechs, or asks about a short put through a PDUFA or readout.
---

# Biotech Ticker Sentinel

This is a monitor, not a full underwriting. Each run answers four questions, in this order:
1. What changed since the last run (news, filings, IV, OI)?
2. Is any leg on the book now in trouble?
3. Does a catalyst land inside a leg's life, and is the premium paying for it?
4. Has the cash floor moved?

Full first-time SOTP/rNPV underwriting of a new name belongs to the biotech underwriting skill (Floor A/B, PoS). The Sentinel refreshes the numbers and flags when a deep audit is needed.

## Data integrity rules (these override everything below)

- **Every number carries its source and timestamp** (e.g. `RH quote 10:42 ET`, `10-Q 6/30/26`, `IBKR IVP`). If a number wasn't retrieved this run, print `n/a` and never estimate, interpolate or reuse a remembered value.
- **Links**: only URLs actually returned by a tool this run. No constructed or remembered URLs.
- **Negative claims need receipts.** `NO NEW NEWS` is allowed only when every source in Step 1 was checked. If any source failed, print `UNVERIFIED (<source> failed)`.
- **Math and date math go through `scripts/sentinel_calc.py`** (`overlay`, `event-move`, `book`, `leg`, `floor`). Don't do arithmetic, DTE counts or weekday lookups in your head. Pass JSON on stdin (example below). If the script can't run, show the formula and inputs so the user can check.
- **Times**: print ET and Da Nang time (ICT, UTC+7). Convert with a real time zone (America/New_York), never a fixed offset: Da Nang is ET+11 during US daylight time and ET+12 after it ends (Nov 1, 2026). Note whether the US market is open; outside regular hours, option quotes and IV are stale and must be labeled `stale (after hours)`.
- **Tool names**: Robinhood tools may carry a connector prefix (e.g. `custom_mcp__get_accounts`). Use whichever name is exposed.
- Mask the account (`••••6081`). Never use Gmail for positions. Don't use the Robinhood equity news feed as a news source.

Calculator call pattern (keep `EOF` at the start of its line):

```bash
python3 scripts/sentinel_calc.py book <<'EOF'
{"nav": 250000, "as_of": "2026-10-28", "positions": [{"ticker": "CAPR", "spot": 6.1, "held_shares": 0, "legs": [{"strike": 4, "credit": 0.55, "qty": 10, "expiry": "2026-12-18", "mark": 0.40, "delta": -0.18}]}]}
EOF
```

## Step 0: Load state

- Read `references/watchlist.md`. If it's more than 14 days old or a listed date has passed, flag it in the banner and refresh it.
- Read the **Sentinel Log** (Google Sheet or Doc in Drive; create it if missing). It holds one row per ticker per run: `run_ts_ET | ticker | spot | front ATM IV | 30-45D ATM IV | post-catalyst ATM IV | IV at each held strike | OI at each held strike | IVP 52w (source) | last news item id/date | net cash/share now | floor source filing + date`. Its last row per ticker is the **baseline**. With no row, the baseline is `none (first run)`; never invent one.
- Scope = the four watchlist tickers, plus any requested ticker, plus any other biotech with an open leg on the account.

## Step 1: News status (one line per ticker, all of them, every run)

Window = since the previous run's timestamp in the log. With no log, use the prior 4:00 PM ET close, and on a Monday extend it back to Friday's close. Check, per ticker:
1. **SEC filings**: Robinhood `get_sec_filing_index` or EDGAR (8-K and item number, 10-Q/K, S-3, 424B5, Form 4, 13D/G, SC TO, DEF 14A).
2. **Company IR press-release page**.
3. **Web/news search** for the ticker and its lead asset, limited to the window.
4. **Regulatory/clinical** where relevant: ClinicalTrials.gov last-update date on the lead NCTs, FDA/CBER actions or AdComm calendar, and congress abstract releases.

Output: `NEW NEWS / FILING` (what, when in ET, link, and a one-line "so what" for the floor or the leg), `NO NEW NEWS (since <ts>; SEC ✓ IR ✓ Web ✓ CT.gov ✓)`, or `UNVERIFIED`.

**Materiality tags.** Mark 🔴 for: offering or ATM use (S-3/424B5/8-K 1.01 financing), CRL, approval, PDUFA change, clinical hold, topline data, debt default or covenant, restructuring or going-concern language, 13D, or an insider **open-market** Form 4 (ignore 10b5-1 and tax withholding). Any 🔴 item triggers Flash mode.

## Step 2: IV and microstructure (one line per ticker, right under the news line)

First run `sentinel_calc.py overlay` for each ticker's next catalyst, using every listed expiry including weeklies, plus market holidays (2026: Nov 26, Dec 25). That tells you which expiry is pre-event and which is post-event. Then pull with `get_option_chains` → `get_option_instruments` → `get_option_quotes`:
- **Front ATM put IV** (nearest monthly ≥ 7 DTE), **30-45 DTE ATM IV**, and the **first post-catalyst expiry ATM IV**. Use the mid, and flag any contract whose bid-ask is more than 30% of mid as `wide` and not IV-reliable. Don't read IV off sub-$0.10 deep-OTM strikes.
- **IV at each held strike** vs baseline: `+/- pts`.
- **IVR/IVP**: only from a source that publishes it (IBKR IV Percentile 52w/26w; Barchart if the user supplies it). Robinhood gives per-contract IV only. Otherwise print `IVR unverified`.
- **OI**: OI updates once overnight (OCC). Compare to the previous trading day's logged OI only, never intraday. Flag ≥ 25% OI change at a held strike or a block trade above 3× average daily volume.
- **Driver**: name one: pre-event expansion, post-event crush, OPEX pinning, offering fear, or no clear driver. Don't make one up.

Format: `CMPX · spot $X (+y%) · Front put IV 182% (+11 vs 10/27) · 45D 165% · Post-cat n/a · IVP52 71 (IBKR) · OI $1P +2.1k · Driver: …`

## Step 3: Book reconciliation (Robinhood, live)

- `get_accounts` → ••••6081. `get_option_positions` (non-zero, **all pages**) → `get_option_instruments` for strike and expiry. `get_option_quotes` for mark, delta and IV. `get_equity_positions` for held and short shares. `get_option_orders` / `get_equity_orders` for resting orders and today's opening tickets. Pull positions every run; never reuse a contract list from an earlier run.
- Run `sentinel_calc.py book` **once** with every name: spot, held shares (negative = short), and each leg's strike, long_strike for spreads, credit, qty, expiry, mark and the short contract's delta. It returns per-leg breakeven, cushion %, captured %, max loss and alarms, plus per-name exposure (held shares + all leg max losses) against the 10% NAV cap, sorted by $ at risk. Don't run `leg` separately per leg, or the NAV cap misses the other legs.
- **Playbook v2 alarms** (from the calculator, plus these checks):
  - ITM, delta ≤ -0.30, or spot within 7% of strike → defense per Playbook v2 (roll out-and-down, or close).
  - ≤ 21 DTE and near the money → act now. Never carry an ITM short into expiration without a buy-to-close limit at or above intrinsic and at or near the **ask**. A BTC limit below intrinsic will not fill.
  - ≥ 50% captured with no GTC take-profit resting → stage one. Mark ≤ $0.05 → buy back (dead collateral).
  - Resting BTC limits below intrinsic, or far from the current mid → stale; replace.
  - New short < 30 DTE without an OPP tag, a second opening ticket on the same name today, a put sold on a name with an underwater held lot, or name exposure > 10% NAV (held shares + short-put max loss) → flag for cancel or trim.
  - **Anti-CAPR**: short stock and a short-put stack on the same name → flag (the calculator does this). Short stock 15% or more against entry → the 15% short stop-loss has triggered.
- **Calendars**: treat back-month long puts as hedges. Show them next to the front short they protect: hedge ratio (long contracts ÷ short contracts), the long's delta, and whether a spot drop or IV spike has made it worth monetizing. Manage each leg on its own rules.

## Step 4: Catalyst × expiry overlay (the main signal)

For each leg, list every dated or windowed binary event (PDUFA, topline, AdComm, earnings, financing window, lock-up) **before its expiry**, from `references/watchlist.md` re-verified this run. The `overlay` output from Step 2 classifies each expiry as `before`, `ambiguous` (weekend/holiday action date right after it), `carries`, or `in_window` (open-ended guidance like "4Q26"). Treat `ambiguous` and `in_window` as carrying the event. `before` only means the scheduled date is later, and an early FDA action can still hit it.
- Run `sentinel_calc.py event-move` with `pre_iv` (ATM IV of the pre-event expiry), `post_iv` and `post_expiry` + `as_of` (post-event expiry), and the leg's `strike` and `credit`. Use the ATM `straddle` only if one side is missing; it overstates the event because it includes base vol. If there's no pre-event expiry (window already open), use the straddle and say so.
- The calculator's verdict, using the expected down level (spot × e^-move):
  - `PAID`: strike at or below it.
  - `THIN`: strike above it, breakeven at or below it.
  - `UNPAID`: breakeven above it, so an average-size bad outcome is a loss.
  Print the verdict with the implied move % and the down level.

## Step 5: Cash floor refresh

Rerun only when a new 10-Q/10-K, a financing, a material cash event (sale, milestone, royalty deal) or debt news landed, or when the user asks. Otherwise carry the last logged floor with its source filing and date. Q3 10-Qs land in early-to-mid November, so expect every watchlist floor to refresh then.
- Inputs from the filing: cash + equivalents + marketable securities (exclude restricted cash); post-period inflows, including ATM/offering net proceeds whenever you add the shares; **debt principal plus exit/prepayment fees** and royalty-financing obligations; AP + accrued; lease liabilities. Exclude non-refundable deferred revenue; include refundable amounts. Burn = operating cash outflow per quarter (not net loss), without one-offs.
- Shares: basic from the latest cover page, plus pre-funded warrants, plus shares issued since (ATM / 424B5), plus convertibles. Count options and warrants by treasury-stock method at the short strike.
- `sentinel_calc.py floor` returns gross cash/share, net cash/share now and **at the expiry you pass** (one call per distinct expiry on the name), and runway. Compare the strike to net cash/share at expiry. A strike above it means the put is underwritten by the pipeline, not the cash. Say so.
- If financing, debt or going-concern language changed, flag `DEEP AUDIT NEEDED` and hand off to the underwriting skill for the SOTP tiers.

## Step 6: Log and deliver

- Append this run's rows to the Sentinel Log (the next run's baseline).
- **Daily report**: a Google Doc. Section order: Banner (news and IV, every ticker) → Action list (alarms ranked by $ at risk, each with a staged order: ticker, action, qty, limit, TIF) → Book ledger table → Catalyst overlay → Floors → Sources. Post the link in the Master Chat with the banner plus the action list. If there are no alarms, say `No action` in one line.
- **Flash** (any 🔴 item, a ±8% spot move, or a ±15-pt IV shift at a held strike): chat only, ≤ 12 lines: the banner line for that ticker, what happened (link), the impact on floor/cushion/event move, and one staged order or `hold, because …`.
- Footer: `Staged orders are proposals. Nothing was placed.` Never place, modify or cancel orders.
