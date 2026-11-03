# Running the reports as a Gemini skill (Gemini 4 Argon)

## 1. Before 17 Nov: clean up the old Gems
Gems become read-only on 17 Nov. On 17 Dec, Google turns each remaining Gem into a skill automatically. If the four old report Gems are still there by then, they come back as four competing skills that all write to `Market Reports`. Delete them, or at least their instructions, before then.

## 2. Install
1. Build the package from the repo root with `skills/build_gemini_skill.sh`, or use `skills/market-alpha-reports-gemini.zip`.
2. In Gemini, go to Skills → Add skill and upload the **folder** `dist/gemini/market-alpha-reports` (best). Or upload the zip; its root holds `SKILL.md`, `modes/` and `references/`.
3. Make sure Gemini can use Google Drive, Docs, Sheets and Search.
4. To update later, go to More → Replace skill and upload the new folder.

The skill contains instructions only, with no scripts. The math runs in Gemini's code execution, using the formulas in `references/core-rules.md`.

## 3. Replace the Claude audit skill (needed for reliable held-name prices)
Upload `skills/daily-portfolio-audit.zip` in **claude.ai** (not Gemini), under Settings → Capabilities → Skills, replacing the old `daily-portfolio-audit`. The new version adds a data appendix to every WarRoom PDF: every position with class and Floor B, quotes, fills and working orders. It also adds an optional PRE snapshot run at 20:45 ICT (19:45 in US daylight time) that gives the pre-market report real pre-market quotes. `references/warroom-feed-spec.md` is documentation only; don't upload it anywhere.

## 4. Scheduled actions (one per mode)
| Report | US standard time (early Nov to mid Mar) | US daylight time (mid Mar to early Nov) | Prompt |
|---|---|---|---|
| PRE | Mon–Fri 21:00 ICT | Mon–Fri 20:00 ICT | `Use the market-alpha-reports skill: run PRE for today's US session.` |
| MID | Tue–Sat 00:30 ICT | Mon–Fri 23:30 ICT | `Use the market-alpha-reports skill: run MID for the US session in progress.` |
| AH | Tue–Fri 09:30 ICT | Tue–Fri 09:30 ICT | `Use the market-alpha-reports skill: run AH for the US session that just closed.` |
| WKND | Sat 10:00 ICT | Sat 10:00 ICT | `Use the market-alpha-reports skill: run WKND for the week that just ended, including Friday's close-out.` |

Change the PRE and MID schedules on the second Sunday of March and again on the first Sunday of November. The skill works out ET by itself, so only the schedule times need moving.

Each run expects its WarRoom PDF to be in `Robinhood Portfolio Review` first: EOD at about 09:00 ICT, MID at about 00:00 ICT (23:00 ICT in daylight time). If an audit is late, the report flags `STALE FEED` instead of guessing.

## 5. Check the first run of each mode
- The Bottom Line has at most 5 actions. Repeat triggers come first.
- Section 7 starts with a `Book feed:` line and a `Trigger scan: N lines checked` line, and N matches the PDF.
- Works Cited has a provenance line for every Bottom Line number, then the Integrity line.
- The Handoff has FEED / ACTIONS / TRIGGERS, plus PUBLISHED CLOSES in AH and WKND.
- The doc shows real headings, with no `#`, `**` or backticks, and only one doc exists for that day and mode.
- In the PRE scorecard: a `Carry-in` line, not HIT grades.
