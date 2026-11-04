---
name: "stock-valuation-engine"
description: "VALU v2. Value a stock from its last 4 earnings, competitors and the market backdrop: owner-FCF reverse DCF (what growth the price implies), bear/base/bull DCF, own-history trough P/FCF, peer forward P/E and P/S on CORE earnings (non-operating marks stripped), a capex-normalized no-growth value for names in a capex build-out, beta, and a 12-week move split into market, sector and company-specific parts. Prints a fair-value range, a floor (or soft floor) per share and a VALU_HANDOFF line the large-cap-put-overreaction (LC) skill takes as val_floor. Use whenever the user types VALU: TICKER, VALU DEEP: TICKER or VALU LC: TICKER, asks what a stock is worth, its fair or intrinsic value, whether it is cheap, expensive, undervalued or overvalued, what growth the price implies, how it stacks up against competitors or peers, whether a sell-off is company-specific or market-driven, or wants a valuation floor under a put strike, or pastes another model's valuation (e.g. Gemini VALU) to audit. Not for clinical-stage biotech (use biotech-options-master-engine); banks and insurers get a P/E-only read."
---

# Stock Valuation Engine (VALU v2)

Price is what you pay; owner cash flow is what you get. Value the stock on OCF − CapEx − SBC (never adjusted EPS alone), test the price from four directions (reverse DCF, forward DCF, its own history, its peers), then say how much of the recent move is the company and how much is the market.

