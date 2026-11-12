# Style: Institutional Macro & Micro Depth with Table-Free Fast Readability

Wilson reads these reports in Da Nang, often at night or right before the open. **Section 1** must give him a **complete 1-minute executive briefing (`10–14` tight bullets, `<= 350 words`, `<= 400` in `WKND`)** covering the macro tape, top market news/earnings/analyst calls, book/execution snapshot, and top priorities so he never misses a catalyst even if he skips Sections 2–4. **Sections 1–4 use zero tables**—relying instead on **Single-Line Ticker Strips (`·`-separated)**, **Stacked 2-Line Mini-Cards**, and **Exception-Only Bullets** so nothing wraps awkwardly in Google Docs. Compact reference tables belong exclusively in **Section 5 (Appendix)**.

## The 10 rules
1. **Strict separation between Section 2 (Market/Stock News) and Section 3 (Contract/Book Audit):**
   - **Section 2** explains what happened across macro, rates, sectors, top market movers, Wall Street analyst ratings/PTs, and how those catalysts impact the **underlying businesses/tickers you own**—with zero option strikes, DTE, cushions, or Playbook rules.
   - **Section 3** translates those moves and SEC filings into **your specific contracts, strike cushions (`%`), diluted `Floor A / Floor B` strike tests, execution grades, and Playbook v2.5 (`R1`–`R12`) compliance**.
2. **Make Section 1 a Comprehensive 1-Minute Executive Briefing (`10–14` bullets, `<= 350 words`, `<= 400` in `WKND`):** Group Section 1 cleanly into (a) Macro/Rates/Vol Tape, (b) Top Market News, Earnings & Street Calls, (c) Book & Execution Snapshot, and (d) Top Priorities & Session Gates. Keep prose sentences crisp (`<= 2` numbers per prose sentence; `·`-separated ticker/macro data strips are fine in `2.1` and `2.2`).
3. **Give Section 2 and Section 3 full institutional depth:** Include exact filing figures (`10-Q` cash, current liabilities, quarterly burn, diluted shares + pre-funded warrants, `Floor A`/`Floor B`, `8-K` trial endpoints and SAE rates, `Form 4` insider buys/sells, `S-3`/`424B5` offerings, named Wall Street PT/rating changes or timestamped lack thereof, and `2Y`/`10Y`/`30Y` yield-curve moves) so Wilson never has to hunt outside the report for the "why."
4. **Zero tables in Sections 1–4:** Never render a table in Sections 1, 2, 3, or 4. Use **Single-Line Ticker Strips** (`2.2`, `3.4`), **Stacked 2-Line Mini-Cards** (`3.1`, `4.1`), and **Exception-Only Bullets** (`3.3`). Full 49+ line position blotters and cross-asset matrices stay in **Section 5 Appendix (`A1`–`A4`)**.
5. **Flag broken feed Greeks and 2x leveraged ETF beta:** Always flag deep-ITM options where broker Greeks violate intrinsic bounds (`bad Greek: true delta -1.00`), and always double (`2x`) the underlying's implied move when evaluating 2x leveraged ETFs (`ASTX`, `CWVX`, `MSTU`, `SOLT`).
6. **One status marker per item:** 🔴 act today / breach / material negative · 🟡 watch / boundary / mixed · 🟢 fine / working / cleared / positive catalyst. These are the only emoji allowed.
7. **Same slots, same order, every report** (see `report-layout.md`):
   - **Section 1:** Comprehensive Executive Summary
   - **Section 2:** `2.0 Market headlines` · `2.1 Macro, rates, geopolitics & breadth` · `2.2 Top market movers, primary reasons & street upgrades/downgrades` · `2.3 Seven-sleeve thematic & sector rotation` · `2.4 Macro & market catalyst calendar (+ Opportunities in PRE/AH/WKND)`
   - **Section 3:** `3.1 Active position alerts, strike cushions & Floor A/B math` · `3.2 Execution scorecard & bleed audit` · `3.3 Playbook v2.5 walkthrough & exception-only R5 concentration check` · `3.4 Held-position binary implied-move vs. cushion radar`
   - **Section 4:** `4.1 Orders (ranked 2-line mini-cards)` · `4.2 Do not touch` · `4.3 Into the close / If-then gates`
   - **Section 5:** Appendix (`A1`–`A6`)
8. **Analyst actions only when real; one sweep line for the rest:** Name the firm, rating and PT change where a call exists. After sweeping Reuters, MarketWatch, Benzinga and company IR, cover every held mover with no call in **one** line: `No public PT/rating change as of HH:MM ET on A, B, C`. Never add a "no change" note to each strip.
8a. **More news, fewer repeats:** Section 2 opens with `2.0 Market headlines` (8–12 one-liners across the whole market). Each story is told once in full; elsewhere it is a six-word pointer. Index levels and bands go to `A2`.
9. **Inline primary links:** Attach verified clickable links to primary SEC filings, company IR releases, and macro sources in Sections 2–3 and/or Section 5 (`A5`) so every catalyst is verifiable in one click.
10. **Active verbs, zero filler, explicit falsification triggers:** End `2.1` and each `2.2c` / `3.1` card with a concrete price, yield, or cash-floor level that falsifies or triggers the call.

---

## Table-Free Component Templates (Sections 2–4)

