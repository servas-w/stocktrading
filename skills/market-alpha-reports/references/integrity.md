# Integrity gate (run before saving)

These checks came out of a review of the Oct 7 to Nov 2 reports. In that period, reports for the same Friday close disagreed by 20–75%:
- AAPL $268 vs $337
- MRNA $222 vs $54
- KOD $99 vs $22.5
- ••••6081 cash $44K vs $304K
- Brent $116.70 vs $113.10

The Nov 2 pre-market also built its triggers from a highlight list instead of the full book. Each check targets one of those failures, and each one asks for something visible in the doc. That way the check can be verified by reading the report, not just by trusting the ✓.

| # | Check | Pass condition (visible in the doc) | On fail |
|---|---|---|---|
| 1 | Book feed | The `Book feed:` line is present with source, time, NAV and line counts. The feed age suits the mode. | Put `STALE FEED (<age>)` first in the Bottom Line |
| 2 | Trigger scan | `Trigger scan: N lines checked · K hits`, where N = the short option lines in the Book feed line | Rescan; add the missing hits |
| 3 | Concentration | R5 % NAV uses the official gross test (puts + shares, long puts not netted); the net-of-hedge column is labelled as information only | Recompute with `core-rules.md` §3 |
| 4 | Published closes | Every "prior close" matches the latest AH/WKND `PUBLISHED CLOSES:` | Restore it; add `(source now shows X)` |
| 5 | Continuity | Every unexplained move is tagged `UNVERIFIED`. Benchmarks are left out of Key levels; held names stay in with `check broker before acting`. | Tag it and move it |
| 6 | Consistency | List every number in the Bottom Line and Key Judgments next to the section value it came from (bands, % NAV, counts, closes); each pair must match. A ticker has the same price, strike and quantity in every section. No claim about earlier reports without evidence. | Fix it to the section value; drop the claim |
| 7 | Provenance | Every Bottom Line and Key Judgment number has a Source Notes line with a link and the page time | Add the line, or remove the number |
| 8 | ✓✓ honesty | ✓✓ only where two independent pages agree within tolerance | Downgrade to ✓ or N/A |
| 9 | Calendar | Every event date has an acceptable source (`core-rules.md` §5) | `date unconfirmed — check before expiry` |
| 10 | Staleness | Gamma, Greeks, stress and IVR are refreshed this run or tagged `STALE (as of …)` | Add the tag |
| 11 | Arithmetic | Bands show their inputs. Spot-check 3 cushions, 3 % NAV rows and the ROC figures with code execution | Recompute |
| 12 | Handoff, REPEAT and format | The Handoff is in a code block with one item per line and has FEED / ACTIONS / TRIGGERS (and PUBLISHED CLOSES in AH/WKND). `REPEAT` appears only on count ≥ 3, repeats lead the Bottom Line, and `Repeat triggers: n` equals the count of open count-≥-3 lines in the Handoff. No markdown inside table cells. The header shows the runner. Within the word cap. | Fix the label, order or count; complete the Handoff; trim |

Print it compactly at the end of the Works Cited, naming the item for anything that isn't a clean ✓. For example:
`Integrity: 1✓ 2✓(53/53) 3✓ 4✓ 5△(MGNX unverified) 6✓ 7✓ 8✓ 9△(APP date unconfirmed) 10△(GEX STALE) 11✓ 12✓`

## Source ladder (best first)
1. The book source and quote source named in the platform `SKILL.md`
2. Primary releases: company IR, SEC EDGAR, BLS/BEA/Census, ISM, Treasury, CBOE, exchanges
3. Market-data pages with a visible timestamp (benchmarks, FX, commodities, crypto)
4. Attributed news (Reuters, AP, CNBC, Bloomberg via a syndicator)
5. Aggregators and blogs: only as `C excerpt-only`, never the sole source for a Bottom Line number

## What never ships
- A price, date or position with no source.
- An `UNVERIFIED` price used as an order limit, or an unverified benchmark in Key levels.
- A Scorecard HIT based on a pre-market or after-hours mark.
- A doc that is empty, a duplicate, a test, or a raw-markdown save.
