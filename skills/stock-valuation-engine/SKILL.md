---
name: "stock-valuation-engine"
description: "Value a stock from its last 4 earnings, auto-picked competitors and the market backdrop: owner-FCF reverse DCF (what growth the price implies), bear/base/bull DCF, own-history trough P/FCF, peer forward P/E and P/S, beta, and a 12-week move split into market, sector and company-specific parts. Prints a fair-value range, a floor per share and a VALU_HANDOFF line the large-cap-put-overreaction (LC) skill takes as val_floor. Use whenever the user types VALU: TICKER, VALU DEEP: TICKER or VALU LC: TICKER, asks what a stock is worth, its fair or intrinsic value, whether it is cheap, expensive, undervalued or overvalued, what growth the price implies, how it stacks up against competitors or peers, whether a sell-off is company-specific or market-driven, or wants a valuation floor under a put strike. Not for clinical-stage biotech (use biotech-options-master-engine); banks and insurers get a P/E-only read."
---

# Stock Valuation Engine (VALU v1)

Price is what you pay; owner cash flow is what you get. Value the stock on OCF − CapEx − SBC (never adjusted EPS alone), test the price from four directions (reverse DCF, forward DCF, its own history, its peers), then say how much of the recent move is the company and how much is the market.

Works alone (**VALU: TICKER**) or as the floor supplier for LC (**VALU LC: TICKER**, or when an LC underwrite's floor check hinges on valuation). It never sizes or recommends a trade; LC does that.

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
| Peers, FY end, adj EPS by quarter, F1/F2 estimates, next ER | Zacks `get_zacks_metrics` (one ticker) | `Top Peers` table = the peer set · `lst_com_fy` = `fy_end` · EPS Estimates table: the (A) cells, oldest→newest → `eps_adj_q` (usually 7) · ANNUAL (E) of the current and next FY = `eps_f1` / `eps_f2` |
| EPS beat/miss, last 4 | Robinhood `get_earnings_results` | rows with `eps.actual` → `surprises: [{est, act}]`, oldest→newest |
| Peer multiples, shares, beta, market move | Zacks `compare_stocks` [TICKER + 4 peers] (default section) | per peer: `pe.pe_f1` → `pe_f1`, `price.ratio.to_sales` → `ps`, `pe.peg_ratio` → `peg`, `price.percent_chg.4_week` / `12_week` → `chg4w` / `chg12w` · ticker column: `issue_attributes.shares_outstanding` → `shares`, `issue_attributes.beta` → `beta`, `pe.peg_ratio` → `peg`, `percent_chg.4_week` / `12_week` → `t_chg4w` / `t_chg12w`, `percent_chg.4w_sp500` / `12w_sp500` → `t_rel4w` / `t_rel12w` (S&P-relative; the calculator backs out the S&P move), `price.previous_day.close` → `zacks_px` (the close those % changes are measured to; the calculator re-marks the stock's leg to live spot) |
| Quarterly cash flow | Zacks `get_cash_flow` [TICKER] `period: "Q"`, `periods: 5` | **Year-to-date figures** → pass as-is in `cf_q` with `cf_mode: "ytd"`; the calculator de-cumulates and builds TTM |
| Annual cash flow (history) | Zacks `get_cash_flow` [TICKER] `period: "A"`, `periods: 5` | → `annual: [{end, ocf, capex}]` |
| Quarterly P&L | Zacks `get_company_snapshot` [TICKER] `period: "Q"`, `periods: 8` | → `is_q: [{end, rev, op_inc, ni, eps}]` (discrete quarters, GAAP EPS). 8 quarters give 4 sales YoY readings; the calculator uses the latest 4 for TTM |
| SBC, cash, debt | `get_sec_filing_index` (symbol, ["10-Q","10-K"], since ≈ 15 months) → one `get_sec_filing_facts` (filing_ids [latest 10-Q, latest 10-K]) with these 10 concepts: `ShareBasedCompensation`, `CashAndCashEquivalentsAtCarryingValue`, `ShortTermInvestments`, `AvailableForSaleSecuritiesDebtSecuritiesCurrent`, `LongTermDebtNoncurrent`, `LongTermDebt`, `LongTermDebtCurrent`, `DebtCurrent`, `CommercialPaper`, `DebtInstrumentCarryingAmount` | SBC TTM = FY + YTD − prior YTD (if SBC is missing, retry once with `AllocatedShareBasedCompensationExpense`). Cash = cash + current investments. Debt = noncurrent (`LongTermDebtNoncurrent`; many filers tag only `LongTermDebt` for it) + current (`DebtCurrent`, else `LongTermDebtCurrent` + CP); no leases. Cross-check against `DebtInstrumentCarryingAmount` (face value) and say so if they're > 10% apart. Use rows with no axis. **Divide raw dollars by 1e6** |
| Fiscal-year lows (history) | Robinhood `get_equity_historicals` [TICKER only] `interval: "month"`, start ≈ 5 years before the latest FY end | → `px_m: {"t":["2021-12",...], "l":[low_price...]}` (~60 bars, ~8k chars). **Never pull weekly multi-year bars or extra symbols**: bars are verbose objects, and 5y weekly × 3 symbols came back at 137k characters |
| Risk-free rate | user-typed, else 4.5% ASSUMED (LEAN) · DEEP: one `web_search_fast` "10 year treasury yield today" | the calculator labels an assumed rf |

**Peer pick (automatic):** from Zacks `Top Peers`, take the first 4 that are US-listed common stock and not the ticker itself. Skip 5-letter tickers ending in F or Y (OTC / ADR lines such as DASTY). If `compare_stocks` returns a peer with a `reason` (unresolved), drop it and carry on with the rest. Name the peers in the card.

**Financials** (banks, brokers, insurers): OCF is distorted by lending and trading flows. Pass `"financial": true` and skip the cash-flow calls; the calculator gives a peer P/E read only and no floor.

## Workflow

**LEAN (10 calls, 2 turns):**
1. **Turn 1 (parallel, 4):** `get_equity_quotes` · `get_zacks_metrics` · `get_earnings_results` · `get_sec_filing_index`.
2. **Turn 2 (parallel, 6):** `compare_stocks` (ticker + 4 picked peers) · `get_cash_flow` Q5 · `get_cash_flow` A5 · `get_company_snapshot` Q8 · `get_sec_filing_facts` · `get_equity_historicals` monthly 5y (ticker only).
3. Run `valu` → card.

**DEEP (≤ 15):** LEAN plus a risk-free web search, `compare_stocks` section `GRAT` (5-year growth estimates: sanity-check `g.base` and override it if the calculator's base differs by > 5 points, saying so), section `ERV` (estimate revisions), and, if the move is COMPANY-SPECIFIC, one `web_search_fast` "TICKER stock drop reason" to name the cause. Full write-up: `references/method.md` only if asked why.

**LC mode:** reuse LC's spot, quotes, earnings and SEC facts from this chat; call only `get_zacks_metrics`, `compare_stocks`, both `get_cash_flow`, `get_company_snapshot` and `get_equity_historicals`. Hand the result back with: *pass `val_floor` (and `val_implied_g`) into the `lc` JSON.*

## `valu` input (JSON)

```json
{"ticker":"XYZ","asof":"2026-10-23","spot":268.54,"shares":389.2,"fy_end":"2025-11-30",
 "cash":5639,"debt":6363,"sbc_ttm":2071,
 "cf_mode":"ytd","cf_q":[{"end":"2026-08-31","ocf":7646,"capex":-180},{"end":"2026-05-31","ocf":5123,"capex":-95},
   {"end":"2026-02-28","ocf":2958,"capex":-37},{"end":"2025-11-30","ocf":10031,"capex":-179},{"end":"2025-08-31","ocf":6871,"capex":-145}],
 "annual":[{"end":"2025-11-30","ocf":10031,"capex":-179},{"end":"2024-11-30","ocf":8056,"capex":-183}],
 "is_q":[{"end":"2026-08-31","rev":6760,"op_inc":2354,"ni":1827,"eps":4.62},{"end":"2026-05-31","rev":6618,"op_inc":2238,"ni":1712,"eps":4.25}],
 "eps_adj_q":[5.08,5.06,5.31,5.5,6.06,5.96,6.13],
 "surprises":[{"est":4.99,"act":5.50},{"est":5.46,"act":6.06},{"est":5.60,"act":5.96},{"est":5.84,"act":6.13}],"est_rev_4wk":0,
 "eps_f1":24.47,"eps_f2":27.7,"peg":0.73,"beta":1.42,
 "t_chg4w":5.97,"t_chg12w":-3.18,"t_rel4w":5.27,"t_rel12w":-8.68,"zacks_px":255.06,
 "px_m":{"t":["2021-12","2022-01"],"l":[538.05,480.62]},
 "peers":[{"t":"INTU","pe_f1":14.28,"ps":4.18,"peg":1.09,"chg4w":17.02,"chg12w":0.74}],
 "rf":0.045}
```
Only actual (A) cells go in `eps_adj_q`; drop (E) cells. Optional: `"sales_q"` (used only if `is_q` has fewer quarters), `"mcap"` + `"mcap_px"` instead of `shares`, `"erp"` (default 0.05), `"g":{"bear","base","bull"}` growth overrides as decimals, `"financial": true`. Money is in $ millions throughout. Missing keys print n/a / UNVERIFIED; pass what you have.

## What the calculator does (so you can explain it, not redo it)

- **Earnings:** beats out of 4, average EPS surprise, sales and adjusted-EPS YoY for each of the last 4 quarters → ACCELERATING / STEADY / DECELERATING / SHRINKING; operating-margin trend; quality = owner FCF ÷ GAAP net income, the adjusted-vs-GAAP EPS gap and SBC/OCF (LOW when conversion < 0.7x, the gap is > 40% or SBC > 25% of OCF).
- **Market:** Zacks beta; the S&P's 4- and 12-week move backed out of the S&P-relative change; the stock's 12-week move split into market-explained (β × S&P) and residual. Relative to the peer median it's checked first: ≥ 8 points apart → COMPANY-SPECIFIC (lagging or leading peers), even when the stock itself is flat. Otherwise NO MAJOR MOVE, MARKET-DRIVEN (residual within 5 points), SECTOR-WIDE (stock and peers both moved ≥ 5% the same way), or MIXED. Zacks % changes are as of its last close; with `zacks_px` the stock's leg is re-marked to live spot first. Discount rate r = rf + β × ERP, clamped 7–14%, with the +100bp sensitivity printed.
- **Valuation:** reverse DCF (the 5-year owner-FCF growth the price implies, fading to 2.5%), a bear/base/bull DCF (base g = average of F1→F2 EPS growth and TTM sales growth, clamped −5% to 20%), P/FCF at each fiscal year's lowest monthly low (trough and median; a year needs ≥ 10 monthly bars), and peer forward-P/E and P/S values.
- **Range:** floor = the lower of the bear DCF and trough P/FCF × owner FCF · fair = the median of base DCF, history-median value and peer forward-P/E value · verdict AT FLOOR (spot within ±2% of the floor: no cushion) / DEEP VALUE (more than 2% below the floor) / UNDERVALUED (< 85% of fair) / FAIRLY VALUED / RICH (> 115%) / SPECULATIVE (no owner cash) · `VALU_HANDOFF` JSON line for LC.

## Output

**Card (LEAN ≤ 350 words, one table).** Start with the `##` heading: no preamble, no turn or call narration, no "building the card" lines. Each bold line is at most 2 sentences; the reality check is at most 4. Never paste raw calculator output; the `VALU_HANDOFF` line is the one exception, printed once as code on the For LC line.
```
## TICKER — VERDICT (as of HH:MM ET, date)
| Floor | Fair | Bull | Spot | Margin of safety | Implied growth |
**Earnings (last 4):** beats x/4 · sales YoY trend · margin trend · quality
**Competitors (A, B, C, D):** fwd P/E and P/S vs peer median · who is growing faster
**Market:** β · 12w move: market-explained vs residual → COMPANY-SPECIFIC / SECTOR-WIDE / MARKET-DRIVEN
**Rates:** r and what +100bp does to fair value
**🧠 Reality check:** ≤ 4 sentences, numbers first — what growth the price really assumes, whether owner cash backs the EPS, and what would make the floor wrong.
**For LC:** val_floor $X · val_implied_g Y% · `VALU_HANDOFF {...}`
```
Mark every UNVERIFIED input. Cite the sell-off cause inline when searched ([Source – date](url)). Attribute Zacks figures to Zacks Investment Research and end with a Sources line linking each ticker: `https://www.zacks.com/stock/quote/<TICKER>?utm_source=zacks_mcp`.
