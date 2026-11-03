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

## Ground rules (Claude)
- **Read-only on the broker.** Never place, modify or cancel an order. Orders appear in the report as staged tickets only.
- **Account:** ••6081 (account_number `5QR66081`). Mask it in the doc. Show ••1686 only if the live pull returns positions for it.
- **Tools:** load connector tools by searching for the bare tool name (server prefixes vary by install). Never type a full prefixed name from memory.
- **Big results:** if a tool result is too large, read it in chunks or filter it with code execution; never summarise a result you only partly read.
- **Model:** these reports are long and number-heavy, so run them on the strongest model available.

## Platform mapping (Claude)
| Need | Source |
|---|---|
| **Book source** | A live Robinhood pull: `get_portfolio`, `get_equity_positions`, `get_option_positions` (all pages, nonzero only), working orders (`get_option_orders` / `get_equity_orders`, state confirmed) and the session's fills (state filled, plus `get_pnl_trade_history` for GTCs created on earlier days). The newest WarRoom PDF for this mode in the Drive folder `Robinhood Portfolio Review` (PRE: today's `PRE` or the latest `EOD`; MID: `MID`; AH: `EOD`; WKND: `WEEKBOOK` + the week's `EOD`) goes **verbatim in Section 7** and is reconciled: `Book reconcile: feed NAV $X vs live $Y (Δ Z%) · short lines feed N vs live M`. If they differ by more than 2%, or the line counts differ, use the live numbers and name the difference. If there's no PDF, say so and use the live pull alone. |
| **Quote source** | Robinhood `get_equity_quotes` and `get_option_quotes` for every held name and every open short. They take up to 20 ids per call, so batch them. Use `get_equity_historicals` for prior closes and gap checks. |
| Class and Floor B | The CLASS and Floor B columns in the WarRoom PDF appendix. If a name is missing: LC rules, `class? UNVERIFIED`. |
| Indices, VIX, futures | Robinhood `get_index_quotes`. Then IBKR `get_price_snapshot` (futures) or Twelve Data ETF proxies (SPY, QQQ, DIA, IWM), labelled as proxies. |
| Rates, FX, commodities, crypto | Alpha Vantage (`TREASURY_YIELD`, `FX_DAILY`, `BRENT`, `WTI`, `GOLD_SILVER_SPOT`) or Twelve Data, then web search for intraday marks with a visible timestamp |
| Earnings, filings, news | Robinhood `get_earnings_calendar`, `get_earnings_results`, `get_sec_filing_index`; Quartr for releases and transcripts; Zacks `get_real_time_news`; then web search |
| IV Rank for the put screener (R1) | IBKR `get_option_data` (IV percentile 52w / 26w). If unavailable: `IVR unverified`. |
| Retail sentiment | Stocktwits `get_sentiment` / `get_trending_symbols`; otherwise N/A |
| Math | Code execution with the formulas in core-rules §6. Show the inputs. |
| Stress source | The WEEKBOOK PDF's S1–S5 table, tagged `STALE (as of <PDF time>)`; otherwise N/A. Never estimate. |
| Journal | Read the Google Sheet `Trade Journal` with Drive `read_file_content`. Claude can't edit Sheets, so AH and WKND put the new rows in Section 11 (AH) or Section 6 (WKND) as a `Journal rows to paste` table in the sheet's column order, and list them in the chat reply. |
| Save | See *Save (Claude)* below. |

## Steps (every mode, in order)
1. **Clock:** core-rules §1.
2. **Book:** the book source → Book feed line → full trigger scan (core-rules §2–3).
3. **Handoffs:** read ACTIONS and TRIGGERS from the previous report, and PUBLISHED CLOSES from the latest AH/WKND (core-rules §4–5, §9). Read the earlier reports with Drive `read_file_content`.
4. **Data:** the mode checklist, batched as macro, then equities, then vol.
5. **Write:** the mode template in order, within the length budget (core-rules §8). Write the whole report as one markdown file in the scratch or outputs folder.
6. **Integrity:** run `integrity.md`; fix or tag anything that fails.
7. **Save and verify** (below). Reply in chat with the doc link, the Bottom Line `Action:` lines and, for AH and WKND, the journal rows.

## Save (Claude; overrides core-rules §11 steps 1–2)
The Drive connector converts markdown into a native Google Doc with real headings, bold, tables and bullets (tested 3 Nov 2026). It can't edit an existing doc's contents, so a re-run replaces the doc instead of updating it.
1. Search `Market Reports` (folder id `1BHRsYiSN8bbSIQvwGwEo1tzQoErO2-s9`) for the exact doc title and note any existing file id.
2. Upload with Drive `create_file`: `title` = the doc title, `parentId` = that folder id, `contentMimeType: "text/markdown"`, `textContent` = the report. **Leave conversion on** (don't set `disableConversionToGoogleType`). On a re-run, set the header line to `Updated HH:MM ET / HH:MM ICT (vN)`.
3. **Verify:** `download_file_content` with `exportMimeType: "text/html"`. Pass if the HTML has `<h1` or `<h2` and, when the report has tables, `<table`, and no literal `**` or a `#` at the start of a line. If it fails, re-upload once; if it fails again, use the plain-text fallback in core-rules §11 step 4.
4. **Only after the new doc verifies**, trash the older doc with the same title (`trash_file`; it stays recoverable for 30 days). Exactly one doc per mode per day remains.
5. Never upload into `Market Reports` without the doc title format above, and never leave test files there.
