# Running the reports as a Gemini skill (Gemini 4 Argon)

## 1. Before 17 Nov: clean up the old Gems
Gems become read-only on 17 Nov. On 17 Dec, Google turns each remaining Gem into a skill automatically. If the four old report Gems are still there by then, they come back as four competing skills that all write to `Market Reports`. Delete them, or at least their instructions, before then.

## 2. Install
1. Build the package from the repo root with `skills/build_gemini_skill.sh`, or use `skills/market-alpha-reports-gemini.zip`. The source is `skills/market-alpha-reports-gemini/` (self-contained; it no longer shares files with the Claude edition).
2. In Gemini, go to Skills → Add skill and upload the zip, or the **folder** `dist/gemini/market-alpha-reports`.
3. Make sure Gemini can use Google Drive, Docs, Sheets and Search.
4. To update later, go to More → Replace skill and upload the new folder.

The skill contains instructions only, with no scripts. The math runs in Gemini's code execution, using the formulas in `references/core-rules.md`.

## 3. Replace the Claude audit skill (needed for reliable held-name prices)
Upload `skills/daily-portfolio-audit.zip` in **claude.ai** (not Gemini), under Settings → Capabilities → Skills, replacing the old `daily-portfolio-audit`. The new version adds a data appendix to every WarRoom PDF: every position with class and Floor B, quotes, fills and working orders. It also adds an optional PRE snapshot run at 20:45 ICT (19:45 in US daylight time) that gives the pre-market report real pre-market quotes. `references/warroom-feed-spec.md` is documentation only; don't upload it anywhere.

## 4. Scheduled action (Gemini runs MID only)
Claude runs PRE, AH and WKND, so they can't overwrite each other's docs (see `references/core-rules.md` §11). Gemini gets one schedule:

| Report | US standard time (early Nov to mid Mar) | US daylight time (mid Mar to early Nov) | Prompt |
|---|---|---|---|
| MID | Tue–Sat 00:30 ICT | Mon–Fri 23:30 ICT | `Use the market-alpha-reports skill: run MID for the US session in progress.` |

Delete any Gemini schedules for PRE, AH and WKND. If one fires anyway, the skill stops without writing a doc.

Each run expects the MID WarRoom PDF in `Robinhood Portfolio Review` first, at about 00:00 ICT (23:00 ICT in daylight time). If the audit is late, the report flags `STALE FEED` instead of guessing.

## 5. Check the first run of each mode
- Section 1 (Summary) is at most 7 lines, and repeat triggers come first.
- The header shows `Runner: Gemini` and the PDF's `CHECK:` line; A1 shows `Trigger scan: N lines checked (Q quoted · U unquoted)` and N matches the PDF's short option lines + stock lines.
- A5 has a source line for every number in Sections 1–3, then the Integrity line.
- No order in Section 3 sits on a `strike inferred` row.
- The Handoff has FEED / ACTIONS / TRIGGERS, plus PUBLISHED CLOSES in AH and WKND.
- The doc shows real headings, with no `#`, `**` or backticks, and only one doc exists for that day and mode.
