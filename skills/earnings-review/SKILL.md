---
name: earnings-review
description: Forensic review of a company's latest earnings print and call. Returns a beat/miss scorecard, green and red flags in the numbers and in the call, a growth-story-intact verdict, a peer comparison, a valuation read (what is priced in), blunt Shkreli-style commentary, and recommendations including an options angle for a premium seller. Use whenever the user types "earning: TICKER", "earnings: TICKER", "ER: TICKER", "earning deep: TICKER", "earning preview: TICKER", or asks how a company's quarter was, whether the earnings were good, what the call said, or whether the thesis survived the print, even if the message is just a ticker plus "earnings?". Not for placing trades or for full put underwriting (hand off to LC: or BIO:).
---

# Earnings review

Read-only research. Never place, modify, cancel or preview orders. Chat reply, no preamble, lead with the verdict.

**Input**: `earning: TICKER` (optional quarter, e.g. `earning: NVDA Q3`). Default is the most recently reported quarter.
- `earning deep: TICKER` adds an 8-quarter trend table, segment detail, peer call read-across and bull / base / bear.
- `earning preview: TICKER` is for a print that has not happened yet: skip to **Preview mode** at the bottom.
- If the company has not reported in the last 100 days, or reports within the next 7 days, say so in the first line.

## Ground rules

- Every number carries its period and source. If a figure cannot be found, write "unverified"; never estimate silently and never fill a gap from memory.
- Call quotes must be verbatim from the transcript, with the speaker. No transcript available: say so and mark the call section "transcript unavailable" rather than reconstructing it from news summaries.
- Compare like with like: GAAP to GAAP, adjusted to adjusted, same fiscal period, consensus as it stood before the print.
- Separate facts (reported), management claims (said on the call) and your inference. Label inference.
- A flag needs evidence and a size ("DSO 71 -> 84 days", not "receivables look high"). No evidence, no flag.

## Step 1: Pull the data

Tool names below were checked against the live connectors. Use what is connected; fall back to web search and the company's IR page for anything missing, and say which source each block came from.

| Need | Use | Notes |
|---|---|---|
| Which quarter, report date, next date | Robinhood `get_earnings_results` | Latest row with a non-null `eps.actual` is the reported quarter; the null row is the next print (tentative if `verified` is false) |
| Call transcript | Alpha Vantage `EARNINGS_CALL_TRANSCRIPT` (`quarter` = fiscal `YYYYQn`) | About 12k tokens per call, with per-paragraph sentiment. Quartr (`search_companies` -> `list_events` -> `read_transcript`) only if the account has Quartr Pro; it returned `subscription_required` when this skill was written, so do not retry it after one failure |
| Press release, 10-Q, slides | Robinhood `get_sec_filing_index` / `get_sec_filing`; web for the IR deck | KPIs such as RPO, ARR, backlog and segment data live here, not in the standardized statements |
| Statements, 8 quarters | Zacks `get_income_statement` / `get_balance_sheet` / `get_cash_flow` (`period: "Q"`, `periods: 8`); Alpha Vantage `INCOME_STATEMENT` / `BALANCE_SHEET` / `CASH_FLOW` | **Quarterly cash flow is fiscal year-to-date.** Subtract the prior YTD figure to get a single quarter before computing FCF, and say so |
| Consensus, surprise, revisions | Zacks `compare_stocks` section `SEH` (EPS surprise history), `ETR` / `ERV` (revisions); Alpha Vantage `EARNINGS_ESTIMATES` (EPS and revenue consensus, 7/30/60/90-day-ago values) | See the consensus rule below. `EARNINGS_ESTIMATES` returns ~40 periods; read only the rows needed |
| Peers | Zacks `compare_stocks` (2-5 tickers; section `PEERS` to find them, default `FOV` for margins) | One section per call |
| Price, reaction, multiples | Robinhood `get_equity_quotes`, `get_equity_fundamentals`, `get_equity_historicals` | Reaction = close before the print to close after |
| Recap, historical reactions | IBKR `search_contracts` -> `search_earnings_insights` -> `get_earnings_insight` | Never guess an insight id; an empty search means no insight exists |
| Implied move and IV | Robinhood `get_option_chains` / `get_option_quotes`, `get_option_historicals` for the ATM straddle at the close before the print | If it cannot be reconstructed, write "implied move unverified". IV-gate math belongs to `LC:` |
| Does Wilson hold it | Robinhood `get_equity_positions`, `get_option_positions` | Read-only |

