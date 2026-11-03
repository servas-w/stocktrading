# Running the reports as a Gemini skill (Gemini 4 Argon)

## 1. Before 17 Nov: clean up the old Gems
Gems become read-only on 17 Nov. On 17 Dec, Google turns each remaining Gem into a skill automatically. If the four old report Gems are still there by then, they come back as four competing skills that all write to `Market Reports`. Delete them, or at least their instructions, before then.

## 2. Install
1. Build the package from the repo root with `skills/build_gemini_skill.sh`, or use `skills/market-alpha-reports-gemini.zip`.
2. In Gemini, go to Skills → Add skill and upload the **folder** `market-alpha-reports` (best). Or upload the zip; its root holds `SKILL.md`, `modes/` and `references/`.
3. Optional: also upload `apply-market-report-standards`, `render-book-desks` and `build-short-bench` as their own skills.
4. Make sure Gemini can use Google Drive, Docs, Sheets and Search.
5. To update later, go to More → Replace skill and upload the new folder.

The skill contains instructions only, with no scripts. Gemini skills can't run bundled scripts that reach the web, so the math runs in Gemini's own code execution, using the formulas in `SKILL.md`.

## 3. Scheduled actions (one per mode)
Times are Da Nang (ICT) during US standard time, from 2 Nov to the second Sunday of March. During US daylight time, run PRE at 20:00.

| Schedule | Prompt |
|---|---|
| Mon–Fri 21:00 | `Use the market-alpha-reports skill: run PRE for today's US session.` |
| Tue–Sat 00:30 | `Use the market-alpha-reports skill: run MID for the US session in progress.` |
| Tue–Fri 09:30 | `Use the market-alpha-reports skill: run AH for the US session that just closed.` |
| Sat 10:00 | `Use the market-alpha-reports skill: run WKND for the week that just ended, including Friday's close-out.` |

Each run expects its WarRoom PDF to be in `Robinhood Portfolio Review` first. The Claude audits create them at about 09:00 ICT (EOD) and 00:00 ICT (MID). If an audit is late, the report flags `STALE FEED` instead of guessing.

## 4. Check the first run of each mode
- The Bottom Line has a `Book feed:` line and at most 5 actions.
- The Integrity line appears at the end of Works Cited.
- The doc shows real headings, with no `#`, `**` or backticks, and only one doc exists for that day and mode.
