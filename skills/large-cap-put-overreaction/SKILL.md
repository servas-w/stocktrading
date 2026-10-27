---
name: "large-cap-put-overreaction"
description: "Screen and underwrite 60-90 DTE deep-OTM short puts and wide bull put spreads on dislocated large-caps ($20B+) with an IV gate of IVR 50 (IBKR IV Percentile 52w ≥ 60 + 26w ≥ 50 via the IBKR connector; Barchart IVR if user-supplied), owner-FCF forensics (OCF minus CapEx minus SBC), debt-adjusted strike cushions, Pennies-for-Parachutes wings, and a calculator for strikes, fills, ROC and management. Use whenever the user asks to scan or screen for put-selling setups, says short large cap put, large cap put overreaction or dislocation alert, asks about post-earnings overreactions or IV spikes, wants to sell cash-secured puts or bull put spreads on a named ticker, or wants a Shkreli-style forensic reality check on a sold-off large-cap, even if the message is just a ticker plus puts?. Also: RS pullbacks to the 9W/21W weekly EMA, 30m reversal trigger, RS scan, RS: TICKER. Not for clinical-stage biotech binaries; use biotech-options-master-engine for those. Also triggers on LC: TICKER or LC DEEP: TICKER."
---

# Large-Cap Put Overreaction Engine (v6 lean-usage + RS-pullback overlay)

Sell fear, not hope: short puts are an implied-volatility mean-reversion trade, so the seller must be paid (IVR ≥ 50), must sit below a real fundamental floor (owner cash flow, not adjusted EPS; equity is junior to debt), and should buy a cheap parachute when one is available.

Two setup classes feed the same underwriting: **DISLOCATION** (oversold quality, the original engine) and **RS-PULLBACK** (a relative-strength name pulling back into a weekly EMA it has held for 10–15 weeks, entered only after a 30m reversal trigger). The overlay changes *which* names, *when* to sell and *where* the strike sits; it never relaxes the IV gate, forensics or cushion.

## Operating rules (why this version is cheap)

Compute is driven by tool output tokens and re-derivation in prose. Most candidates die at the IV gate, so:

1. **Gate before you gather.** Order: IV Rank → earnings / Anti-ORCL → forensics → option chain. Stop at the first hard fail and print the 2-line early exit. Never pull filings or chains for a name that already failed.
2. **Batch independent calls in one turn.** Budget (data calls; calculator runs don't count): **LEAN** ≤5 for an IVR rejection (Turn 1's 4 calls + the IBKR snapshot), ≤13 for a full approval (Turns 1–5, with one `get_option_instruments` call per strike; exposure check excluded unless requested) · **DEEP** ≤19. All budgets include the 2 IBKR IV calls. Hitting the budget means stop and report what is UNVERIFIED, not keep searching.
3. **The calculator does the math.** `python3 scripts/underwrite.py strikes|lc '<json>'`. Copy its numbers; don't recompute them in prose. Missing inputs print n/a / UNVERIFIED and it never crashes — pass what you have. Don't open the script (~8k tokens): the JSON example below is its full interface.
4. **Fresh data only.** Every number comes from this session's tool calls, stamped "as of". Never reuse figures from memory, past chats or search snippets. A gap is written UNVERIFIED, never filled with a remembered number.
5. **Compact card by default.** Full dossier only when asked ("full", "deep", "dossier") — then read `references/full-dossier.md`.
6. **Scope.** Pre-commercial / clinical-stage biotech with a PDUFA, AdComm or Phase 3 readout inside the contract is out of scope here → biotech-options-master-engine.
7. **Language.** A BUY on a name the user is short is "Buy to Cover", never accumulation.

## Usage budget (v5 — read first; overrides any looser rule below)

Default mode is **LEAN**. Switch to **DEEP** only when the user types DEEP / full / dossier.

