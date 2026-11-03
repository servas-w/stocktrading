#!/usr/bin/env bash
# Builds the Gemini edition of market-alpha-reports from the shared sources.
# Output: dist/gemini/market-alpha-reports/ (folder to upload) and
#         skills/market-alpha-reports-gemini.zip (SKILL.md at the zip root).
set -euo pipefail
cd "$(dirname "$0")/.."
src=skills/market-alpha-reports
out=dist/gemini/market-alpha-reports
rm -rf "$out" && mkdir -p "$out/modes" "$out/references"
cp "$src/gemini/SKILL.md" "$out/SKILL.md"
cp "$src"/modes/*.md "$out/modes/"
cp "$src/references/integrity.md" "$out/references/"
rm -f skills/market-alpha-reports-gemini.zip
(cd "$out" && zip -rq "$OLDPWD/skills/market-alpha-reports-gemini.zip" .)
echo "Built $out and skills/market-alpha-reports-gemini.zip"
