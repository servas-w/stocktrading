# WarRoom feed spec (what the Claude audit PDFs must contain)

The Gemini edition can't reach Robinhood, so the WarRoom PDFs in `Robinhood Portfolio Review` are its only view of the book and of held-name prices. When the PDF leaves something out, Gemini goes looking on Google Search. Search is unreliable for microcap quotes, and that is where figures like MRNA $54 vs $222 came from.

**Done for `daily-portfolio-audit`:** the updated skill in `skills/daily-portfolio-audit/` (zip: `skills/daily-portfolio-audit.zip`) already writes this appendix, plus an optional PRE snapshot. Upload it in claude.ai to replace the old one. The block below is for any other skill that writes WarRoom PDFs, such as the weekly WEEKBOOK. The 1–2 page limit applies to the narrative only; these tables go on appendix pages.

---
**Paste into the audit skill:**

> **Appendix for the market reports (always include, after the narrative; plain tables, one row per line, no merged cells):**
> 1. **Header:** account(s) · audit type (PRE / MID / EOD / WEEKBOOK) · run time `HH:MM ET / HH:MM ICT` · session date.
>    **CHECK line**, exactly: `CHECK: <N> short option lines · <M> stock lines · $<X> short-put notional` (N = short rows printed in table 4).
> 2. **SNAPSHOT:** NAV · cash · buying power · options value long/short · short put notional · net delta $ · theta $/day · vega $/pt.
> 3. **STOCK POSITIONS (every line):** ticker · class (LC/MC or BIO/SC) · qty (negative = short) · cost basis · spot · spot time · unrealized $ · unrealized %.
> 4. **OPTION POSITIONS (every line, not just flagged ones):** ticker · class · Floor B · type · strike · expiry · qty (negative = short) · avg open price · mark · Δ · DTE · cushion % · % captured.
> 5. **QUOTES:** every underlying held or optioned: last · prior close · pre-market or after-hours mark if any · quote time.
> 6. **FILLS (this session):** time · ticker · contract or shares · side · qty · price · opening/closing.
> 7. **WORKING ORDERS:** ticker · contract · side · qty · limit · tif · placed time.
> 7b. **TRANSFERS (EOD/WEEKBOOK):** date · deposit/withdrawal · amount (for the QQQ benchmark); include QQQ and SPY in table 5.
> 8. **WEEKBOOK only, STRESS:** S1 SPX −10% × β + 10 IV pts · S2 tech/AI −20% + 10 IV pts · S3 IV +15 pts · S4 largest name −30% · S5 biotech sleeve −20% + 10 IV pts: loss $, % NAV, worst 3 contributors.
> File names carry type and run time: `WarRoom_<date>_<n>-<TYPE>-<HHMM>.pdf` (TYPE = PRE, MID, EOD or WEEKBOOK; HHMM = ET run time), so no two files share a name. Tickers exactly as the API returns them.
---

## Optional: a PRE snapshot
The EOD PDF is about 12 hours old by the time PRE runs. A small `PRE` audit at about 20:45 ICT (08:45 ET), with only sections 1, 2, 5 and 7, gives the pre-market report real pre-market quotes for held names. Without it, PRE searches only the triggered names and the top 10 exposures, and labels the rest `as of feed`.
