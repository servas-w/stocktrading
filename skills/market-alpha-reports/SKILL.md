---
name: market-alpha-reports
description: Generates Wilson's four US-session market reports as Google Docs in Market Reports. PRE = Pre-Market Alpha Report (PLAN: futures, 8:30/10:00 ET data, BMO earnings, gappers, book triggers, opening-bell checklist). MID = Mid-Day Institutional Market Report (ADJUST: changes since the open, rotations, intraday 8-Ks, live book, afternoon gameplan). AH = After-Hours Alpha Report (GRADE & JOURNAL: close, AMC earnings, post-close filings, P&L, Trade Journal, hunt list). WKND = Weekend Stock Market Report (STRATEGY & RISK: weekly ledger, journal analytics, S1-S5 stress test, biotech roadmap, Short Bench, week ahead). Use for PRE, MID, AH or WKND, a pre-market report, morning briefing, mid-day report, intraday update, after-hours report, daily recap, weekend report or weekly market review, including scheduled runs.
---
# Market Alpha Reports (master)

One skill, four reports. Each mode has its own job, horizon and template (in `modes/`). The rules in this file apply to all four. They override anything looser in the mode files or the helper skills.

| Mode | Job | Ref | Doc title | Runs (ICT, from 2 Nov; ET = ICT − 12h) | Mode file |
|---|---|---|---|---|---|
| **PRE** | PLAN | `PM-<date>` | `YYYY-MM-DD — Pre-Market Alpha Report` | 21:00 Mon–Fri (09:00 ET, after 8:30 data) | `modes/pre-market.md` |
| **MID** | ADJUST | `MD-<date>` | `YYYY-MM-DD — Mid-Day Institutional Market Report` | 00:30 Tue–Sat (12:30 ET) | `modes/mid-day.md` |
| **AH** | GRADE & JOURNAL | `AH-<date>` | `YYYY-MM-DD — After-Hours Alpha Report` | 09:30 Tue–Fri (grades Mon–Thu) | `modes/after-hours.md` |
| **WKND** | STRATEGY & RISK | `WK-<date>` | `YYYY-MM-DD — Weekend Stock Market Report` | Sat 10:00 (also grades Friday) | `modes/weekend.md` |

Before 2 Nov (EDT), ET = ICT − 11h: PRE ran at 20:00 ICT and MID at 13:30 ET.

**Use with:** `apply-market-report-standards` (templates, render check) · `render-book-desks` (Section 7, Book line, Book Map, `references/trade-journal.md`) · `build-short-bench` · `desk_math.py` (`bands`, `stress`, `journal`). Open them before writing. If one of them conflicts with this file, this file wins.

