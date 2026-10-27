# RS-Pullback Overlay (v6) — method notes

Read only when the user asks "why" about the overlay, a scanner result looks wrong, or a threshold needs changing. The operating rules live in SKILL.md.

## Source idea (paraphrased from a member report the user supplied)

1. Trade relative-strength names — stocks that outperformed the market and kept a clean trend — and buy them on pullbacks. Even in a weak tape some sectors lead (energy, photonics in March 2026).
2. The strongest names hold their weekly EMAs. A name that has closed above its 9W (or 21W) EMA for ~10–15 weeks is far more likely to meet a responsive buyer at that EMA than one that chops above and below it. The longer the hold, the higher the odds — but a long hold can still break (STX sliced through a multi-year 21W hold on Toshiba news).
3. Layer a short-term reversal trigger on the 30-minute chart: after a sell-off (one big red 30m bar or a run of red bars), the FIRST 30m candle to close green is the marker. Entry is when a later candle (ideally the next) closes above the marker's high. Stop = the marker's low (typically ~2%). Feedback is fast: the reversal holds or it doesn't. When the weekly EMA is slicing, the trigger usually does not fire, or it stops out quickly.
4. Improve odds by: not trading in negative-liquidity periods; not trading within a week of earnings; preferring names whose fundamental story you know.

## Translation to 60–90 DTE short puts (what changes, what doesn't)

| Report (stock buyer) | This skill (put seller) |
|---|---|
| Buy at the 9W/21W EMA | Sell the put *after* the 30m trigger confirms a buyer at the EMA; strike goes below the NEXT weekly support, not at the EMA being tested |
| 2% stop at the marker low | Not usable on a 60–90 DTE short put (a 2% wiggle is noise to the option). The marker low is an **entry invalidation only**: if it breaks before you're filled, cancel the order. After the fill, the Playbook defense rules govern |
| Weekly EMA break = exit | Weekly close below the defended EMA = **structure-break flag** (no adds, no new tickets on the name); weekly close below the next support (the strike's backstop) = defend now (roll out/down for credit or close), don't wait for the 7%/Δ−0.30 trigger |
| Avoid earnings within a week | Hard block on new entries ≤ 6 calendar days before earnings. The existing CLEAN/HAZARD expiry rule still applies on top |
| Avoid negative liquidity | Regime proxy from the Liquidity Regime scan (SPY, HYG, RSP vs their 21W EMA). RISK-OFF = no RS-pullback entries; CAUTION = spread-only, half size |
| Fundamental conviction | Already enforced by owner-FCF forensics and the structural-impairment REJECT |

**The IV gate is unchanged.** A calm RS pullback is often a low-IVR event — the stock is drifting to its EMA, nobody is panicking. An RS-pullback name that fails the IV gate goes to the Pullback Watchlist; it does not become a short put because the chart is pretty. The overlay's best case is the overlap: a strong name hit by a sharp, news-driven flush INTO its weekly EMA, which spikes IV and prints the 30m trigger the same session — sell the premium while it's rich, with a buyer already showing up.

## Scanner thresholds (`scripts/rs_pullback.py`)

- Zone band ±3% around the EMA; BROKEN = spot > 3% below the 21W.
- 9W is "unreliable" when its consecutive-close run is < 6 weeks but the 21W run is ≥ 6 → the 21W becomes the defended level (the report's "breaking above and below the 9W" case).
- Grade A: run ≥ 10 consecutive weekly closes above the defended EMA, ≥ 13 of the last 15, 9W > 21W with the 21W rising (and 21W > 50W when available), RS vs SPY > 0. Grade B: run ≥ 6, ≥ 10 of 15, 9W > 21W. C: in zone but weaker. F: broken or 9W < 21W.
- Weekly EMAs: preferably server-computed (`get_equity_technical_indicators`, `output: last:16`) so only ~17 weekly bars are needed; the script's own SMA-seeded EMA matched the server's within ~0.1% on TER/WDAY. RS vs SPY compares completed weeks to completed weeks (13W).
- A 30m trigger that fires while price is BETWEEN the 9W and 21W is downgraded to WATCH: there is no weekly support under it.
- A bar that undercuts the marker low and then closes above the marker high is treated as an invalidation (the stop would have been hit first in the worst case).
- 30m sell-off: a red bar whose low is ≥ 1.5% below the highest high of the prior 8 bars. Marker = first green close after it. Marker invalid if a later bar's low undercuts it before the trigger. Trigger = close above the marker high. A trigger more than 1 session old is stale (WATCH, not READY). Bars with volume < 10% of the median are dropped as odd-lot/glitch prints (Robinhood returns some). The in-progress bar is excluded when `asof` is passed.
- Confluence: marker low within −3%/+2.5% of the defended weekly EMA.
- Strike ceiling = min(next weekly support, spot × (1 − required cushion)). Next support: 21W EMA when defending the 9W; 50W EMA when defending the 21W (needs ≥ 55 weekly bars), else the 13W swing low (conservative fallback — fetch ~60 weeks to avoid it).

## Saved Robinhood scans (Legend)

- **LC Put – RS Pullback to Weekly EMA** `2a180f78-9e8b-40b8-8a9e-224629d42d81` (v2 config) — mcap ≥ $20B; 9W EMA > 21W EMA; price > 13 weeks ago × 1.15; price ≤ 9W × 1.03; price ≥ 21W × 0.97; Robinhood ivRank ≥ 0.30; days to earnings ≥ 7 (`daysFromNow(fundamental.earningsYmd)` — names with no earnings date drop out); total put OI ≥ 10,000 (kills illiquid ADRs). Columns: % vs 9W, % vs 21W, 13W change, 21W>50W, ATM IV 60D, Days to ER, Put OI. It is a coarse universe filter — it cannot count consecutive weeks held; the script does that.
- **LC Put – IV Spike Dislocation** `81e24168-a345-40b5-aee8-74e7f051cc10` — the DISLOCATION feeder: mcap ≥ $20B; RH ivRank ≥ 0.40; 5-day change ≤ −5%; put OI ≥ 10k; days to ER ≥ 7. Columns: 5D chg, IV30/HV30 (`atmIv30Day / statVol1Month`), RSI 14D, % vs 21W/50W EMA, off 52W high, days to ER. IV > realized was tested as a filter and dropped (it left 1 name: right after a flush realized vol spikes too); it is a scoring penalty in `triage` instead.
- **LC Put – Liquidity Regime** `f759011a-9c23-4491-9b40-7d492bc95b8b` — SPY, QQQ, IWM, RSP, HYG with % vs 9W/21W EMA, 9W>21W, ATM IV, IV rank.

Robinhood's ivRank is a pre-filter only (0–1 scale); the authoritative gate is still IBKR IVP via the ladder in SKILL.md.

## Limits

- Not backtested here. Treat grades as a ranking, not a probability. Log each READY entry's outcome (held / sliced) so the thresholds can be tuned on the user's own results.
- The regime test is a proxy for "liquidity", not a measure of Fed net liquidity.
- EMA values differ slightly from TradingView (SMA-seeded EMA, regular-session weekly bars); differences of a few tenths of a percent don't change the zone call except at band edges.
