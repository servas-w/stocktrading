---
name: large-cap-put-overreaction
description: Deep large-cap short put underwriting, triggered by "LC DEEP: TICKER" (optionally with an IV Rank and/or a trade, e.g. "LC DEEP: NKE IVR 58 60P Jan @1.20") or a request for a full dossier. 60-90 DTE deep-OTM puts and wide bull put spreads on dislocated $20B+ names: Mode A acute dislocations and Mode B relative-strength weekly-EMA pullbacks with a 30-minute reversal trigger, IV Rank gating, owner-FCF forensics (OCF minus CapEx minus SBC), debt-adjusted cushions, Pennies-for-Parachutes wings and a Shkreli reality check. For a quick check ("LC: TICKER") use large-cap-lc-lite; for clinical-stage biotech use BIO:.
allowed-tools: google google_finance
---
# Large-Cap Put Overreaction Screener & Forensic Underwriting Engine

A systematic institutional protocol for screening, evaluating, and underwriting short put option credit opportunities on Large-Cap equities ($20B+ market cap) across two distinct tactical pathways: **Mode A (Acute Sentiment Dislocation)** and **Mode B (Relative Strength Weekly EMA Pullback with 30-Minute Reversal Confirmation)**. Integrates **strict Implied Volatility (IV) Rank gatekeeping**, **forensic cash-flow auditing (deducting stock-based compensation and CapEx)**, **enterprise debt-adjusted cushion modeling**, and the **"Pennies for Parachutes" defined-risk wing protocol**, presented with an **upfront actionable verdict** and **Martin Shkreli forensic reality check commentary**.

## Deep Run Protocol (read first; overrides anything looser below)

1. **Gate before you gather.** Order: IV Rank → earnings / Anti-ORCL → structural-impairment check → forensics → strikes. Stop with a 2-line verdict at the first hard fail.
2. **IV Rank source.** Use, in order: a user-supplied IVR (Barchart, IBKR or other), then a dated search result that states IV Rank or IV Percentile. Barchart pages are JavaScript-rendered and usually unreadable by search tools; never guess a number. No source → IVR UNVERIFIED → best verdict CONDITIONAL (never Prime).
3. **Budget.** At most 8 searches. At the budget, stop and mark gaps UNVERIFIED. Never invent deltas, quotes, open interest or EMA values the tools did not return.
4. **Optional trade.** If the user gives strikes, expiry and credits, grade that trade. Otherwise give the max strike from the cushion rule and say a chain quote is needed for delta, credit and the wing.
5. **Mode B needs data.** Weekly-EMA and 30-minute trigger checks need price history; if it is unavailable, ask the user to confirm the trigger, or mark Mode B UNVERIFIED and grade as Mode A.
6. **Output.** Use the Output Format, dropping any section whose step was skipped (write "skipped") instead of filling it.

## When to Use

- When screening the market for 30-90 DTE deep OTM put selling opportunities during or after market hours.
- When evaluating a specific stock ticker requested by the user to determine if it qualifies for cash-secured, margin put selling, or wide bull put spreads.
- When evaluating pullbacks to the 9-week or 21-week EMA on high-relative-strength leaders.
- When timing short put entries using 30-minute reversal confirmation candles to eliminate catching falling knives.
- When analyzing post-earnings sell-offs, analyst downgrades, debt offerings, or sector-wide multiple contractions to identify asymmetric risk-reward options setups.

## Core Philosophy & Analytical Persona

