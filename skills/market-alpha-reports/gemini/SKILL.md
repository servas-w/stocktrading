---
name: market-alpha-reports
description: Writes Wilson's four US-session market reports as Google Docs in the Drive folder Market Reports, focused on what is moving in the market, why, how it hits his options book, what to watch, and how the book is doing against QQQ. PRE is the Pre-Market Alpha Report (plan). MID is the Mid-Day Institutional Market Report (adjust). AH is the After-Hours Alpha Report (grade and journal). WKND is the Weekend Stock Market Report (strategy and risk). Reads the latest WarRoom PDF for the book and Google Search for market data. Use when the user or a scheduled action asks for PRE, MID, AH or WKND, a pre-market report, opening-bell outlook, mid-day report, intraday update, after-hours report, post-market recap, weekend report or weekly market review.
---
# Market Alpha Reports (Gemini 4 Argon)

You write Wilson's US-session market reports as Google Docs. Wilson is a premium seller in Da Nang (ICT, UTC+7): short puts, put spreads, covered calls and some short stock. The reports are mostly **market intelligence tied to his book**: what moved, why, what it means for his positions, what to watch, and what to do.

| Mode | Job | Ref | Doc title (em dash) | Mode file |
|---|---|---|---|---|
| PRE | PLAN | `PM-<date>` | `YYYY-MM-DD — Pre-Market Alpha Report` | `modes/pre-market.md` |
| MID | ADJUST | `MD-<date>` | `YYYY-MM-DD — Mid-Day Institutional Market Report` | `modes/mid-day.md` |
| AH | GRADE & JOURNAL | `AH-<date>` | `YYYY-MM-DD — After-Hours Alpha Report` | `modes/after-hours.md` |
| WKND | STRATEGY & RISK | `WK-<date>` | `YYYY-MM-DD — Weekend Stock Market Report` | `modes/weekend.md` |

**Pick the mode:** the prompt names it. If not, convert the current time to ET (`core-rules.md` §1): Mon–Fri 04:00–09:29 ET → PRE · Mon–Fri 09:30–15:59 ET → MID · Mon–Thu 16:00 ET until 04:00 ET next day → AH · Fri 16:00 ET until Mon 04:00 ET → WKND.

**Runner:** see the table in `core-rules.md` §11 (default: Gemini runs MID; Claude runs PRE, AH, WKND). Write `Runner: Gemini` in the header. For another runner's mode, run only if Wilson asks directly in this conversation, and never replace a doc whose header names the other runner.

**Read before writing, every run:** the mode file, `references/report-layout.md`, `references/style.md`, `references/core-rules.md`, `references/playbook.md` (v2.5, R1–R12) and `references/integrity.md`.

## Platform mapping (Gemini)
| Need | Source |
|---|---|
| **Book source** | The newest WarRoom PDF for this mode in the Drive folder `Robinhood Portfolio Review`. File names carry the run time (`WarRoom_<date>_<n>-<TYPE>-<HHMM>.pdf`); if two share a name, take the later run time inside the file. PRE → today's `PRE`, else the latest `EOD` · MID → today's `MID` · AH → the latest `EOD` · WKND → the latest `WEEKBOOK` + that week's `EOD` files. Read **every page**, especially the appendix: A1 header, A2 snapshot, `CHECK:` line, A3 stock positions, A4 option positions, A5 quotes, A6 fills, A7 working orders, A8 transfers. This is the **only** source for positions, cash, NAV, Greeks, fills, orders and deposits. Older than the mode expects → `STALE FEED (<age>)` first in Section 1. |
| **Quote source** | The PDF's A5 quotes and A3/A4 marks (`as of feed <time>`). Search for fresher quotes only for triggered names and the top 10 exposures; no timestamped quote found → keep the PDF mark. |
| Market data, news, causes | Google Search grounding: each figure with its page and the time it shows; each "why" with its source, else `cause unconfirmed`. Prefer primary sources (company IR, SEC, exchanges, CBOE, BLS/BEA, ISM, Treasury). |
| Benchmarks | QQQ, SPY closes (published closes or Google Finance); CBOE PUT index from CBOE, else N/A. |
| Expected move | Implied move quoted by a source, or front ATM straddle ÷ spot when an option chain page shows it; else N/A. |
| Stress | WEEKBOOK S1–S5 table, tagged `STALE (as of <PDF time>)`; else N/A. Never estimate. |
| Math | Code execution with `core-rules.md` §6–7. Show the inputs in the Appendix. |
| Journal | Google Sheet `Trade Journal` (AH and WKND append rows per `core-rules.md` §12; WKND reads it for the scorecard). |
| Save | Google Docs in the Drive folder `Market Reports` (`core-rules.md` §11). |

## Steps (every mode, in order; don't write before step 5)
1. **Clock** (`core-rules.md` §1).
2. **Book:** read the whole PDF; copy the `CHECK:` line; build the position list from A3/A4 only; full trigger scan (§2–3).
3. **Handoffs:** ACTIONS and TRIGGERS from the previous report; PUBLISHED CLOSES and NAV lines from the latest AH/WKND. Nothing else from older reports.
4. **Market data** per the mode checklist: macro, then movers and news, then vol and calendar.
5. **Write** in the `report-layout.md` order using `style.md`: Section 1 last, copying values from Sections 2–3 and the Appendix.
6. **Integrity:** run all 13 checks in `integrity.md`; fix or tag.
7. **Save and verify** (§11). Reply in chat with the doc link and the Section 1 summary only.

## Hard rules (re-read before saving)
1. Every position named anywhere exists in the PDF's A3/A4 tables with the same ticker, strike, expiry and quantity. Section 3 rows carry the feed row. No row → no item.
2. The `CHECK:` line is copied exactly and the A1 count matches it.
3. Never invent, imply or interpolate a price, date, cause, position or account. Missing → N/A or `cause unconfirmed`.
4. Prior closes come from the latest PUBLISHED CLOSES, not a new search.
5. Unverified held-name moves stay in, tagged `check broker before acting`; never used as an order limit.
6. Sections 1–3: plain sentences, at most 2 numbers per sentence, a 🔴/🟡/🟢 marker on every item, no links or rule tags, within the word caps.
7. Performance vs QQQ is time-weighted (deposits stripped) and shown with drawdown and leverage.
8. One doc per mode per day, em-dash title, runner in the header, Handoff in a code block, no markdown symbols visible after saving.
