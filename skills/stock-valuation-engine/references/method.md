# VALU v2 method notes (read only when asked why / tuning)

## Why owner FCF
Adjusted EPS adds back stock-based pay, which is a real cost paid in dilution. Owner FCF = OCF − CapEx − SBC is the cash a shareholder could take out without shrinking the business or their stake. Every DCF here discounts owner FCF, which matches LC's forensics.

## Why a reverse DCF leads
A forward DCF is only as good as its growth guess. The reverse DCF asks the market's question instead: what 5-year growth makes today's EV fair at this discount rate? Compare that figure with the last 4 quarters' sales and EPS trend:
- implied growth well below the recent trend → the price assumes the slowdown continues (often LC's sweet spot)
- implied growth above the trend → the price needs acceleration; a floor built on it is thin

## The DCF shape
- Years 1–5: g. Years 6–10: linear fade from g to 2.5%. Then a Gordon terminal at 2.5%.
- r = rf + β × ERP (default ERP 5%), clamped to 7–14%, so a low-beta name is never discounted below 7%.
- Bear = base g − max(5 points, half of |base|), at r + 1%. Bull = base g + max(3 points, half of |base|), capped at 30%, at r − 0.5%.

## Own-history trough
For each of the last 5 fiscal years: the lowest monthly low in the 12 monthly bars ending in the FY-end month, times that year's share count, divided by that year's FCF (OCF − CapEx). The minimum is the trough multiple. When annual NI/EPS aren't passed, today's share count is used. Buybacks then make past multiples look lower, which is conservative for a floor. The trough floor applies that FCF multiple to today's smaller owner FCF, which is conservative again.

## Move classification (12 weeks)
The S&P move comes from Zacks' S&P-relative change: S&P = (1 + stock) / (1 + relative) − 1. Checked in this order:
- stock ≥ 8 points from the peer median → COMPANY-SPECIFIC (lagging or leading). This is checked first because a flat stock in a rising tape is still lagging. Go find the cause; LC's sell-off triage decides transient vs structural
- |move| < 5% and residual after β × S&P within 5 points → NO MAJOR MOVE
- residual within 5 points → MARKET-DRIVEN: usually the most tradeable for put sellers
- stock and peer median both moved ≥ 5% in the same direction → SECTOR-WIDE
- otherwise MIXED (behind or ahead of the market, but within 8 points of peers)

Zacks % changes are measured to its last close. When `zacks_px` is passed, the stock's 4w and 12w moves are re-marked by spot ÷ zacks_px before classifying. The S&P leg is backed out from the unadjusted figures and left alone; peers aren't re-marked, a one-day mismatch.

Second ADBE run lesson: Zacks closed at $255.06 and spot was $268.52 (+5.3%). Re-marked, the 12-week move went from −3.2% to +1.9%, and the gap to peers from −9.2 to −4.0 points. That's MIXED, not COMPANY-SPECIFIC.

Dry-run lesson (ADBE, Oct 2026): the stock was −3.2% over 12 weeks while the S&P was +6.0% and peers +6.0%. The first version called that NO MAJOR MOVE; it was really a 9-point company-specific lag.

## v2: core earnings (why GAAP EPS is not used when non-op items are large)
GAAP pre-tax income includes revaluations of equity stakes and investment gains. When those exceed 15% of operating income over 4 quarters, both trailing EPS and consensus F1 EPS are inflated (or deflated) by marks that will not recur. Core EPS = (operating income − interest expense) × (1 − tax) ÷ shares. Interest expense stays in because it recurs: stripping it would make every leveraged company look cheaper (a test case with $200M/qtr interest went from $6.00 to $7.90 core EPS and +32% fair value before this fix). With interest unknown, only net *gains* are flagged.

**Forward core EPS (matches the peers' forward P/E).** Peer `pe_f1` is price ÷ current-fiscal-year EPS, so it has to be applied to a current-fiscal-year core EPS, not a trailing one:
- (a) **preferred:** consensus F1 minus the one-off marks already booked in this fiscal year (pre-tax − (operating income − interest) for each quarter after the last FY end), after tax. Analysts don't forecast marks, so what's left is the core forecast. Used when it lands within 0.7–1.6× core TTM EPS.
- (b) **fallback:** core TTM EPS × (1 + TTM operating-income growth, clamped −20%/+30%)^(months left to FY end ÷ 12).
- (c) core TTM EPS when neither is available (conservative, labelled).
The first v2 draft used core TTM EPS and called the gap "about a year of growth". That overstated it: the gap is only the months left in the fiscal year (3 for GOOG in November), so the fix moves GOOG's core EPS from $10.52 to $11.26 (a) or $11.15 (b), not to ~$13.

**Net cash on the core route.** Core EPS excludes interest income, and the P/E route values equity directly, so positive net cash per share is added back to the peer-P/E value on the core route. Net debt is not subtracted, because interest expense is already inside core earnings. On GOOG this adds $11.36/sh. It also counts the SpaceX stake once, at its balance-sheet mark, instead of through the gains.

**Leave-one-peer-out range.** With 3+ peers the calculator reprints the peer-P/E value dropping each peer in turn. A wide range means one peer drives the answer (e.g. ORCL after a −54% year); say so.

EPS F1→F2 growth is dropped from base g because it compares a marked year with an unmarked one.

GOOG lesson (Nov 2026): $130.7B of TTM non-operating gains (mostly the SpaceX mark) against $157.0B of operating income. v1 applied the peer P/E of 19.8x to F1 EPS of $19.80 (marks included) and got $393/sh, which put fair value at $306.53. With forward core EPS of $11.26 plus $11.36 of net cash, the peer value is $234.68 (range $225.73–$243.64 dropping one peer at a time). Fair value is $220.33.

## v2: SBC is subtracted once
OCF adds SBC back, so owner FCF subtracts it. Operating income already expenses SBC; subtracting it again from NOPAT counts it twice. (A Gemini VALU run did this and called GOOG "33.7–35x core owner NOPAT"; the correct figure was 25.7–26.8x.)

## v2: capex-normalized lens and the soft floor
A hyperscaler-style build-out can push CapEx well above D&A and owner FCF below zero, even when the operating business is strong. v1 then had nothing to discount and returned SPECULATIVE. v2 adds Greenwald's earnings-power view:
- maintenance capex = the largest of TTM D&A, run-rate D&A (latest quarter × 4) and, when `ppe_net` is passed, net PP&E ÷ `ppe_life` (default 10 years). Everything above it is growth capex. Run-rate D&A matters in a build-out: depreciation lags capex, so TTM D&A understates what standing still will cost (GOOG: $33.5B run-rate vs $28.0B TTM). Net PP&E ÷ life is the stricter test: what depreciation will be once today's asset base is in service
- normalized owner FCF = OCF − SBC − maintenance capex
- EPV = normalized owner FCF ÷ r + net cash: the value with zero growth. Every dollar of price above EPV is paid for growth
- the reverse DCF on normalized FCF says how much growth that is
EPV is a **soft floor**: it is not the bear case of a cash flow that exists today, so it never becomes `val_floor` and LC never anchors a strike on it. Growth must be paid for: a forward DCF on normalized FCF at the sales growth rate would count growth without paying for its capex, so v2 does not run one.

**Own history on normalized FCF.** The history P/FCF multiples were struck in years of normal capex, so in a capex surge they are applied to normalized FCF (OCF − maintenance capex) instead of today's depressed FCF. That gives a third, independent leg:
- owner FCF ≤ 0 (CAPEX-CYCLE): fair = median(peer P/E value, history × normalized FCF, P/S value). P/S ignores margins (AMZN ~10%, GOOG ~33%), so it is never the only comparable; in a median of three it can't pull the answer outside the other two.
- owner FCF > 0 but squeezed (capex > 2× D&A, e.g. META or MSFT mid build-out): the floor still uses the real owner FCF (conservative), but fair = median(base DCF, history × normalized FCF, peer P/E value), and the normalized line and soft floor print alongside.

## v2: no hand-typed FCF paths
A model that writes "−$50B → +$7B → +$74B → +$131B → +$178B" has decided the answer in the forecast. About 90% of the resulting value sits in terminal value, and each ±$20B on the last year moves value by about ±$18/sh (GOOG). VALU keeps one DCF shape for every stock and lets only g and r move, by rule.

## v2: one asset base
Net cash = cash + current marketable investments − debt. Long-term and private stakes (e.g. non-marketable equity) are not added in any scenario. A model that adds them in one scenario and not another, then blends the two, is averaging two different companies.

## Known limits
- Zacks quarterly cash flow is year-to-date; the calculator needs 5 quarterly rows to build TTM and 4 discrete quarters.
- Past net debt isn't modeled; the history multiple is P/FCF (equity basis), not EV/FCF.
- Highly cyclical names (energy, materials, autos): trough FCF years can make P/FCF meaningless; lean on the peer and bear-DCF values and say so.
- Banks and insurers: P/E only. Pre-revenue or clinical-stage names: out of scope.
- Maintenance capex is still an estimate: run-rate D&A lags in a fast build-out, and net PP&E ÷ life depends on the life you pick (servers ~6 years, buildings 25+, land never). Pass `ppe_net` and a realistic `ppe_life` when the soft floor matters.
- Consensus F1 minus booked marks assumes analysts forecast no further marks for the rest of the year. If F1 drops by more than the marks booked (revisions), method (b) is the cross-check.