- **One ticker per chat.** Every new message re-processes all earlier tool output, so long multi-ticker threads burn the usage limit. If this chat already holds two finished underwrites, answer the request, then end with one line: *New chat recommended for the next ticker (usage).*
- **Search:** LEAN ≤ 2 `web_search_fast` per ticker (one sell-off-cause query for survivors; a second only if the cause is ambiguous). Never `web_search` in LEAN. No image search, visualizer, memory reads or past-chat search unless asked.
- **Fetch:** every `web_fetch` carries `text_content_token_limit` ≤ 2500. Fetch the 8-K exhibit 99.1 earnings release, never the full 10-Q HTML (10–20k tokens).
- **Chains:** always pass `expiration_dates` (≤ 2 monthlies) and a strike filter when the tool accepts one; never pull an unfiltered chain. Quote ≤ 6 contracts in one call.
- **Exposure is opt-in.** Don't call `get_equity_positions`, `get_option_positions` or `get_portfolio` unless the user says "check my book" / "exposure", or names a position in this ticker. The user can clear the exposure gate inline — `have: none` or `have: -7x Nov 2.5P, NAV 375k` — pass that as `existing`. Otherwise cap at CONDITIONAL and print *exposure not checked (say "check my book")*. When checking: `get_option_positions` with `chain_ids` + `nonzero: true` only; `get_equity_positions` and `get_portfolio` at most once per chat.
- **Read once.** Don't re-open this file or a reference already read in this chat. Never open `scripts/underwrite.py`.
- **Tool loading:** `tool_search` with `limit` ≤ 3, using the exact queries in Data routing; don't load tools you won't call.
- **Output:** LEAN card ≤ 200 words with one table; early exits stay at 2 lines. Never paste raw calculator output.
- **Stop rule:** at the budget, stop and mark gaps UNVERIFIED. Never re-call a tool to "double check" unless the user asks.

## Data routing

| Need | Tool | Notes |
|---|---|---|
| Spot | Robinhood `get_equity_quotes` (≤20 symbols/call) | Use the fresher of `last_trade_price` / `last_non_reg_trade_price`; state its time |
| Mcap, P/E, dividend yield, 52w low, shares, avg volume | `get_equity_fundamentals` (≤10/call) | `dividend_yield` is already in % points → pass as-is |
| Last / next earnings | `get_earnings_results` (1 symbol/call) | `eps.actual` null = upcoming; `verified:false` = tentative date |
| IV gate | IBKR `search_contracts` → `get_price_snapshot` (ladder below) | Never Barchart fetch |
| OCF, CapEx, SBC, cash, debt | `get_sec_filing_index` → `get_sec_filing_facts` | Concept sets below; ~2k tokens total |
| Contracts | `get_option_instruments` (chain_symbol, expiration_dates, type=put, strike_price "180.0000") → `get_option_quotes` (all ids in one call) | Monthlies are 3rd Fridays; if a query comes back empty, retry once with 2–3 comma-separated monthlies in `expiration_dates` (`get_option_chains` may not load) |
| Weekly EMAs | `get_equity_technical_indicators` type `ema`, interval `week`, start ≈ 17 weeks back, `output: "last:16"`: period 9 and period 21 (two calls, ≤10 symbols each); period 50 with `output: "latest"` for 21W-defended names | Server handles warm-up → no long history needed. Pass as `e9`/`e21` lists, `e50` number |
| Weekly closes/lows | `get_equity_historicals` `interval: week`, same 17-week start (≤10 symbols) | Columnar `{"c":[],"l":[]}`. Robinhood weekly bars exclude the in-progress week, so they align with the EMA series |
| 30m trigger | `get_equity_historicals` `interval: 30minute`, start 2–3 sessions back, survivors only | Rows `[t,o,h,l,c,v]`; always pass `asof` (current UTC) so the forming bar is dropped |
| Liquidity regime | `run_scan` **LC Put – Liquidity Regime** `f759011a-9c23-4491-9b40-7d492bc95b8b` | Pass the `% vs 21W EMA` column as ratios: `{"SPY":..,"HYG":..,"RSP":..}` |
| Sell-off cause | `web_search_fast` "TICKER stock drop reason" or "TICKER selloff today" — survivors only | Cite inline |

Tools are deferred: load Robinhood tools with one or two `tool_search` calls. Load IBKR with `tool_search "search_contracts"` and `tool_search "get_price_snapshot implied volatility"`. Search by the bare tool name: the server prefix varies by install (`mcp__Interactive_Brokers_IBKR__…` on some, an ID-style prefix on others), so a full-name query can miss, and a generic "IBKR" query does not surface `search_contracts`.

