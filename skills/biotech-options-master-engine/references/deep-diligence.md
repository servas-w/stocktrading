# Deep Diligence Modules (load only when a Mode B/C verdict hinges on PoS, DCF, pipeline or management, or when asked)

Contents: 1 Tool plan · 2 PoS model · 3 Biostatistics gatekeeper · 4 Napkin DCF · 5 Pipeline SOTP · 6 Management call forensics · 7 Dilution & financing · 8 Mode C decision table · 9 Feeding the calculator

## 1. Tool plan (≈ +6 calls; stop when the verdict stops moving)
- Trial design: Clinical Trials `search_trials` (sponsor, phase, status, page_size ≤ 5) → `analyze_endpoints(nct_id)` for the primary endpoint and comparator. Do not call `get_trial_details` (it lists every site).
- Efficacy data and review type (BICR vs investigator): one `web_search_fast` on the latest readout, `web_fetch` the press release or conference abstract for the review-type detail.
- Class / MoA attrition: one Elicit `search_papers` query ("clinical trial history of TARGET inhibitors Phase 2 and Phase 3 outcomes") — literature search is Elicit's purpose, and it beats a generic web search for attrition-rate meta-analysis.
- Management: one `web_search_fast` for the latest earnings call Q&A / transcript recap (Quartr `read_transcript` if the full call needs a close read).
- Epidemiology for the DCF: one `web_search_fast` for incidence/prevalence of the indication.
One focus per search; cite every source inline.

## 2. PoS model
Final PoS = baseline × Π(1 + factor), then apply caps. Baselines are in SKILL.md. This is the **event PoS** (the transition the in-contract readout decides). For the DCF, chain it: LoA = event PoS × each later transition baseline (e.g. Ph2 readout 0.25 × Ph3→filing 0.55 × approval 0.88 = 0.12): pass `pos_loa_after: [0.55, 0.88]` and the calculator multiplies in the event PoS.

| # | Factor | Range |
|---|---|---|
| 1 | Target validation / human genetics / same-MoA precedent / synthetic lethality | ±5–15% |
| 2 | Biomarker enrichment (selected vs all-comers) | ±10–15% |
| 3 | Prior efficacy signal vs standard of care (ORR, CR, DCR) | ±10–20% |
| 4 | Safety / therapeutic window (discontinuations, Gr3/4, prior holds) | −5 to −25% |
| 5 | Design rigor (randomized double-blind vs single-arm open-label) | ±5–10% |
| 6 | Tier-1 pharma partnership / co-development / opt-in / equity | +5–12% |
| 7 | Tier-1 specialist funds (≥ 2 of Baker Bros, OrbiMed, RA, Perceptive, Deerfield, BVF, RTW, EcoR1) holding ≥ 15% FD **and** in a financing within 12 months | +3–5% max |

Caps and penalties (apply after the product):
- Target class with > 80% historical failure → cap 20–25%, whatever the early ORR.
- Silent protocol amendment (late N increase, endpoint reshuffle, timeline creep) without an 8-K → −10 to −15%.
- Dual hurdle: for marginal, single-arm or compromised designs, P(approval) is 20–40% below P(stat-sig); pass `p_statsig` and the calculator prints P(approval) at −30%.
- Passive indexers and stale 13F positions earn nothing (see §7 traps).

## 3. Biostatistics & trial-rigor gatekeeper
1. **Central vs investigator review:** investigator-assessed ORR/DoR/CBR → haircut 15–20% before scoring factor 3.
2. **Surrogate vs hard endpoint:** check FDA precedent for accelerated approval on that surrogate in that indication. If confirmatory OS is required and crossover will dilute it → −10 to −15%.
3. **Placebo / standard-of-care hurdle** (non-onc, autoimmune, CNS, pain, NASH, IBD, asthma): historical placebo response > 25–30% → verify ≥ 80% power at α 0.05 for the needed delta; if not, factor 5 negative.
4. **Event-delay trap:** event-driven trial ≥ 6–12 months past projected unblinding without a positive DMC action is not proof the drug works — the modern control arm is likely outliving historical assumptions. Stress control survival +25–50%; if the delta narrows or vanishes → −15 to −25% and classify as likely failure.
Anything that cannot beat real-world standard of care at p < 0.05 is treated as a failure case.