**Consensus rule.** Sources disagree (for one checked quarter the EPS estimate was 1.89 on Robinhood and 1.94 on Zacks and Alpha Vantage, which turns the same print into a 10.6% or a 7.7% beat). Pick one source for the whole scorecard, name it in the table header, and never mix sources within a row. Revenue consensus comes from Alpha Vantage `EARNINGS_ESTIMATES` or Zacks; Robinhood has EPS only.

**Depth and budget.** Default: this quarter's transcript in full, the prior quarter's transcript for tone and guidance, statements for 8 quarters, peers by numbers only. `deep` adds the two closest peers' transcripts (their comments on the shared end market) and segment tables. If the print is less than 48 hours old, the transcript, 10-Q or post-print revisions may be missing: mark the report **PRELIMINARY** and list what is not yet available.

## Step 2: Write the report

Keep it to what changes a decision. Tables for numbers, short bullets for flags. Default run fits in roughly two screens; `deep` can run longer.

### 0. Verdict line
One line: **quarter grade A-F**, **story: INTACT / WOBBLING / BROKEN**, **valuation: cheap / fair / rich / priced for perfection**, and the stock's reaction (print-day move vs the option-implied move, if known).
- Grade: **A** beat on revenue and EPS, guide raised above street, cash conversion confirms it, no red flag. **B** beat with an in-line guide or one minor red flag. **C** in line or mixed, or a low-quality beat (one-offs, tax, share count). **D** miss on revenue or a guide cut. **F** miss plus a cut plus a balance-sheet or disclosure red flag.
- Story: **BROKEN** if any pillar in section 4 is broken; **WOBBLING** if any pillar wobbles or its KPI has deteriorated two quarters running; otherwise **INTACT**.

### 1. Scorecard
Table: revenue, gross margin, operating margin, EPS (GAAP and adjusted), FCF, plus the 2-3 KPIs that matter for this business (see sector notes). Columns: actual, consensus, beat/miss %, YoY, QoQ. Then guidance: new guide vs prior guide vs street, and whether the raise is smaller than the beat (a hidden cut for the remaining quarters).

### 2. Numbers: green and red flags
Check each of these and report only the ones that fire, green or red, with the number:
- **Quality of the beat**: organic vs acquired vs FX; price vs volume; one-offs, tax rate, lower share count or below-the-line items doing the work; pull-forward from next quarter.
- **Cash vs earnings**: OCF and FCF vs net income; owner FCF (OCF - capex - SBC); GAAP to adjusted gap and whether it is widening; capitalised costs.
- **Balance sheet tells**: DSO and receivables vs revenue growth; inventory vs sales; deferred revenue, RPO, backlog, book-to-bill; payables stretch; debt, maturities, interest cover; cash runway if burning.
- **Dilution and capital allocation**: share count trend, SBC % of revenue, buybacks funded by debt, ATM or shelf activity, insider selling around the print.
- **Margin direction**: gross and operating margin trend, incremental margin, where the leverage or the squeeze comes from.
- **Disclosure changes**: KPI dropped, redefined or re-segmented; guidance range widened; metric moved from quarterly to annual; restatement, auditor or CFO change.

### 3. Call: green and red flags
- **Tone delta vs last quarter**: what language is new ("elongated cycles", "macro", "prudent", "back-half weighted") and what disappeared.
- **Prepared remarks vs Q&A**: where the script and the answers diverge.
- **Dodges**: questions answered with a different question, "we don't guide to that", or a handoff. Quote the question and the non-answer.
- **Analyst pushback**: what the sell side kept returning to. Three analysts asking the same thing is the real story of the call.
- **Guidance philosophy**: sandbagging track record (beats vs own guide over the last 4-8 quarters) vs stretching.
- **Specifics vs adjectives**: management giving numbers, customers and dates is green; "strong momentum" without a number is not.
Give 2-4 verbatim quotes that carry the most information.

### 4. Is the growth story intact?
State the bull thesis as 3 pillars, each tied to one measurable KPI. For each: **Intact / Wobbling / Broken**, the evidence this quarter, and the 4-quarter trend. Then the question the next print must answer. If the story the market tells and the story the numbers tell differ, say which one you believe and why.

