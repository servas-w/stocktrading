# Full Forensic Dossier (load only when the user asks for "full", "deep" or "dossier")

Same data and calculator output as the compact card — this template only adds narrative. Do not make extra tool calls for it beyond: one extra `web_search_fast` query for upcoming corporate catalysts (investor day, guidance window) if not already known, and the stock's historical trough EV/FCF multiple if the floor check is borderline.

```markdown
# Forensic Large-Cap Options Underwriting Dossier: TICKER (Company)
*As of HH:MM ET, date. All figures from this session's tool calls; UNVERIFIED where marked.*

### Executive Summary & Verdict
* **Spot**: $X.XX · **Verdict**: SELL PUT SPREAD (Prime) / SELL PUT (Prime) / CONDITIONAL (Hedged Only) / REJECTED (NO-GO) / PULLBACK WATCHLIST
* **Structure**: e.g., Dec 18 '26 $160P / $100P bull put spread (86 DTE)
* **Net credit**: $X.XX (fill rule used) · **BE & cushion**: $X.XX (XX.X% below spot)
* **PoT**: XX% (vs Δ XX) · **ROC**: XX% ann. on max risk / cash · Reg-T est XX%
* **IV Rank**: XX (IVP XX, source) → GREEN / YELLOW / RED
* **Earnings runway**: CLEAN (next ER date, X days after expiry) / HAZARD (spans ER date)
* **Forensic solvency & SBC**: PASS / FAIL with owner FCF figure

### 🧠 Reality Check (forensic commentary)
Acerbic, spreadsheet-first dissection: the narrative vs owner cash flow, non-GAAP add-backs of SBC, CapEx incineration, debt ahead of equity, management excuses, and whether the structure exploits a genuine mispricing or is an amateur retail trap. 1–2 paragraphs.

### 1. Dislocation Context & Catalyst Horizon
* Company profile, market cap, sector
* Catalyst audit: root cause of the sell-off; transient sentiment vs structural decay (cite sources inline)
* Upcoming corporate catalysts: next earnings, investor days, guidance windows

### 2. IV Rank & Volatility Gate
* Current ATM IV · HV20 · IV30/HV20 ratio
* IV Rank / Percentile with source (IBKR IVP 13w/26w/52w → IVR-eq, Barchart, or proxy + cross-check result)
* Anti-ORCL status (sessions since last earnings)
* Gate verdict with the volatility-regime rationale

### 3. Forensic Solvency, SBC & Owner Cash Flow
* GAAP OCF (TTM) · CapEx (flag a guided CapEx surge that turns forward FCF negative) · SBC (subtracted as real dilution)
* Owner FCF = OCF − CapEx − SBC, and owner-FCF yield on market cap
* Cash vs funded debt; net cash / net debt; Debt/EV and the resulting cushion multiplier
* Required strike cushion and the reasons (base / mid-cap / forward FCF<0 or CapEx surge / D/EV)

### 4. Underwriting Matrix
| Ticker | Spot | Short K | Wing K | Structure | % OTM | Δ | IV | IVR (src) | Gate | Net credit | BE | BE cushion | PoT | ROC ann. | Valuation rationale |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

### 5. Pennies-for-Parachutes Spread Architecture
* Short leg: strike, bid/ask, Δ, credit
* Wing: strike (40–60% below spot), ask, OI
* Wing cost ratio = wing ask ÷ short mid = X.X% (≤ 5.0% → mandatory spread)
* Why it matters: cuts buying-power encumbrance roughly 50–75% vs a naked put, hard-caps a multi-sigma crash loss (no forced liquidation), and typically costs only 1–2 points of annualized return.

### 6. Execution & Management Blueprint
* Order staging: exact legs, limit price per the fill rule, session (regular hours; avoid the first 15 minutes)
* GTC buy-to-close at 50% of credit (typically hit in 20–35 days on 60–90 DTE when IV normalizes)
* Quick win: 65–75% within ~14 days → take it
* 21 DTE: close or roll (gamma)
* Defense: Δ ≤ −0.30 or spot within 7% of the short strike → roll 30–60 days out for a net credit

### Scenario Boundaries
| Scenario | Path | P&L per contract |
|---|---|---|
| Bull | Relief rally, IV crush → quick win | +$ |
| Base | Theta + drift → 50% GTC | +$ |
| Bear | Breach below BE → spread max loss / CSP at −40% mark | −$ |
```

Principles behind the rules (for the narrative, not for re-derivation):
- Selling below IVR 30 is picking up pennies in front of a steamroller: thin extrinsic, and a market pullback expands IV against the position.
- Adjusted EPS that adds back SBC is fiction; SBC is recurring dilution and is subtracted.
- Equity is the most junior claim; high Debt/EV accelerates equity losses in a downturn, hence the wider cushion.
- PoT ≈ 2|Δ| is disclosed upfront so an intra-cycle touch is expected, not panic-inducing.
