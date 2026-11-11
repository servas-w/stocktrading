---
name: readout-review
description: Forensic review of a biotech clinical data readout or regulatory event and what it does to the stock's value. Grades the actual result against the registered endpoint, the trial's own powering bar, standard of care and competitor data; checks the press release for spin; gives the regulatory read; then rebuilds the valuation before vs after (PoS, peak sales, timing, risk-adjusted value, pipeline SOTP, cash, dilution, Floor A/B, bear/base/bull) and compares the stock's move with the modelled move. Ends with Shkreli-style commentary and recommendations for a premium seller. Use whenever the user types "readout: TICKER", "readout deep: TICKER", "readout preview: TICKER", or asks how a trial result, topline data, interim analysis, conference presentation, FDA decision, CRL, AdComm vote or clinical hold reads, whether the data is good, why a biotech moved on data, or how a competitor's data reads through to a name he holds. Not for underwriting the trade itself (hand off to BIO: TICKER).
---

# Readout review

The post-event counterpart of `BIO:`. `BIO:` underwrites the bet before the data; this reads the data after it lands and re-prices the company. Read-only research: never place, modify, cancel or preview orders. Chat reply, no preamble, lead with the verdict.

**Input**: `readout: TICKER` (optionally the drug, trial or event, e.g. `readout: FHTX FHD-909 Ph1`). Default is the most recent data or regulatory event for that company.
- `readout deep: TICKER` adds the statistical teardown, a rebuilt asset-by-asset SOTP with a napkin DCF for the lead, and a competitor data table.
- `readout preview: TICKER` is for an event that has not happened yet: skip to **Preview mode**.
- `readout: TICKER rt: AAA, BBB` adds read-through to the named tickers. Even without `rt:`, check whether the result reads through to a name Wilson holds or watches (same indication, mechanism, target or platform) and say so.
- **Events covered**: topline, interim or final trial data; full data at a conference or in a paper; FDA approval, CRL, AdComm vote, clinical hold, label or REMS change; partner opt-in or termination driven by data. For a purely regulatory event, section 1 becomes "what the agency decided and why" and the statistics checks apply to the data the decision rested on.
- If no data or regulatory event can be found in the last 60 days, say so in the first line and ask which event is meant.

## Ground rules

- **Primary sources first**: the company press release and slide deck, the conference abstract or paper, the ClinicalTrials.gov record, the 8-K and latest 10-Q. News summaries are a last resort and are labelled as such.
- Every number carries its arm, population, timepoint and source. If a figure was not disclosed, write "not disclosed". If it cannot be found, write "unverified". Never fill a gap from memory or from what the class usually shows.
- **The registered endpoint is the result.** Grade against the primary endpoint and analysis population as registered before the data, not the endpoint the press release leads with.
- **The powering assumption is rarely in the registry.** ClinicalTrials.gov gives endpoints, N and dates, not the effect size the trial was powered to detect. Look for it in earlier company slides, the 10-K, a protocol or design paper. If it is not public, write "powering assumption not disclosed" and grade against the target the company stated before the data and the competitor bar instead. Never invent one.
- Quotes are verbatim with the speaker, or they are not quoted.
- Separate what was reported, what management claims, and your inference. Label inference.
- Cross-trial comparisons are indicative only: say what differs (population, line of therapy, endpoint definition, follow-up, assessment method) every time one is made.
- Share counts are always fully diluted: basic + pre-funded warrants + penny warrants + as-converted preferred, from the latest 10-Q plus any later 8-K or 424B5. Broker share counts leave out pre-funded warrants and overstate cash per share.
- Valuation inputs are assumptions. Show each one, its source or reasoning, and what the answer is sensitive to. Never use sell-side price targets as an input.
- **Day-one rule**: topline releases are thin. If the event is less than 48 hours old, mark the report **PRELIMINARY**, list what was not disclosed, and end with the date full data is expected (conference, paper, 10-Q).

