# PRE — Pre-Market Alpha Report (job: PLAN)

Gives the verdict, opening posture, risk budget and execution shortlist for today's session.
- **Reads:** the latest AH/WKND Handoff (ACTIONS, TRIGGERS, PUBLISHED CLOSES), the latest weekend stress test, the book source and the quote source.
- **Hands off to:** MID and the Mid-Market War Room.
- **Runs:** 09:00 ET, after the 8:30 data: 21:00 ICT in US standard time, 20:00 ICT in US daylight time. Re-runs update the same doc (vN).
- **Budget:** ≤ 3,500 words plus the feed.

## Checklist (after core steps 1–3 in the platform SKILL.md)
- [ ] Book (batch D): book source → Book Map → full trigger scan. Pre-market quotes for every name with a trigger plus the top 10 exposures by % NAV (movers ≥ ±5%, tripwire distances). Other names keep their book-source mark, labelled `as of feed`.
- [ ] Macro (batch A): ES/NQ/YM/RTY ✓✓ with clocks; 2Y/10Y/30Y; DXY, EUR/USD; Brent/WTI (contract month), gold, BTC; IG/HY credit; OAT–Bund; Europe/Asia closes; 8:30/10:00 releases vs consensus vs prior; Fed speakers today
- [ ] Equities (batch B): BMO earnings with guidance; > $50B pre-market gappers with RVOL and catalyst; analyst actions 05:00–08:30 ET; retail sentiment (Source-or-N/A)
- [ ] Vol & screens (batch C): VIX, VIX1D, VXN → bands; dealer gamma (N/A unless a live source); put screener; Short Bench refresh + Rolling Over scan

## Template (keep this numbering; the Handoff and feeds rely on it)
Header + Metadata (`Ref: PM-<date>`) · Bottom Line · Scorecard (Carry-in + Repeat triggers; see core-rules §7) · Key Judgments (≤ 4)
1. **Shkreli book autopsy & executive summary:** net exposure to the overnight driver; the 2–4 positions nearest a trigger, chosen from the full trigger scan; session posture (Capital Preservation / Tactical Put Writing / Downside Hedging)
2. **Overnight handover & index futures:** Cross-Asset Dashboard (futures ✓✓, cash vs futures clocks tagged; prior close = PUBLISHED CLOSES)
3. **Macro data & central bank schedule:** 8:30/10:00 ET table (Consensus · Prior · Actual), anti-synthesis enforced
4. **BMO earnings deconstruction:** EPS/revenue vs consensus, guidance (`[Guidance ≠ Realized Cash Flow]`), sympathy names; breadth check `[Aggregate ≠ Breadth]`. 6 names max, held and sympathy names first.
5. **Pre-market large-cap movers (> $50B):** top 5 gainers and losers with RVOL and catalyst
6. **Analyst actions (05:00–08:30 ET):** held and watchlist names first, 6 max
7. **Portfolio & watchlist radar:** Book feed line · Trigger scan line · feed verbatim · Harvest open plan · Tripwire top 5 · themes ≥ 5% NAV · lot-desk exceptions · held movers ≥ ±5% pre-market (price, %, volume, catalyst, strike impact, or the None line) · Greeks (or STALE) · Book Triggers
8. **Opening gamma & expected-move bands:** gamma levels or N/A/STALE; daily 1σ/2σ for SPX and NDX (core-rules §6), inputs shown
9. **Policy, geopolitics & commodities:** three-layer unbundling + Strategic Themes Desk (full on Mondays and after a holiday; brief otherwise)
10. **Retail sentiment radar** (Source-or-N/A; one line if nothing new)
11. **Opening-bell checklist:** staged order table (all orders, ranked by risk removed) · put shortlist (top 3 or the No-tickers line) · Short Bench (held shorts first) · if-then triggers for the open · Scenario Map (today's session) · Indicators & Warning Signs · Decision Gates
12. **Works Cited** (Source Notes with provenance lines) + Integrity line
War Room Handoff (core-rules §9; HELD MOVERS = pre-market)

## Mode rules
- A held name quoted through its tripwire pre-market becomes a Bottom Line `Action:`.
- Harvest open plan: HARVEST rows plus HOLD rows within 10% of target, each with a GTC buy-to-close price to enter before the bell.
- Pre-market marks are previews: write `PM $X (as of HH:MM ET)` and never grade anything on them.
- Defense first: while any R3 or R5 trigger is open, the put shortlist prints `No new underwriting until <triggers> are cleared`.
- The ACTIONS in this Handoff are today's plan. MID grades them.

## Common mistakes
- Running before the 8:30 ET releases.
- Quoting futures and cash yields as one synchronized mark.
- Treating a pre-market gap as confirmed before the open (`[Price ≠ Proof]`).
- Using last night's option marks for harvest $ without the label `as of feed <time>`.
- Listing only the names the book source's summary highlighted (that is how the 2 Nov report missed 7 ITM Nov-20 lines).
