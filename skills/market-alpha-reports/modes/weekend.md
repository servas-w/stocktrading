# WKND — Weekend Stock Market Report (job: STRATEGY & RISK)

Stress-tests the book, grades the week's discipline, builds the Short Bench and maps the week ahead. **This report also grades Friday's session**, which covers Friday's AH duties: published closes, Friday fills and the Trade Journal.
- **Reads:** the Google Sheet `Trade Journal`, the week's War Room Handoffs and EOD feeds, the Held-Lot Plans doc and the live Robinhood book.
- **Hands off to:** Monday's PRE.
- **Runs:** Saturday 10:00 ICT (after Friday's EOD audit).
- **Budget:** about 35 data calls plus 8 for the Short Bench; ≤ 6,000 words plus the feed.

## Checklist (after shared pipeline steps 1–3)
- [ ] Scorecard: grade last weekend's posture and Scenario Map against the week; **Execution: X of Y actions done this week** (from every Handoff `ACTIONS:` Mon–Fri)
- [ ] Book (batch D): live pull + Friday EOD feed → Book Map; the week's EOD feeds (missed harvest, days each lot has been flagged); Held-Lot Plans doc; covered-call quotes at/above basis for flagged lots the audit didn't quote (≤ 4 chains)
- [ ] Friday close-out: publish Friday's closes (as AH would); append Friday's fills to `Trade Journal`
- [ ] Stress test: `desk_math.py stress` with every leg and stock position → S1–S5 table (N/A if the script can't run, never an estimate)
- [ ] Journal: `desk_math.py journal` on the week's closed trades (and year to date if the sheet allows)
- [ ] Macro (batch A): weekly closes ✓✓; curve steepener/flattener; commodities, FX, digital assets; credit; Europe sovereign
- [ ] Equities (batch B): 11 sectors by 5-day %; > $50B leaders/laggards; Mag 7 weekly; biotech readouts, PDUFA dates, congresses for held and watched names
- [ ] Vol & screens (batch C): VIX, VVIX, VXN, term structure; gamma/OPEX walls (or N/A); weekly `bands`; put screener; Short Bench full build
- [ ] Week-ahead calendar: CPI/PPI/jobs/PMIs/auctions, BMO/AMC earnings, Fed speakers and blackout (each date sourced ≤ 7 days old)

## Template (keep this numbering)
Header + Metadata (`Ref: WK-<date>`) · Bottom Line · Scorecard (Tape + Execution + Repeat) · Key Judgments (≤ 5)
1. **Shkreli book autopsy & weekly macro/biopharma summary:** the week's driver vs the book's exposure; the positions nearest a trigger going into next week
2. **Weekly closing ledger & cross-asset matrix:** Cross-Asset Dashboard (weekly comparators, `PUBLISHED CLOSE`), curve shifts, commodities/FX/crypto + Strategic Themes Desk (full, all four desks)
3. **Sector dispersion & capital rotation:** 5-day leaderboard, cyclical vs defensive vs duration thesis
4. **Large-cap leaders & laggards (> $50B) + Mag 7 weekly matrix:** breadth check `[Aggregate ≠ Breadth]`
5. **Biotech pipelines & FDA catalyst roadmap:** `[Trial Design ≠ Clinical Efficacy]`; endpoints, control arms, dilution overhangs; held names and names with open puts first
6. **Trade Journal analytics:** closed trades, win rate, average win/loss, expectancy, average captured %, days held, rule-adherence %, Cost of Indiscipline; harvested $ vs missed $; **Repeat-trigger table** (trigger · first flagged · reports flagged · status)
7. **Portfolio, risk limits & stress test:** book reconcile line · feed verbatim · Greeks · Book Triggers (full scan) · Tripwire Map (all names) + alert coverage · Theme Concentration (single method, labelled) · Held-Lot Repair Desk (full) · S1–S5 stress table · risk-limits audit (`limit not set` where unset)
8. **Options regime & screeners:** VIX/VVIX/term structure; gamma/OPEX walls (or N/A); weekly 1σ/2σ for SPX (VIX) and NDX (VXN) from `bands`; put screener (top 3 or the No-tickers line); **Short Bench, full build** (held shorts first, ≥ 1 per lane when a theme ≥ 5% NAV exists); Weekly Decision Gates
9. **Week-ahead calendar:** macro releases, earnings, Fed speakers/blackout · Scenario Map (week ahead + Regime line, 1–3 months) · Indicators & Warning Signs
10. **Works Cited** (Source Notes) + Integrity line
War Room Handoff (incl. `PUBLISHED CLOSES:` for Friday and Monday's `ACTIONS:`)

## Mode rules
- A setup below 10 closed trades gets no verdict (`n<10: no verdict`).
- Days flagged for a held lot = days since the first EOD feed in which it crossed its threshold. Flag `Rule 7 deadline passed` after 7 days with no plan.
- The Repeat-trigger table is the core of the weekly review: anything flagged in 3 or more reports goes to the Bottom Line with its day count.

## Common mistakes
- Estimating a stress-test number when the script can't run (print N/A).
- Building the Short Bench from the noisy pool without the multiple-expansion gate (refiners on crack spreads are fundamentals).
- Stating calendar dates that no source gave you (say "check whether earnings land before expiry").
- Weekend short-bench spots that disagree with the live book (on Oct 30 the MRNA/KOD/XBI spots conflicted with the 2 Nov report by 20–75%).
