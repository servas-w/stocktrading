---
name: large-cap-lc-lite
description: Fast, low-compute large-cap short put check. Triggered by "LC: TICKER", optionally with an IV Rank and/or a trade to grade (e.g. "LC: NKE IVR 58" or "LC: NKE 60P Jan @1.20 /40P @0.05"). Checks the IV gate, earnings timing, owner FCF (OCF minus CapEx minus SBC), debt-to-EV and sell-off cause, then returns the required cushion, max strike and a GO / CONDITIONAL / WATCHLIST / NO-GO verdict in a short card, stopping at the first hard fail. Not for "LC DEEP:" (use large-cap-put-overreaction for the full dossier, RS weekly-EMA pullbacks and wing architecture) and not for clinical-stage biotech (use BIO:).
allowed-tools: google google_finance
---

# LC: lite large-cap check

Sell fear, not hope. A short put is an IV mean-reversion trade: you must be paid (IV Rank), sit below a real floor (owner cash flow, debt ahead of equity), and buy a cheap parachute when one exists. This is the cheap pass; anything that needs a chain, a chart study or a dossier goes to `LC DEEP:`.

## Budget

- At most **4 tool calls**: 1 `google_finance` + up to 3 `google` searches.
- Reply **≤ 220 words**; an early exit is 2 lines.
- Fresh numbers only, each with source and "as of" date. Never fill a gap from memory: write UNVERIFIED.

## Input

`LC: TICKER [IVR n] [STRIKE P EXPIRY @CREDIT [/WING P @ASK] [delta d]]`. IVR and trade are optional.

## Steps

1. **`google_finance TICKER`**: spot, market cap, P/E, dividend yield, 52-week range, recent % move.
2. **Search 1, cause + earnings**: `TICKER stock drop reason next earnings date`. Take the sell-off cause (one sentence), last and next earnings dates.
3. **Search 2, cash flow**: `TICKER trailing twelve months operating cash flow capital expenditures stock based compensation cash debt`. Prefer the company's latest earnings release or 10-Q/10-K figures.
4. **Search 3, IV Rank (only if the user didn't give one)**: `TICKER IV rank implied volatility percentile`. Accept a number only from a dated source that states it is IV Rank or IV Percentile; otherwise IVR = UNVERIFIED. Never fetch or guess Barchart.

## Hard gates (check each as its data arrives; stop at the first fail)

- Market cap < $10B → out of scope. Clinical-stage biotech with a binary inside the contract → use `BIO:`.
- Structural impairment (patent cliff, lost franchise, fraud, going-concern, distress dividend cut) → NO-GO regardless of IV.
- Next earnings ≤ 7 calendar days away → WATCHLIST (blocked until after the report).
- Verified IVR < 30 → WATCHLIST (options too cheap; re-check when IVR ≥ 50).
- 1–10 sessions after earnings with verified IVR < 35 → NO-GO (Anti-ORCL: post-crush scrap).
- TTM owner FCF ≤ 0 → NO-GO (banks, brokers, insurers: write "forensics n/m (financial)" and skip this gate).

## Math (one line each, show the numbers)

- **Owner FCF** = OCF − CapEx − SBC (TTM); **owner FCF yield** = owner FCF ÷ market cap. SBC not found → show OCF − CapEx labelled "pre-SBC" and cap the verdict at CONDITIONAL.
- **Debt-to-EV** = funded debt ÷ (market cap + debt − cash).
- **Required cushion**: 15% base ($20B+), 25% for $10–20B. 30% when guided or forward FCF turns negative from a CapEx surge. If Debt-to-EV > 25%, multiply by (1 + 1.5 × Debt-to-EV) and require a spread.
- **Max strike** = spot × (1 − required cushion), then the listed strike at or below it. Ideal delta −0.10 to −0.15, but the cushion wins.
- **Expiry**: a 60–90 DTE monthly. Expires before the next earnings → CLEAN. Spans earnings → HAZARD: spread mandatory, and say the IV is earnings-inflated.
- **Floor check**: breakeven at or below the 52-week low → ✅, else ⚠️ (not a gate).
- **Trade given**: breakeven, cushion %, ROC = credit ÷ (strike − credit) for a naked put or credit ÷ (width − credit) for a spread, annualized. Delta given → Probability of Touch ≈ 2 × |delta|. Wing given → wing cost = wing ask ÷ short credit; ≤ 5% → spread mandatory.
- **Liquidity** (if the user gives OI or bid/ask): OI < 150 or a spread wider than 25% of mid → one ⚠️ line, never a rejection.

## Verdict

- **GO**: verified IVR ≥ 50, CLEAN or spread for HAZARD, all gates pass, cushion met.
- **CONDITIONAL**: IVR 30–50 and either P/E < 10, yield > 3.5% or a defined-risk spread; or IVR UNVERIFIED or SBC missing with everything else passing.
- **WATCHLIST**: quality name but IVR < 30, or blocked by earnings timing.
- **NO-GO**: any other hard gate (out of scope, structural impairment, Anti-ORCL, owner FCF ≤ 0), or the cushion can't be met at any listed strike.

End the card with **→ LC DEEP: TICKER** when the trade needs a chain-based wing quote, the name is a weekly-EMA pullback (RS setup), Debt-to-EV > 25%, IVR is within 5 points of 30/35/50, or the user asks for the full dossier.

## Output

```
**TICKER $spot (as of date) — VERDICT** · IVR n (source) or UNVERIFIED · earnings CLEAN/HAZARD (date)
| Owner FCF (yield) | Debt/EV | Cushion | Max strike | BE vs 52w low |
Trade: K exp @credit (/wing) · BE · cushion % · ROC ann. · PoT (or "no trade given")
Cause: one sentence, transient or structural.
🧠 Three blunt, numbers-first sentences: owner FCF vs headline EPS, SBC dilution, debt ahead of equity, retail trap or real mispricing.
Manage: GTC buy-to-close at 50% · take 65–75% inside 14 days · close/roll at 21 DTE · defend at delta −0.30 or spot within 7% of strike, roll for a credit only.
→ LC DEEP: TICKER (only when the rule above says so)
```

Early exit: `**TICKER $spot — NO-GO / WATCHLIST:** gate + numbers.` plus one 🧠 sentence.
