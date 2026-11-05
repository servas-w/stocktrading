# PRE — Pre-Market Alpha Report (job: PLAN)

What happened overnight, what it means for the book, and the plan for the open.
- **Reads:** the book source (today's PRE snapshot if present, else the latest EOD), the latest AH/WKND Handoff (ACTIONS, TRIGGERS, PUBLISHED CLOSES, NAV), the quote source.
- **Hands off to:** MID.
- **Runs:** 09:00 ET, after the 8:30 data (21:00 ICT in US standard time, 20:00 ICT in daylight time). Never before 08:30 ET. Re-runs update the same doc (vN).
- **Caps:** Section 1 ≤ 120 words · Section 2 ≤ 1,200 · Section 3 ≤ 500.

## Data checklist (after core steps 1–3)
- Book: feed + CHECK → full trigger scan → pre-market quotes for every triggered name and the top 10 exposures (others keep the feed mark, `as of feed`).
- Overnight: ES/NQ/YM/RTY with clocks; Asia and Europe closes; overnight news on held names, peers and themes; crypto (Mondays: the whole weekend) for MSTR, IBIT, COIN; China ADR moves for BABA, BIDU.
- Today: 8:30/10:00 ET data vs consensus vs prior; Fed speakers; BMO earnings (held names, peers, > $50B) with guidance; earnings tonight for held names and peers with the **expected move**; analyst actions 05:00–08:30 ET on held and watched names; overnight 8-K, S-3/ATM, offerings on held names.
- Vol: VIX, VIX1D, VXN; IV on names with events; gamma (N/A unless sourced).

## What goes in each slot
**Section 1 — Summary:** market overnight in one sentence · book (NAV, cash vs floor, positions needing action) · `Carry-in: N actions staged from <Ref>` · top 3–5 items with 🔴/🟡, repeats first.

**Section 2 — Market & your book**
- **2.1 Overnight story:** what moved futures and why; the morning's data and how it landed; any running-story chapter.
- **2.2 Pre-market movers:** (a) your names gapping ±3% or more, (b) peers and suppliers that move them, (c) > $50B gappers with RVOL and cause.
- **2.3 Themes:** one line per theme you hold, with today's setup.
- **2.4 Your book this morning:** positions closer to a trigger after the overnight move; events this week with **expected move vs cushion**; expiry and assignment exposure this week vs buying power; short-squeeze watch (short interest, borrow, overnight move) on short stock; red flags filed overnight.
- **2.5 What to watch today:** the day's calendar in ET and ICT (data, Fed, auctions, earnings of held names and peers); if-then lines for the open; top 3 risks and their early-warning sign.
- **2.6 Opportunities:** pre-market dislocations in large caps, labelled `candidate — run LC/BIO underwriting first`. While any R3, R5 or R12 trigger is open: `No new underwriting until <triggers> are cleared`.

**Section 3 — Action plan:** orders for the open (feed-row column filled), do-not-do list, gates for 09:30–10:30 ET.

**Appendix:** A1 book tables · A2 futures/yields/FX/commodities/crypto dashboard, bands, vol · A5 sources + Integrity · A6 Handoff (`HELD MOVERS` = pre-market).

## Mode rules
- Pre-market prints are previews: write `PM $X (as of HH:MM ET)` and never grade on them.
- A held name quoted through its tripwire pre-market becomes a 🔴 item and a Section 3 order.
- The Handoff ACTIONS are today's plan; MID grades them.

## Common mistakes
- Running before 08:30 ET (the 4 Nov PRE ran at 05:02 ET and missed the data).
- Treating a pre-market gap as confirmed.
- Using last night's option marks as live (`as of feed <time>`).
- Listing positions that aren't in the feed (the 4 Nov PRE invented CAPR $35/$32/$30 puts).