## Step 1: Pull the data

Use what is connected; fall back to web search for anything missing and say which source each block came from.

| Need | Use | Notes |
|---|---|---|
| The result | Web search for the press release, 8-K exhibit, slide deck, abstract | Robinhood `get_sec_filing_index` to find the 8-K; its text is often unreadable there, so do not retry a failed filing |
| What was promised | Clinical Trials `search_trials` with `intervention` = the drug name (most reliable: the registered sponsor is often a subsidiary or the partner, so `search_by_sponsor` on the listed company can miss it) -> `analyze_endpoints` with the `nct_id` for primary and secondary endpoints, `get_trial_details` for design, N and dates | The registry shows the current record only: no powering assumption and no change history. Compare the registered primary endpoint with the one in the press release |
| The bar | Web search for standard-of-care and competitor data in the same setting (labels, pivotal press releases, papers); Clinical Trials `search_trials` by `condition` to list competitor trials | Label every cross-trial comparison. Scite `search_literature` is for `deep` only: it requires formal references and a citation report, so follow its rules when used |
| Cash, debt, shares | Robinhood `get_sec_filing_facts` on the latest 10-Q; later 8-K / 424B5 for raises | Fully diluted, per the ground rule |
| Price and reaction | Robinhood `get_equity_quotes`, `get_equity_historicals` (close before the event to latest; after-hours with timestamp) | |
| Options state | Robinhood `get_option_chains` / `get_option_quotes` | IV before vs after if recoverable; else "unverified" |
| Wilson's exposure | Robinhood `get_equity_positions`, `get_option_positions`; Robinhood watchlist "Biotech Sentinel" | Read-only. Covers both the name and read-through names |
| Prior view | Google Drive `search_files` for a prior `BIO:` card, readout note or journal entry on the ticker | If found, show its PoS and floor next to the rebuilt "before"; if they differ, say why. If none, rebuild fresh and say so |

**Floors and SOTP use the `BIO:` definitions.** If the biotech-options-master-engine skill is installed, run its `underwrite.py bio` twice with no `short` block, once for the pre-event state and once for the post-event state, so both skills print the same Floor A / Floor B. Checked against the calculator:
- Pass `catalyst` in **both** runs: the event itself for "before", the **next** catalyst for "after" (A2 = net liquid less 1.5x quarterly burn for the quarters to the catalyst window end, so a missing or different window changes the floor).
- Lead entry: `{"name":..,"lead":true,"pivotal_positive":true|false}`. The lead enters the SOTP only when `pivotal_positive` is true and `catalyst.efficacy_readout` is explicitly false; setting `stage` on the lead does not put it in the floor.
- Base and Bull need both `dcf` and `pos_loa`. The `dcf` keys are `patients`, `biomarker`, `line_share`, `list_price`, `gtn`, `penetration`, `years`, `wacc`, `multiple`; any other key is ignored silently and prints a $0 PV.
- A failed program: remove it, or drop it one `stage` if a rescue trial is credible. Add post-event raises to cash and shares.
- With no `short` the output ends in "FLOORS ONLY", a MODE line and a "MISSING ... expiry" line: ignore those; use the Shares, Floors, SOTP, Napkin DCF and Targets lines.
If the calculator is not available, use the fallback math in section 4 and label the floors "approximate, not the BIO calculator".

## Step 2: Write the report

Tables for numbers, short bullets for everything else. Keep it to what changes the value or a decision.

### 0. Verdict line
One line: **result grade**, **thesis** (STRONGER / INTACT / DAMAGED / DEAD), **Base value per share before -> after**, **floor before -> after**, and the stock's move vs the modelled move (OVERREACTION / UNDERREACTION / FAIR).

