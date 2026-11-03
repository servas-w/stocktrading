# AH — After-Hours Alpha Report (job: GRADE & JOURNAL)

Answers whether the plan worked, what the book earned or missed, and what was logged, then builds tomorrow's hunt list. **This report publishes the session's official closes.** Every later report reuses them.
- **Horizon:** the trailing 24 hours (the last cash session plus post-market).
- **Reads:** MID and its `ACTIONS:`, the EOD WarRoom feed (audit ~09:00 ICT), the live Robinhood book and the session's fills.
- **Hands off to:** the EOD War Room and the next PRE.
- **Runs:** 09:30 ICT Tue–Fri. The session date is the previous ICT date. Friday's session is graded by WKND, not by a separate AH.
- **Budget:** ≤ 4,000 words plus the feed.

## Checklist (after shared pipeline steps 1–3)
- [ ] Scorecard: grade the MID call and Scenario Map against the close; **Execution: X of Y PRE + MID actions done**
- [ ] Book (batch D): live pull + EOD feed → Book Map; after-hours quotes on held names (movers ≥ ±5%); tripwire refresh; session fills from FILLS
- [ ] Macro (batch A): closes for SPX/NDX/DJI/RUT ✓✓; 2s10s; DXY; crude (contract month), gold, BTC; credit; Europe close. **Record these as the published closes.**
- [ ] Equities (batch B): 11 sectors; > $50B leaders/laggards with closing volume; PT changes since the open; AMC earnings (GAAP vs non-GAAP, guidance, call disclosures); SEC filings 16:00–18:30 ET (8-K, S-3, Form 4); Mag 7 closes + extended-hours marks
- [ ] Vol & screens (batch C): put screener + next-session hunt list; Short Bench status
- [ ] Trade Journal: append the session's fills to the Google Sheet `Trade Journal` with the Playbook v2 rules check

## Template (keep this numbering)
Header + Metadata (`Ref: AH-<date>`) · Bottom Line · Scorecard (Tape + Execution + Repeat) · Key Judgments (≤ 4)
1. **Shkreli book autopsy & cash-close summary:** what the close did to the positions nearest a trigger; earnings quality vs closing euphoria or panic
2. **Closing ledger & cross-asset matrix:** Cross-Asset Dashboard (closing clocks, marked `PUBLISHED CLOSE`), curve + Strategic Themes Desk (brief)
3. **Sector dispersion & rotations** (11 sectors, rotation status)
4. **Large-cap leaders & laggards (> $50B)** with closing volume and catalyst (top 3 each)
5. **Analyst PT upgrades & downgrades** since the open (held and watchlist names first, 8 max)
6. **AMC earnings deconstruction & sympathy matrix:** `[Guidance ≠ Realized Cash Flow]`; conference-call disclosures (capex, margins, backlog); breadth check `[Aggregate ≠ Breadth]`. Held names and names with open puts first.
7. **Portfolio closing ledger & P&L attribution:** book reconcile line · feed verbatim · session fills (net credit/debit) · **missed harvest** (every HARVEST row still open at the close, $ total) · Tripwire top 5 (after-hours) · themes ≥ 5% NAV · held-lot status table (triggered or ±5% rows only) · held movers ≥ ±5% after-hours (or the None line) · Greeks (or `STALE`) · Book Triggers (full scan) · held-lot unrealized beside realized P&L
8. **Post-close SEC filings (16:00–18:30 ET):** 8-K, S-3 dilution, Form 4 `[Plan ≠ Realized Execution]`; if none: `None filed during this window.`
9. **Mag 7 closing matrix & post-market microstructure:** close, extended-hours mark, volume vs average, IV status
10. **Screener & hunt list:** put candidates (top 3 or the No-tickers line) · next-session hunt list (GREEN) · Short Bench (held shorts first; next-session trigger and stop) · Scenario Map (next session) · Indicators & Warning Signs · Decision Gates
11. **Trade Journal logging summary:** rows added or closed, any rule numbers broken, and today's rule-adherence score
12. **Works Cited** (Source Notes) + Integrity line
War Room Handoff (incl. `After-hours held movers (≥ 5%)`, `PUBLISHED CLOSES:` and `ACTIONS:`)

## Mode rules
- Held movers line when none: `Active Position Movers (≥ 5%): None — all held positions within ±5% after hours.`
- New shorts under 30 DTE are allowed (Rule 3 changed 2 Oct); don't log them as breaches.
- The Handoff's `PUBLISHED CLOSES:` block lists the benchmarks plus every held name's close. PRE and MID read their prior closes from it.

## Common mistakes
- Treating an extended-hours print as the close.
- Logging assigned-lot losses as options P&L.
- Grading entries against old rules (60–90 DTE, Δ 0.10–0.15). Use Playbook v2 (45–90 DTE, Δ 0.10–0.20).
- Publishing a close that disagrees with a held name's Robinhood close without a note.
