# VALU method notes (read only when asked why / tuning)

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

## Known limits
- Zacks quarterly cash flow is year-to-date; the calculator needs 5 quarterly rows to build TTM and 4 discrete quarters.
- Past net debt isn't modeled; the history multiple is P/FCF (equity basis), not EV/FCF.
- Highly cyclical names (energy, materials, autos): trough FCF years can make P/FCF meaningless; lean on the peer and bear-DCF values and say so.
- Banks and insurers: P/E only. Pre-revenue or clinical-stage names: out of scope.