Works alone (**VALU: TICKER**) or as the floor supplier for LC (**VALU LC: TICKER**, or when an LC underwrite's floor check hinges on valuation). It never sizes or recommends a trade; LC does that.

The Gemini skill `stock-valuation-engine-gemini` (in `skills/stock-valuation-engine-gemini/`) runs the same method and prints the same card, so the two outputs can be compared line for line.

## Hard rules (shared with the Gemini skill)

1. **SBC is subtracted once, from cash flow only.** Owner FCF = OCF − CapEx − SBC, because OCF adds SBC back. Operating income, EBIT, NOPAT and EPS already expense SBC: never subtract it from them again.
2. **Core earnings for multiples.** Core pre-tax = operating income − interest expense (interest is recurring and stays in). When the rest of the non-operating line (pre-tax − core pre-tax) exceeds 15% of operating income over 4 quarters, GAAP EPS and consensus EPS carry one-off marks (equity-stake revaluations, investment gains, impairments). Peer forward P/E is then applied to **forward core EPS** (consensus F1 minus the marks already booked this fiscal year, after tax; fallback: core TTM EPS grown to FY end), plus positive net cash per share, because core EPS leaves out interest income. The EPS F1→F2 growth leg is dropped from base growth. If interest is unknown, only net non-operating *gains* are flagged; a net expense is assumed to be interest. The calculator does this when `pretax` and `tax` (and ideally `int_exp`) are in `is_q`.
3. **No invented cash-flow paths.** Never type in a year-by-year FCF forecast. The DCF shape is fixed (5 years at g, a linear fade to 2.5% over years 6–10, then a Gordon terminal value); only g and r move, and both come from rules.
4. **Capex surge (CapEx > 2× D&A)** gets the capex-normalized lens: maintenance capex = the largest of TTM D&A, run-rate D&A (last quarter × 4) and net PP&E ÷ life (when `ppe_net` is passed); normalized owner FCF = OCF − SBC − maintenance. Its no-growth value (EPV = normalized owner FCF ÷ r + net cash) is a **soft floor**, never `val_floor`. Own-history P/FCF is applied to normalized FCF. With negative owner FCF the verdict is CAPEX-CYCLE and fair = median(peer P/E value, history × normalized FCF, P/S value); with positive but squeezed owner FCF the floor still uses real owner FCF, and fair swaps in the normalized history value.
5. **One asset base for every scenario.** Net cash = cash + current marketable investments − debt (no leases, no preferred stock). Long-term or private stakes are not added to any value. If they exceed 5% of market cap, name their size in the reality check.
6. **One share count** (Zacks `shares_outstanding`) for every per-share figure.
7. **Primary data only.** Statement figures come from Zacks, SEC XBRL or the company's filings. Blogs and news sites may only explain why the stock moved, cited inline, and never supply a number in the table.
8. **Valuation only.** No IV gate, no strikes, no "buy/sell" calls: hand the result to LC.

## Operating rules

1. **Cheapest route first.** Zacks returns several things per call (peers, estimates, surprises, beta, FY end); use it before anything else. Batch independent calls in one turn.
2. **Budget (data calls; calculator runs don't count):** **LEAN** ≤ 10 · **DEEP** ≤ 15 · **LC mode** ≤ 6 when LC already ran in this chat (reuse its spot, SBC, cash, debt and earnings). At the budget, stop and mark gaps UNVERIFIED.
3. **The calculator does the math.** `python3 scripts/valuation.py valu '<json>'` (inline JSON, a file path, or `-` for stdin). Copy its numbers; don't recompute in prose. Don't open the script: the JSON example below is its full interface.
4. **Fresh data only.** Every number comes from this session's tool calls, stamped "as of". A gap is UNVERIFIED, never a remembered number.
5. **Never call** Alpha Vantage `TREASURY_YIELD` (returns ~70 years, ~15k tokens) or full 10-Q HTML. Zacks statement calls always pass `periods`.
6. **Language.** Valuation is an estimate with stated assumptions, not a price target or advice. Say "the model implies", not "the stock will".

## Data routing

| Need | Tool | Notes |
|---|---|---|
| Spot | Robinhood `get_equity_quotes` | fresher of `last_trade_price` / `last_non_reg_trade_price` |
| Peers, FY end, adj EPS by quarter, F1/F2 estimates, next ER | Zacks `get_zacks_metrics` (one ticker) | `Top Peers` table = the peer set · `lst_com_fy` = `fy_end` · EPS Estimates table: the (A) cells, oldest→newest → `eps_adj_q` (usually 7) · ANNUAL (E) of the current and next FY = `eps_f1` / `eps_f2`. **Snapshot-type reports** (no Top Peers or EPS table): take `eps_f1`/`eps_f2` from `compare_stocks`, `eps_adj_q` from Robinhood earnings actuals, and pick the 4 closest US-listed competitors yourself, labelled "peers: manual" |
| EPS beat/miss, last 4 | Robinhood `get_earnings_results` | rows with `eps.actual` → `surprises: [{est, act}]`, oldest→newest |
| Peer multiples, shares, beta, market move | Zacks `compare_stocks` [TICKER + 4 peers] (default section) | per peer: `pe.pe_f1` → `pe_f1`, `price.ratio.to_sales` → `ps`, `pe.peg_ratio` → `peg`, `price.percent_chg.4_week` / `12_week` → `chg4w` / `chg12w` · ticker column: `issue_attributes.shares_outstanding` → `shares`, `issue_attributes.beta` → `beta`, `pe.peg_ratio` → `peg`, `percent_chg.4_week` / `12_week` → `t_chg4w` / `t_chg12w`, `percent_chg.4w_sp500` / `12w_sp500` → `t_rel4w` / `t_rel12w`, `price.previous_day.close` → `zacks_px` |
| Quarterly cash flow | Zacks `get_cash_flow` [TICKER] `period: "Q"`, `periods: 5` | **Year-to-date figures** → pass as-is in `cf_q` with `cf_mode: "ytd"`, **including `da` (`depreciation_amortization`)**; the calculator de-cumulates and builds TTM OCF, CapEx and D&A |
| Annual cash flow (history) | Zacks `get_cash_flow` [TICKER] `period: "A"`, `periods: 5` | → `annual: [{end, ocf, capex}]` |
| Quarterly P&L | Zacks `get_income_statement` [TICKER] `period: "Q"`, `periods: 8` | → `is_q: [{end, rev, op_inc, ni, eps, pretax, tax, int_exp}]` (`revenue`, `operating_income`, `net_income`, `eps_diluted`, `pretax_income`, `income_tax`, `interest_expense`; discrete quarters; omit `int_exp` when Zacks returns null). They drive the core-earnings check |
| SBC, cash, debt | `get_sec_filing_index` (symbol, ["10-Q","10-K"], since ≈ 15 months) → one `get_sec_filing_facts` (filing_ids [latest 10-Q, latest 10-K]) with these 10 concepts: `ShareBasedCompensation`, `CashAndCashEquivalentsAtCarryingValue`, `ShortTermInvestments`, `AvailableForSaleSecuritiesDebtSecuritiesCurrent`, `LongTermDebtNoncurrent`, `LongTermDebt`, `LongTermDebtCurrent`, `DebtCurrent`, `CommercialPaper`, `DebtInstrumentCarryingAmount` | SBC TTM = FY + YTD − prior YTD (if SBC is missing, retry once with `AllocatedShareBasedCompensationExpense`). Cash = cash + current investments; if the investment concepts come back empty, use Zacks `get_balance_sheet` `cash_and_st_investments` (one more call). Debt = noncurrent + current (`DebtCurrent`, else `LongTermDebtCurrent` + CP); no leases. Cross-check against `DebtInstrumentCarryingAmount` and say so if they're > 10% apart. Use rows with no axis. **Divide raw dollars by 1e6** |
| Net PP&E (optional, sharper soft floor) | Zacks `get_balance_sheet` [TICKER] `period: "Q"`, `periods: 1` | `ppe_net` → `ppe_net`; pass `ppe_life` (years, default 10) only with a reason. Make this call in DEEP, or in LEAN when CapEx > 2× D&A and a call is left in the budget |
| Fiscal-year lows (history) | Robinhood `get_equity_historicals` [TICKER only] `interval: "month"`, start ≈ 5 years before the latest FY end | → `px_m: {"t":["2021-12",...], "l":[low_price...]}`. **Never pull weekly multi-year bars or extra symbols** |
| Risk-free rate | user-typed, else 4.5% ASSUMED (LEAN) · DEEP: one web search "10 year treasury yield today" | the calculator labels an assumed rf |

**Peer pick (automatic):** from Zacks `Top Peers`, take the first 4 that are US-listed common stock and not the ticker itself. Skip 5-letter tickers ending in F or Y (OTC / ADR lines). If `compare_stocks` returns a peer with a `reason` (unresolved), drop it. Name the peers in the card.

**Financials** (banks, brokers, insurers): pass `"financial": true` and skip the cash-flow calls; the calculator gives a peer P/E read only and no floor.

## Workflow

**LEAN (10 calls, 2 turns):**
1. **Turn 1 (parallel, 4):** `get_equity_quotes` · `get_zacks_metrics` · `get_earnings_results` · `get_sec_filing_index`.
2. **Turn 2 (parallel, 6):** `compare_stocks` (ticker + 4 peers) · `get_cash_flow` Q5 · `get_cash_flow` A5 · `get_income_statement` Q8 · `get_sec_filing_facts` · `get_equity_historicals` monthly 5y (ticker only).
3. Run `valu` → card.

**DEEP (≤ 15):** LEAN plus a risk-free web search, `compare_stocks` section `GRAT` (sanity-check `g.base`; override it if the calculator's base differs by > 5 points, saying so), section `ERV` (estimate revisions), and, if the move is COMPANY-SPECIFIC, one web search "TICKER stock drop reason" to name the cause.

**LC mode:** reuse LC's spot, quotes, earnings and SEC facts; call only `get_zacks_metrics`, `compare_stocks`, both `get_cash_flow`, `get_income_statement` and `get_equity_historicals`. Hand back: *pass `val_floor` (and `val_implied_g`) into the `lc` JSON. `val_soft_floor` is context only, never a strike anchor.*

**AUDIT mode** (the user pastes another model's VALU, e.g. Gemini): run LEAN, then add one table, "Their number / Ours / Why it differs", for verdict, fair, floor, owner FCF, core EPS and implied growth. Flag every breach of the hard rules above by number.

## `valu` input (JSON)

```json
{"ticker":"XYZ","asof":"2026-10-23","spot":268.54,"shares":389.2,"fy_end":"2025-11-30",
 "cash":5639,"debt":6363,"sbc_ttm":2071,
 "cf_mode":"ytd","cf_q":[{"end":"2026-08-31","ocf":7646,"capex":-180,"da":610},{"end":"2026-05-31","ocf":5123,"capex":-95,"da":405},
   {"end":"2026-02-28","ocf":2958,"capex":-37,"da":200},{"end":"2025-11-30","ocf":10031,"capex":-179,"da":820},{"end":"2025-08-31","ocf":6871,"capex":-145,"da":612}],
 "annual":[{"end":"2025-11-30","ocf":10031,"capex":-179},{"end":"2024-11-30","ocf":8056,"capex":-183}],
 "is_q":[{"end":"2026-08-31","rev":6760,"op_inc":2354,"ni":1827,"eps":4.62,"pretax":2290,"tax":463},
   {"end":"2026-05-31","rev":6618,"op_inc":2238,"ni":1712,"eps":4.25,"pretax":2150,"tax":438}],
 "eps_adj_q":[5.08,5.06,5.31,5.5,6.06,5.96,6.13],
 "surprises":[{"est":4.99,"act":5.50},{"est":5.46,"act":6.06},{"est":5.60,"act":5.96},{"est":5.84,"act":6.13}],"est_rev_4wk":0,
 "eps_f1":24.47,"eps_f2":27.7,"peg":0.73,"beta":1.42,
 "t_chg4w":5.97,"t_chg12w":-3.18,"t_rel4w":5.27,"t_rel12w":-8.68,"zacks_px":255.06,
 "px_m":{"t":["2021-12","2022-01"],"l":[538.05,480.62]},
 "peers":[{"t":"INTU","pe_f1":14.28,"ps":4.18,"peg":1.09,"chg4w":17.02,"chg12w":0.74}],
 "rf":0.045}
```
Only actual (A) cells go in `eps_adj_q`. Optional: `"ppe_net"` + `"ppe_life"`, `"sales_q"`, `"mcap"` + `"mcap_px"` instead of `shares`, `"erp"` (default 0.05), `"tax_rate"` (used when `tax` is missing; else 21% ASSUMED), `"g":{"bear","base","bull"}` growth overrides as decimals, `"financial": true`. Money is in $ millions throughout. Missing keys print n/a / UNVERIFIED; pass what you have.

## What the calculator does (so you can explain it, not redo it)

- **Earnings:** beats out of 4, average EPS surprise, sales and adjusted-EPS YoY for each of the last 4 quarters → ACCELERATING / STEADY / DECELERATING / SHRINKING; operating-margin trend; quality = owner FCF ÷ GAAP net income, the adjusted-vs-GAAP EPS gap and SBC/OCF (LOW when conversion < 0.7x, the gap is > 40% or SBC > 25% of OCF).
- **Core earnings:** non-operating ex-interest = TTM pre-tax − (TTM operating income − interest). If it is > 15% of operating income → NON-OP DISTORTION (with interest unknown, gains only). Core EPS = (operating income − interest) × (1 − tax), with tax = the TTM effective rate clamped to 10–25%. Forward core EPS = consensus F1 minus FY-to-date marks after tax (used when within 0.7–1.6× core TTM), else core TTM × (1 + op-income growth)^(months to FY end ÷ 12). Peer P/E × forward core EPS + positive net cash/sh is the peer value, with a leave-one-peer-out range; EPS F1→F2 drops out of base g.
- **Market:** Zacks beta; the S&P's move backed out of the S&P-relative change; the stock's 12-week move split into market-explained (β × S&P) and residual. ≥ 8 points from the peer median → COMPANY-SPECIFIC; otherwise NO MAJOR MOVE, MARKET-DRIVEN, SECTOR-WIDE or MIXED. The stock's leg is re-marked to live spot via `zacks_px`. r = rf + β × ERP, clamped 7–14%.
- **Valuation:** reverse DCF (the 5-year owner-FCF growth the price implies, fading to 2.5%), a bear/base/bull DCF (base g = average of F1→F2 EPS growth and TTM sales growth, clamped −5% to 20%), P/FCF at each fiscal year's lowest monthly low (trough and median), and peer forward-P/E and P/S values.
- **Capex-normalized:** when CapEx > 2× D&A or owner FCF ≤ 0: maintenance capex (largest of TTM D&A, run-rate D&A, net PP&E ÷ life), normalized owner FCF, EPV = normalized FCF ÷ r + net cash (soft floor), the normalized growth the price implies, and history-median P/FCF × normalized FCF.
- **Range:** floor = the lower of the bear DCF and trough P/FCF × owner FCF · fair = the median of base DCF, history value (on normalized FCF in a capex surge) and peer forward-P/E value; with no owner cash, the median of peer P/E, history × normalized FCF and P/S values · verdict AT FLOOR / DEEP VALUE / UNDERVALUED (< 85% of fair) / FAIRLY VALUED / RICH (> 115%) / **CAPEX-CYCLE (rel. to peers)** (negative owner FCF, capex surge, positive normalized FCF) / SPECULATIVE (no owner cash at all) · `VALU_HANDOFF` JSON line for LC.

## Output

**Card (LEAN ≤ 350 words, one table).** Start with the `##` heading: no preamble, no call narration. Each bold line is at most 2 sentences; the reality check is at most 4. Never paste raw calculator output; the `VALU_HANDOFF` line is the one exception, printed once as code on the For LC line.
```
## TICKER — VERDICT (as of HH:MM ET, date)
| Floor | Soft floor | Fair | Bull | Spot | Margin of safety | Implied growth |
**Earnings (last 4):** beats x/4 · sales YoY trend · margin trend · quality
**Core vs GAAP:** (only if NON-OP DISTORTION or a capex surge) core TTM and forward core EPS vs GAAP EPS · CapEx ÷ D&A and the maintenance basis · normalized owner FCF and the growth the price implies on it
**Competitors (A, B, C, D):** fwd P/E (core if flagged) and P/S vs peer median · peer value with its leave-one-out range · who is growing faster
**Market:** β · 12w move: market-explained vs residual → COMPANY-SPECIFIC / SECTOR-WIDE / MARKET-DRIVEN
**Rates:** r and what +100bp does to fair value
**🧠 Reality check:** ≤ 4 sentences, numbers first: what growth the price really assumes, whether owner cash backs the EPS, and what would make the floor wrong.
**For LC:** val_floor $X · val_implied_g Y% · `VALU_HANDOFF {...}`
```
Columns with no value print "n/a"; never fill one with a guess. Mark every UNVERIFIED input. Cite the sell-off cause inline when searched ([Source – date](url)). Attribute Zacks figures to Zacks Investment Research and end with a Sources line linking each ticker: `https://www.zacks.com/stock/quote/<TICKER>?utm_source=zacks_mcp`.