### 5. Versus competitors
Table of 3-5 closest peers: latest-quarter revenue growth, gross and operating margin, beat/miss and guide direction, and one valuation multiple. Then: who is taking share, whether this company's result is company-specific or industry-wide (what peers said about the same end market), and where it ranks.

### 6. Valuation now
A quick read, not a full model. The full valuation (reverse DCF, owner-FCF floor, own-history trough multiples) belongs to `VALU: TICKER`; biotech goes to `BIO: TICKER`.
- Current multiples that fit the business (forward P/E, P/S, P/FCF or FCF yield; biotech: EV vs cash) vs peers, from the same source and date for every name in the table.
- Own-history comparison only if the history was actually pulled; otherwise write "history unverified -> VALU".
- Estimate revisions since the print: direction and size for next quarter and next fiscal year, with the as-of dates.
- **What is priced in**, in one sentence: the growth the current multiple needs, and whether this quarter makes that easier or harder to hit. Label it a rough read.
- `deep`: add bull / base / bear with the one assumption that separates them, or end with *-> VALU DEEP: TICKER*.

### 7. Shkreli-style commentary
A blunt, forensic take on everything above, in the style of Martin Shkreli's stream analysis: follow the cash, read the filing not the press release, name what the market is afraid of and whether it is right, call out financial engineering and management spin, state plainly whether this is a real business at this price. Dry, sharp, irreverent, first-principles; roast the company and the numbers, not people. 5-8 punchy lines covering the print, the call, the story, the peers and the price. This is commentary written in that style, not his words: never attribute quotes or positions to him.

### 8. Recommendations
- **Stance**: buy the dip / hold / trim / avoid / short candidate, with the reason and what would change it.
- **Kill metrics**: the 2-3 numbers to check next quarter and the level at which the thesis is dead.
- **Options angle** (Wilson sells premium: 60-90 DTE deep-OTM puts and wide defined-risk credit spreads behind an IV gate): is IV still elevated or already crushed after the print, is the sell-off an overreaction or a justified repricing, and does the next earnings date fall inside a 60-90 DTE window. If it looks like a setup, say so and hand off: `VALU LC: TICKER` for the floor, then `LC: TICKER` (large-cap) or `BIO: TICKER` (biotech) for the IV gate, strike and sizing. Do not quote a strike, a floor or a size here. A rejected put sale is not a long put.
- **If Wilson holds it**: what the print means for the open position (short strikes vs new floor, held lots), in one or two lines.
- **Dates**: next earnings date, investor day, and any catalyst before then.

End with a **Sources** list: every source used, with links (Zacks links per ticker in the form `https://www.zacks.com/stock/quote/TICKER?utm_source=zacks_mcp`), and one line on anything marked unverified.

Footer: "Points to weigh, not orders."

## Sector notes

Swap the KPIs and the flags to fit the business:
- **Clinical-stage biotech** (little or no revenue): the "quarter" is cash, burn, runway in quarters, dilution (ATM use, shelf, warrants), pipeline timeline slips, enrolment, partner payments. Story pillars are catalysts, not growth rates. Valuation is EV vs cash plus risk-adjusted pipeline.
- **Software / SaaS**: ARR, NRR, RPO and cRPO, billings, customer counts by tier, Rule of 40, SBC.
- **Semis / hardware**: inventory days (own and channel), backlog, lead times, customer concentration, gross margin by mix.
- **Banks / insurers**: NII and NIM, deposit beta, credit costs and reserves, CET1, combined ratio; skip EV multiples, use P/TBV and ROTCE.
- **Consumer / retail**: comps (traffic vs ticket), inventory, promotions, gross margin, store economics.
- **Energy / materials**: realised price, volumes, unit cost, capex, hedges, FCF at strip.

## Preview mode (`earning preview: TICKER`)

Before the print: date and time, consensus and the whisper if findable, what moved estimates this quarter, peers that already reported and what they imply, the 3 numbers that decide the reaction, option-implied move vs the average and maximum move of the last 8 prints, and the IV state for a premium seller (sell before for the crush, or wait for the overreaction after). End with the same Shkreli-style commentary and recommendations, clearly marked as pre-print.