## IV gate ladder

1. **IBKR connector (primary, free, exchange data).** Turn 1: `search_contracts` {query: TICKER} → take `underlying_contract_id` from the row whose `symbol` exactly equals the ticker, US primary listing, with OPT in `sections`. Turn 2: `get_price_snapshot` {contract_id, market_data_names: ["last","implied_vol_underlying","implied_volatility_percentile","historical_vol","top_status"]}. Response keys are hyphenated.
   - `implied-volatility-percentile.high_52w / high_26w / high_13w` → pass as `ivp_52w`, `ivp_26w`, `ivp_13w` (fractions are fine; the calculator converts).
   - `implied-vol-underlying.annual_iv` → `iv30`; `historical-vol.annual_pct` → `hv20` (it is 30-day HV; label it so).
   - `ivr_src: "ibkr"`, leave `ivr` null. `top-status` DELAYED/FROZEN is fine for percentiles; state it.
   - **IBKR returns IV Percentile, not IV Rank.** The calculator converts: IVR-equivalent = IVP52 − 10, so the gates read IVP52 ≥ 60 GREEN · 40–60 YELLOW · < 40 RED · Anti-ORCL < 45. GREEN also needs IVP26 ≥ 50 (otherwise the regime is unconfirmed → max CONDITIONAL). Report both: "IVR-eq 64 (IBKR IVP 52w 74 / 26w 66)".
   - `implied-vol-underlying.is_valid: false` or no percentile block → drop to rung 3.
2. **User-supplied Barchart IVR** (typed "NVDA 62", screenshot, or CSV) → `ivr_src: "barchart"`. Authoritative; skips the IBKR calls. If both exist and disagree by > 15 gate points, use the stricter and say so.
3. **Proxy (IBKR unavailable only):** `web_search_fast "optionsanalysissuite TICKER iv-hv-history"` → `web_fetch` the returned optionsanalysissuite.com `/stocks/ticker/iv-hv-history` URL with `text_content_token_limit: 1500` → read the "Snapshot as of" block (ATM IV, HV20, IV Rank, IV Pctl). Pass `ivr_src: "OAS proxy"`, `iv30` = its ATM IV, `hv20`. Search snippets are stale; always fetch. Its high-IV-rank screener page is junk data — never use it. Other proxies count only if they give the ATM IV they were computed on; two proxies > 15 points apart → UNVERIFIED.
4. **Nothing** → leave `ivr` null → UNVERIFIED → best possible verdict is CONDITIONAL.

Never `web_fetch` barchart.com: pages are JavaScript-rendered and return no numbers. The calculator enforces the proxy guards: proxy IVR within ±5 of a gate (30/35/50) → confirm on IBKR IVP before entry; proxy ATM IV more than 30% away from the live chain's ATM IV (`atm_iv`) → proxy rejected. IV30/HV20 < 1 means realized volatility exceeds implied — premium is not rich even at a high IVR; say so.

Gate table (IVR, or IBKR IVR-equivalent = IVP52 − 10):

| IVR | Status | Rule |
|---|---|---|
| ≥ 50 (ideal 60–70+) | 🟢 GREEN | Sell. Rich vega + theta drive the 50% target fast |
| 30–50 | 🟡 YELLOW | Only with P/E < 10 or yield > 3.5%, or as a defined-risk spread |
| < 30 | 🔴 RED | NO-GO → Pullback Watchlist, even for fortress names |

**Anti-ORCL:** ≤10 sessions after earnings with IVR < 35 (IBKR IVP52 < 45) → NO-GO (post-crush scrap, still exposed to downgrade drift).

## RS-pullback overlay (v6)

Run when the name came from the RS scan, the user types RS: TICKER, or a dislocation candidate is sitting on a weekly EMA. Method notes, thresholds and the report it came from: `references/rs-pullback.md` (read only if asked why / tuning).

