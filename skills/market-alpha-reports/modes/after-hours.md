# AH — After-Hours Alpha Report (job: GRADE & JOURNAL)

Answers whether the plan worked, what the book earned or missed, and what was logged, then builds tomorrow's hunt list. **This report publishes the session's official closes (PUBLISHED CLOSES).** Every later report reuses them.
- **Horizon:** the trailing 24 hours (the last cash session plus post-market).
- **Reads:** MID (ACTIONS, TRIGGERS), this session's PRE ACTIONS, the end-of-day book source with the session's fills, and the quote source.
- **Hands off to:** the EOD War Room and the next PRE.
- **Runs:** after the end-of-day audit, about 09:30 ICT Tue–Fri. The session date is the previous ICT date. Friday's session is graded by WKND.
- **Budget:** ≤ 4,000 words plus the feed.

## Checklist (after core steps 1–3 in the platform SKILL.md)
- [ ] Scorecard: Tape grade for the MID call and today's Scenario Maps against the close; `Execution: X of Y actions done today` (PRE + MID)
- [ ] Book (batch D): end-of-day book source → Book Map → full trigger scan; after-hours quotes on held names (movers ≥ ±5%); tripwire refresh; the session's fills
- [ ] Macro (batch A): closes for SPX/NDX/DJI/RUT ✓✓; 2s10s; DXY; crude (contract month), gold, BTC; credit; Europe close. **Record these as PUBLISHED CLOSES**, along with every held name's close.
- [ ] Equities (batch B): 11 sectors; > $50B leaders/laggards with closing volume; price-target changes since the open; AMC earnings (GAAP vs non-GAAP, guidance, call disclosures); SEC filings 16:00–18:30 ET (8-K, S-3, Form 4); Mag 7 closes + extended-hours marks
- [ ] Vol & screens (batch C): put screener + next-session hunt list; Short Bench status
- [ ] Trade Journal: append the session's fills to the Google Sheet `Trade Journal`, with the rule check from `playbook.md`

## Template (keep this numbering)
Header + Metadata (`Ref: AH-<date>`) · Bottom Line · Scorecard (Tape + Execution + Repeat triggers) · Key Judgments (≤ 4)
1. **Shkreli book autopsy & cash-close summary:** what the close did to the positions nearest a trigger; earnings quality vs closing euphoria or panic
2. **Closing ledger & cross-asset matrix:** Cross-Asset Dashboard (closing clocks, marked `PUBLISHED CLOSE`), curve + Strategic Themes Desk (brief)
3. **Sector dispersion & rotations** (11 sectors, rotation status)
4. **Large-cap leaders & laggards (> $50B)** with closing volume and catalyst (top 3 each)
5. **Analyst price-target upgrades & downgrades** since the open (held and watchlist names first, 8 max)
6. **AMC earnings deconstruction & sympathy matrix:** `[Guidance ≠ Realized Cash Flow]`; conference-call disclosures (capex, margins, backlog); breadth check `[Aggregate ≠ Breadth]`. Held names and names with open puts first.
7. **Portfolio closing ledger & P&L attribution:** Book feed line · Trigger scan line · feed verbatim · session fills (net credit/debit) · **missed harvest** (every HARVEST row still open at the close, $ total) · Tripwire top 5 (after-hours) · themes ≥ 5% NAV · held-lot status table (triggered or ±5% rows only) · held movers ≥ ±5% after hours (or the None line) · Greeks (or STALE) · Book Triggers · held-lot unrealized beside realized P&L
8. **Post-close SEC filings (16:00–18:30 ET):** 8-K, S-3 dilution, Form 4 `[Plan ≠ Realized Execution]`; if none: `None filed during this window.`
9. **Mag 7 closing matrix & post-market microstructure:** close, extended-hours mark, volume vs average, IV status
10. **Screener & hunt list:** put candidates (top 3 or the No-tickers line) · next-session hunt list (GREEN) · Short Bench (held shorts first; next-session trigger and stop) · Scenario Map (next session) · Indicators & Warning Signs · Decision Gates
11. **Trade Journal logging summary:** rows added or closed, rules broken (by number and name), and today's rule-adherence %
12. **Works Cited** (Source Notes with provenance lines) + Integrity line
War Room Handoff (core-rules §9, including PUBLISHED CLOSES; HELD MOVERS = after hours; ACTIONS = next session)

## Mode rules
- PUBLISHED CLOSES use the official 16:00 ET close. For held names, use the book or quote source's close; if a search source differs by more than 0.5%, note it.
- New shorts under 30 DTE are allowed (tag them OPP); don't log them as breaches.

## Common mistakes
- Treating an extended-hours print as the close.
- Logging assigned-lot losses as options P&L.
- Grading entries against an old DTE/delta window. Use `playbook.md`.
- Publishing a close that disagrees with the book source's close without a note.