## 4. Napkin DCF (Mode B and pipeline value; never use sell-side targets)
- Patients = incidence or prevalence × % biomarker-positive × % eligible for the line of therapy.
- Net price = list × (1 − GTN): US GTN 30–40%; ex-US / China 60–75% (NRDL tenders, single payer).
- Peak revenue = patients × penetration (15–30%) × net price. Unrisked PV = peak × 2.5 ÷ (1 + WACC 12–15%)^years to peak.
- Risk-adjusted PV/share = unrisked PV × **LoA** ÷ FD shares. LoA = cumulative approval odds from today (event PoS × every later transition baseline), never the event PoS alone.
- **Rule:** market EV > unrisked PV → priced for perfection → Mode B disqualified (calculator flags it).
- Targets: Bear = Floor B (A2 + SOTP; SOTP netted against debt first) · Base = (net liquid + SOTP ex-lead + lead PV × LoA) ÷ FD · Bull = (net liquid + SOTP ex-lead + unrisked lead PV) ÷ FD, both floored at 0. The lead's DCF replaces its Ph3-rung SOTP credit (no double count). The calculator warns if Base < Bear (DCF × LoA below the lead's floor credit → recheck the DCF).

## 5. Pipeline SOTP residual (feeds Floor A / Floor B)
- **Lead asset out, unless de-risked.** Exclude the program the trade is betting on; when two programs could be the lead, exclude the more valuable/advanced one. **Exception:** if the lead already has positive pivotal (Phase 3 or registrational) data and the event inside the contract is not an efficacy readout (NDA/BLA submission, FDA filing acceptance, conference rehash of known data, or no event), include the lead at the Phase 3 rung ($300M) with the normal partner haircut. Never use the lead's napkin DCF in the floor; that belongs in Base/Bull. The exception switches off automatically once a PDUFA date, AdComm or new efficacy readout falls inside the contract.
- **Other indications of the lead molecule** are separate SOTP entries at their own stage (a failed or subgroup-rescued trial drops one rung). They count even when the lead itself is excluded, unless their own readout is the in-contract binary.
- **Unrisked value per secondary program:** a program-level napkin DCF (§4) if one exists; otherwise the stage ladder the calculator applies from `stage`: preclinical/discovery $15M · Phase 1 or 1/2 $75M · Phase 2 with proof-of-concept data $150M · Phase 3 $300M. The ladder is an assumption, not disclosure; label it as such.
- **Haircuts:** Tier 1 pharma partner 45% (keep 55%); unpartnered 82.5% (keep 17.5%).
- **Counts as unpartnered:** China/regional-only licences (the partner holds only that territory), supply-only or clinical-collaboration deals with no economics, big-pharma deals that have ended or are about to lapse.
- **Don't double count:** upfronts already received sit in cash. Royalties already sold (Sagard, Royalty Pharma, DRI) are worth $0 to equity until the cap is repaid.
- **Discovery collaborations** with several unnamed targets: one bucket at the preclinical rung per program still active, partnered haircut.
- **Unpartnered after a positive Phase 2 for 2+ years:** drop one rung (the market has already priced it).
- **Debt and burn:** Floor = max(0, net liquid − burn + SOTP) ÷ FD shares, always. When net cash is negative, an acceleration trap exists, or net cash is below the burn to the catalyst, the pipeline fills that hole before equity gets anything. (Before v5.1 the burn-shortfall case added the full SOTP on top of a $0 cash floor and overstated Floor B.)
- Chinese licensing income: apply the NRDL haircut and low royalty tiers before counting any of it.