Result grade:
- **CLEAN WIN**: primary endpoint met on the registered analysis, effect at or above the trial's powering assumption (or, if undisclosed, the target the company stated beforehand) and competitive with the bar, safety unremarkable.
- **WIN WITH ASTERISKS**: primary met, but at least one of: effect below the powering assumption or the competitor bar, a safety or tolerability signal, reliance on a subgroup or post hoc analysis, single-arm or investigator-assessed data, key numbers withheld.
- **MIXED**: primary missed with a credible key secondary or pre-specified subgroup, one of several co-primaries met, or an inconsistent dose response.
- **FAIL**: primary missed and nothing pre-specified rescues it, or a safety finding that ends the program.
- **UNINTERPRETABLE**: too little disclosed to grade. Say exactly which numbers are needed.

### 1. What actually happened
- **Trial in one line**: phase, design (randomized? blinded? control?), N per arm, population and line of therapy, primary endpoint and timepoint, as registered.
- **Result table**: endpoint | treatment | control | difference | p-value / CI | powering assumption | met?  Primary first, then key secondaries in their hierarchy.
- **Against the bar**: the same endpoint for standard of care and the best competitor, with the caveats on comparability.
- **Safety table**: discontinuations due to AEs, grade 3+ or serious AEs, deaths, AEs of special interest for the class, dose reductions.
- **Quality checks** (report the ones that fire, with the number):
  - Analysis population: ITT vs modified ITT vs per-protocol vs evaluable; how many randomized patients are missing from the headline number.
  - Dropouts and missing data, and how they were handled.
  - Control-arm behaviour: placebo or standard-of-care response vs history (an underperforming control flatters the delta).
  - Dose response: present, flat or inverted.
  - Assessment: blinded independent central review vs investigator-assessed. Haircut investigator-assessed response rates 15-20%.
  - Endpoint type: hard outcome vs surrogate, and whether regulators have accepted that surrogate in this indication.
  - Multiplicity: was the win inside the pre-specified hierarchy with alpha left, or nominal?
  - Durability and follow-up: median follow-up, data maturity, how many patients are still on drug.
  - Subgroups: pre-specified and stratified, or found afterwards.
  - Interim vs final: stopping boundary, information fraction, what the DMC actually said.
- **What was not disclosed**: list it. Omissions in a topline release are deliberate until shown otherwise.

### 2. Spin check
- Headline claim vs the registered primary endpoint and population. Flag any change of endpoint, analysis population, timepoint or comparator, and whether it was made before unblinding. Evidence comes from earlier press releases, 10-K trial descriptions and the registry's change history if it can be read; the current registry record alone cannot show a change, so if no earlier description is found write "endpoint history unverified".
- Language tells: "clinically meaningful", "numerical trend", "in patients who", "nominal p", "encouraging", "supports advancement" with no number attached.
- What management said on the call vs what the table shows; any question that got a non-answer.
- Timing tells: data released after hours, bundled with a financing, or cut down to a subset; a raise priced within days.

### 3. Clinical and regulatory read
- **Is it approvable or registrational as it stands?** If not, what is the next trial, how big, how long, how much.
- **Path and dates**: next FDA interaction, filing, PDUFA, AdComm likelihood, confirmatory requirements, accelerated vs full approval.
- **Label and market**: which patients, which line, monotherapy or combination, boxed-warning or REMS risk. Has the addressable population grown or shrunk vs the pre-event assumption?
- **Competitive rank** after this data on efficacy, safety, convenience and timing: best-in-class, me-too, or behind.
- **Partner and strategic read**: opt-in, milestone triggered or lost, makes the company a target or removes the bid.

### 4. Valuation and SOTP: before vs after
This is the core of the report. Build both columns even when the "before" has to be reconstructed.

**a. Lead asset (the program that read out)**

| Input | Before | After | Why it moved |
|---|---|---|---|
| Stage / next gate | | | |
| Likelihood of approval (LoA) | | | event resolved; data quality |
| Peak sales | | | label breadth, competitive rank, price |
| Launch year | | | extra trial or faster path |
| Unrisked PV | | | |
| Risk-adjusted PV per FD share | | | |

