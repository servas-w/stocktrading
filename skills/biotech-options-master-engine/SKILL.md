---
name: "biotech-options-master-engine"
description: "Underwrite clinical-stage and small-cap biotech options from the cash up. Fully diluted cash floors plus pipeline SOTP (Floor A/B), debt-acceleration traps, dilution and ATM audits, catalyst mapping into Mode A (pre-catalyst IV harvest), Mode B (binary event, Tier 1 fortress put) or Mode C (priced-for-perfection short via bear put debit spreads), Bayesian PoS, napkin DCF and a bundled calculator. Use whenever the user gives a biotech ticker or says audit, underwrite or evaluate a biotech, sell puts on a biotech, check my put math, cash floor, SOTP, drug PoS, PDUFA, AdComm, Phase 1/2/3 readout, catalyst, dilution, ATM, S-3 or pre-funded warrants, short a biotech run-up, or floors and catalysts for a list of tickers, even if the message is just a ticker. No liquidity gate: the user handles fills. Enforces Anti-CAPR and the False Dichotomy rule (a rejected put sale is not a long put). Triggers on BIO: TICKER (lean, optional trade) and BIO DEEP: TICKER; LEAN:/DEEP: still work."
---

# Biotech Options Master Engine (v5 lean-usage: cash + SOTP floors, BE-gated Mode B, split PoS, no liquidity gate, opt-in exposure)

Clinical biotechs are liquidating bank accounts holding lottery tickets. Underwrite the cash, harvest inflated IV, never pay for hope — and short only what is priced for perfection.

## Operating rules (why this version is cheap)