### 0. Section 2.0 — Market headlines (one line each, whole market)
* 🔴 **Macro data:** October CPI rose 0.4% on the month against 0.3% expected; shelter drove it (BLS, 08:30 ET).
* 🟡 **Fed:** Two governors backed further tightening; futures now price a December hike at 60% (CME FedWatch, 15:00 ET).
* 🟢 **Earnings:** Cisco beat with revenue of $14.9B vs $14.6B expected and raised its full-year guide; shares +5% after hours (company release, 16:05 ET).
* 🟡 **Deals:** AstraZeneca agreed to buy Rhythm for $10B in cash (company release, 07:00 ET).
* 🔴 **Single-stock:** Nvidia's board met to consider removing its CEO; shares -8% after hours (Reuters, 17:30 ET) (held).
* 🟢 **Overseas:** Hang Seng +3% on stimulus headlines; Kospi -4.8% on chip weakness (Reuters, close).

### 1. Section 2.2 — Single-Line Ticker Strip (Top Market & Held-Ticker Movers)
* 🟢 **NVDA (Non-Held)** `$148.20 (+4.8%)` · **Why:** Taiwan supply-chain checks cite +18% QoQ Blackwell rack shipments · **Street:** Morgan Stanley `OW` (`$150 -> $168`), BofA reiterates `Buy` · **Ticker Read-Through:** Lifts AI optical & storage peers (`GLW`, `AVGO`, `WDC`).
* 🟢 **GLW (Held)** `$51.40 (+3.9%)` · **Why:** Enterprise optical fiber demand follow-through post-Q3 beat.
* 🔴 **FHTX (Held)** `$2.85 (-7.4%)` · **Why:** `cause unconfirmed` (no `8-K`, `Form 4`, or IR release; `XBI` `-1.8%`).
* 🔴 **SMCI (Non-Held)** `$24.10 (-14.2%)` · **Why:** 10-Q delay and revenue miss · see card 1.

### 2. Section 2.2 — Single-Line Street Upgrades & Downgrades Strip
* 🔴 **JPMorgan on SMCI (Non-Held):** Downgrades `Neutral -> Underweight`, cuts PT `$35 -> $23` · **Thesis & Read-Through:** Form `12b-25` delay and governance overhang shift AI server orders toward `DELL`; no custom ASIC bleed to `AVGO`.
* 🟢 **Held-Ticker Street Sweep:** No public sell-side upgrades, downgrades, or PT changes across held movers as of 12:30 ET.

### 3. Section 2.2 — Market & Filing Deep-Dive Card (Stock-Level Only)
* 🔴 **Super Micro Computer (`SMCI` `-14.2%` to `$24.10`, Non-Held Bellwether) — Form 12b-25 Delay & Server Share Shift:**
  * **Filing & Print Forensics:** Filed SEC Form `12b-25` (NT 10-Q) stating Q1 FY27 `10-Q` remains delayed pending independent governance committee review; preliminary revenue `$5.9B–$6.0B` missed `$6.45B` consensus.
  * **Street Consensus & Analyst Reaction:** JPMorgan downgraded to `Underweight` (`PT $35 -> $23`); Wedbush cut PT `$32 -> $24`, citing customer allocation shifts.
  * **Fundamental Read-Through to Your Tickers:** Direct enterprise AI server share tailwind for held `DELL`; zero impact on hyperscaler custom ASIC networking demand for held `AVGO` and optical cabling for `GLW`.

### 4. Section 3.1 — Stacked 2-Line Position Audit Mini-Card (Contract & Floor B Math)
* 🔴 **FHTX — Short Nov 21 `$2.50P` x 10 (`Spot $2.85 · Cushion +12.3% · Delta -0.28 · 9 DTE · Mark $0.14`)**
  * **Floor B & Rule Check:** `Q3 10-Q` cash `$168.4M` minus current liabilities `$14.2M` / `45.3M` diluted shares (`38.1M` common + `7.2M` pre-funded warrants) = `Floor A $3.40/sh`; minus 2Q burn (`$20.4M`) = `Floor B $2.95/sh` (`0.65 x Floor B = $1.92`). Strike `$2.50` sits above `0.65 x Floor B` with spot inside the `15%` `R4` buffer at `9 DTE` (`R3`) -> **CLOSE / DEFEND**.

### 5. Section 3.3 — Exception-Only R5 Concentration Callouts
* 🟢 **R5 Portfolio Summary:** 47 of 49 underlyings sit below the `8.0%` NAV amber gate (`BIO/SC` sleeve at `18.4%` vs. `25.0%` cap). Active exceptions & dead-collateral flags:
* 🟡 **CAPR (`8.7% of NAV · $30,600 max loss`):** 153 short Dec `$2.00P` (`unpaired` — Nov 27 long `$2.00P` expires before short: `hedge expires first`) · **`$30,600` gross collateral tied up**.
* 🟡 **ACRS (`0.0% of NAV · $0 max loss`):** 233 short Nov `$3.00P` paired with 238 long Dec `$3.00P` (`hedged` calendar) · **`$69,900` gross collateral tied up (`R2` dead pennies — close short legs)**.

### 6. Section 4.1 — Stacked 2-Line Ranked Order Mini-Card
1. 🔴 **#1 REPEAT ×3 — Buy to Close `FHTX` Nov 21 `$2.50P` x 10 @ `$0.15` limit** (`Mid $0.14 · Mark $0.14`)
   * **Feed row:** `FHTX · PUT · $2.50 · 2026-11-21 · -10` · **Rule:** `R3 Time / R4 Defense` · **Cushion:** `+12.3%` · **Cash / Margin impact:** `-$150` debit; frees `$2,500` collateral · **Why:** Inside 15% biotech defense buffer at 9 DTE with strike above `0.65 x Floor B`.