- **LoA mechanics.** LoA = the product of every transition still ahead. Baselines: Phase 1->2 solid tumor 38-42%, heme 45-52%, non-oncology 55-65% · Phase 2->3 unselected solid tumor 22-28%, biomarker-selected 35-42%, immunology 30-38%, rare genetic 45-55%, CNS 18-25% · Phase 3->filing oncology 50-60%, non-oncology 60-70% · filing->approval 85-90%. A positive readout sets that transition to 1 and leaves the later ones; then adjust the *next* transition for what the data showed (strong effect and clean safety up, asterisks down, by no more than 20% relative per factor, and say which). A failed primary sets LoA to 0 unless a pre-specified subgroup supports a new trial, in which case the asset drops one stage and restarts at that baseline. A marginal or single-arm win: probability of approval sits 20-40% below the probability of statistical success.
- **Napkin DCF.** Patients = incidence or prevalence x % eligible (biomarker, line of therapy). Net price = list x (1 - gross-to-net): US 30-40% off, ex-US 60-75% off. Peak revenue = patients x penetration (15-30%) x net price. Unrisked PV = peak x 2.5 / (1 + 12-15%)^years to peak. Risk-adjusted PV = unrisked PV x LoA. State every input.

**b. Rest of the pipeline (read-through)**
One row per program and per other indication of the same molecule: stage, partner, value before, value after, and the reason. Same molecule in another indication, same target, same mechanism or same platform all move on this data; unrelated programs do not. Without a program-level DCF use the stage ladder as unrisked value (preclinical $15M, Phase 1 $75M, Phase 2 with proof of concept $150M, Phase 3 $300M) and keep 55% if a top-tier pharma partner holds it, 17.5% if unpartnered. The ladder is an assumption; label it.

**c. Cash, debt and dilution**
- Net liquid assets now, quarterly burn, runway before vs after (a win usually adds a bigger trial and a launch build; a fail usually triggers cuts).
- **The financing that follows.** After good data: expect a raise. State shelf and ATM capacity, the likely size against the next trial's cost, and the dilution at the current price. After bad data: runway, covenant or acceleration risk on any debt (if failure lets a lender accelerate and cash is at or below debt plus the covenant minimum, the floor is $0), reverse-split or listing risk, strategic alternatives.
- Milestones triggered or forfeited, royalties already sold.

**d. Floors and targets, fully diluted**

| Per share | Before | After |
|---|---|---|
| Net cash | | |
| SOTP residual | | |
| Floor B | | |
| Floor A | | |
| Bear / Base / Bull | | |

- Use the `BIO:` calculator for both columns when available (Step 1). Fallback, same definitions: A1 = net liquid / FD shares; A2 = max(0, net liquid - 1.5 x quarterly burn x quarters to the next catalyst (minimum 1)) / FD shares; Floor A = A1 + SOTP residual per share; Floor B = A2 + SOTP residual per share. If debt exceeds cash, the SOTP fills that hole before equity gets anything. Label fallback floors approximate.
- Bear = Floor B. Base = (net liquid + SOTP ex-lead + lead risk-adjusted PV) / FD shares. Bull = same with the lead unrisked. The lead's DCF replaces its ladder credit; never count both.
- **The lead enters the floor only when de-risked**: positive pivotal data and no further efficacy readout pending. After a positive early or mid-stage readout the lead is still the bet and stays out of the floor, so expect the floor to move little on a Phase 1 or 2 win: the gain shows up in Base and Bull. Say so, so a flat floor is not read as "nothing changed".
- The distressed floor also depends on how far away the next catalyst is (more quarters of burn to fund lowers it). When the floor moves for that reason and not because of the data, say which.