## Step 0: Pick the mode
1. An explicit word wins (`PRE`, `pre-market`, `MID`, `mid-day`, `AH`, `after-hours`, `WKND`, `weekend`).
2. Otherwise go by the ICT clock: 19:00–23:59 Mon–Fri → PRE · 00:00–05:59 Tue–Sat → MID · 06:00–18:59 Tue–Fri → AH · Sat from 06:00, Sun, or Mon before 19:00 → WKND (if this week's WKND doc already exists, ask in one line).
3. Open the mode file, then follow the shared pipeline below in order.

## Shared pipeline (every mode, in this order)
- [ ] **1. Clock:** session date, DST (EDT until 1 Nov, EST from 2 Nov), holiday or half-day. Every timestamp is printed as `HH:MM ET / HH:MM ICT`.
- [ ] **2. Book (batch D):** see *Book truth* below. This runs before any market data.
- [ ] **3. Prior report and Handoff:** read the previous report's War Room Handoff and its `ACTIONS` list (see *Scorecard*).
- [ ] **4. Macro (batch A), equities (batch B), vol & screens (batch C):** as listed in the mode file.
- [ ] **5. Write:** follow the mode template in order and stay within its length budget.
- [ ] **6. Integrity gate:** run every check in *Integrity gate*. Fix or label anything that fails. Never publish before this step.
- [ ] **7. Save:** see *Save*, then return the doc link and print the Bottom Line `Action:` lines in chat.

## Book truth (stops positions from drifting between reports)
- **Pull the book live every run.** Use Robinhood `get_portfolio`, `get_equity_positions`, `get_option_positions` (all pages, nonzero only) and working orders. Use the WarRoom feed for this mode (PRE/AH: latest EOD; MID: MID feed; WKND: Friday EOD plus the week's EODs) **verbatim in Section 7** as the audit narrative. All numbers in the Book Map, triggers and concentration come from the live pull.
- **Never copy positions, share counts, cost bases, cash or NAV from an earlier report.** Earlier reports are only used for the plan-vs-execution check.
- **Reconcile.** Print one line: `Book reconcile: feed NAV $X (as of <time>) vs live $Y (Δ Z%) · short lines feed N vs live M`. If NAV differs by more than 2% or the line counts differ, use the live numbers and name the difference.
- **Accounts:** ••••6081 is the primary account. Show ••••1686 or any other account only when the live pull or the feed actually returns it. Never infer another account's positions.
- **Completeness:** compute Book Triggers from the **full** position list, not from the feed's highlight list. Every short line that is ITM at ≤ 21 DTE, within 7% of strike, at Δ ≤ −0.30, or ≥ 80% captured must appear, whether or not the feed mentions it.
- **One concentration method:** % NAV per name = naked short-put strike notional + defined-risk spread width (max loss) + shares at market − long puts that expire **on or after** the short leg. Label each row `naked`, `spread width` or `net of hedge`. Theme and biotech-sleeve caps use the same method. Use this method in every mode.
- **Carry escalation:** any trigger flagged in 3 or more consecutive reports goes to the top of the Bottom Line as `REPEAT (n reports / since <date>)`, ahead of new items.

## Integrity gate (stops numbers from being made up)
Full rules and the check table are in `references/integrity.md`. Minimum rules:
- **Every figure needs a mark time and a source.** Use `✓✓` only when two independent sources agree (index/ETF ±0.1%, single stock ±0.5%, yield ±2 bp, FX ±0.1%, commodities ±0.5%). A single source gets `✓`. No source means print `N/A`, never a guess. Each link must go to the page that shows that number. A generic quote page is a valid link only for a live or closing quote, not for a pre-market mark it doesn't display.
- **Closes are fixed once published.** A session's close (index, held names, commodities, FX, BTC) is set by the first AH or WKND report for that session. Every later report reuses those exact numbers as its "prior close". If a fresh source disagrees, keep the published number and add `(source now shows X)`.
- **Continuity check.** Compare each benchmark and held-name price with the prior report. If it moved more than 5% for a stock, or more than 2% for an index, FX, a commodity or BTC, and you can cite no catalyst, re-pull from Robinhood. If it still doesn't reconcile, print `UNVERIFIED` and leave it out of the Bottom Line and the orders.
- **Calendar facts:** earnings dates, PDUFA dates and data release times need a source dated within the last 7 days. If sources conflict, print `date unconfirmed — check before expiry`.
- **Stale analytics:** gamma levels, Greeks, stress tests and IV ranks that were not refreshed this run print `STALE (as of <date time>)`. Never carry them forward silently.
- **Bands:** SPX daily bands use VIX1D (or VIX if VIX1D is missing), and weekly bands use VIX. NDX uses **VXN**. Centre the bands on the stated reference spot and show the inputs.

## Scorecard (grades whether the plan was carried out, not just whether the tape agreed)
Keep each mode's Scorecard block and add these three lines:
- `Tape: HIT | PARTIAL | MISS | NOT TESTABLE`. A pre-market mark can never count as a HIT for a call made pre-market. Grade only against cash-session prices.
- `Execution: X of Y prior actions done`. List what was missed by name, using the prior Handoff's `ACTIONS`.
- `Repeat triggers: n` (from Carry escalation).

## Length budget and brevity
- Word caps: PRE ≤ 3,500 · MID ≤ 3,000 · AH ≤ 4,000 · WKND ≤ 6,000, plus the verbatim feed. Over budget, trim tables before cutting judgments.
- **Bottom Line `Action:`** gets 5 numbered orders at most, ranked by risk removed, each with ticker, contract, side, quantity, limit and the rule it fixes. The full order list goes in the mode's checklist or gameplan section.
- **Shkreli Read:** 3 sentences at most under each table. It must name a book exposure or a trigger level; drop it otherwise.
- **Unchanged section:** one line, `No change since <Ref> — <key number>`.
- Tables have 10 rows at most unless the mode file says otherwise. For held names, show only rows that are triggered or have moved ±5%. Summarise the rest in one line.
- Never repeat a number in several sections. State it once and refer back with `(see §7)`.

## Save (one doc per mode per day, no empty docs)
- Search `Market Reports` for the exact doc title. If it exists, **update it in place** and change the header line to `Updated HH:MM ET / HH:MM ICT (v2)`. Never create a second doc with a time suffix.
- Write the doc in native Docs formatting (headings, bold, tables). After saving, read back the first 1,000 characters. If you see literal `\#`, `\*\*`, a backtick wrapping a number, or the file is under 2 KB, the save failed: re-save with formatting and check again. Never leave an empty or test doc in the folder.
- The War Room Handoff closes every report. It includes an `ACTIONS:` list (`id · ticker · contract · side · qty · limit · rule`) that the next report grades.

## Common mistakes (all modes)
- Building the Book from the previous report or the feed's highlight list instead of the live pull.
- Re-sourcing a published close and getting a different number.
- Grading a call HIT on pre-market prices.
- Copying Greeks, gamma or stress numbers forward without a STALE tag.
- Using the VIX for NDX bands.
- Creating version-suffixed duplicate docs, or saving raw markdown.