## 6. Management call forensics (latest earnings call; the edge is in unscripted Q&A)
1. **Guidance fidelity:** compare wording with the prior 10-Q / deck ("by mid-year" → "second half" / "year-end" = slippage). Any unguided slip invalidates Mode A (`guidance_slipped: true`).
2. **FDA dialogue:** "constructive dialogue" ≠ "formal agreement on the SAP". Watch Type A/B/C, AdComm, late-cycle, CRL remediation, inspections / Form 483.
3. **CFO runway language:** "opportunistic", "monitoring market windows", runway "through initial data" = raise coming. Check guided runway against modeled burn.
4. **CMC / commercial realism:** CDMO capacity, batch release, device integration, CSO deployment, SG&A or CapEx ballooning pre-launch.
5. **Analyst friction:** the same question asked twice without a straight answer.
Score: **GREEN** clear timelines, transparent FDA, stable runway → pass. **YELLOW** mild elasticity or evasive runway → shorter DTE, OTM ≥ 50%, tighter profit target. **RED** confirmed slip, unresolved FDA/device flags, financing distress → no underwriting.

## 7. Dilution & financing
- S-3 shelf: unallocated balance and expiry. ATM: agent, capacity, pacing (424B5 dates in the filing index).
- ATM wet blanket = quarterly burn ÷ (ADV × spot × 63); > 15% → persistent selling into every 5–10% pop (calculator prints it).
- Timing: runway < 12 months → > 90% chance of an offering on any 15%+ rally; > 18–24 months → low near-term overhang.
- Specialist backstop matters most when runway < 12 months: board seats or history of leading PIPEs/registered directs at or above market lowers death-spiral risk.
- **13F traps:** 45-day reporting lag; venture cost bases of pennies; hedged or collared positions; biology dominates pedigree (specialists eat 70–90% collapses every quarter). Never let ownership justify a Tier 3 setup.
- Nasdaq < $1 bid deficiency or pending reverse split → disqualify underwriting.

## 8. Mode C decision table
| Condition | Naked long put | Bear put debit spread | Short put | Action |
|---|---|---|---|---|
| High PoS (> 50%), high IVR (> 60%), far above cash | ❌ vega trap | ❌ high PoS | ❌ Tier 3 | Walk away |
| Low PoS (≤ 30%), high IVR (> 60%), overextended | ❌ overpaying vega | ✅ | ❌ | Debit spread |
| Low PoS (≤ 30%), low IVR (< 40%), overextended | ✅ cheap gamma | ✅ | ❌ | Naked put or spread |
| High PoS (> 50%), high IVR (> 60%), near cash | ❌ CAPR trap | ❌ | ✅ Tier 1 | Cash-secured put |

Spread: buy ATM put (Δ −0.45…−0.55), sell OTM put at the distressed floor A2 (Δ −0.10…−0.20); target R:R 3:1 to 5:1 on a 60–85% Class B collapse; max loss = debit. Tactical equity short on momentum exhaustion only with Buy to Cover ≥ 48 h before the data window. Optional richness check: 25Δ put IV ÷ 25Δ call IV ≥ 1.3 means downside panic is richly priced (favors selling puts, disfavors buying them naked).

## 9. Feeding the calculator
- `pos` (decimal) or `pos_model: {"baseline":0.25,"factors":[0.10,-0.15,0.05],"cap":0.25}` — one factor per applied adjustment (penalties negative); `cap` only when a cap rule applies.
- `p_statsig`: optional, prints the dual-hurdle approval odds.
- `pos_loa` (decimal) or `pos_loa_after: [next transition, …, approval]` (event PoS multiplied in) — required for Base whenever a `dcf` is passed; the calculator flags LoA > event PoS as inconsistent.
- `pipeline: [{"name": "LEAD", "lead": true, "pivotal_positive": true}, {"name": "X", "stage": "ph1", "partnered": false}, {"name": "Y", "pv": 150000000, "partnered": true}]` — one entry per program/indication; `pv` overrides the stage ladder for non-lead entries. Pair with `catalyst.efficacy_readout` (true/false).
- `dcf: {"patients":40000,"biomarker":0.3,"line_share":0.5,"list_price":150000,"gtn":0.35,"penetration":0.2,"years":6,"wacc":0.13,"multiple":2.5}` — `patients` is the raw incidence/prevalence; `biomarker` and `line_share` are the funnel fractions.
- `runup` (decimal), `debit_spread: {"long":{strike,bid,ask},"short":{strike,bid,ask}}`.
Report PoS as a range when inputs are soft; if the verdict flips inside the range, the answer is DO NOTHING until the load-bearing input is verified.