**e. Market reaction vs modelled move**
- Modelled change = value per share after - before (Base case), plus the dilution effect of the expected raise.
- Actual change = close before the event to the latest price, with timestamp.
- **Market-implied odds before the event** (rough): (price before - fail value) / (success value - fail value). Success value = Base with the event transition set to 1; fail value = Floor B with the lead at zero (or one stage down if a rescue is credible). One of the two is the scenario that happened; build the other as the counterfactual. Say whether the market was pricing a win, a coin flip or a fail, and whether the move is consistent with that.
- Verdict: OVERREACTION, UNDERREACTION or FAIR, with the gap in dollars per share. If enterprise value is above the unrisked PV, say it is priced for perfection.

### 5. Read-through to other names
For each `rt:` ticker and any held or watched name affected: the link (indication, target, mechanism, platform, shared partner), direction and rough size of the effect on its lead PoS, and whether the market has already moved it. One or two lines each. A competitor's win can be bad (crowded market, higher bar) or good (mechanism validated): say which and why.

### 6. Shkreli-style commentary
A blunt, forensic take on everything above in the style of Martin Shkreli's stream analysis: read the table not the headline, name the trick if there is one, say whether the drug works and whether it matters commercially, follow the cash to the raise that is coming, and say plainly what the company is worth now. Dry, sharp, irreverent, first-principles; roast the data and the spin, not people. 5-8 punchy lines covering the result, the spin, the regulatory path, the valuation and the stock's move. This is commentary written in that style, not his words: never attribute quotes or positions to him.

### 7. Recommendations
- **Stance on the stock**: accumulate / hold / trim / avoid / short candidate, with the reason and what would change it.
- **Next catalysts with dates**: full data, FDA meeting, next trial start, next readout, cash runway end. Flag any that slipped.
- **Kill triggers**: the 2-3 facts that would break the new thesis (a safety update, an FDA request for another trial, a raise below a stated price, competitor data on a stated date).
- **Options angle** for a premium seller: IV after the binary (crushed or still elevated because another event is close), where the new Floor B sits against the listed strikes, the dilution overhang, and when the next binary falls relative to a 60-90 DTE window. Flag a setup or say there is none. Do not quote a strike or a size here: hand off to `BIO: TICKER` (or `BIO DEEP: TICKER`) for the trade. Two standing rules: never short or buy bearish options on a name already priced near its cash floor, and a rejected put sale is not a reason to buy puts; the default is to do nothing.
- **If Wilson holds it or a read-through name**: what the result means for each open position (short strikes vs the new floor, held lots vs the new Base), in one or two lines.

End with a **Sources** list (every source with a link, and one line on anything marked unverified or not disclosed).

Footer: "Points to weigh, not orders."

## Deep mode additions (`readout deep:`)

- **Statistical teardown**: powering assumptions vs observed (effect size, variance, event rate), what the confidence interval excludes, fragility (how many events or responders flip the result), the multiplicity plan, sensitivity analyses reported or missing, and whether the control arm matched history.
- **Competitor table**: the same endpoint across every relevant trial with population, line, N, follow-up and assessment method side by side.
- **Full SOTP rebuild**: a napkin DCF per material program, not the ladder, and a sensitivity grid for the lead (LoA x peak sales) in dollars per share.
- **Financing model**: likely raise size, price and resulting share count; value per share after dilution.

## Preview mode (`readout preview: TICKER`)

Before the data: set the bar so the result can be graded without hindsight.
- The trial as registered: design, N, primary endpoint, analysis population, powering assumption, expected timing and whether guidance has slipped.
- The bar in numbers: what CLEAN WIN, WIN WITH ASTERISKS, MIXED and FAIL each look like on the primary endpoint and on safety, against standard of care and the best competitor.
- Event PoS from the baselines above with the adjustments stated, and the market-implied odds from the current price.
- Value per share in each scenario (win / mixed / fail), the floor in each, and the financing that follows each.
- What to look for in the first five minutes of the press release: the registered endpoint, the population, the p-value, discontinuations, and what is missing.
- The trade before the event belongs to `BIO: TICKER`; do not underwrite it here.
End with the Shkreli-style commentary and recommendations, clearly marked as pre-event.
