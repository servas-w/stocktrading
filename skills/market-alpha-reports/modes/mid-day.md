# MID — Mid-Day Institutional Market Report (job: ADJUST)

Covers what changed since the open, which pre-market levels broke, which of this morning's orders were actually placed, and what to adjust for the afternoon.
- **Horizon:** only what happened since 09:30 ET.
- **Reads:** this morning's PRE plan and its `ACTIONS:`, the MID WarRoom feed (audit ~00:00 ICT) and the live Robinhood book with working orders.
- **Hands off to:** the Mid-Market War Room and AH.
- **Runs:** 00:30 ICT (12:30 ET from 2 Nov; 13:30 ET before).
- **Budget:** ≤ 3,000 words plus the feed.

## Checklist (after shared pipeline steps 1–3)
- [ ] Scorecard: grade the PRE posture, levels and Scenario Map against the cash tape; **Execution: X of Y PRE actions done** from today's fills and working orders
- [ ] Book (batch D): live pull + MID feed → Book Map; live option marks for HARVEST/HOLD rows near target; live spots → tripwire refresh; working-order audit (opening orders on tested names, lottery tickets, stale GTCs)
- [ ] Macro (batch A): SPX/NDX/DJI/RUT ✓✓; 2Y/10Y/30Y; DXY; crude (contract month), gold, BTC; credit; reaction to morning data; 13:00 ET auction; Fed remarks
- [ ] Equities (batch B): 11-sector leaderboard; did the morning gaps hold or fade; A/D ratio (Source-or-N/A); > $50B top 3 gainers/losers with volume pacing; Mag 7; 8-Ks, S-3/ATM, executive changes since the open
- [ ] Vol & screens (batch C): VIX, VIX1D, VVIX; gamma pins (N/A unless sourced); put screener; Rolling Over scan; squeeze watch on held shorts

## Template (keep this numbering)
Header + Metadata (`Ref: MD-<date>`) · Bottom Line · Scorecard (Tape + Execution + Repeat) · Key Judgments (≤ 4)
1. **Shkreli book autopsy & tape summary:** what the plan said vs what was done (by name); morning follow-through vs traps; the positions the morning moved toward a trigger; afternoon posture
2. **Mid-day cash session & index matrix:** Cross-Asset Dashboard (cash vs futures clocks tagged)
3. **Sector dispersion & flow rotations:** leaderboard, gap hold/fade check, breadth (Source-or-N/A), `[Aggregate ≠ Breadth]` (is the index move carried by a handful of mega-caps?)
4. **Large-cap leaders & laggards (> $50B) + Mag 7 intraday matrix**
5. **Fixed income, macro events & the Fed:** data reaction, 13:00 ET auction, Fed remarks + Strategic Themes Desk (brief: only desks with new facts)
6. **8-K filings & breaking news:** `[Plan ≠ Realized Output]`; held names first; if none: `None filed or announced during this session window.`
7. **Portfolio & intraday tracker:** book reconcile line · feed verbatim · morning fills and working-order hygiene (cancel list) · Harvest board live (what to bank before the lunch lull) · Tripwire top 5 live (flag moves inside 3%) · themes in one line unless a limit is crossed · Rule 7 breaches · afternoon risk flags (tested strikes, roll triggers, pending assignment) · Greeks (or `STALE`) · Book Triggers (full scan)
8. **Gamma pinning & 0DTE desk:** spot vs zero gamma, pin strikes (or N/A/STALE), VIX/VIX1D/VVIX slope
9. **Options screener:** put candidates (top 3 or the No-tickers line) · Short Bench: triggers fired since the open + held-short squeeze watch (unchanged bench = one line)
10. **Afternoon gameplan:** pre-staged order table · levels for the final 2 hours · if-then rules for resting orders and hedges · Scenario Map (rest of session) · Indicators & Warning Signs · Decision Gates
11. **Works Cited** (Source Notes) + Integrity line
War Room Handoff (incl. `ACTIONS:`)

## Mode rules
- Every market number refers to the window since 09:30 ET. Overnight context appears only as a labelled comparator.
- Harvest: if live marks were pulled, recompute with the render-book-desks formulas; otherwise label `as of feed <time>`.
- Brevity: a section with nothing new since PRE gets one line (`No change since PM-<date> — <number>`).
- Working orders that open risk on a triggered name (adding in defense, underwater lot, LEAPS) go to the Bottom Line as `Cancel:` before any new idea.

## Common mistakes
- Re-reporting pre-market news as if it were new.
- Quoting % above VWAP, volume pacing or 0DTE flow without a live source (print N/A).
- Calling a lunch-hour drift a reversal without a level (`[Price ≠ Proof]`).
- Grading the tape and skipping the execution check (whether the morning orders were actually placed is the most useful line in this report).
