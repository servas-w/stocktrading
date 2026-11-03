---
name: market-alpha-reports
description: Generates Wilson's four US-session market reports as Google Docs in Market Reports. PRE = Pre-Market Alpha Report (PLAN: futures, 8:30/10:00 ET data, BMO earnings, gappers, book triggers, opening-bell checklist). MID = Mid-Day Institutional Market Report (ADJUST: changes since the open, rotations, intraday 8-Ks, live book, afternoon gameplan). AH = After-Hours Alpha Report (GRADE & JOURNAL: close, AMC earnings, post-close filings, P&L, Trade Journal, hunt list). WKND = Weekend Stock Market Report (STRATEGY & RISK: weekly ledger, journal analytics, S1-S5 stress test, biotech roadmap, Short Bench, week ahead). Use for PRE, MID, AH or WKND, a pre-market report, opening-bell outlook, mid-day report, intraday update, after-hours report, post-market recap, weekend report or weekly market review, including scheduled runs.
---
# Market Alpha Reports (Claude edition)

Four reports, one skill. Each mode has its own job and template. The rules shared by all four are in `references/core-rules.md`; rules and terms are in `references/playbook.md`.

| Mode | Job | Ref | Doc title | Mode file |
|---|---|---|---|---|
| PRE | PLAN | `PM-<date>` | `YYYY-MM-DD — Pre-Market Alpha Report` | `modes/pre-market.md` |
| MID | ADJUST | `MD-<date>` | `YYYY-MM-DD — Mid-Day Institutional Market Report` | `modes/mid-day.md` |
| AH | GRADE & JOURNAL | `AH-<date>` | `YYYY-MM-DD — After-Hours Alpha Report` | `modes/after-hours.md` |
| WKND | STRATEGY & RISK | `WK-<date>` | `YYYY-MM-DD — Weekend Stock Market Report` | `modes/weekend.md` |

**Pick the mode:** an explicit word wins (PRE, MID, AH, WKND, or the report name). Otherwise convert the current time to ET (core-rules §1) and use: Mon–Fri 04:00–09:29 ET → PRE · Mon–Fri 09:30–15:59 ET → MID · Mon–Thu 16:00 ET until 04:00 ET the next day → AH · Fri 16:00 ET until Mon 04:00 ET → WKND. If that week's WKND doc already exists, ask in one line.

**Read before writing:** the mode file, `references/core-rules.md`, `references/playbook.md` and `references/integrity.md`. If `apply-market-report-standards`, `render-book-desks` or `build-short-bench` are installed, use them for desk layouts; where they conflict with these files, these files win.

## Platform mapping (Claude)
| Need | Source |
|---|---|
| **Book source** | A live Robinhood pull: `get_portfolio`, `get_equity_positions`, `get_option_positions` (all pages, nonzero only), working orders and the session's filled orders. The WarRoom PDF for this mode (PRE/AH: latest EOD; MID: MID; WKND: WEEKBOOK + the week's EOD) goes **verbatim in Section 7** and is reconciled against the live pull: `Book reconcile: feed NAV $X vs live $Y (Δ Z%) · short lines feed N vs live M`. If they differ by more than 2%, or the line counts differ, use the live numbers and name the difference. |
| **Quote source** | Robinhood `get_equity_quotes` / `get_option_quotes` for every held name. |
| Market data | Market-data connectors (Twelve Data, Alpha Vantage, IBKR), primary releases, then web search, following the source ladder in `integrity.md` |
| Stress source | `desk_math.py stress` if it's available, else the WEEKBOOK PDF's S1–S5 tagged STALE, else N/A |
| Journal | The Google Sheet `Trade Journal` |
| Save | Google Docs in the Drive folder `Market Reports` |

## Steps (every mode, in order)
1. **Clock:** core-rules §1.
2. **Book:** the book source → Book feed line → full trigger scan (core-rules §2–3).
3. **Handoffs:** read ACTIONS and TRIGGERS from the previous report, and PUBLISHED CLOSES from the latest AH/WKND (core-rules §4–5, §9).
4. **Data:** the mode checklist, batched as macro, then equities, then vol.
5. **Write:** the mode template in order, within the length budget (core-rules §8).
6. **Integrity:** run `integrity.md`; fix or tag anything that fails.
7. **Save and verify** (core-rules §11). Reply in chat with the doc link and the Bottom Line `Action:` lines.
