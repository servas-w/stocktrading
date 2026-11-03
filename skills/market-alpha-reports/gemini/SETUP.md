# Running the reports on Gemini 4 Argon

## 1. Create one Gem
- **Name:** Market Alpha Reports
- **Model:** Gemini 4 Argon
- **Instructions:** paste all of `GEM_INSTRUCTIONS.md`
- **Knowledge files:** attach
  - `modes/pre-market.md`, `modes/mid-day.md`, `modes/after-hours.md`, `modes/weekend.md`
  - `references/integrity.md`
  - Optional, if you have them as files: `apply-market-report-standards`, `render-book-desks` (with `references/trade-journal.md`), `build-short-bench`, Playbook v2.5
- **Apps / extensions:** Google Drive, Google Docs, Google Sheets, Google Search. Turn on code execution if your plan has it.

Retire the four old report Gems or prompts so that only this one writes to `Market Reports`.

## 2. Scheduled actions (one per mode, all using this Gem)
Times are Da Nang (ICT) during US standard time, from 2 Nov to the second Sunday of March. During US daylight time, run PRE an hour earlier (20:00).

| Schedule | Prompt |
|---|---|
| Mon–Fri 21:00 | `Run PRE for today's US session.` |
| Tue–Sat 00:30 | `Run MID for the US session in progress.` |
| Tue–Fri 09:30 | `Run AH for the US session that just closed.` |
| Sat 10:00 | `Run WKND for the week that just ended, including Friday's close-out.` |

Each run expects its WarRoom PDF to be in `Robinhood Portfolio Review` first. The Claude audits create them at about 09:00 ICT (EOD) and 00:00 ICT (MID). If an audit is late, the report flags `STALE FEED` instead of guessing.

## 3. Check the first run of each mode
- The Bottom Line has a `Book feed:` line and at most 5 actions.
- The Integrity line appears at the end of Works Cited.
- The doc shows real headings, with no `#`, `**` or backticks, and only one doc exists for that day and mode.
