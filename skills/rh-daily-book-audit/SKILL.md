---
name: rh-daily-book-audit
description: Wilson's daily audit of the positions he OPENED in the latest US session on Robinhood account 5QR66081, with blunt Shkreli-style forensic commentary on each new trade and on how it changes his portfolio composition. Grades each new leg against Playbook v2, stress-tests it, gives a verdict, then shows before/after book concentration. Use when the user says "RH daily audit", "daily book audit", "audit today's trades" or "audit my new positions today". For the weekly version use rh-weekly-book-audit; for Axe/Wendy roleplay use the war room skill.
---

# RH daily book audit

Requires the **Robinhood** connector. Read-only: never place, modify or cancel orders. Account `5QR66081` only. If a result is too large, use code execution (jq/python) or read in chunks. Do not call `get_equity_news` (unreliable). Reply in chat, no preamble. Email (Gmail, wilsonhersandy@gmail.com) only if asked.

**Scope = positions opened in the session.** Session = today's US session if it has traded, else the latest finished one; match each execution's `trade_date`, not `created_at`.

**Step 1: Opens**
- `get_option_orders` and `get_equity_orders` (state=filled, last 5 days, all pages). Keep executions with `trade_date` = session and opening effect (open, buy, sell_short). Group multi-leg orders into one position (spread, calendar, covered call, roll = close + open).
- Also list working orders (state open) as "pending".
- **No opens**: say so in one line, show only Step 4 (composition + fire alarms), stop.

**Step 2: Data per new position**
`get_option_instruments`, `get_option_quotes` (delta, IV, mark), `get_equity_quotes`, `get_equity_fundamentals`, `get_earnings_results` (next date; "tent." if unverified), `get_equity_historicals` (day, ~6 days: flag >= 8% moves; cause "unknown" unless sourced), `get_sec_filing_index` for sub-$10B names (8-K, offerings, 13D/G, going concern). Use `get_financials` / `get_equity_analyst_ratings` when the forensic read needs them.

**Step 3: Per new position (the core)**
Metrics: credit, cushion %, delta, IV, DTE, breakeven, assignment notional, max loss, ROC and annualized ROC, % NAV (notional + held shares).
- **Grade (Playbook v2)**: A fits every rule; B event before expiry or DTE slightly off 60-90; C delta >= 0.25, ITM, <= 30 DTE, unstructured binary, or sub-$5 biotech sold >= 0.40 delta (stock replacement). Also check IV gate (IVR >= 50 or spread exception), one opening ticket per name per day, OPP tag if < 30 DTE, no puts on underwater lots, 3:1 on debit trades.
- **Forensic read, Shkreli-style** (blunt, skeptical, funny, numbers first, never padded): follow the cash. Biotech: cash/share vs strike, burn runway, ATM/dilution, debt, Floor A/B. Large-cap: owner FCF (OCF - CapEx - SBC), debt, what the sell-off priced in. Say what the market is actually afraid of, whether you're being paid for it, and what the strike really means in dollars per share.
- **The bear case in one line** (best argument you're wrong) and **kill-shot** (the single fact that would make you close: price, filing, date).
- **Stress**: P&L at -10% / -20% / -35% on the underlying vs the premium collected. How many days of theta does one bad day cost?
- **Verdict**: one sentence + "Would I do it again? Y/N".

**Step 4: Portfolio composition (before vs after today)**
`get_portfolio`, `get_equity_positions`, `get_option_positions` (nonzero, all pages; strip trailing digits from adjusted chains).
- Show **before -> after**: % NAV by name (notional + shares), by theme (biotech / AI-semis / crypto / large-cap / index), net delta $, theta/day, cash and BP %.
- Mark names >= 8% NAV amber, >10% red (10% NAV cap counts held shares). Flag if today's trade stacked an existing theme or the same earnings week.
- **Fire alarms** on the rest of the book, one line each, max 4: ITM, delta <= -0.30, within 7% of strike, <= 21 DTE, >= 50% captured with no GTC resting, short stock.

**Journal + scoreboard (Google Drive, optional)**
Append-only, one small file per entry. The Drive connector's `update_file` changes metadata only, never content, so never edit an existing file: write a new one.
- **Folders**: `search_files` with `title = 'RH Trade Journal' and mimeType = 'application/vnd.google-apps.folder'` (same for **"RH Audit Scoreboard"**); if missing, `create_file` with `contentMimeType: application/vnd.google-apps.folder`. Keep both folder ids.
- **Read the journal**: for each new position, `search_files` with `parentId = '<journal folder id>' and title contains '<TICKER>'`, then `read_file_content` each hit. Entry titles are `YYYY-MM-DD TICKER EXPIRY STRIKES STRUCTURE` (expiry `YYYY-MM-DD`, strikes like `4-3`); match by ticker + expiry + strikes, and if several match, the newest date wins. Show **"Your thesis"** (the line you wrote) next to the outcome, and say whether the thesis held, was wrong, or was never written (then ask for a one-liner and offer to log it).
- **Write a journal entry** (a thesis given now, or a considered trade now filled): `create_file` in the journal folder with `parentId`, the title above, `contentMimeType: text/plain`, `disableConversionToGoogleType: true`, and `textContent` = `date | ticker | structure | strikes | expiry | qty | price | grade | thesis | kill-shot | status: filled`.
- **Scoreboard**: after the audit, `create_file` in the scoreboard folder (same settings) titled `YYYY-MM-DD daily` with `textContent` = the header `date,type,trades,avg_grade,premium_sold,pct_captured,cap_breaches,rule_score,sleep_score,top_theme_pct,week_pnl` plus one row.
If Drive is off, skip silently and print the row at the end of the reply instead.

**Sleep-at-night score (0-10, 10 = sleeps fine)**: start at 10. Subtract: 1 per name over 8% NAV (2 if over 10%), 1 per short leg ITM or within 7% of strike, 1 per short leg <= 21 DTE and near the money, 1 if net short-stock/unlimited risk is open, 1 if a -20% market day costs > 5% NAV, 1 if cash+BP < 20% NAV, 1 if > 40% NAV sits in one theme. Floor 0. Show the score with the 2-3 biggest deductions and the single fix that adds the most points.

**Output (chat), in this order**
1. Headline in one punchy line: e.g. "3 new trades: A, B, C. Book is 41% biotech. Shkreli would raise an eyebrow."
2. Trade cards (one per new position): grade badge, metrics line, **your thesis (from journal)**, forensic read, bear case, kill-shot, stress, verdict.
3. Composition before -> after (compact table) + a **Concentration meter** (e.g. biotech ████████░░ 38%). Then **Sleep-at-night: X/10** with deductions and the best fix.
4. Fire alarms.
5. Scoreboard row logged (or printed). **One lesson for tomorrow** (the rule or habit today's trades most tested).
6. Footer: "Points to weigh, not orders."

Tone: dry, sharp, a bit irreverent; roast the trade, not the person; no hype, no filler. Short sentences. Numbers beat adjectives.
