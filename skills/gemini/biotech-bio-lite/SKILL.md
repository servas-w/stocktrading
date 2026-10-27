---
name: biotech-bio-lite
description: Fast, low-compute biotech put check from the cash up. Triggered by "BIO: TICKER", optionally with a trade to grade (e.g. "BIO: FHTX 2.5P Jan @0.45"), or by a bare biotech ticker. Returns net cash per share, Floor A / Floor B, catalyst timing and mode, max strike, dilution and compliance flags, and a GO / CONDITIONAL / WAIT / NO-GO verdict in a short card, stopping at the first hard fail. Not for "BIO DEEP:" (use biotech-options-master-engine for Bayesian PoS, napkin DCF, management forensics and the full dossier).
allowed-tools: google google_finance
---

# BIO: lite biotech check

Clinical biotechs are bank accounts holding lottery tickets. Underwrite the cash, never pay for hope. This is the cheap pass: answer in a few searches, stop at the first hard fail, and send anything that needs science-grade work to `BIO DEEP:`.

## Budget

- At most **4 tool calls**: 1 `google_finance` + up to 3 `google` searches. No other research.
- Reply **≤ 250 words**; an early exit is 2 lines.
- Fresh numbers only, each with its source and "as of" date. Never fill a gap from memory: write UNVERIFIED and keep going.

## Input

`BIO: TICKER` or `BIO: TICKER STRIKE[P|C] EXPIRY @CREDIT [xQTY] [OI n] [bid/ask]`. A trade is optional; without one, output the max eligible strike instead of grading a trade.

## Steps

1. **`google_finance TICKER`**: spot, market cap, 52-week range, average volume.
2. **Search 1, cash**: `TICKER latest quarter results cash runway shares outstanding`. Prefer the company's own earnings press release (8-K exhibit 99.1) over news. Take: cash + marketable securities, debt, quarterly operating cash burn (net loss only as a labelled proxy), common shares, pre-funded warrants if stated, runway guidance, balance-sheet date.
3. **Search 2, catalyst**: `TICKER next data readout PDUFA topline 2026 2027`. Take: event type, guided window, whether it is an efficacy readout, and whether guidance slipped versus earlier statements.
4. **Search 3, only if search 1 didn't already answer it**: `TICKER ATM offering S-3 reverse split Nasdaq deficiency`.

## Hard gates (check each as soon as its data arrives; stop at the first fail, 2-line output)

- Reverse split pending or Nasdaq bid-price deficiency → NO PUTS.
- Debt a lender can accelerate on clinical failure and cash ≤ debt + any minimum-cash covenant → floor $0 → NO PUTS.
- Runway < 6 months → NO PUTS (a raise is near-certain).
- A bearish idea on a name trading below 1.5× Floor B → NO SHORT (Anti-CAPR).

## Math (one line each, show the numbers)

- **FD shares** = basic + pre-funded warrants. PFWs not found → write "PFW unverified" and cap the verdict at CONDITIONAL.
- **Net cash** = cash + securities − debt, less burn since the balance-sheet date (q_burn × days ÷ 91).
- **Raw cash/share** = net cash ÷ FD shares.
- **Floor A** (expires before the catalyst) = (net cash − q_burn × DTE ÷ 91 × 1.2) ÷ FD shares. No trade given: use the latest expiry that still leaves 14 days before the window.
- **Floor B** (holds through the catalyst) = (net cash − q_burn × 1.5 × quarters to the end of the window) ÷ FD shares. Cash only: partnered pipeline value is a DEEP item.
- **Mode**: expiry ≥ 14 days before the window → **A** (pre-catalyst harvest). Anything later, including expiry inside the 14-day buffer → **B** (binary). No window found → treat as B. No trade given → show the max strike for both A and B. **C** (bearish) is only in play if spot ≥ 3× Floor B and the stock is up ≥ 50% in 6 months; lite never approves a Mode C trade (it needs the PoS ≤ 30% check), it only says "Mode C possible → BIO DEEP:". Otherwise the short side is closed.
- **Max strike**: Mode A → breakeven ≤ Floor A and strike ≤ raw cash/share. Mode B → strike ≤ Floor B (Tier 1) or breakeven ≤ Floor B (Tier 1B, lower tier).
- **Stock replacement**: a sub-$5 put struck at ≥ 90% of spot (about delta 0.40 or more) is a share purchase in disguise. SR-pass if breakeven ≤ raw cash/share, else SR-fail.
- **Trade given**: breakeven, OTM %, ROC = credit ÷ (strike − credit), annualized, tier, pass/fail against the floor.
- **Liquidity is a warning only**: OI < 150 or a bid/ask wider than 25% of mid gets one ⚠️ line, never a rejection.
- **IV is context only**: Gemini has no IV Rank. Write "IVR unverified" and never reject on it.

## Verdict

- **GO**: passes the floor test for its mode, runway ≥ 12 months, no gate hit, PFWs verified.
- **CONDITIONAL**: would be GO, but PFWs unverified, burn estimated, runway 6–12 months (Mode A needs > 12), or the catalyst date is soft.
- **WAIT**: the floor works only after a known event (e.g. post-raise), or the catalyst date is unknown.
- **NO-GO**: fails the floor or a hard gate.

End the card with **→ BIO DEEP: TICKER** when the trade is Mode B or C, a floor is within 10% of the strike or breakeven, or the user asks about PoS, DCF or management.

## Hard rules

- A rejected put sale is not a reason to buy puts (False Dichotomy). The default is DO NOTHING / CASH.
- Never sell covered calls into a binary. Never hold a naked equity short through data.

## Output

```
**TICKER $spot (as of date) — VERDICT** · Mode A/B/C · catalyst: event, window (source)
| Net cash/sh | Floor A | Floor B | Max strike | Runway | Debt |
Trade: K exp @credit · BE · OTM % · ROC ann. · tier (or "no trade given")
Flags: PFW · ATM/S-3 · compliance · liquidity ⚠️ · IVR unverified
🧠 Three blunt, numbers-first sentences: what retail misreads, the cash reality, whether the structure is +EV.
Kill-shot: the single fact that flips the verdict.
→ BIO DEEP: TICKER (only when the rule above says so)
```

Early exit: `**TICKER $spot — NO-GO:** gate + numbers.` plus one 🧠 sentence.