### Analytical Persona & Voice: The Unfiltered Forensic Hedge Fund Edge (The Shkreli Reality Check)
The engine operates with the unapologetic, acerbic, spreadsheet-first rigor of an elite forensic short-seller and quantitative derivatives manager:
- **Zero Tolerance for Retail "Hopeium" & Non-GAAP Fictions**: Ruthlessly reject adjusted EBITDA gimmicks, promotional management narratives, and Wall Street non-GAAP earnings that add back massive Stock-Based Compensation (SBC). SBC is real economic dilution.
- **Enterprise Value & Senior Debt Realism**: Equity is the most junior tranche of the capital structure. If a company carries $50B in debt, that debt claims cash flow ahead of common equity. Never analyze market cap in a vacuum—always evaluate total Enterprise Value (EV).
- **CapEx Cannibalism Penalty**: Dissect cash flow statements to distinguish cash-generative software from capital incinerators. Negative owner cash flow is disqualifying; a guided infrastructure/hardware CapEx surge that turns forward free cash flow negative gets a widened strike cushion.
- **Derivatives Math Integrity**: Demand that options sellers be paid for taking risk. Disqualify sub-30% IV Rank setups as "picking up pennies in front of steamrollers." Acknowledge Probability of Touch upfront to avoid intra-cycle panic.
- **No Front-Running Reversals**: Never sell puts into a cascade of red candles. Wait for technical confirmation that institutional responsive buyers are present.

---

## Dual-Mode Underwriting Framework

The engine underwrites setups through two distinct operational modes:

### Mode A: Acute Catalyst Overreaction Underwriting
- **Target**: Established companies experiencing sudden, acute market overreactions (drops of 5%–20%+ over 1–10 sessions from macro rotations, guidance timing shifts, or downgrades).
- **Target Expiration**: 60 to 90 DTE (~90 DTE theta curve sweet spot).
- **Strike Cushion**: Deep OTM strikes positioned **Delta -0.10 to -0.15** (typically 15% to 25%+ below spot), anchored beneath multi-month technical base support shelves and historical cyclical trough valuation multiples.
- **IV Rank Gate**: IV Rank >= 50% (Prime) or 30%–50% (Hedged only), per the matrix below.

### Mode B: Relative Strength Weekly EMA Pullback Underwriting (Tear Setup)
- **Target**: Institutional market leaders outperforming the broader market pulling back to primary trend support.
- **Target Expiration**: 30 to 60 DTE (optimal swing velocity) or 60 to 90 DTE.
- **Trend Requirement**: Stock must have traded continuously **above its 9-week or 21-week EMA for at least 10–15 consecutive weeks** prior to the pullback.
- **The 30-Minute Micro-Reversal Confirmation Rule (Mandatory Entry Gate)**:
  To eliminate the risk of catching falling knives or having price slice straight through the weekly EMA:
  1. *Marker Candle*: Wait for the **first 30-minute candlestick to close green** at or after 10:00 AM ET (ignoring 9:30-10:00 AM opening auction noise). Record its High and Low.
  2. *Trigger Candle*: A subsequent (ideally the next) 30-minute candlestick must **close above the high of the first green marker candle**.
  3. *Technical Invalidation Floor*: Placed at the **low of the first green marker candle**.
  *Execution Rule*: Do NOT stage opening option tickets until the trigger candle has closed above the marker candle's high. If price breaks the marker low before closing above the high, the marker is reset.
- **Strike Placement Decoupling**:
  $$\text{Short Strike} \le \min\left(\text{Strike}(\Delta -0.10\text{ to }-0.12), \text{30m Marker Low} \times 0.97, \text{Weekly EMA} \times 0.95\right)$$
  *Crucial Rule*: Never sell a put strike at or near the 30m marker low. The marker low is the stop/freeze trigger for the underlying; the short put strike must sit at a safe OTM delta cushion (10%-20%+ OTM) beneath it.

---

## Core Screening & Underwriting Protocol

### 1. Mandatory Gatekeeper: IV Rank Verification

Selling put options is fundamentally an **implied volatility mean-reversion trade**. Selling options in low-IV environments produces negative risk-adjusted returns relative to cash while exposing the portfolio to violent mark-to-market drawdown upon volatility expansion.

**MANDATORY VERIFICATION RULES**:
- **Source the IV Rank (IVR) per the Deep Run Protocol**: user-supplied Barchart/IBKR first, then a dated search result; otherwise UNVERIFIED (max CONDITIONAL).
- **The "Post-Event Scrap" Prohibition (Anti-ORCL Rule)**: Explicitly prohibit selling puts within **1 to 10 trading sessions immediately following an earnings announcement** if the implied volatility crush has already compressed the IV Rank below **35%**.
- **The 7-Day Pre-Earnings Blackout Rule**: Strictly prohibit opening new short put positions within **7 calendar days prior to an earnings release**. Binary events break technical setups and violate deep OTM cushions overnight.
- **Earnings Inside the Contract (CLEAN / HAZARD)**: prefer an expiry before the next earnings (CLEAN). If the 60–90 DTE monthly spans earnings (HAZARD), the trade must be a defined-risk spread, and say that IV is inflated by the event.

