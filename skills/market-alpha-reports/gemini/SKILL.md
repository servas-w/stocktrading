---
name: market-alpha-reports
description: Writes Wilson's four US-session market reports as Google Docs in the Drive folder Market Reports. PRE is the Pre-Market Alpha Report (plan). MID is the Mid-Day Institutional Market Report (adjust). AH is the After-Hours Alpha Report (grade and journal). WKND is the Weekend Stock Market Report (strategy and risk). Each report reads the latest WarRoom PDF for the book and Google Search for market data. Use when the user or a scheduled action asks for PRE, MID, AH or WKND, a pre-market report, opening-bell outlook, mid-day report, intraday update, after-hours report, post-market recap, weekend report or weekly market review.
---
# Market Alpha Reports (Gemini 4 Argon)

You write Wilson's US-session market reports as Google Docs. Wilson is a premium seller in Da Nang (ICT, UTC+7) who sells short puts and defined-risk put spreads. There are four modes, and each has its own job:

| Mode | Job | Ref | Doc title | Mode file |
|---|---|---|---|---|
| PRE | PLAN | `PM-<date>` | `YYYY-MM-DD — Pre-Market Alpha Report` | `modes/pre-market.md` |
| MID | ADJUST | `MD-<date>` | `YYYY-MM-DD — Mid-Day Institutional Market Report` | `modes/mid-day.md` |
| AH | GRADE & JOURNAL | `AH-<date>` | `YYYY-MM-DD — After-Hours Alpha Report` | `modes/after-hours.md` |
| WKND | STRATEGY & RISK | `WK-<date>` | `YYYY-MM-DD — Weekend Stock Market Report` | `modes/weekend.md` |

**Pick the mode:** the prompt names it. If it doesn't, convert the current time to ET (core-rules §1) and use: Mon–Fri 04:00–09:29 ET → PRE · Mon–Fri 09:30–15:59 ET → MID · Mon–Thu 16:00 ET until 04:00 ET the next day → AH · Fri 16:00 ET until Mon 04:00 ET → WKND.

**Runner:** Gemini runs **MID**; Claude runs PRE, AH and WKND (core-rules §11). Write `Runner: Gemini` in the header. If a scheduled run asks for another mode, stop and reply `<mode> belongs to Claude; not written`. Run it only if Wilson asks for it directly in this conversation, and never replace a doc whose header says `Runner: Claude`.

**Read before writing:** the mode file, `references/core-rules.md`, `references/playbook.md` and `references/integrity.md`. They define every rule, term and formula the templates use. If the skills `apply-market-report-standards`, `render-book-desks` or `build-short-bench` are installed, use them for desk layouts; where they conflict with these files, these files win.

## Platform mapping (Gemini)
| Need | Source |
|---|---|
| **Book source** | The newest WarRoom PDF in the Drive folder `Robinhood Portfolio Review` for this mode: PRE → today's `*PRE*` if it exists, otherwise the latest `*EOD*` · MID → today's `*MID*` · AH → the latest `*EOD*` · WKND → the latest `*WEEKBOOK*` plus that week's `*EOD*` files. Read **every page**, including the appendix tables (positions, quotes, fills, working orders, stress). It is the **only** source for positions, cash, NAV, Greeks, fills and orders. If it's older than the mode expects, put `STALE FEED (<age>)` first in the Bottom Line. |
| **Quote source** | The PDF's QUOTES and positions tables (label `as of feed <time>`). Search Google for fresher held-name quotes **only** for names with a trigger and the top 10 exposures; if search gives no timestamped quote, keep the PDF mark. Never guess a held-name price. |
| Market data | Google Search grounding. Each figure needs the page and the time it shows. |
| Stress source | The WEEKBOOK PDF's S1–S5 table, tagged `STALE (as of <PDF time>)`; otherwise N/A. Never estimate. |
| Math | Code execution with the formulas in core-rules §6. Show the inputs. |
| Journal | The Google Sheet `Trade Journal` (WKND reads it; AH and WKND append fills) |
| Save | Google Docs in the Drive folder `Market Reports` (core-rules §11, including the plain-text fallback) |

## Steps (every mode, in order; don't start writing before step 4)
1. **Clock:** core-rules §1.
2. **Book:** read the whole PDF → Book feed line → full trigger scan (core-rules §2–3).
3. **Handoffs:** read ACTIONS and TRIGGERS from the previous report, and PUBLISHED CLOSES from the latest AH/WKND. Read nothing else from earlier reports.
4. **Data:** the mode checklist, batched as macro, then equities, then vol.
5. **Write:** the mode template in order, within the length budget (core-rules §8).
6. **Integrity:** run `integrity.md`; fix or tag anything that fails.
7. **Save and verify** (core-rules §11). Reply in chat with the doc link and the Bottom Line `Action:` lines only.

## Hard rules (re-read before saving)
1. Positions come only from the PDF; market numbers come only from retrieved pages. Otherwise print N/A.
2. Never invent, imply or interpolate a price, date, position or account.
3. Prior closes come from the latest PUBLISHED CLOSES, not from a new search.
4. Triggers come from the full position list, and the Trigger scan count matches the PDF's line count.
5. Unverified held-name moves stay in the Bottom Line as `check broker before acting`; never use them as an order limit.
6. No HIT on pre-market or after-hours prices. PRE prints Carry-in, not grades.
7. Stay within the word cap, with at most 5 Bottom Line actions; every Bottom Line number has a provenance line.
8. One doc per mode per day, with no markdown symbols visible after saving: no `**` inside table cells, and the Handoff inside a code block.
9. Only run MID unless Wilson asks directly; never overwrite a Claude-run doc.
