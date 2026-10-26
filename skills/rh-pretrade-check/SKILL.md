---
name: rh-pretrade-check
description: Wilson's pre-trade check for a trade he is CONSIDERING (not yet placed) on Robinhood account 5QR66081. Takes a pasted trade (e.g. "sell 5 FHTX Jan 2 put spread 4/3 for 0.45") and returns the same trade card as the daily audit - Playbook v2 grade, Shkreli-style forensic read, bear case, kill-shot, stress, and before/after portfolio composition including 10% NAV cap and sleep-at-night score - then logs his thesis to the Drive trade journal. Use when the user says "RH pretrade", "pre-trade check", "check this trade before I place it", "should I sell...", or pastes a proposed option trade. Never places orders.
---

# RH pre-trade check

Requires the **Robinhood** connector (Google Drive optional for the journal). Read-only: never place, modify, cancel or even preview orders. Account `5QR66081` only. Do not call `get_equity_news`. Chat reply, no preamble.

**Input**: ticker, structure, strikes, expiry, qty, limit price. If any is missing, ask once, in one line. Quantity default: 1.

**Step 1: Live data** - `get_option_chains` / `get_option_instruments` to find the contract(s), `get_option_quotes` (bid/ask, delta, IV, OI), `get_equity_quotes`, `get_equity_fundamentals`, `get_earnings_results`, `get_equity_historicals` (day, ~10 days, >= 8% moves), `get_sec_filing_index` for sub-$10B names. Check whether the limit price is inside the bid/ask (flag a fill-unlikely or giving-away price). `get_equity_orders`/`get_option_orders` for a same-name opening ticket today (rule: one opening ticket per name per day) and any resting order on the name.

**Step 2: Trade card** - credit, cushion %, delta, IV (and IV rank if the data supports it; else say "IVR unverified"), DTE, breakeven, assignment notional, max loss, ROC and annualized ROC, % NAV.
- **Grade (Playbook v2)**: A fits all rules; B event before expiry or DTE slightly off 60-90; C delta >= 0.25, ITM, <= 30 DTE, unstructured binary, sub-$5 biotech sold >= 0.40 delta. Also check: IV gate (IVR >= 50 or spread exception), OPP tag if < 30 DTE, no puts on underwater lots, 3:1 on debit trades, 10% NAV cap counting held shares.
- **Shkreli-style forensic read**: follow the cash (biotech: cash/share vs strike, runway, dilution, Floor A/B; large-cap: owner FCF, debt, what the sell-off priced in). What is the market afraid of, and does this strike get paid for it?
- **Bear case** (one line), **kill-shot** (exact trigger to close), **stress** at -10 / -20 / -35% vs premium, **better version** (one alternative strike/expiry/structure if it grades B or C).

**Step 3: Portfolio impact** - `get_portfolio`, `get_equity_positions`, `get_option_positions` (nonzero, all pages; strip trailing digits). Show **before -> after**: % NAV by name and theme with concentration meters, net delta, theta/day, cash/BP, earnings-week stacking, and **sleep-at-night score** before -> after (start 10; -1 per name > 8% NAV (-2 if > 10%), -1 per short leg ITM/within 7% of strike, -1 per near-the-money leg <= 21 DTE, -1 open short stock, -1 if a -20% market day costs > 5% NAV, -1 if cash+BP < 20% NAV, -1 if > 40% NAV in one theme).

**Step 4: Verdict + journal** - one line: **GO / TRIM SIZE / WAIT / PASS** with the reason, and the max qty that keeps the name <= 10% NAV. Ask Wilson for a one-line thesis if he hasn't given one. If Google Drive is on, `search_files` "RH Trade Journal" (create it if missing), `read_file_content`, append `date | ticker | structure | strikes | expiry | qty | price | grade | thesis | kill-shot | status: considered` and `update_file`. The daily/weekly audits will match this entry to the fill later. Do not log if he says pass.

Footer: "Points to weigh, not orders." Tone: dry, sharp, a bit irreverent; roast the trade, not the person.
