# Sentinel watchlist: catalyst sheet

**As of 2026-10-28.** These are starting points, not facts to repeat. Re-verify every line against the company's latest 8-K/10-Q or IR page before it goes in a report. If a date below has passed, or this sheet is more than 14 days old, say so in the report and refresh it (edit this file) before using it.

Positions, strikes and contract counts do **not** live here. Always pull them live from Robinhood.

## CAPR: Capricor Therapeutics
- **Asset**: deramiocel (CAP-1002), allogeneic cardiosphere-derived cells, DMD cardiomyopathy / upper-limb function.
- **Regulatory**: CRL (Jul 2025) → Class 2 resubmission with HOPE-3 data, PDUFA Aug 22, 2026 → **extended to Nov 22, 2026** after an amendment (HOPE-3 24-month OLE data plus a narrower upper-limb indication). Sources: [Capricor IR](https://www.capricor.com/investors/news-events/press-releases/detail/338/capricor-therapeutics-announces-establishment-of-new-pdufa), [8-K Aug 24, 2026](https://www.sec.gov/Archives/edgar/data/0001133869/000110465926100071/capr-20260824xex99d1.htm).
- **Expiry overlay**: Nov 22, 2026 is a **Sunday**. CBER can act on or before Fri **Nov 20**, which is also the November monthly expiry, or it can miss the date entirely. Check the weeklies too (Nov 13 is `before`, Nov 20 is `ambiguous`; run `overlay` rather than trusting this line). A decision after the Nov 20 close lands on Nov options already expired; one before it hits them directly. Every Dec 18 and later leg carries the full binary. Also watch for an early action, a CRL leak, a labeling-discussion 8-K, or a PRV announcement.
- **Rules**: Anti-CAPR applies (no short stock against a short-put stack on this name).

## ACRS: Aclaris Therapeutics
- **Assets**: bosakitug (ATI-045, anti-TSLP mAb), Ph2 atopic dermatitis, n≈109, primary endpoint % change in EASI at wk 24, **topline guided 4Q 2026** (slipped from 2H26); ATI-052 (TSLP × IL-4Rα bispecific) Ph1b; ATI-2138 (ITK/JAK3) Ph2. Sources: [10-Q Q2 2026](https://www.sec.gov/Archives/edgar/data/0001557746/000110465926092065/acrs-20260630x10q.htm), [Jul 2026 snapshot](https://investor.aclaristx.com/system/files-encrypted/nasdaq_kms/assets/2026/07/14/9-43-28/July%20ACRS%20snapshot_071326%20Final.pdf).
- **Expiry overlay**: the readout window is **open now** and has no fixed date. Treat every Nov/Dec/Jan leg as straddling a binary. The bar is the single-arm Ph2a (94% EASI-75, n=17); a placebo-controlled trial will look worse than that, and the stock may trade on the gap.

## MGNX: MacroGenics
- **Assets**: MGC026 (B7-H3 TOP1 ADC) Ph1; MGC028 (ADAM9 ADC), prelim data guided **late 2026**; MGC030 IND cleared 2Q26; lorigerlimab (PD-1 × CTLA-4) LINNET, **partial clinical hold (Mar 2026)**, now enrolling 20 more clear-cell gyn patients at 3 mg/kg, update **1H 2027**. ESMO 2026 posters for MGC026 and lorigerlimab: check whether they have been presented and what they showed. Sources: [MacroGenics IR](https://ir.macrogenics.com/node/16211/html), [Q1 2026 results](https://www.1stoncology.com/blog/?p=110956).
- **Cash**: manufacturing operations sold for **$122.5M (Jul 2026)**. Add it as a post-period inflow if it is not in the latest 10-Q balance sheet.

## CMPX: Compass Therapeutics
- **Assets**: tovecimig (CTX-009, DLL4 × VEGF-A), 2L biliary tract cancer; CTX-8371 (PD-1 × PD-L1); CTX-10726 (PD-1 × VEGF-A).
- **COMPANION-002 (Apr 27, 2026)**: ORR 17.1% vs 5.3% (p=0.031), PFS 4.7 vs 2.6 mo (HR 0.44), but **OS missed** (8.9 vs 9.4 mo, HR 1.05). Management blames 54% crossover. The stock fell more than 60%. The approval path is now uncertain: track any FDA meeting outcome, a BLA-or-not decision, the full-data conference presentation, and any restructuring. Source: [Targeted Oncology](https://www.targetedonc.com/view/tovecimig-improves-pfs-but-misses-os-end-point-in-biliary-tract-cancer).
- **Shares**: pre-funded warrants are material. Pull the current count from the latest 10-Q; do not reuse an old figure.

## All four
- Q3 2026 10-Qs (balance sheet dated 9/30) are due early-to-mid November. Refresh every floor when they land, and watch for a same-day S-3/ATM.

## Adding a ticker
For any single-ticker request outside this list, build the same block live (asset, next dated catalyst, expiry overlay, cash notes) and offer to add it here.
