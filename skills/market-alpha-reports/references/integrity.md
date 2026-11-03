# Integrity gate (run at step 6, before saving)

These checks came out of a review of the Oct 7 to Nov 2 reports. In that period, reports for the same Friday close disagreed by 20–75%:
- AAPL $268 vs $337
- MRNA $222 vs $54
- KOD $99 vs $22.5
- ••••6081 cash $44K vs $304K
- Brent $116.70 vs $113.10

The Nov 2 pre-market also missed ACRS (20% NAV), META (21% NAV) and 7 ITM Nov-20 lines. Each check below targets one of those failures.

## Check table: print it at the end of the Works Cited, one line per row
| # | Check | Pass condition | On fail |
|---|---|---|---|
| 1 | Book reconcile | Feed NAV vs live NAV within 2%; short-line counts equal | Use the live numbers; name the difference in Section 7 |
| 2 | Trigger completeness | Every live short line is checked against the ITM ≤ 21 DTE, ≤ 7% cushion, Δ ≤ −0.30 and ≥ 80% captured gates | Add the missing lines to Book Triggers and the Bottom Line |
| 3 | Concentration method | Every % NAV row is labelled `naked` / `spread width` / `net of hedge` | Recompute with the SKILL.md method |
| 4 | Published closes | Prior-close values match the first AH/WKND report for that session | Restore the published value; add `(source now shows X)` |
| 5 | Continuity | No unexplained move > 5% (stock) or > 2% (index/FX/commodity/BTC) versus the prior report | Re-pull from Robinhood, then mark `UNVERIFIED` and drop it from the Bottom Line and orders |
| 6 | Cross-section consistency | The same ticker has the same price, share count and strike in every section of this report | Fix it to the Section 7 live value |
| 7 | Source honesty | `✓✓` only where two sources agree within tolerance; every link shows the number it backs | Downgrade to `✓` or `N/A`; replace the link |
| 8 | Calendar | Every event date has a source ≤ 7 days old; no conflicting dates | `date unconfirmed — check before expiry` |
| 9 | Staleness | Gamma, Greeks, stress and IVR are refreshed this run or tagged `STALE (as of …)` | Add the tag |
| 10 | Bands | SPX uses VIX1D/VIX; NDX uses VXN; inputs and reference spot shown | Recompute |
| 11 | Arithmetic | Spot checks: % changes, cushions, collateral = strike × 100 × qty, % NAV | Recompute with `desk_math.py` or inline |
| 12 | Length | Within the mode's word budget (feed excluded) | Trim tables, then Reads |

Print it compactly, for example: `Integrity: 1✓ 2✓ 3✓ 4✓ 5✓(MRNA re-pulled) 6✓ 7✓ 8△(APP earnings unconfirmed) 9△(GEX STALE) 10✓ 11✓ 12✓`.

## Tolerances for ✓✓
Index/ETF ±0.1% · single stock ±0.5% · yields ±2 bp · FX ±0.1% · commodities ±0.5% · BTC ±0.5% · VIX ±0.2 pt.

## Source ladder (best first)
1. Robinhood connector (held names, options, quotes, fundamentals, SEC filings)
2. Primary releases: company IR, SEC EDGAR, BLS/BEA/Census, ISM, Treasury, CBOE
3. Market-data connectors (Twelve Data, Alpha Vantage, IBKR) for benchmarks, FX, commodities
4. Attributed news (Reuters, AP, CNBC, Bloomberg via a syndicator)
5. Aggregators and blogs: usable only as `C excerpt-only`, never as the sole source for a Bottom Line number

## What never ships
- A price, date or position with no source.
- A figure tagged `UNVERIFIED` inside the Bottom Line, Key Judgments or an order line.
- A Scorecard HIT based on a pre-market mark.
- A doc that is empty, a test, or a raw-markdown save.
