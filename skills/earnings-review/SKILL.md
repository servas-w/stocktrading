---
name: earnings-review
description: Forensic review of a company's latest earnings print and call. Returns a beat/miss scorecard, green and red flags in the numbers and in the call, a growth-story-intact verdict, a peer comparison, a valuation read (what is priced in), blunt Shkreli-style commentary, and recommendations including an options angle for a premium seller. Use whenever the user types "earning: TICKER", "earnings: TICKER", "ER: TICKER", "earning deep: TICKER", "earning preview: TICKER", or asks how a company's quarter was, whether the earnings were good, what the call said, or whether the thesis survived the print, even if the message is just a ticker plus "earnings?". Not for placing trades or for full put underwriting (hand off to LC: or BIO:).
---

# Earnings review

Read-only research. Never place, modify, cancel or preview orders. Chat reply, no preamble, lead with the verdict.

**Input**: `earning: TICKER` (optional quarter, e.g. `earning: NVDA Q3`). Default is the most recently reported quarter.
- `earning deep: TICKER` adds an 8-quarter trend table, segment detail and a reverse DCF.
- `earning preview: TICKER` is for a print that has not happened yet: skip to **Preview mode** at the bottom.
- If the company has not reported in the last 100 days, or reports within the next 7 days, say so in the first line.

## Ground rules

- Every number carries its period and source. If a figure cannot be found, write "unverified"; never estimate silently and never fill a gap from memory.
- Call quotes must be verbatim from the transcript, with the speaker. No transcript available: say so and mark the call section "transcript unavailable" rather than reconstructing it from news summaries.
- Compare like with like: GAAP to GAAP, adjusted to adjusted, same fiscal period, consensus as it stood before the print.
- Separate facts (reported), management claims (said on the call) and your inference. Label inference.
- A flag needs evidence and a size ("DSO 71 -> 84 days", not "receivables look high"). No evidence, no flag.

## Step 1: Pull the data

Use what is connected, in this order, and fall back to web search and the company's IR page for anything missing.

| Need | First choice | Fallback |
|---|---|---|
| Transcript, slides, press release, 10-Q/8-K | Quartr: `search_companies` -> `list_events` -> `read_transcript`, `get_event_summary`, `list_documents`/`read_document` | Alpha Vantage `EARNINGS_CALL_TRANSCRIPT`; Robinhood `get_sec_filing_index`/`get_sec_filing`; web |
| Reported financials, 8 quarters | Quartr `get_financials` | Zacks `get_income_statement`/`get_balance_sheet`/`get_cash_flow`; Alpha Vantage `INCOME_STATEMENT`/`BALANCE_SHEET`/`CASH_FLOW` |
| Actual vs consensus, surprise history, estimate revisions | Alpha Vantage `EARNINGS`, `EARNINGS_ESTIMATES`; Robinhood `get_earnings_results`; IBKR `get_earnings_insight` | Zacks `get_zacks_metrics`, `get_company_snapshot` |
| Peers | Quartr `list_related_companies`; Zacks `compare_stocks` | web |
| Price, reaction, multiples | Robinhood `get_equity_quotes`, `get_equity_fundamentals`, `get_equity_historicals`, `get_equity_analyst_ratings` | Twelve Data `get_statistics`, `get_quote` |
| Options state | Robinhood `get_option_chains`/`get_option_quotes`; IBKR `get_option_data` | skip and say "IV unverified" |
| Does Wilson hold it | Robinhood `get_equity_positions`, `get_option_positions` | skip |

Also read the **prior quarter's** transcript (or its summary) so tone and guidance can be compared quarter on quarter. Peer transcripts are only needed for the two or three closest competitors, and only their comments on the shared end market.

## Step 2: Write the report

Keep it to what changes a decision. Tables for numbers, short bullets for flags. Default run fits in roughly two screens; `deep` can run longer.

### 0. Verdict line
One line: **quarter grade A-F**, **story: INTACT / WOBBLING / BROKEN**, **valuation: cheap / fair / rich / priced for perfection**, and the stock's reaction (print-day move vs the option-implied move, if known).

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
- Multiples that fit the business (EV/Sales, EV/EBITDA, P/E, P/FCF, FCF yield; biotech: EV vs cash and pipeline) vs its own 5-year range and vs peers.
- Estimate revisions since the print: direction and size for next quarter and next fiscal year.
- **What is priced in**: the growth and margin the current price requires (quick reverse DCF or multiple-on-forward-FCF), stated in one sentence, and whether this quarter makes that easier or harder to hit.
- Bull / base / bear value with the one assumption that separates them.

### 7. Shkreli-style commentary
A blunt, forensic take on everything above, in the style of Martin Shkreli's stream analysis: follow the cash, read the filing not the press release, name what the market is afraid of and whether it is right, call out financial engineering and management spin, state plainly whether this is a real business at this price. Dry, sharp, irreverent, first-principles; roast the company and the numbers, not people. 5-8 punchy lines covering the print, the call, the story, the peers and the price. This is commentary written in that style, not his words: never attribute quotes or positions to him.

### 8. Recommendations
- **Stance**: buy the dip / hold / trim / avoid / short candidate, with the reason and what would change it.
- **Kill metrics**: the 2-3 numbers to check next quarter and the level at which the thesis is dead.
- **Options angle** (Wilson sells premium: 60-90 DTE deep-OTM puts and wide defined-risk credit spreads, IVR >= 50 gate): is IV still elevated or already crushed, is the sell-off an overreaction or a repricing, where the valuation floor sits and which strike zone is below it. If it looks like a setup, say so and hand off to `LC: TICKER` (large-cap) or `BIO: TICKER` (biotech) for full underwriting; do not size a trade here. A rejected put sale is not a long put.
- **If Wilson holds it**: what the print means for the open position (short strikes vs new floor, held lots), in one or two lines.
- **Dates**: next earnings date, investor day, and any catalyst before then.

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
