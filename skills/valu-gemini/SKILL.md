---
name: stock-valuation-engine
description: VALU for Gemini Spark. Values a stock on owner cash flow (operating cash flow minus capex minus stock-based pay, never adjusted EPS alone), tests the price four ways (reverse DCF, bear/base/bull DCF, its own P/FCF history, peer multiples), and says how much of the recent move is the company versus the market and its sector. Ends in a floor / fair / bull range and a verdict (AT FLOOR, DEEP VALUE, UNDERVALUED, FAIRLY VALUED, RICH, SPECULATIVE). Use when Wilson types VALU: TICKER or VALU DEEP: TICKER, or asks what a stock is worth, whether it's cheap or expensive, what growth the price implies, or for a valuation floor before selling puts. It never sizes or recommends a trade.
---

# Stock Valuation Engine (VALU, Gemini Spark edition)

Price is what you pay; owner cash flow is what you get. The method:
1. Value the stock on **owner FCF = operating cash flow − capex − stock-based compensation**.
2. Test the price from four directions: reverse DCF, forward DCF, its own history and its peers.
3. Say how much of the recent move is the company and how much is the market.

**Triggers**:
- `VALU: TICKER`: lean run.
- `VALU DEEP: TICKER`: adds the live risk-free rate, the analysts' 5-year growth check, and the cause of a company-specific move.
- `VALU: TICKER peers A,B,C,D`: overrides the peer set.

## Rules (override everything below)

1. **Numbers come from pages you opened this run.** Stamp them "as of" and write each with its source. A missing number is `UNVERIFIED`, never estimated or remembered.
2. **The calculator does the math.** Run `scripts/valuation.py`:
   - in a Python sandbox: `import sys; sys.path.insert(0, 'scripts'); import valuation; valuation.valu({...})`
   - from a shell: `python3 scripts/valuation.py valu '<json>'`
   
   Copy its numbers; don't recompute them in prose. The JSON below is its full interface.
3. **If Python can't run**: give a **reduced card**, not a hand-built full one.
   - Compute owner FCF (TTM operating cash flow − capex − SBC) and EV (spot × shares + debt − cash), showing every input.
   - Use `references/dcf_table.md` for the reverse DCF and the bear/base DCF.
   - Do the peer forward-P/E value as the peer median × the matching EPS (next-year P/E × next-year EPS).
   - Write `n/a (no calculator)` for own-history, the market-move label, the earnings trend and quality.
   - Floor = bear DCF only. Fair = the median of base DCF and peer value. Use the same verdict rules.
   - Label the card `approx. (no calculator)`.
4. **Language**: valuation is an estimate with stated assumptions, not a price target or advice. Say "the model implies", not "the stock will".
5. **Budget**: LEAN opens about 13 pages, DEEP about 17. At the limit, stop and mark the gaps `UNVERIFIED`.
6. **Out of scope**: pre-revenue and clinical-stage biotechs (no owner cash; say so and stop).
   - For banks, brokers and insurers, set `"financial": true`. That gives a peer P/E read only, with no floor.

## Data sources (fixed, so runs compare)

Money goes in **$ millions** and shares in **millions**. **Pass numbers and dates exactly as the page prints them**: `"10,031"`, `"(85)"`, `"389.20M"`, `"1.2B"`, `"-3.18%"`, `"Aug 31, 2026"`. The calculator parses them, and K/M/B/T suffixes convert to millions. Unreadable rows are listed under `INPUT WARNINGS` and never silently skipped. **Any warning means fix that input and rerun before writing the card.**

