# Integrity gate (run before saving)

Why these checks exist:
- **Oct 7 – Nov 2:** reports for the same Friday close disagreed by 20–75% (AAPL $268 vs $337, MRNA $222 vs $54, cash $44K vs $304K).
- **Nov 3 AH, Nov 4 PRE, Nov 4 MID:** each described positions that were not in the WarRoom PDF it cited (CAPR $35/$32/$30 puts at "$29", CMPX $7.5 puts, NVAX, ABEO, REPL/ETNB/KALV puts, MRNA at $25). Each still printed ✓ on every check.

So every check asks for something a reader can verify in the doc, not just a ✓.

| # | Check | Pass condition (visible in the doc) | On fail |
|---|---|---|---|
| 1 | Feed & check figure | Header and A1 show the feed name, run time and `CHECK:` line; the short option lines listed in A1 equal N | `STALE FEED` / recount; never invent lines to match |
| 2 | Feed-row rule | Every Section 3 order has a feed-row cell copied from the book source; every position named in Sections 1–2 exists in the book source | Remove the item |
| 3 | Trigger scan | `Trigger scan: N lines checked (Q quoted · U unquoted) · K hits` with N = CHECK's short option lines + stock lines; unquoted lines named; no order staged on a `strike inferred` row | Rescan; drop the order |
| 4 | Concentration | R5 uses the max-loss method; each row labelled `naked` / `spread width` / `hedged`, collateral column shown | Recompute (`core-rules.md` §3) |
| 5 | Published closes | Every prior close matches the latest `PUBLISHED CLOSES` | Restore; add `(source now shows X)` |
| 6 | Continuity | Unexplained moves tagged `UNVERIFIED` (benchmarks out of Section 1; held names in, with `check broker before acting`) | Tag and move |
| 7 | Consistency & claims | Each Section 1 number equals its source section's number; same ticker = same price/strike/qty everywhere; no claim about earlier reports without Handoff evidence | Fix to the source section; drop the claim |
| 8 | Provenance & causes | Every Section 1–3 number has an A5 line; every "why" has a source or says `cause unconfirmed` | Add the line or remove the number |
| 9 | Calendar | Every date has an acceptable source | `date unconfirmed — check before expiry` |
| 10 | Staleness | Gamma, Greeks, stress, IVR refreshed or `STALE (as of …)` | Add the tag |
| 11 | Arithmetic | Spot-check 3 cushions, 3 R5 rows, the bands and the benchmark return with code execution; inputs shown in the Appendix | Recompute |
| 12 | Readability | Section 1 ≤ 7 lines; no sentence in Sections 1–3 with more than 2 numbers; every item has 🔴/🟡/🟢; no links, rule tags or bracket tags in Sections 1–3 (except the order table's rule column); word caps from `report-layout.md` met | Rewrite the offending lines |
| 13 | Handoff, title, runner | Handoff in a code block with FEED / CHECK / ACTIONS / TRIGGERS (+ PUBLISHED CLOSES and NAV in AH/WKND); `REPEAT` only at count ≥ 3; title uses the em dash; header shows the runner | Fix |

Print it compactly at the end of A5, naming the item for anything that isn't clean. For example:
`Integrity: 1✓(51/51) 2✓(7/7 rows) 3✓ 4✓ 5✓ 6△(MGNX unverified) 7✓ 8△(AI-infra cause unconfirmed) 9✓ 10△(GEX STALE) 11✓ 12✓ 13✓`

## Source ladder (best first)
1. The book source and quote source in the platform `SKILL.md`
2. Primary releases: company IR, SEC EDGAR, BLS/BEA/Census, ISM, Treasury, CBOE, exchanges
3. Market-data pages with a visible timestamp
4. Attributed news (Reuters, AP, CNBC, Bloomberg via a syndicator)
5. Aggregators and blogs: context only, never the sole source for a Section 1–3 number

## What never ships
- A position that isn't in the book source, or an order without its feed row.
- A price, date or cause stated as fact with no source.
- An `UNVERIFIED` price used as an order limit.
- A HIT grade on a pre-market or after-hours mark.
- An empty, duplicate, draft, test or raw-markdown doc.