1. **Gate before you gather.** Cash, dilution and catalyst timing first; option chain only if a strike can exist; PoS / DCF / management deep-dives only when a Mode B or C verdict hinges on them. Stop at the first hard fail.
2. **Batch independent calls in one turn.** Budgets (data calls; calculator runs don't count): **LEAN** early exit ≤7 (Turn 1's 5 calls + Turn 2's financials and IV snapshot: every early exit needs those) · Mode A ≤11 · Mode B/C ≤12 (exposure check excluded unless requested) · Math-check ≤5 · **DEEP** ≤21. +2 when IVR comes from the proxy, +1 for the debt text block. At the budget, stop and mark gaps UNVERIFIED.
3. **The calculator does the math:** `python3 scripts/underwrite.py bio|strikes '<json>'`. Copy its numbers; never re-derive floors, EV or targets in prose. Missing inputs print n/a / UNVERIFIED — it never crashes. Don't open the script (~8k tokens): the JSON example below is its full interface.
4. **Fresh data only.** Every figure from this session's tool calls with an "as of"; never from memory, past chats or snippets.
5. **Compact card by default.** Load `references/deep-diligence.md` for Mode B/C PoS, napkin DCF, pipeline SOTP or management forensics; `references/full-dossier.md` only when asked for "full", "deep" or "dossier".
6. **Language.** A BUY on a name the user is short is "Buy to Cover". Large-caps without a binary inside the contract → large-cap-put-overreaction.
7. **The user handles execution.** He can usually get filled on thin small-cap chains. The engine's job is the math: floors, strike vs floor, BE, ROC, EV, catalyst timing. Never reject or early-exit on open interest, bid size or spread width.

## Usage budget (v5 — read first; overrides any looser rule below)

Default mode is **LEAN**: `BIO: TICKER`, `LEAN: TICKER` or a bare ticker. Switch to **DEEP** only when the user types `BIO DEEP:` / `DEEP:` / full / dossier, or a Mode B/C verdict flips across the PoS range. A trade after the ticker (`BIO: FHTX 2.5P Jan @0.45`, with either prefix) means Math-check mode at that depth. A LEAN card that is Mode B or C, or has the strike or BE within 10% of a floor, ends with one line: *→ BIO DEEP: TICKER for PoS / DCF / management.*

- **One ticker per chat.** Every new message re-processes all earlier tool output, so long multi-ticker threads burn the usage limit. If this chat already holds two finished underwrites, answer the request, then end with one line: *New chat recommended for the next ticker (usage).*
- **Search:** LEAN ≤ 2 `web_search_fast` per ticker (one combined catalyst + pipeline query, one financials fallback). Never `web_search` in LEAN. No image search, visualizer, memory reads or past-chat search unless asked.
- **Fetch:** every `web_fetch` carries `text_content_token_limit` ≤ 2500. Fetch the 8-K exhibit 99.1 earnings release, never the full 10-Q HTML (10–20k tokens).
- **Chains:** always pass `expiration_dates` (≤ 2 monthlies in LEAN; small caps need no strike filter); never pull a chain without an expiry filter. Quote ≤ 6 contracts in one call.
- **Exposure is opt-in.** Don't call `get_equity_positions`, `get_option_positions` or `get_portfolio` unless the user says "check my book" / "exposure", or names a position in this ticker. The user can clear the exposure gate inline — `have: none` or `have: -7x Nov 2.5P, NAV 375k` — pass that as `existing`. Otherwise cap at CONDITIONAL and print *exposure not checked (say "check my book")*. When checking: `get_option_positions` with `chain_ids` + `nonzero: true` only; `get_equity_positions` and `get_portfolio` at most once per chat.
- **Read once.** Don't re-open this file or a reference already read in this chat. Never open `scripts/underwrite.py`.
- **Tool loading:** `tool_search` with `limit` ≤ 3, using the exact queries in Data routing; don't load tools you won't call.
- **Output:** LEAN card ≤ 200 words with one table; early exits stay at 2 lines. Never paste raw calculator output.
- **Stop rule:** at the budget, stop and mark gaps UNVERIFIED. Never re-call a tool to "double check" unless the user asks.

## Hard rules

- **Anti-CAPR:** never short, or buy bearish options on, a name priced for failure (near its cash floor; calculator flags spot < 1.5× A2). Short alpha only for priced-for-perfection run-ups: run-up ≥ 50%, spot ≥ 3× A2, PoS ≤ 30%.
- **False Dichotomy:** a rejected put sale does not justify buying puts. Default is DO NOTHING / CASH.
- **Vehicles:** naked long puts only if IVR < 40 and PoS ≤ 30% and priced for perfection and no M&A overhang; otherwise a bear put debit spread. Never hold a naked equity short through data — Buy to Cover ≥ 48 h before the window. Never sell covered calls into a binary.
- **Cap table:** always fully diluted (basic + pre-funded + penny warrants + as-converted preferred). Robinhood `get_equity_fundamentals` share counts EXCLUDE pre-funded warrants (FHTX: 59.4M vs 70.6M FD, which overstated cash/sh by 19%), so never use them for FD. Take basic from the latest 10-Q cover and PFWs from its equity note (plus any post-quarter 8-K / 424B5); always pass `pfw` (0 only when verified none) and `shares_src`. Missing `pfw` caps every verdict at CONDITIONAL.
- **Debt:** if clinical failure lets a lender accelerate and liquid cash ≤ debt + covenant minimum, the floor is $0.
- **Floor = cash + SOTP.** Floor A = A1 + SOTP residual; Floor B = A2 + SOTP residual. Every non-lead program and every other indication of the lead molecule goes in the SOTP (haircuts in deep-diligence §5). **De-risked lead exception:** the lead asset also goes in, at the Phase 3 rung, when it already has positive pivotal data AND the event inside the contract is not an efficacy readout (filing, FDA acceptance, conference rehash, or nothing). Otherwise the lead stays out: it is the bet, and the floor must survive it failing. **Mode B gates on break-even, not strike:** K ≤ Floor B → Tier 1 fortress · K > Floor B but BE ≤ Floor B on an OTM strike → **Tier 1B BE-anchored put (lower tier:** the premium, not the strike, sits on the floor; the card prints the gap % and the credit hurdle K − Floor B) · ITM strike above Floor B → synthetic long, not a premium harvest → no · BE > Floor B → Tier 3. The cash-only A2 prints beside it as a ⚠️ line when the trade leans on the SOTP. Net debt, an acceleration trap, or net cash below the burn to the catalyst: the SOTP fills that hole first (calculator nets it). **Priced for perfection** (market EV > the lead's unrisked napkin-DCF PV) blocks Mode B outright: the calculator turns the verdict into NO SHORT PUT.
- **EV ≤ 0 → NO-GO**, even with the strike below the floor.
- **No liquidity gate.** Price the short at the user's fill (`short.fill`), else the mid. Bid, ask and OI are information only: OI < 150 or a market wider than 25% of mid gets one ⚠️ line on the card, never a rejection. **Stub quotes:** a 0 bid (or a market > 100% wide) makes the mid meaningless; the calculator then refuses to price it and prints the minimum credit for 25% annualized ROC, so quote that as the fill target instead of a fake mid.
- **Disqualifiers:** pending reverse split or Nasdaq bid-price deficiency; timeline slippage kills Mode A (becomes B*, Tier 1 standards); 13F ownership never substitutes for cash or trial rigor; ex-US / China licensing takes a 60–75% NRDL price haircut.

## Data routing

| Need | Tool | Notes |
|---|---|---|
| Spot | Robinhood `get_equity_quotes` | Fresher of regular / non-regular trade |
| ADV, 52w low | `get_equity_fundamentals` | `average_volume_30_days` as ADV proxy. **Never the share count** (excludes PFWs) |
| Filings & dilution history | `get_sec_filing_index` (form types 10-Q, 10-K, 8-K, S-3, 424B5, S-1; since 12 months) | 424B5 = ATM/offering takedowns; 8-K = financing, debt, timeline |
| Cash, debt, burn, shares | `get_sec_filing_facts` ×2 (sets below); if empty (unindexed small-cap 10-Q — common), `web_search_fast` "COMPANY quarter year 10-Q cash runway" then `web_fetch` the SEC press-release exhibit it returns | The 8-K earnings exhibit usually states cash, shares and runway in one document — faster and more reliable than the XBRL backup for small/mid-cap biotech |
| Debt terms (only if debt > 0) | `get_sec_filing_facts` concept `DebtDisclosureTextBlock` (or `LongTermDebtTextBlock`) | Covenant minimum cash; clinical-failure / MAC acceleration |
| Catalyst window & fidelity | `web_search_fast` "COMPANY upcoming data readout 2026" (+ `web_fetch` the company's own press release or IR page for a specific date) | Compare with prior guidance → slipped? Cite inline |
| Management Q&A | `web_search_fast` "COMPANY earnings call transcript Q&A" (Quartr `search_companies` → `read_transcript` if a full transcript read is needed) | Needed for a Mode A/B approval (mgmt gate); mark UNVERIFIED rather than guess if nothing turns up |
| Put chain | `get_option_instruments` (chain_symbol, type=put, `expiration_dates` = 2–3 candidate monthlies comma-separated, e.g. "2026-10-16,2026-11-20,2027-01-15"; no strike filter) → `get_option_quotes` | Small caps often skip monthlies; one multi-expiry call avoids an empty result. Quote only strikes ≤ max eligible + ATM (≤6 ids LEAN, ≤20 DEEP, one call) |
| IV gate | IBKR `search_contracts` → `get_price_snapshot` (ladder below) | Never Barchart fetch |
| Trial design (B/C deep only) | Clinical Trials `search_trials` (small page_size) → `analyze_endpoints` | Avoid `get_trial_details` (lists every site) |

**IV gate ladder** (same as the large-cap skill): (1) **IBKR, primary** — `search_contracts` {query: TICKER} (exact `symbol` match, US listing, OPT in sections) → `get_price_snapshot` with `["last","implied_vol_underlying","implied_volatility_percentile","historical_vol"]`; pass `ivr_src:"ibkr"`, `ivp_52w`/`ivp_26w`/`ivp_13w` = `implied-volatility-percentile.high_52w/26w/13w`, `iv30` = `implied-vol-underlying.annual_iv`, leave `ivr` null. IBKR gives IV Percentile, not IVR: the calculator uses IVR-eq = IVP52 − 10, so the 40/50/70 gates read IVP52 50/60/80, and GREEN needs IVP26 ≥ 50. Load IBKR with `tool_search "search_contracts"` and `tool_search "get_price_snapshot implied volatility"`. Search by the bare tool name: the server prefix varies by install, so a full-name query can miss. (2) user-supplied Barchart IVR → `ivr_src:"barchart"`; (3) proxy, only if IBKR fails — `web_search_fast "optionsanalysissuite TICKER iv-hv-history"`, then `web_fetch` that URL with `text_content_token_limit: 1500`, pass `ivr_src:"OAS proxy"`, `iv30` = its ATM IV, plus `atm_iv` from the live chain (proxy auto-rejected if > 30% apart; near 40/50/70 → confirm on IBKR IVP); (4) none → UNVERIFIED → CONDITIONAL at best. Never fetch barchart.com (JavaScript-rendered, returns nothing).

**Financials fallback chain:** (1) `get_sec_filing_facts` on the latest 10-Q — sets below; (2) empty (unindexed small-cap filing) → `web_search_fast` "COMPANY quarter year 10-Q cash runway" then `web_fetch` the SEC exhibit 99.1 / press-release URL it returns, which typically states cash, shares outstanding and runway guidance together (confirmed working on MGNX 9/25); (3) still missing an item → mark it UNVERIFIED rather than estimate. Pre-funded warrants specifically: check the 10-Q equity note (`get_sec_filing` section read) or a post-quarter 8-K; if genuinely not stated anywhere, leave `pfw` unpassed (caps the verdict at CONDITIONAL) rather than assuming 0.

**XBRL sets** (backup; guess directly; `get_sec_filing_facts_catalog` once only if a load-bearing concept is missing):
- Call 1, latest 10-Q: `CashAndCashEquivalentsAtCarryingValue`, `ShortTermInvestments`, `MarketableSecuritiesCurrent`, `AvailableForSaleSecuritiesDebtSecuritiesCurrent`, `RestrictedCashCurrent`, `RestrictedCashNoncurrent`, `LongTermDebt`, `LongTermDebtNoncurrent`, `ConvertibleNotesPayable`, `ClassOfWarrantOrRightOutstanding`.
- Call 2, latest 10-Q + 10-K: `NetCashProvidedByUsedInOperatingActivities`, `EntityCommonStockSharesOutstanding`, `CommonStockSharesOutstanding`, `ClassOfWarrantOrRightExercisePriceOfWarrantsOrRights1`, `PreferredStockSharesOutstanding`.
- Burn: TTM OCF = FY + YTD − prior YTD; `q_burn` = TTM/4, but use the latest quarter if it exceeds TTM/4 by > 25% (accelerating burn). Shares: latest cover-page count; warrants with exercise price ≤ $0.01 are pre-funded/penny → `pfw`. If the warrant breakdown is ambiguous, read `StockholdersEquityNoteDisclosureTextBlock` once. Don't double count cash that filers tag under two concepts.
- A 424B5 / financing 8-K dated after the 10-Q → add its net proceeds to cash and its shares/PFWs to the cap table (post-quarter raises move the floor).
- **XBRL backup comes back empty** (filing not indexed; `get_sec_filing` may 404 too): don't call the catalog or the text reader — mark the item UNVERIFIED.
- **Royalty-monetization / synthetic royalty liabilities** (Sagard, Royalty Pharma, etc.): treat as non-recourse (exclude from `debt`) only if the filing says repayment is limited to the royalty stream; otherwise include. Either way, name it as load-bearing if it exceeds 25% of cash.
- **Burn not stated:** back it out of runway guidance (cash ÷ quarters of guided runway) and label it an estimate.
- **ATM sales after quarter-end** (disclosed in the 10-Q equity note): add net proceeds to cash and shares to the cap table.
- **Cash is as of the balance-sheet date:** subtract burn for the days elapsed since then (q_burn × days/91) before passing `cash`.

## Workflow

1. **Turn 1 (parallel):** quotes, fundamentals, filing index, ONE combined search (`"COMPANY pipeline catalyst readout 2026"`), IBKR `search_contracts` (skip if the user gave Barchart IVR).
   - **User brought the trade** (strike + premium, or "I sold / I'm selling X"): skip the chain and go straight to Math-check mode below.
   - The combined search covers the pipeline (a second pipeline-only search is DEEP-only): every program and indication with its stage, whether a Tier 1 pharma partner holds it, and whether the lead already has positive pivotal data. Classify the in-contract catalyst as an efficacy readout or not (`catalyst.efficacy_readout`).
2. **Turn 2 (parallel):** `get_sec_filing_facts` financials + IBKR `get_price_snapshot` (+ debt text block if a credit facility exists; proxy search/fetch only if IBKR fails). XBRL empty → `web_search_fast` + `web_fetch` the earnings press release in the next turn. No window found → set `window_start` = today (Tier 1 standards, conservative).
3. **Pre-chain `bio` run** (no `short`, always with `pipeline`): floors, SOTP, runway, ATM wet blanket, mode, max eligible strike. **Early exits:**
   - Reverse split / deficiency → no put underwriting.
   - Max eligible strike (Floor B in Mode B) ≤ $0 or below the smallest *listed* strike, and Mode C not in play → pass `listed_strikes` so the calculator prints the Tier 1B hurdle (credit ≥ K − Floor B) for each OTM strike above the floor; quote the lowest one (1 call). Its mid (or the user's fill) below the hurdle → **DO NOTHING / CASH**. Strike existence counts; bids and OI don't.
   - Verified IVR < 50 → **warning only** (Playbook Rule 1: for biotech the floors carry the trade, not the IV). Keep underwriting; the gate prints ⚠️, and the card says the premium is thin and quotes the min-credit-for-25%-ROC line.
   - Mode C is in play only if spot ≥ 3× A2 (then fetch `runup`, which must be ≥ 50%); otherwise the short side is closed (Anti-CAPR) — skip PoS work.
4. **Turn 3 (parallel):** put instruments for the chosen expiry (+ management Q&A search if heading for approval).
   - Mode A: expiry 30–90 DTE and ≥ 14 days before `window_start`. Mode B: expiry after the window, BE ≤ Floor B (A2 + SOTP): Tier 1 when K ≤ Floor B, Tier 1B when only BE clears it. Buffer impossible → B*.
   - Strike: any listed strike at or below max eligible; list them with mid credits and let the user work the fill. Mode A also needs net BE ≤ anchor A, K ≤ raw cash/share, runway > 12 m, OTM ≥ 35% (≥ 50% if mgmt YELLOW). Target ROC ≥ 25% annualized on cash.
5. **Turn 4 (parallel):** `get_option_quotes` (+ exposure only if opted in per Usage budget: `get_option_positions` with `chain_ids` + `nonzero`, `get_equity_positions` / `get_portfolio` once per chat; main book = default margin account ending 6081, Shadow Delta = ending 1686; or use the user's inline `have:`) → full `bio` run with `existing` (`{"shares","avg_cost","short_puts","short_calls","nav","max_name_pct"}`, default cap 10% of NAV with every put assigned; without it approvals cap at CONDITIONAL) → card. Holding the stock > 15% under cost → no new puts on that name.
6. **Assigned / held biotech lots:** run `bio` without `short` for the floors. Cost basis ≤ Floor B → hold or wheel calls. Cost basis > Floor B with a binary inside the next 90 days → exit or collar before the window (a held lot through data is naked binary exposure above the floor). Cost basis > Floor B with no near binary → no new puts; covered calls only. Track assigned-lot P&L separately from option P&L.
7. **Mode B/C only:** two probabilities, never one. **Event PoS** (`pos` / `pos_model`) = odds the binary inside the contract is positive; it drives binary EV and Mode C. **LoA** (`pos_loa`, or `pos_loa_after` = the transition baselines after the event; the calculator multiplies in the event PoS) = the lead's cumulative odds of approval; it only risk-adjusts the napkin DCF. A Phase 1 readout at 40% event PoS is ~5% LoA; using 40% on the DCF inflates Base 8×. **Sensitivity rule:** run `bio` at both ends of the range; same verdict → done (report the range); verdict flips → load `references/deep-diligence.md` and model the factors before any trade. Mode C adds `runup` (spot ÷ lowest weekly close of ~6 months via `get_equity_historicals` − 1; 52w-low fallback flagged as an upper bound) and a `debit_spread` (buy ATM Δ −0.45…−0.55, sell OTM at A2, Δ −0.10…−0.20).

## Math-check mode (default when the user brings a trade)

The user usually already has the fill. Verify his numbers; don't re-scout the chain.

1. **Turn 1 (parallel):** quotes, fundamentals, filing index, financials search, pipeline + catalyst search. Skip IVR work unless he asks.
2. **One `bio` run** with `short: {"strike", "fill"}` (delta if he has it), `pipeline`, `pfw` + `shares_src`, `pos` (baseline table; a range if soft → run both ends), and `pos_loa_after` when a DCF is in play.
3. **Report:** Floor A / Floor B vs strike and vs BE (and vs cash-only A2), tier (1 / 1B / 3), BE, OTM %, ROC on cash (on extrinsic if ITM), binary EV, every catalyst date inside the contract, verdict. Flag any arithmetic in his message that disagrees with the calculator, showing both numbers.
4. Budget ≤ 5 data calls (LEAN).

## Floor scan (several tickers)

When asked for "floors and catalysts" on a list: one `bio` run per ticker (no `short`), then one table: Ticker · Spot · Net cash/sh · A2 · SOTP/sh · **Floor B** · Floor A · Spot ÷ Floor B, followed by a per-ticker list of what sits in each SOTP and a dated catalyst list with citations. Budget ≤ 3 data calls per ticker; if the list exceeds 5 tickers, split it across chats.

**PoS baselines (%)**

| Transition | Baseline |
|---|---|
| Phase 1→2 | solid tumor 38–42 · heme 45–52 · non-onc 55–65 |
| Phase 2→3 | unselected solid tumor 22–28 · biomarker-selected 35–42 · immunology 30–38 · rare genetic 45–55 · CNS 18–25 |
| Phase 3→filing | oncology 50–60 · non-onc 60–70 |
| Filing→approval | standard 85–90 · priority/accelerated 88–92 |

Investigator-assessed responses (no BICR): haircut response rates 15–20% before using them. Class with > 80% historical failure: cap PoS at 20–25%.

## `bio` input (JSON)

```json
{"ticker":"BIOX","asof":"2026-09-23","spot":6.10,"exp":"2026-11-20",
 "ivr_src":"ibkr","ivp_52w":0.82,"ivp_26w":0.77,"ivp_13w":0.91,"iv30":110,"atm_iv":105,
 "cash":9.0e7,"st_inv":6.0e7,"restricted":2.0e6,"debt":0,"covenant_min":0,"accel_on_failure":false,
 "basic_shares":3.0e7,"pfw":4.0e6,"shares_src":"10-Q 6/30 cover + equity note","penny_warrants":0,"pref_as_converted":0,
 "ocf_ttm":-4.8e7,"adv20":9.0e5,
 "catalyst":{"type":"Ph2 topline","window_start":"2027-01-01","window_end":"2027-03-31","guidance_slipped":false,"efficacy_readout":true},
 "short":{"strike":2.5,"fill":0.35,"bid":0.30,"ask":0.40,"delta":-0.10},
 "mgmt":"GREEN","reverse_split_pending":false,
 "pos":null,"pos_model":{"baseline":0.25,"factors":[0.10,-0.10],"cap":0.25},"p_statsig":null,
 "pos_loa_after":[0.55,0.88],"listed_strikes":[2.5,5],
 "pipeline":[{"name":"LEAD","lead":true,"pivotal_positive":false},{"name":"LEAD 2nd indication","stage":"ph2"},
              {"name":"PROG-2","stage":"ph1"},{"name":"PROG-3","stage":"preclinical","partnered":true},{"name":"PROG-4","pv":2.0e8}],
 "runup":null,"debit_spread":null,"dcf":null}
```
Omit keys you don't have. Probabilities as decimals; `runup` as a decimal (0.8 = +80%); dollars raw. `short.fill` = the user's actual premium (overrides mid). `pipeline` items take `stage` (preclinical / ph1 / ph2 / ph3 → ladder value) or an explicit `pv`, plus `partnered` for Tier 1 pharma. Always list the lead with `lead: true` and `pivotal_positive`; the calculator includes it at the Phase 3 rung only when `pivotal_positive` is true and `catalyst.efficacy_readout` is explicitly false (missing = treated as an efficacy readout), and prints why it was in or out. `pos` / `pos_model` = event PoS; `pos_loa` (decimal) or `pos_loa_after` (transitions after the event; event PoS is multiplied in) = the lead's LoA for the DCF only — without it Base prints n/a rather than borrow the event PoS. `pfw`: omit only if truly unknown (verdict caps at CONDITIONAL); 0 = verified none. `listed_strikes`: pre-chain run prints the Tier 1B hurdle per OTM strike above Floor B. `pos_model`, `dcf`: see deep-diligence.

## Management

GTC buy-to-close at 50% of credit immediately · IV-deflation exit when IVR falls 20–30 points below entry (calculator prints the levels) · 48-hour escape hatch: buy to close before any ad-hoc data, abstract or partner presentation scheduled inside the contract · Class B collapse on a Tier 1 put: cash covers assignment; re-audit salvage value, never roll for a debit · Mode C spread: risk is the debit; no adjustments that add risk.

## Output

**Early exit (2 lines):** `**TICKER $spot — DO NOTHING / CASH:** reason with the numbers (e.g., max eligible strike $0.85 vs lowest listed $2.50; spot 1.2× A2 → Anti-CAPR).` + one 🧠 sentence.

**Full card:**
```
## ⚡ TICKER — VERDICT (as of HH:MM ET, date)
**Trade:** Sell Nov 20 '26 2.5P · 58 DTE · limit $0.35 (fill rule) · BE $2.15 · Mode A (expires 42 d before window) · Mode B cards state the tier (1 / 1B + gap %)
| Credit | BE | OTM | Δ | ROC ann. | EV/ct (Δ-only) | IVR (src) |
**Targets:** Bear $x (Floor B) | Base (net cash + SOTP ex-lead + lead DCF × LoA) | Bull (net cash + SOTP ex-lead + unrisked lead DCF)
**Catalyst:** event · window · source · guidance fidelity (verified / softened / slipped)
**Cash anchor:** FD shares · gross / net liquid · raw & net cash/share · runway · debt, covenant, acceleration
**Floors:** A2 cash-only · SOTP residual/sh (assets, stage, partner; lead in or out and why) · **Floor B** · Floor A
**Vitals:** ATM wet blanket % · dilution history (S-3, ATM, 424B5 dates) · mgmt GREEN/YELLOW/RED
**Gates:** one ✅/⚠️/❌ line from the calculator
**🧠 Reality check:** ≤5 sentences, acerbic and numbers-first — what retail misreads, the trial-design or cash reality, and whether the vehicle is +EV or a broken structure.
**Manage:** GTC price · IV-deflation exit levels · 48 h escape-hatch date · invalidation triggers (clinical hold, partner exit, pre-event raise)
```
Mode C card: replace Trade with the debit spread (debit, max gain, R:R vs 3:1, BE, EV) and add the Anti-CAPR evidence (run-up, spot ÷ A2, PoS). Cite catalyst and management sources inline.
