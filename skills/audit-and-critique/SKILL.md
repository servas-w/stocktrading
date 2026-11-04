---
name: audit-and-critique
description: Adversarial self-review of Claude's previous response (or a plan or text the user pastes). Lists the assumptions behind it, flags the weak or unverified ones and checks the checkable ones with tools. Then it hunts for contradictions, vague claims and unsupported assertions, red-teams how the plan could fail in the real world, scores it against a standard, and rewrites it. Use when the user says "audit and critique", "AC", "critique that", "red team this", "tear this apart", "stress test your answer" or "what did you miss". This reviews a response, not the brokerage book. "Audit my portfolio", "midday audit", "RH daily audit" and similar portfolio audits go to the portfolio audit skills.
---

# Audit and critique

Review the **target** as a strict, skeptical reviewer, then fix it. The target is Claude's previous substantive response, unless the user pastes text or names something else ("critique the plan above", "AC this: …").

The point is to find real defects, not to perform skepticism. Follow these rules throughout:
- **Don't make up flaws.** If a section holds, say "holds" and move on. "No material issues" is a valid result.
- **Don't flip a conclusion without new evidence.** A rewrite can change a verdict only because a check failed or new data arrived, never because the user pushed back.
- **Check, don't just re-reason.** If an assumption can be tested with a tool you have (market data, option chains, filings, files in the repo, web search), test it before you grade it. Re-reading your own text in the same context won't find blind spots you share with the original answer.
- **Label every judgment** as `VERIFIED` (checked now, cite the source), `REASONED` (logic only, not checked) or `UNVERIFIABLE` (no data available; say what would settle it).
- Be concise. Use tables and bullets, not essays.

## Step 1: Assumption ledger
List every assumption the target depends on: stated, implied, data inputs, causal claims, timing, and "this rule applies here". For each one:

| # | Assumption | Status | Strength | Why / evidence |
|---|---|---|---|---|

- Status is `VERIFIED`, `REASONED` or `UNVERIFIABLE`. Strength is `Solid`, `Weak` or `Unsupported`.
- Check numeric and factual inputs first: prices, IV/IVR, DTE, earnings and catalyst dates, cash, debt, share count, rule thresholds. Stale or invented numbers are the most common failure.
- Sort by how much the conclusion depends on each one, most load-bearing first.

## Step 2: Defect scan
Quote the exact text, then say what's wrong. Each finding falls into one of these groups:
- **Contradiction**: two statements that can't both be true, or a number that doesn't match its own math.
- **Vague**: a claim too hedged or fuzzy to act on or falsify ("likely", "significant", "should be fine", no number, no date).
- **Unsupported**: an assertion with no evidence, or evidence that doesn't support it.
- **Math**: recompute every derived figure (ROC, breakeven, cushion %, annualized return, sizing vs NAV cap). Show the corrected value.

## Step 3: Red team
Attack the logic. Answer:
1. **How does this fail in the real world?** Give the 3–5 most plausible failure paths, with rough likelihood and impact.
2. **What was missed?** Risks, alternatives, data or second-order effects that were never mentioned.
3. **What single fact, if wrong, kills the thesis?** Name it and say how to check it.
4. **Strongest counter-argument**: steelman the opposite view in 2–3 lines.

For trading or options targets, always test against these: gap and overnight risk through the strike, earnings or binary catalysts before expiry, IV crush or expansion and skew, assignment and early-exercise mechanics, liquidity and bid/ask on the exit (not just the entry), correlation with existing book exposure, margin and buying-power stress, dilution or ATM/S-3 overhang (biotech), and whether the setup still clears the IV gate.

## Step 4: Scorecard
Score 1–10 on each criterion, with one line of justification each, then give the overall score. Anchor the scale like this: **10** = nothing to fix, **7** = minor gaps, **5** = material gap that changes the action, **3** or below = wrong or unusable. Don't give a 9 or 10 if Steps 1–3 found a material issue.

**Criteria, in order of preference:**
1. Criteria the user supplies ("evaluate against X").
2. **Trading or options targets:** Wilson's Playbook v2 and underwriting rules, which are DTE window (60–90 for new shorts; under 30 DTE needs an OPP tag), IV gate (IVR ≥ 50, spread exception), strike cushion and debt-adjusted floor, the 10% NAV cap counting held shares, one opening ticket per name per day, catalyst before expiry, velocity profit-take and defense triggers (delta −0.30 or spot within 7% of strike), and held-lot discipline (no puts on underwater lots).
3. **Anything else:** Accuracy · Evidence · Completeness · Internal consistency · Actionability · Risk disclosure · Clarity.

List the gaps that cost points.

## Step 5: Revised response
Rewrite the target. Defend each weak assumption with evidence or remove it, fix each defect, and add whatever the red team found missing. Keep the original's format and length unless the defects demand otherwise. If nothing material changed, say **"Original stands"**, give at most a few line edits, and stop.

End with a **change log**:
- **Changed:** what changed and why (link to the step and # that caused it).
- **Verdict change:** yes or no. If yes, name the evidence.
- **Still open:** unverifiable items and how to settle them.

## Modes
- **"AC lite"** or **"quick critique"**: give only the top 3 weak assumptions, the top 3 defects and the top 3 failure paths, then a rewrite of the affected parts. No scorecard.
- **"AC: <criteria>"**: use the given criteria for the Step 4 scorecard.
