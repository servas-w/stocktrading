# Playbook v2.5 reference (rules, gates and terms)

This is the only place the reports take rule definitions from. Cite a rule by **number and name**, for example `R3 Time`. Confirmed by Wilson on 5 Nov 2026: Playbook **v2.5 (R1–R12)**, with a 60–90 DTE entry window for large caps, no hard VIX gate, concentration measured by spread width, R6 biotech catalyst exception, R8 structure limits and the R10 WING/LOTTO limits.

**Classes:** LC/MC rules apply to large- and mid-caps; BIO/SC rules apply to biotech and small-caps. A name's class comes from the CLASS column in the WarRoom PDF appendix. If it's missing, classify it automatically: market cap under $2B, or a biotech/pharma name under $10B -> BIO/SC; otherwise LC/MC. Tag it `class (auto)`. If market cap isn't available either, apply the LC rules and tag it `class? UNVERIFIED`.

## The rules
| # | Rule | Gate -> required action |
|---|---|---|
| R1 | IV gate | Sell naked premium only when IV Rank >= 50 (IBKR IV percentile 52w >= 60 and 26w >= 50 counts). Defined-risk spreads are exempt. If IVR can't be sourced: `IVR unverified`. VIX is context only, never a gate. |
| R2 | Profit take | Rest a 50% GTC buy-to-close at fill. **Velocity:** % captured >= 2 x % of time elapsed **and** >= 25% -> take it. **Dead pennies:** mark <= $0.05 or >= 80% captured, still open -> close this session. A short with no working buy-to-close is flagged. |
| R3 | Time | ITM short at <= 21 DTE -> act within 1 session (close, or roll 30–60 days for a net credit); `2nd session` if already flagged. Shorts opened under 30 DTE are allowed but tagged **OPP**. Non-OPP LC shorts at <= 21 DTE and under 80% captured -> close or roll. |
| R4 | Defense + one ticket | **LC/MC:** Delta <= -0.30 or spot within 7% of strike -> defend. **BIO/SC:** strike above `0.65 x Floor B` (or above `Floor B` when `Floor B` is unverified) with spot within 15% of strike -> defend (Floor B missing or stale -> flag at 15%, `Floor B UNVERIFIED`). **No adding in defense:** no opening fill or working sell-to-open on a triggered name. **One opening ticket per name per session.** |
| R5 | Concentration | Per name <= 10% of NAV (amber >= 8%, red > 10%), measured as **max loss**: naked put = strike x 100 x qty; defined-risk spread = width x 100 x qty (gross of credit, on purpose: conservative); plus shares x spot. BIO/SC sleeve <= 25% of NAV, summed with the same max-loss method. Method in `core-rules.md` §3. |
| R6 | Earnings | Check whether earnings land before expiry for every short, and compare the **expected move** with the cushion. Unsourced date: `earnings date UNVERIFIED — check before expiry`. No new short stock into a print. **LC/MC:** no new naked short premium into a print; enter after it. **BIO/SC:** premium into a catalyst is allowed only as a biotech-engine **Mode A** (pre-catalyst IV harvest, tag BIO-A) or **Mode B** (Tier 1 fortress put at or below `0.65 x Floor B`, tag BIO-B); any other naked short into a binary is a breach. |
| R7 | Held lots | Lots more than 15% below cost (BIO/SC) or 25% (LC/MC): no new puts and no working sell-to-open on that name; covered calls only at or above basis. Lots more than 25% below cost need a written plan within 7 days of first flag, otherwise `Rule 7 deadline passed`. Never dump assigned shares within 5 sessions. |
| R8 | Structure limits | No short options expiring in 2028 or later (no LEAPS shorts). Debit trades need 3:1 reward-to-risk at entry. No directional long calls or puts into a binary print. |
| R9 | Style (entry window) | **LC/MC: 60–90 DTE, \|Delta\| <= 0.20 at entry. BIO/SC: 30–90 DTE.** OPP shorts are exempt. Scalp cap: OPP shorts at <= 7 DTE plus other scalps <= 1% of NAV at risk. |
| R10 | Lottery longs | Every long option opened at <= $0.10 is either a **WING** (hedges a short on the same name, in the same ticket or against an open short) or **LOTTO** (one-line thesis in the journal). Limits: <= 3 LOTTO opening tickets per day; LOTTO premium <= 0.25% of NAV per calendar month; **no penny scalping** (opening and closing the same contract priced <= $0.20 in one session is a breach, whatever the P&L). **Orphan wings:** a wing whose short is closed becomes LOTTO; sell it within 5 sessions or it counts against the monthly cap. |
| R11 | Short stock | Hard buy-to-cover stop at +15% from entry. Each short-stock line <= 2% of NAV. No new short stock on sub-$5 clinical biotech or into earnings (R6). |
| R12 | Dry powder | Cash + SGOV + STRC >= 15% of NAV (target 15–20%). Below 15%: no new opening risk until it's restored. |

**Grades for new entries:** A = fits every rule. B = event before expiry, or DTE outside the R9 window but >= 30. C = Delta >= 0.25, ITM at entry, an unstructured binary, or a sub-$5 biotech sold at Delta >= 0.40 without `0.65 x Floor B` at or above the strike.

## Book limits
- Stress: S1–S5 scenario loss <= 20% of NAV; a breach goes in the Summary.
- Short Bench sizing: 2% of NAV at risk per idea.

## Journal setup tags
LC · BIO-A · BIO-B · BIO-C · WHEEL-CC · SHORT-STOCK · LOTTO · SCALP · INDEX · OTHER. Use exactly these in the Trade Journal's Setup column; the weekend scorecard groups by them.

## Terms used in the templates
- **HARVEST / HOLD:** HARVEST = meets R2 velocity, >= 50% captured, or a dead penny. HOLD = below target; show it only if within 10% of target.
- **Tripwire:** a short line close to a trigger, shown with strike, spot, cushion %, Delta and DTE.
- **Expected move:** the options market's priced move into an event = front-week ATM straddle / spot (or the implied move a source quotes). Compare it with the cushion: cushion < expected move means the strike is inside the priced range.
- **Floor A / Floor B:** biotech cash floor per share (`Floor A` = `(Cash - Current Liabilities) / Diluted Shares` including pre-funded warrants; `Floor B` = `Floor A - 2Q Burn`, or `4Q Burn` when next catalyst is > 6 months out; `0.65 x Floor B` is the maximum naked short put strike).
- **Strategic themes:** (1) AI capex & semis, (2) energy & geopolitics, (3) rates, Fed & liquidity, (4) biotech & FDA, (5) crypto, (6) China & consumer.
- **Cause tags:** earnings · guidance · macro · rates · oil · rotation · analyst · M&A · FDA/trial · filing · flows/expiry · no news.
- **Bracket tags** (appendix only): `[Guidance != Realized Cash Flow]`, `[Aggregate != Breadth]`, `[Price != Proof]`, `[Trial Design != Clinical Efficacy]`.