`python3 scripts/rs_pullback.py scan '<json>'` → per name: grade A/B/C/F, zone, weeks held, RS, 30m state, verdict, **strike ceiling**. Input: `{"asof","cushion","regime":{SPY,HYG,RSP},"bench":{"c":[SPY completed weekly closes]},"names":[{"ticker","spot","next_earnings","weekly":{"c":[],"l":[]},"e9":[],"e21":[],"e50":n,"m30":[[t,o,h,l,c,v],...]}]}`. Without `e9`/`e21` it computes EMAs itself and needs ≥ 30 weekly bars (55+ for the 50W). Don't open the script.

Rules it enforces (copy its output, don't re-derive):
1. **Structure:** price at the 9W counts only if the 9W has held ≥ 6 consecutive weekly closes; otherwise the 21W is the defended level (9W UNRELIABLE → WAIT for the 21W test). Grade A = ≥ 10 consecutive closes and ≥ 13/15 above, stacked and rising EMAs, RS > SPY. F (BROKEN: > 3% below the 21W, or 9W < 21W) → no RS-pullback entry; the name can only re-enter as a DISLOCATION candidate through the normal gates.
2. **Trigger:** first green 30m close after a ≥ 1.5% sell-off = marker; a later close above its high = TRIGGERED. Sell only on a fresh trigger (≤ 1 session old). Marker low broken before the fill → cancel the order. The report's ~2% stop is an entry invalidation here, not a put stop.
3. **Strike map:** short strike ≤ min(next weekly support below the defended EMA, spot × (1 − required cushion)), then the usual Δ −0.10/−0.15 at or below it. Cushion still beats delta; the EMA can only push the strike lower.
4. **Earnings:** no new entry ≤ 6 days before earnings (BLOCKED-ER). Expiry CLEAN/HAZARD rule still applies.
5. **Regime (liquidity proxy):** RISK-OFF (SPY & HYG below 21W) → STAND DOWN on RS-pullbacks; CAUTION (SPY, HYG or RSP below 21W) or UNVERIFIED → run `lc` with `force_spread: true`, half the usual contracts, verdict max CONDITIONAL.
6. **IV gate unchanged.** RS-pullback names usually arrive with low IVR; a pretty chart with IVR-eq < 30 is a Pullback Watchlist name, not a trade. Best case = a news flush into the EMA that spikes IV and prints the trigger the same session.

Verdicts: READY (grade A/B) → IV gate + full `lc` · READY-C (weak hold) → same, verdict max CONDITIONAL · WATCH → offer (don't create unasked) a Robinhood `create_alert` price alert at the defended EMA or marker high, re-scan · a trigger between the EMAs is WATCH, not READY · WAIT (extended, 9W unreliable, between EMAs) · FAILED-TODAY · BLOCKED-ER · STAND DOWN · VOID.

## Single-ticker workflow

1. **Turn 1 (parallel):** quotes + fundamentals + earnings + IBKR `search_contracts` (skip if the user gave Barchart IVR). For `RS: TICKER` also add weekly historicals + EMA 9/21/50 + 30m bars, and run `rs_pullback.py` in Turn 2 alongside the IV gate (+4 to the budget).
2. **Turn 2:** IBKR `get_price_snapshot` (proxy search → fetch only if IBKR fails) → run `lc` with spot/IVP/earnings/mcap only. RED, Anti-ORCL or out-of-universe → early exit, stop.
3. **Turn 3 (parallel):** `get_sec_filing_index` (symbol, form_type ["10-Q","10-K"], since ≈15 months ago) + `strikes` grid (spot, ATM IV, DTE) + `web_search_fast` cause search.
4. **Turn 4 (parallel):** two `get_sec_filing_facts` calls + `get_option_instruments` (one call per strike) for 2 candidate shorts, 1 wing, and the ATM strike (ATM only when IVR is a proxy; IBKR already gives ATM IV).
5. **Turn 5 (parallel):** `get_option_quotes` (one call) + **existing exposure only if opted in** (Usage budget) for the account the trade goes into: `get_option_positions` (`chain_ids` = the chain_id from the instrument results, `nonzero: true`), `get_equity_positions` and `get_portfolio` once per chat — or the user's inline `have:`. Accounts: main book = the default margin account ending 6081; agentic / Shadow Delta = ending 1686 (full numbers via `get_accounts`). → full `lc` run with `existing` → card.
   - `existing`: `{"shares", "avg_cost", "short_puts", "short_calls", "nav", "max_name_pct"}` (contract counts as positive numbers; the calculator also accepts `-7`) (default cap 10% of NAV counting every put as assigned). Without it the verdict caps at CONDITIONAL.
   - Holding the stock more than the Rule 7 threshold under cost → no new puts on that name (no averaging down); run `lot` instead. Threshold by `universe.md` class: 25% for LC/MC (the default here), 15% for BIO/SC. Pass `"class"` in the `lc` JSON when the name isn't LC.

**Expiry:** a monthly in 60–90 DTE. Prefer one that expires before the next earnings (CLEAN). If none does, keep the 60–90 DTE monthly and structure it as a spread (HAZARD). With HAZARD, say that IV and IVR are inflated by the earnings event, and weigh waiting for the post-report crush: re-enter 1–10 sessions after earnings only if IVR stays ≥ 35 (Anti-ORCL).

**XBRL concepts** (guess directly; call `get_sec_filing_facts_catalog` with `concept_contains` once only if a load-bearing one is missing):
- Cash-flow call, filing_ids = [latest 10-Q, latest 10-K]: `NetCashProvidedByUsedInOperatingActivities`, `PaymentsToAcquirePropertyPlantAndEquipment`, `PaymentsToAcquireProductiveAssets`, `ShareBasedCompensation`, `AllocatedShareBasedCompensationExpense`. TTM = FY + YTD(current) − YTD(prior year); if the 10-K is the latest filing, FY = TTM.
- Balance-sheet call, filing_ids = [latest filing only]: `CashAndCashEquivalentsAtCarryingValue`, `MarketableSecuritiesCurrent`, `ShortTermInvestments`, `AvailableForSaleSecuritiesDebtSecuritiesCurrent`, `LongTermDebtNoncurrent`, `LongTermDebtCurrent`, `LongTermDebt`, `CommercialPaper`, `DebtCurrent`. Debt = funded debt (long-term + current + CP), excluding operating leases; don't double count `LongTermDebt` with its parts.
- Banks, brokers, insurers: OCF is distorted by lending/trading flows — omit OCF/CapEx inputs and write "forensics n/m (financial)".

**Structure rules** (`lc` checks them):
- Short strike: listed strike with Δ −0.10 to −0.15 that also clears the required cushion — 15% base; 25% for $5–20B mid-caps (which also need OCF > 0; < $5B is out); 30% when FCF < 0 (CapEx cannibalism); × (1 + 1.5·D/EV) when D/EV > 25%. Cushion beats delta: go further OTM rather than breach it.
- Owner FCF (OCF − CapEx − SBC) ≤ 0 → REJECT (NO-GO), same bar as `lot`. Financials with OCF omitted show the gate as UNVERIFIED, not failed.
- Probability of Touch ≈ 2|Δ|: state it upfront so a normal intra-cycle touch doesn't trigger panic rolls.
- Pennies for Parachutes: quote a wing 40–60% below spot (liquid strike, OI ≥ 100). Wing ask ≤ 5% of the short mid → spread is mandatory; otherwise optional (`force_spread: true` to model it anyway).
- Floor check: BE should sit at/below the 52-week low or at a BE-implied EV/owner-FCF at/below the stock's own trough multiple. When the verdict hinges on it (or the user says "with VALU"), run the stock-valuation-engine skill in LC mode (reuses this chat's spot, SBC, cash, debt, earnings; ≤ 6 extra calls, outside this skill's budget) and pass its `VALU_HANDOFF` values as `"val_floor"` and `"val_implied_g"` in the `lc` JSON. BE above `val_floor` → max CONDITIONAL. Quote the implied growth in the reality check.
- Fills: width ≤ 20% of mid → mid; 20–25% → halfway to bid; > 25% → bid. OI ≥ 150 pass, 100–149 warn, < 100 fail.

**Sell-off triage** (one sentence in the card): transient sentiment (guidance timing, macro rotation, debt-issuance noise, downgrade) → tradeable. Structural impairment (patent cliff, lost franchise, fraud, going-concern, dividend cut from distress) → REJECT regardless of IVR.

## `lc` input (JSON)

```json
{"ticker":"XYZ","asof":"2026-09-23","spot":200,"exp":"2026-12-18",
 "ivr_src":"ibkr","ivp_52w":0.74,"ivp_26w":0.66,"ivp_13w":0.90,"iv30":45,"atm_iv":44,"hv20":40,
 "last_earnings":"2026-08-20","next_earnings":"2027-01-28",
 "short":{"strike":160,"bid":2.40,"ask":2.50,"delta":-0.12,"oi":4200},
 "wing":{"strike":100,"bid":0.08,"ask":0.11,"oi":900},
 "ocf_ttm":9e9,"capex_ttm":3e9,"sbc_ttm":1.5e9,"cash":6e9,"debt":1.2e10,
 "mcap":8e10,"pe":22,"div_yield":0.8,"low_52w":150}
```
Barchart instead: replace the IV keys with `"ivr":58,"ivp":81,"ivr_src":"barchart"`. Proxy: `"ivr":52,"ivr_src":"OAS proxy","iv30":45,"atm_iv":44`.
`strikes`: `{"spot":200,"iv":45,"dte":86,"inc":5}` (add `"skew":1.0` if `iv` is already the OTM strike's IV). Units: IV/HV as % or decimal; IVR in points; dollars raw.

## Held and assigned lots (`lot`)

Assignment moves a put's loss out of the options P&L into the stock column, so every assigned or underwater lot gets re-underwritten as if it were a fresh entry today. Run it when a put is assigned, when the exposure check flags an underwater lot, or when the user asks to review holdings.

`python3 scripts/underwrite.py lot '{"ticker","class":"LC","spot","shares","avg_cost","nav","mcap","ocf_ttm","capex_ttm","sbc_ttm","cash","debt","iv","dte":38,"structural_impairment":false}'` (`class` from universe.md: LC/MC or BIO/SC; default LC) (forensics from the same XBRL sets; `iv` = live ATM IV).
- **EXIT OR HEDGE** when it would not pass as a fresh entry (owner FCF ≤ 0, mcap < $5B, D/EV > 50%, or the thesis is structurally broken).
- **KEEP ONLY WITH A PLAN** when it passes but sits > 25% under cost: covered calls at/above basis only if premium allows (the calculator warns when the Δ0.30 strike is below basis — assignment there realizes the loss, so choose consciously), no new puts on the name until back within the Rule 7 threshold (25% LC/MC, 15% BIO/SC), and a written plan within 1 week.
- **KEEP – WHEEL** otherwise. Report assigned-lot P&L as its own bucket, never folded into options P&L.

## Management (printed by `lc` with exact prices)

GTC buy-to-close at 50% of credit immediately after the fill · Quick win: take 65–75% if it arrives within ~14 days · Close or roll at 21 DTE (gamma) · Defense: spot within 7% of the short strike or Δ ≤ −0.30 → roll out 30–60 days to the next monthly for a net credit, never for a debit. When closing a spread early, the near-worthless long wing may be kept (user practice: preserves margin headroom).
RS-pullback entries also carry a **structure check** at each weekly close: close below the defended EMA → structure-break flag (no adds, no new ticket on the name); close below the next support (the strike's backstop) → defend now (roll out/down for credit or close) without waiting for the 7% / Δ −0.30 trigger.

## Screen mode

1. **Primary:** `run_scan` **LC Put – IV Spike Dislocation** `81e24168-a345-40b5-aee8-74e7f051cc10` (mcap ≥ $20B, RH IV rank ≥ 0.40, 5-day ≤ −5%, put OI ≥ 10k, ER ≥ 7 days; columns IV30/HV30, RSI, % vs 21W/50W EMA, off 52W high) + the Liquidity Regime scan, then `python3 scripts/rs_pullback.py triage '{"rows":[{"t","ivr","ivhv","chg5","rsi","vs21","vs50","er"}...]}'` (ratios as the scan prints them). It classes each name EMA-FLUSH (sold into a weekly EMA → also run the RS overlay), EXTENDED, MID-AIR or BROKEN (below the 50W → sell-off triage before any IV call), penalises IV/HV < 0.8 (realized > implied) and marks the top 3 non-BROKEN names for step 3. Zero extra data calls. **Fallback** if that scan errors: `run_scan` **Oversold Quality Screener** `8726485e-b7ad-49a6-804a-71f9fa226503` (mcap > $10B, RSI14 < 35) and/or **Large Cap Losers 50B** `f7f85d4f-a4a3-42eb-b3f4-757b112092e8`. Use the noisy Large Cap Dislocation Screener (`6db40aac-d15c-42ab-a2ed-672598e72c28`, 1-day < −0.5%, ~60+ rows) only if asked, keeping rows with day % ≤ −3%. If an id errors, call `get_scans` once and match by name.
2. From rows: mcap ≥ $20B (≥ $5B only if mid-caps requested), drop clinical biotech, rank by drawdown and the scan's IV column when present; keep the top 3 (LEAN) / 4 (DEEP).
3. IV gate for those names: IBKR `search_contracts` in one turn, `get_price_snapshot` in the next (proxy only for names IBKR can't price). Full chain + `lc` only for the single best GREEN name in LEAN (≤ 2 in DEEP); list the rest as "GREEN — run next in a new chat".
4. **RS mode** ("RS scan", "pullback scan", "weekly EMA scan"): (a) `run_scan` **LC Put – RS Pullback to Weekly EMA** `2a180f78-9e8b-40b8-8a9e-224629d42d81` + **LC Put – Liquidity Regime** `f759011a-9c23-4491-9b40-7d492bc95b8b` in one turn (the scan already drops ER < 7 days and put OI < 10k); RISK-OFF → stop and print the regime line; (b) keep ≤ 9 names ranked by RH IV rank (0–1 scale, pre-filter only) then closeness to the 9W/21W; (c) one turn: weekly historicals (those + SPY) + EMA 9 + EMA 21 calls → `rs_pullback.py` without 30m; (d) IBKR IV gate for grade A/B names in zone or BETWEEN; (e) one 30minute call for GREEN/YELLOW survivors → rerun with `m30`; (f) full single-ticker `lc` workflow (Turns 3–5) only for READY names: 1 in LEAN, 2 in DEEP. Budget: LEAN ≤ 9 data calls up to (e), ≤ 15 total; DEEP ≤ 24.
5. Nothing passes → print exactly: **No tickers currently meet strict underwriting criteria.** then the table with what would flip each name (e.g., "IVR 41 → needs 50").

## Output

**Early exit (2 lines):**
> **XYZ $200.00 — REJECTED (NO-GO): IVR-eq 13 (IBKR IVP 52w 23 / 26w 18, as of date) < 30 → Pullback Watchlist.** Re-check when IVP52 ≥ 60.
> 🧠 One acerbic, numbers-first sentence on why cheap options on a great company are still a bad sale.

**Approved / conditional card:**
```
## TICKER — VERDICT (as of HH:MM ET, date)
**Trade:** Sell Dec 18 '26 160P / buy 100P · 86 DTE · limit $X.XX net (fill rule) · earnings CLEAN/HAZARD
| Net credit | BE (cushion) | Δ / PoT | ROC ann. | Max risk/ct | IVR (src) |
**Gates:** one line of ✅/⚠️/❌ from the calculator
**Forensics:** OCF − CapEx − SBC = owner FCF (yield) · D/EV · required cushion and why
**Structure (RS only):** grade · defended EMA $ · weeks held · 30m trigger/stop · strike ceiling & which support set it · regime
**Scenarios/ct:** Bull +$ (quick win) | Base +$ (50% GTC) | Bear −$ (spread max loss / −40% mark)
**Manage:** GTC price · quick-win range · 21-DTE date · defense trigger
**🧠 Reality check:** ≤5 sentences, acerbic and numbers-first — owner FCF vs headline EPS, SBC dilution, debt ahead of equity, what the sell-off is really pricing, and whether this trade exploits a mispricing or is a retail trap.
```
Cite the sell-off cause inline ([Source – date](url)). Mark every UNVERIFIED input.

**Screen table:** `Ticker | Spot | Day % | Mcap | IV30 | IVR (src) | Gate | Next ER | Verdict`
**RS screen table:** `Ticker | Grade | Zone | Run/In15 | vs 9W | vs 21W | 30m | IVR (src) | ER | Verdict` with the regime on the line above.