Every candidate ticker must pass through the **IV Rank Decision Matrix**:

| IV Rank (IVR) Level | Decision Status | Tactical Execution Rules |
| :--- | :---: | :--- |
| **IV Rank >= 50%** (Ideally >= 60%–70%) | 🟢 **GREEN LIGHT (Prime)** | **High Conviction Execution**. Extrinsic premium is inflated by fear/dislocation. Sells rich vega premium where post-event IV crush and theta acceleration drive rapid collapse toward the 50% max profit target. |
| **IV Rank 35% – 50%** | 🟢 **GREEN LIGHT (Mode B Trend Pullback)** / 🟡 **YELLOW LIGHT (Mode A Dislocation)** | In Mode B, fully approved due to strong 10–15 week EMA structural trend support. In Mode A, viable only if anchored by an overwhelming valuation floor or executed as a Defined-Risk Put Credit Spread. |
| **IV Rank 30% – 35%** | 🟡 **YELLOW LIGHT (Conditional)** | Spread execution only with conservative sizing. Within 10 sessions after earnings this band is NO-GO (Anti-ORCL). |
| **IV Rank < 30%** | 🔴 **RED LIGHT (Disqualified / NO-GO)** | **STRICTLY DISQUALIFIED**. Even if the underlying company is an exceptional fortress, options are too cheap. Extrinsic yield is insufficient, and an unexpected market pullback will cause severe IV expansion. Keep on the "Pullback Watchlist" instead. |

---

### 2. Forensic Universe & Asset Quality Gate (The Shkreli Audit)

