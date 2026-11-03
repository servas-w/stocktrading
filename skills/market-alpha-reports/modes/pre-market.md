# PRE — Pre-Market Alpha Report (job: PLAN)

Gives the verdict, opening posture, risk budget and execution shortlist for today's session.
- **Reads:** the last AH or WKND Handoff, the latest weekend stress test, the latest EOD feed, and the live Robinhood book.
- **Hands off to:** MID and the Mid-Market War Room.
- **Runs:** 21:00 ICT (09:00 ET, after the 8:30 data), once. Re-runs update the same doc as v2 and v3; never create a new doc.
- **Budget:** ≤ 3,500 words plus the feed.

## Checklist (after shared pipeline steps 1–3)
- [ ] Book (batch D): live pull → Book Map → **full** trigger scan; Robinhood pre-market quotes for every held name (movers ≥ ±5%, tripwire distances)
- [ ] Macro (batch A): ES/NQ/YM/RTY ✓✓ with clocks; 2Y/10Y/30Y; DXY, EUR/USD; Brent/WTI (contract month), gold, BTC; IG/HY credit; OAT–Bund; Europe/Asia closes; 8:30/10:00 releases vs consensus vs prior; Fed speakers today
- [ ] Equities (batch B): BMO earnings with guidance; > $50B pre-market gappers with RVOL and catalyst; analyst actions 05:00–08:30 ET; retail sentiment (Source-or-N/A)
- [ ] Vol & screens (batch C): VIX, VIX1D, VXN → `bands`; dealer gamma (N/A unless a live source); put screener; Short Bench refresh + Rolling Over scan

## Template (keep this numbering; the Handoff and feeds rely on it)
Header + Metadata (`Ref: PM-<date>`) · Bottom Line · Scorecard (grades the last AH/WKND, plus Execution and Repeat lines) · Key Judgments (≤ 4)
1. **Shkreli book autopsy & executive summary:** net exposure to the overnight driver; the 2–4 positions nearest a trigger, **chosen from the full live trigger scan**; session posture (Capital Preservation / Tactical Put Writing / Downside Hedging)
2. **Overnight handover & index futures:** Cross-Asset Dashboard (futures ✓✓, cash vs futures clocks tagged). "Prior close" = the published AH/WKND close.
3. **Macro data & central bank schedule:** 8:30/10:00 ET table (Consensus · Prior · Actual), anti-synthesis enforced
4. **BMO earnings deconstruction:** EPS/revenue vs consensus, guidance (`[Guidance ≠ Realized Cash Flow]`), sympathy names; breadth check `[Aggregate ≠ Breadth]`. Cap of 6 names: held or sympathy names first.
5. **Pre-market large-cap movers (> $50B):** top 5 gainers and losers with RVOL and catalyst
6. **Analyst actions (05:00–08:30 ET):** held and watchlist names first, 6 max
7. **Portfolio & watchlist radar:** book reconcile line · feed verbatim · Harvest open plan · Tripwire top 5 · themes ≥ 5% NAV · lot-desk exceptions · held movers ≥ ±5% pre-market (price, %, volume, catalyst, strike impact, or the None line) · Greeks (or `STALE`) · Book Triggers (full scan)
8. **Opening gamma & expected-move bands:** gamma levels or N/A/STALE; daily 1σ/2σ for SPX (VIX1D) and NDX (VXN) from `bands`, inputs shown
9. **Policy, geopolitics & commodities:** three-layer unbundling + Strategic Themes Desk: **full (all four desks) on Monday**, otherwise brief (only desks with new facts since the last report)
10. **Retail sentiment radar** (Source-or-N/A; one line if nothing new)
11. **Opening-bell checklist:** staged order table (all orders, ranked by risk removed) · put shortlist (top 3 or the No-tickers line; none while ITM ≤ 21 DTE triggers are open) · Short Bench (held shorts first) · if-then triggers for the open · Scenario Map (today's session) · Indicators & Warning Signs · Decision Gates
12. **Works Cited** (Source Notes) + Integrity line
War Room Handoff (incl. `Pre-market held movers (≥ 5%)` and `ACTIONS:`)

## Mode rules
- A held name quoted through its tripwire pre-market becomes a Bottom Line `Action:`.
- Harvest open plan: HARVEST rows plus HOLD rows within 10% of target, each with a BTC GTC price to enter before the bell.
- Held movers line when none: `Active Position Movers (≥ 5%): None — all held positions within ±5% pre-market.`
- Pre-market marks are previews: write `PM $X (as of HH:MM ET)` and never grade anything on them.
- Defense first: if any ITM ≤ 21 DTE or Rule 5 (> 10% NAV) trigger is open, the shortlist prints `No new underwriting until triggers <list> are cleared`.

## Common mistakes
- Running before the 8:30 ET releases (after 1 Nov, a fixed 19:30 ICT schedule lands at 07:30 ET).
- Quoting futures and cash yields as one synchronized mark.
- Treating a pre-market gap as confirmed before the open (`[Price ≠ Proof]`).
- Using last night's option marks for harvest $ without the label `as of feed <time>`.
- Listing only the names the feed highlighted (this is how ACRS at 20% NAV and 7 ITM Nov-20 lines were missed on 2 Nov).