| Need | Page | Calculator key |
|---|---|---|
| Spot, shares, beta, PEG, % moves | **Finviz** quote page `finviz.com/quote.ashx?t=TICKER` | `spot` = Price, `shares` = Shs Outstand, `beta` = Beta, `peg` = PEG, `t_chg4w` = Perf Month, `t_chg12w` = Perf Quarter |
| S&P move | **Finviz** `finviz.com/quote.ashx?t=SPY` | `s_chg4w` = Perf Month, `s_chg12w` = Perf Quarter |
| Peers | Wilson's list if given. Otherwise the peers listed on the Finviz quote page (the "Peers" link). | Take the first 4 that pass the **peer test**: US-listed common stock, not the ticker, not a 5-letter ticker ending in F or Y (OTC/ADR), same Finviz industry, market cap between 0.2× and 5× the ticker's, positive Forward P/E. If fewer than 3 pass, add the largest same-industry names that pass, and say `peers auto-picked, thin set`. The card always says whether peers were Wilson's or auto-picked. |
| Peer multiples and moves | **Finviz** quote page for each peer | `peers: [{t, pe_f2: Forward P/E, ps: P/S, peg: PEG, chg4w: Perf Month, chg12w: Perf Quarter}]`. Finviz's Forward P/E is on **next** fiscal year's EPS, so pass it as `pe_f2`; the calculator then compares it with `eps_f2`. |
| Quarterly cash flow | **stockanalysis.com** `/stocks/TICKER/financials/cash-flow-statement/?p=quarterly` | `cf_q: [{end, ocf: Operating Cash Flow, capex: Capital Expenditures}]` (latest 5 quarters), `cf_mode: "discrete"`. **SBC TTM** = the sum of the last 4 quarters of Stock-Based Compensation → `sbc_ttm` |
| Annual cash flow | same page, annual view | `annual: [{end, ocf, capex}]` for 5 fiscal years. `fy_end` = the latest fiscal year's period-end date |
| Quarterly P&L | **stockanalysis.com** `/financials/?p=quarterly` | `is_q: [{end, rev: Revenue, op_inc: Operating Income, ni: Net Income, eps: EPS (Diluted)}]` for 8 quarters |
| Cash and debt | **stockanalysis.com** `/financials/balance-sheet/?p=quarterly`, latest quarter | `cash` = Cash & Equivalents + Short-Term Investments. `debt` = Short-Term Debt + Current Portion of Long-Term Debt + Long-Term Debt. **Exclude lease liabilities.** |
| Estimates and surprises | **Yahoo Finance** `finance.yahoo.com/quote/TICKER/analysis` | `eps_f1` / `eps_f2` = Earnings Estimate Avg for Current Year / Next Year. `surprises: [{est, act}]` from Earnings History, oldest first. `eps_adj_q` = those 4 actual EPS, oldest first. `est_rev_4wk` = (EPS Trend Current Year "Current Estimate" ÷ "30 Days Ago" − 1) × 100 |
| Monthly lows, 5 years | **Yahoo Finance** `/quote/TICKER/history/?frequency=1mo`, covering about 5 years before the latest fiscal year end | `px_m: {"t": ["Oct 1, 2021", ...], "l": [Low, ...]}`. Pass the Date and Low columns as printed. **Skip dividend and split rows**, which have no Low. |
| Risk-free rate | LEAN: 4.5%, labelled ASSUMED. DEEP: a search for "10 year treasury yield today", read from CNBC or the Treasury. | `rf` |

**Fallbacks**:
- If **Finviz** blocks the browser, use Yahoo Finance's key-statistics page for shares, beta, forward P/E, P/S and PEG. Then the 4- and 12-week moves come from the Yahoo history pages, so say so. Yahoo doesn't document which year its Forward P/E uses: pass it as `pe_f2` and write `peer P/E basis unverified` on the competitors line.
- If **stockanalysis.com** fails, use Yahoo's quarterly financials pages. **They print figures in thousands**: pass them as printed and add `"statement_units": "thousands"`, and the calculator converts cash, debt, SBC and every statement row to millions (shares and EPS are left alone). Yahoo's total debt includes leases, so add up the debt lines without leases, or mark debt `UNVERIFIED`.
- If **Yahoo's analysis page** fails, use Finviz's `EPS next Y` for `eps_f2`, and mark `eps_f1`, the surprises and adjusted EPS `UNVERIFIED`.
- **Adjusted EPS year-over-year is always `n/a` here.** Yahoo shows only 4 actual quarters. Say `adj EPS YoY n/a (4 quarters on Yahoo)` on the earnings line; the sales trend carries it.

## Workflow

**LEAN (about 13 pages)**:
1. Finviz: the ticker and SPY. Pick the peers.
2. Finviz: 4 peers.
3. stockanalysis.com: quarterly cash flow, annual cash flow, quarterly income statement, quarterly balance sheet.
4. Yahoo: analysis page and monthly history.
5. Build the JSON and run `valu`, then write the card.

**DEEP (about 17 pages)**: LEAN, plus:
- the live 10-year yield
- Yahoo's Growth Estimates "Next 5 Years" for the ticker, or Finviz's `EPS next 5Y` if Yahoo no longer shows it, as a sanity check on `g.base`. If the calculator's base differs by more than 5 points, override with `"g": {"base": ...}` and say so.
- if the move is COMPANY-SPECIFIC, one search for "TICKER stock drop reason" to name the cause, cited inline

Read `references/method.md` only if Wilson asks why.

## `valu` input (JSON)