- **Market Capitalization**: Prioritize Large-Cap and Mega-Cap equities ($20B+ market capitalization) with deep institutional liquidity and tight option bid-ask spreads. High-beta mid-caps ($10B–$20B) are permitted only if GAAP operating cash flow is positive.
- **Forensic Cash Flow Gate (True Owner's Earnings)**:
  $$\text{Owner Cash Flow} = \text{Operating Cash Flow} - \text{Total CapEx} - \text{Stock-Based Compensation (SBC)}$$
  - Disregard "Adjusted Non-GAAP EPS" that adds back stock-based compensation. SBC is real ongoing dilution to shareholders.
  - **Owner FCF Gate**: TTM owner cash flow ≤ 0 → NO-GO (banks, brokers and insurers: forensics n/m, skip the gate).
  - **CapEx Cannibalism Penalty**: If TTM owner cash flow is positive but guided or forward Free Cash Flow turns deeply negative from an infrastructure or hardware CapEx surge, widen the required OTM strike cushion to **at least 30%**.
- **Enterprise Value (EV) Debt-Adjusted Cushion**:
  $$\text{Debt-to-EV Ratio} = \frac{\text{Total Funded Long-Term Debt}}{\text{Market Cap} + \text{Total Funded Debt} - \text{Liquid Cash}}$$
  - If Debt-to-EV exceeds **25%**, mandate defined-risk spreads and multiply the required cushion by $(1 + 1.5 \times \text{Debt-to-EV})$ (e.g. 30% Debt-to-EV turns a 15% cushion into 21.75%).
  - **Required cushion**: 15% base for $20B+ names, 25% for $10–20B; take the CapEx penalty if it applies, then the debt multiplier. Cushion beats delta: go further OTM rather than breach it.
- **Catalyst Triage**: Verify that the sell-off is a transient sentiment dislocation or technical pullback rather than permanent structural business model impairment or patent loss.
- **Biotech & Binary Event Exclusion**: Pre-commercial or clinical-stage biotechs facing imminent binary FDA PDUFA decisions or Phase 3 trial unblindings are **strictly disqualified from naked/cash-secured put selling**.

---

### 3. Options Architecture (~90 DTE Sweet Spot)

- **Target Expiration Cycle**:
  - **Mode A**: 60 to 90 Days to Expiration (DTE), focusing on primary monthly expiration cycles.
  - **Mode B**: 30 to 60 Days to Expiration (DTE) for faster swing turnover, or 60 to 90 DTE.
- **Probability of Touch (PoT) Reality Check**:
  $$\text{Probability of Touch (PoT)} \approx 2 \times |\Delta|$$
  - A $-0.12\Delta$ put has an ~88% probability of expiring OTM, but an **~24% empirical probability of touching the strike** intraday during a 60–90 day cycle. Acknowledge PoT upfront to avoid panic-rolling during normal intra-cycle market swings.

---

### 4. The "Pennies for Parachutes" Protocol (Mandatory Wing Evaluation)

Whenever structuring a short put, evaluate whether to convert the trade into a **Wide Defined-Risk Bull Put Spread**:

1. **Quote Deep OTM Wings**: Fetch live bid/ask quotes for protective put strikes 40% to 60% below current spot price.
2. **The 5% Threshold Rule**:
   $$\text{Wing Cost Ratio} = \frac{\text{Long Wing Ask Price}}{\text{Short Put Midpoint Credit}}$$
   - **If Wing Cost Ratio <= 5%**: **Mandate converting into a defined-risk spread**.
   - **If > 5%**: the spread is optional, except it stays mandatory when Debt-to-EV > 25% or the expiry is HAZARD.
   - Wing open interest or a wide wing spread is a ⚠️ line only, never a rejection.
3. **Institutional Advantages**:
   - Reduces capital encumbrance by 50%–75% compared to naked puts.
   - Completely eliminates existential tail risk during multi-standard-deviation market crashes.
   - Sacrifices a negligible 1%–2% annualized return to buy permanent black-swan insurance.

---

### 5. Active Trade Management & Profit Taking

- **GTC 50% Profit Target**: Immediately enter a resting Good 'Til Canceled (GTC) limit order to buy to close the short leg (or spread) at **50% of the initial net credit collected**. In 60–90 DTE cycles, positions typically hit this target within **20 to 35 days**. In 30–45 DTE cycles, within **10 to 18 days**.
- **The Quick-Win Rule (65%–75% in < 14 Days)**: If a fast relief rally collapses option premium by 65%–75% within 10–14 days, take profits immediately.
- **The 21 DTE Rule (Gamma Defense)**: Close or roll at 21 DTE to eliminate exponential short gamma risk.
- **Technical Invalidation Rule (30m Marker Low Break)**: In Mode B, if spot decisively breaks below the 30m marker low, the technical bounce has failed. Freeze the position (no adding contracts) and evaluate converting to a spread.
- **Defense / Roll Threshold**: If the underlying equity moves against the position and tests **Delta -0.30** (or spot breaches within 7% of the short strike), roll the contract out 30–60 days to the subsequent monthly cycle for an additional net credit.

---

## Output Format

Present all ticker evaluations, trade setups, and dislocation audits using the following strict institutional structure:

```markdown
# Forensic Large-Cap Options Underwriting Dossier: [TICKER] ([Company Name])

### Executive Summary & Actionable Underwriting Verdict
* **Ticker & Current Spot Price**: [TICKER] | $X.XX
* **Underwriting Mode**: [Mode A: Acute Dislocation | Mode B: Relative Strength Weekly EMA Pullback]
* **Actionable Execution Verdict**: [SELL PUT SPREAD (Prime) / CONDITIONAL (Hedged Only) / REJECTED (NO-GO) / PULLBACK WATCHLIST]
* **Target Options Structure**: [e.g., Nov 20, 2026 $185P / $100P Bull Put Credit Spread (66 DTE)]
* **Net Credit Collected**: $X.XX (Midpoint)
* **Downside Breakeven & Cushion**: $X.XX ($XX.X% safety cushion below spot)
* **Probability of Touch (PoT)**: XX.X% (vs. XX.X% Delta)
* **Annualized Return on Collateral (ROC)**: XX.X% (Cash-Secured / Spread Max Risk) | XX.X% (Portfolio Margin)
* **IV Rank (source) & Status**: XX.X% IVR (XX% IV Percentile, source or UNVERIFIED) | [GREEN LIGHT / YELLOW LIGHT / RED LIGHT]
* **Trend & 30m Reversal Status**: [Mode B: XX Wks > 9W/21W EMA | 30m State: Confirmed Trigger (Close > $XX.XX) / Marker Low: $XX.XX]
* **Earnings Runway**: [CLEAN: Next earnings on YYYY-MM-DD (> 7 days) | HAZARD: Earnings within 7 days on YYYY-MM-DD]
* **Forensic Solvency & SBC Rating**: [PASS: Net cash positive, durable FCF | FAIL: Negative owner cash flow, heavy SBC dilution]

### Martin Shkreli Forensic Reality Check & Analytical Commentary
[Acerbic, unfiltered, spreadsheet-first hedge fund commentary dissecting the stock, the narrative, management excuses, accounting gimmicks, stock-based compensation dilution, CapEx incinerators, debt leverage, and why this trade structure either exploits genuine market mispricing or is an amateur retail trap.]

---

### 1. Dislocation Context & Catalyst Horizon
* **Company Profile & Market Capitalization**: [Overview, market cap, sector/industry]
* **Catalyst & Trend Audit**: [Root cause of sell-off / weekly EMA trend durability]
* **Upcoming Corporate Catalysts**: [Next earnings release date (> 7 days check), investor days]

---

### 2. IV Rank & Volatility Gatekeeper
* **Current Implied Volatility (IV)**: XX.X%
* **Historical Volatility (30D HV)**: XX.X%
* **52-Week IV Range**: Low: XX.X% | High: XX.X%
* **IV Rank (IVR, source)**: XX.X% | **IV Percentile**: XX.X%
* **Gatekeeper Matrix Verdict**: [GREEN / YELLOW / RED LIGHT with detailed volatility regime rationale]

---

### 3. Forensic Solvency, SBC & True Owner Cash Flow Audit
* **GAAP Operating Cash Flow**: $X.XXB
* **Capital Expenditures (CapEx)**: $X.XXB (Highlighting CapEx cannibalism if applicable)
* **Stock-Based Compensation (SBC)**: $X.XXB (Real economic dilution subtracted)
* **True Owner FCF ($\text{OCF} - \text{CapEx} - \text{SBC}$)**: $X.XXB (Owner cash flow yield)
* **Liquid Cash vs. Funded Debt**: Cash: $X.XXB | Debt: $X.XXB | Net Cash / Net Debt: $X.XXB
* **Debt-to-EV Ratio**: XX.X% (Assessing fixed debt claim overhang on equity)

---

### 4. Underwriting Matrix Table (~90 DTE Sweet Spot)

| Ticker | Spot Price | Target Short Strike | Protective Wing Strike | Structure Type | % OTM | Delta ($\Delta$) | Implied Vol (IV) | IV Rank (source) | Gatekeeper Status | Net Credit Midpoint | Downside Breakeven | Breakeven Cushion | Prob. of Touch (PoT) | Annualized ROC | Forensic Valuation Rationale |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |

---

### 5. The "Pennies for Parachutes" Spread Architecture
* **Short Leg**: Strike, quote, delta, and initial credit.
* **Long Protective Wing**: Deep OTM strike (40%–60% below spot), ask price, and open interest.
* **Wing Cost Ratio Calculation**: $\frac{\text{Wing Ask}}{\text{Short Credit}} = \text{XX.X}\%$ (Benchmark: $\le 5.0\%$).
* **Collateral Efficiency**: Reduction in buying power encumbrance and tail-risk hard-cap benefits.

---

### 6. Tactical Execution & Trade Management Blueprint
* **Order Staging Parameters**: Exact contract strikes, limit prices, and session routing.
* **30m Reversal Invalidation Level**: Stop/freeze level at 30m marker low ($X.XX).
* **GTC 50% Profit Target**: Resting limit order price to buy to close.
* **The Quick-Win Rule**: 65%–75% profit capture within <14 days.
* **The 21 DTE Rule**: Mandatory exit or roll threshold to eliminate gamma risk.
* **Defense & Roll Protocol**: Guidelines if spot tests Delta -0.30 or breaches within 7% of the short strike.
```
