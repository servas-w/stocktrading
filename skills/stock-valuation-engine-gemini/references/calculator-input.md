# valuation.py: input and output

Run: `python3 scripts/valuation.py valu '<json>'` (inline JSON, a file path, or `-` for stdin). Standard library only.

## Input JSON
Money is in **$ millions**, shares in **millions**, prices and EPS per share. Rates as decimals (0.045) or percent (4.5). Percent changes in percentage points (−5.3 = −5.3%). Missing keys print n/a or UNVERIFIED; pass what you have.

```json
{"ticker":"XYZ","asof":"2026-10-23","spot":268.54,"shares":389.2,"fy_end":"2025-11-30",
 "cash":5639,"debt":6363,"sbc_ttm":2071,
 "cf_mode":"ytd","cf_q":[{"end":"2026-08-31","ocf":7646,"capex":-180,"da":610},{"end":"2026-05-31","ocf":5123,"capex":-95,"da":405},
   {"end":"2026-02-28","ocf":2958,"capex":-37,"da":200},{"end":"2025-11-30","ocf":10031,"capex":-179,"da":820},{"end":"2025-08-31","ocf":6871,"capex":-145,"da":612}],
 "annual":[{"end":"2025-11-30","ocf":10031,"capex":-179},{"end":"2024-11-30","ocf":8056,"capex":-183}],
 "is_q":[{"end":"2026-08-31","rev":6760,"op_inc":2354,"ni":1827,"eps":4.62,"pretax":2290,"tax":463,"int_exp":60},
   {"end":"2026-05-31","rev":6618,"op_inc":2238,"ni":1712,"eps":4.25,"pretax":2150,"tax":438,"int_exp":58}],
 "eps_adj_q":[5.08,5.06,5.31,5.5,6.06,5.96,6.13],
 "surprises":[{"est":4.99,"act":5.50},{"est":5.46,"act":6.06},{"est":5.60,"act":5.96},{"est":5.84,"act":6.13}],"est_rev_4wk":0,
 "eps_f1":24.47,"eps_f2":27.7,"peg":0.73,"beta":1.42,
 "t_chg4w":5.97,"t_chg12w":-3.18,"t_rel4w":5.27,"t_rel12w":-8.68,"zacks_px":255.06,
 "px_m":{"t":["2021-12","2022-01"],"l":[538.05,480.62]},
 "peers":[{"t":"INTU","pe_f1":14.28,"ps":4.18,"peg":1.09,"chg4w":17.02,"chg12w":0.74}],
 "rf":0.045}
```

| Key | What to put in it |
|---|---|
| `spot`, `asof` | latest trade price and its date |
| `shares` | shares outstanding, millions |
| `fy_end` | last completed fiscal year end (YYYY-MM-DD) |
| `cash` | cash + current marketable investments |
| `debt` | current + non-current debt (no leases) |
| `sbc_ttm` | stock-based compensation, trailing 4 quarters |
| `cf_q` | the last 5 quarterly cash-flow rows as filed. US 10-Q cash flows are **year-to-date**: pass them as filed with `"cf_mode":"ytd"` and the calculator de-cumulates them. If you already have single quarters, pass `"cf_mode":"discrete"`. `capex` may be negative or positive; `da` = depreciation and amortization |
| `annual` | 5 fiscal years of `{end, ocf, capex}` |
| `is_q` | 8 discrete quarters: `rev`, `op_inc`, `ni`, `eps` (diluted GAAP), `pretax`, `tax`, `int_exp` (omit `int_exp` if unknown) |
| `eps_adj_q` | up to 7 quarters of adjusted EPS actuals, oldest first (GAAP EPS if no adjusted figure exists) |
| `surprises` | last 4 quarters `{est, act}`, oldest first |
| `est_rev_4wk` | % change in the current-year EPS consensus over 4 weeks (optional) |
| `eps_f1`, `eps_f2` | consensus EPS for the current and next fiscal year |
| `beta`, `peg` | stock beta and PEG |
| `t_chg4w`, `t_chg12w` | the stock's 4- and 12-week % change |
| `t_rel4w`, `t_rel12w` | the stock's % change **relative to the S&P 500** over the same windows. If you only have the S&P's own move, compute relative = (1 + stock) ÷ (1 + S&P) − 1, in percent |
| `zacks_px` | the closing price the % changes were measured to (lets the calculator re-mark them to spot) |
| `px_m` | monthly lows: `t` = ["YYYY-MM", ...], `l` = [low, ...], about 60 months |
| `peers` | 4 peers: `t`, `pe_f1`, `ps`, `peg`, `chg4w`, `chg12w` |
| `rf` | 10-year Treasury yield; omit and 4.5% is used and labelled ASSUMED |

Optional: `"ppe_net"` (net PP&E) with `"ppe_life"` (years, default 10) for a stricter maintenance-capex estimate, `"erp"` (default 0.05), `"tax_rate"` (used when `tax` is missing), `"g":{"bear","base","bull"}` growth overrides as decimals, `"mcap"` + `"mcap_px"` instead of `shares`, `"financial": true` for banks and insurers (peer P/E only, no floor).

## Output lines (what each one means)
- **Earnings:** beats out of 4, average surprise, sales and adjusted-EPS YoY for the last 4 quarters with the trend label, operating margins.
- **Core earnings:** operating income, interest, pre-tax, non-operating ex-interest as a % of operating income, NON-OP DISTORTION or clean, core TTM EPS vs GAAP EPS, and (when flagged) forward core EPS with how it was built.
- **Owner cash:** OCF − CapEx − SBC = owner FCF, how TTM was built, SBC/OCF, owner FCF ÷ GAAP net income, and the de-cumulated quarters.
- **Market:** beta, 12-week stock / S&P / peer-median moves, market-explained vs residual, the classification.
- **Rates / Reverse DCF / DCF/sh:** discount rate, +100bp sensitivity, implied growth, bear/base/bull values.
- **Capex-normalized** (only in a capex surge or with negative owner FCF): CapEx ÷ D&A, the maintenance-capex basis, normalized owner FCF, EPV soft floor, implied normalized growth.
- **Own history, Peers:** trough and median P/FCF (and the median applied to normalized FCF in a surge), peer P/E value (forward core EPS + net cash if flagged) with its leave-one-out range, P/S value.
- **Range, VERDICT, VALU_HANDOFF:** floor, fair, bull, margin of safety, the verdict, and the one-line JSON for LC. Copy these into the card; never paste the raw output.
