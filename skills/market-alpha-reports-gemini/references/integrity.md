# Integrity gate (run before saving)

Why these checks exist:
- **Oct 7 – Nov 2:** reports for the same Friday close disagreed by 20–75% (AAPL $268 vs $337, MRNA $222 vs $54, cash $44K vs $304K).
- **Nov 3 AH, Nov 4 PRE, Nov 4 MID:** each described positions that were not in the WarRoom PDF it cited (CAPR $35/$32/$30 puts at "$29", CMPX $7.5 puts, NVAX, ABEO, REPL/ETNB/KALV puts, MRNA at $25). Each still printed ✓ on every check.

So every check asks for something a reader can verify in the doc, not just a ✓.

| # | Check | Pass condition (visible in the doc) | On fail |
|---|---|---|---|
| 1 | Feed & check figure | Header and A1 show the feed name, run time and `CHECK:` line; the short option lines listed in A1 equal N | `STALE FEED` / recount; never invent lines to match |
| 2 | Book Lock, feed-row & Section 2/3 boundary rule | A1 shows the `BOOK LOCK:` line and was written before any market search. With code execution, every `Feed row:` in Section 4.1 and every position named in Sections 1, 3 and 4 (ticker + type + strike + expiry + quantity) is matched against the A1 tables; print `matched X of X`. A quantity, strike or expiry the feed prints as `n/q` or `see RH` stays `n/q` everywhere and is never filled in. Every ticker marked `Held` in Section 2 is in A1. Section 2 contains zero option strikes, DTE, cushions, or Playbook rules | Remove the unmatched item (never edit A1 to fit it), or move contract math to Section 3 |
| 3 | Trigger scan | `Trigger scan: N lines checked (Q quoted · U unquoted) · K hits` with N = CHECK's short option lines + stock lines; unquoted lines named; no order staged on a `strike inferred` row | Rescan; drop the order |
| 4 | Concentration | R5 in Section 3.3 uses the max-loss method (`core-rules.md` §3); every exception bullet is labelled `naked` / `spread width` / `hedged` / `hedge expires first` and shows gross collateral tied up | Recompute (`core-rules.md` §3) |
| 5 | Published closes | Every prior close matches the latest `PUBLISHED CLOSES` | Restore; add `(source now shows X)` |
| 6 | Continuity | Unexplained moves tagged `UNVERIFIED` (benchmarks out of Section 1; held names in, with `check broker before acting`) | Tag and move |
| 7 | Consistency & claims | Each Section 1 number equals its source section's number; same ticker = same price/strike/qty everywhere; no claim about earlier reports without Handoff evidence | Fix to the source section; drop the claim |
| 8 | Provenance, causes & analyst sweep | Every Section 1–4 number has an A5 line; every "why" has a source or says `cause unconfirmed`; every Section 2.0 headline shows its source and time, and every earnings headline shows the actual numbers; real analyst calls are named, and one sweep line covers held movers with `No public PT/rating change as of HH:MM ET` | Add the line/tag or remove the number |
| 9 | Calendar | Every date has an acceptable source | `date unconfirmed — check before expiry` |
| 10 | Staleness | Gamma, Greeks, stress, IVR refreshed or `STALE (as of …)` | Add the tag |
| 11 | Arithmetic | Spot-check 3 cushions, 3 R5 rows, the bands and the benchmark return with code execution; inputs shown in the Appendix | Recompute |
| 12 | Readability & Table-Free Sections 1–4 | Section 1 is 10–14 bullets (<= 350 words; <= 400 in WKND) covering macro tape, market news/Street calls, book/execution, and top priorities; **zero tables in Sections 1–4** (tables only in Section 5 Appendix, with zero `**` or `*` markdown inside cells); prose sentences in Section 1 keep <= 2 numbers (`·`-separated data strips allowed in `2.1`/`2.2`); every item has 🔴/🟡/🟢; Section 2 opens with 8–12 headlines, at least half not about held names; no story's numbers appear in more than one Section 2 slot; **word counts for Sections 1–4 are computed with code execution, printed in the Integrity line (`12✓(S1 340 · S2 1,380 · S3 960 · S4 470)`) and are each at or under the cap in `report-layout.md`** | Cut the section to its cap; rewrite the offending lines or convert tables to strips/mini-cards |
| 13 | Handoff, title, runner | Handoff in a code block with FEED / CHECK / ACTIONS / TRIGGERS (+ PUBLISHED CLOSES and NAV in AH/WKND); `REPEAT` only at count >= 3; title uses the em dash; header shows the runner | Fix |

Print it compactly at the end of A5, naming the item for anything that isn't clean. For example:
`Integrity: 1✓(51/51) 2✓(7/7 rows) 3✓ 4✓ 5✓ 6△(MGNX unverified) 7✓ 8△(AI-infra cause unconfirmed) 9✓ 10△(GEX STALE) 11✓ 12✓ 13✓`

## Source ladder (best first)
1. The book source and quote source in the platform `SKILL.md`
2. Primary releases: company IR, SEC EDGAR, BLS/BEA/Census, ISM, Treasury, CBOE, exchanges
3. Market-data pages with a visible timestamp
4. Attributed news (Reuters, AP, CNBC, Bloomberg via a syndicator)
5. Aggregators and blogs: context only, never the sole source for a Section 1–4 number

## What never ships
- A table anywhere in Sections 1, 2, 3, or 4, or literal `**` / `*` inside Section 5 table cells.
- Option strikes, DTE, cushions, or Playbook v2.5 rules inside Section 2.
- A position that isn't in the A1 Book Lock, or a Section 4.1 order without its verbatim `Feed row:`.
- A share count, strike or expiry that the feed printed as `n/q` or `see RH` and the report filled in.
- A section over its word cap, or a ✓ on check 12 without the measured counts.
- A price, date, analyst action, or cause stated as fact with no source.
- An `UNVERIFIED` price used as an order limit.
- A HIT grade on a pre-market or after-hours mark.
- An empty, duplicate, draft, test or raw-markdown save.