```json
{"ticker":"XYZ","asof":"2026-10-30","spot":"$268.54","shares":"389.20M","fy_end":"2025-11-30",
 "cash":5639,"debt":6363,"sbc_ttm":2071,
 "cf_mode":"discrete","cf_q":[{"end":"Aug 31, 2026","ocf":"2,523","capex":"(85)"},{"end":"2026-05-31","ocf":2165,"capex":-58},
   {"end":"2026-02-28","ocf":2958,"capex":-37},{"end":"2025-11-30","ocf":3160,"capex":-34},{"end":"2025-08-31","ocf":2187,"capex":-48}],
 "annual":[{"end":"2025-11-30","ocf":10031,"capex":-179},{"end":"2024-11-30","ocf":8056,"capex":-183}],
 "is_q":[{"end":"2026-08-31","rev":6760,"op_inc":2354,"ni":1827,"eps":4.62},{"end":"2026-05-31","rev":6618,"op_inc":2238,"ni":1712,"eps":4.25}],
 "eps_adj_q":[5.50,6.06,5.96,6.13],
 "surprises":[{"est":4.99,"act":5.50},{"est":5.46,"act":6.06},{"est":5.60,"act":5.96},{"est":5.84,"act":6.13}],"est_rev_4wk":0,
 "eps_f1":24.47,"eps_f2":27.7,"peg":0.73,"beta":1.42,
 "t_chg4w":5.97,"t_chg12w":-3.18,"s_chg4w":0.7,"s_chg12w":6.0,
 "px_m":{"t":["2021-12","2022-01"],"l":[538.05,480.62]},
 "peers":[{"t":"INTU","pe_f2":"12.61","ps":"4.18","peg":"1.09","chg4w":"17.02%","chg12w":"0.74%"}],
 "rf":0.045}
```

The values above are illustrative only.
- **Optional keys**: `"g": {"bear","base","bull"}` (decimals), `"erp"` (default 0.05), `"financial": true`, `"statement_units": "thousands"` (Yahoo financials), `pe_f1` instead of `pe_f2` if the peer P/E is on the current fiscal year, `"ref_px"` (if spot is newer than the close the % moves were measured to), `"mcap"` with `"mcap_px"` instead of `shares`.
- **Missing keys** print `n/a` / `UNVERIFIED`. Pass what you have.

## What the calculator does (so you can explain it, not redo it)

- **Earnings**:
  - beats out of 4 and the average EPS surprise
  - sales YoY for each of the last 4 quarters → ACCELERATING / STEADY / DECELERATING / SHRINKING
  - the operating-margin trend
  - quality: owner FCF ÷ GAAP net income, the adjusted-vs-GAAP EPS gap, and SBC as a share of operating cash flow. It's LOW when conversion is under 0.7x, the gap is over 40%, or SBC is over 25% of operating cash flow.
- **Market**:
  - the stock's 12-week move split into the part beta × S&P explains and the residual
  - first, the stock vs the peer median: 8 points or more apart → COMPANY-SPECIFIC
  - otherwise NO MAJOR MOVE, MARKET-DRIVEN, SECTOR-WIDE or MIXED
  - discount rate r = rf + β × 5%, clamped to 7–14%
- **Valuation**:
  - **Reverse DCF**: the 5-year owner-FCF growth the price implies, fading to 2.5%.
  - **Bear/base/bull DCF**: base g = the average of next-year EPS growth and TTM sales growth, clamped to −5% to 20%.
  - **Own history**: P/FCF at each fiscal year's lowest monthly low, giving a trough and a median.
  - **Peers**: forward P/E and P/S values.
- **Range**:
  - **Floor**: the lower of the bear DCF and trough P/FCF × owner FCF.
  - **Fair**: the median of the base DCF, the history-median value and the peer forward-P/E value.
  - **Verdict rules**:
    - AT FLOOR: spot within ±2% of the floor
    - DEEP VALUE: spot more than 2% below the floor
    - UNDERVALUED: spot under 85% of fair
    - FAIRLY VALUED
    - RICH: spot over 115% of fair
    - SPECULATIVE: no owner cash
  - It also prints a `VALU_HANDOFF` line for Claude's LC skill.

## Output

**Card**:
- 350 words or fewer, with one table.
- Start with the heading: no preamble, no narration of pages opened.
- Each bold line is at most 2 sentences; the reality check is at most 4.
- Never paste raw calculator output, except the `VALU_HANDOFF` line once.

```
## TICKER — VERDICT (as of HH:MM ET, date)
| Floor | Fair | Bull | Spot | Margin of safety | Implied growth |
**Earnings (last 4):** beats x/4 · sales YoY trend · margin trend · quality (adj EPS YoY n/a)
**Competitors (A, B, C, D):** fwd P/E and P/S vs peer median · who is growing faster
**Market:** β · 12w move: market-explained vs residual → COMPANY-SPECIFIC / SECTOR-WIDE / MARKET-DRIVEN
**Rates:** r and what +100bp does to fair value
**🧠 Reality check:** ≤ 4 sentences, numbers first: what growth the price really assumes, whether owner cash backs the EPS, and what would make the floor wrong.
**For LC (Claude):** val_floor $X · val_implied_g Y% · `VALU_HANDOFF {...}`
```

- Mark every `UNVERIFIED` input. If `INPUT WARNINGS` remain after a rerun, list them under the table.
- `INCOMPLETE` means owner-FCF inputs were missing. It's a data gap, not a verdict on the stock.
- Cite the cause of a sell-off inline when searched: [Source – date](url).
- End with a **Sources** line linking every page used.
