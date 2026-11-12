#!/usr/bin/env bash
# Builds the Gemini edition of market-alpha-reports.
# Source: skills/market-alpha-reports-gemini/ (self-contained: SKILL.md, modes/, references/).
# Output: skills/market-alpha-reports-gemini.zip with one top folder, market-alpha-reports/.
set -euo pipefail
cd "$(dirname "$0")/.."
src=skills/market-alpha-reports-gemini
out=dist/gemini/market-alpha-reports
rm -rf dist/gemini && mkdir -p "$out"
cp "$src/SKILL.md" "$out/" && cp -r "$src/modes" "$src/references" "$out/"
rm -f skills/market-alpha-reports-gemini.zip
(cd dist/gemini && zip -rq "$OLDPWD/skills/market-alpha-reports-gemini.zip" market-alpha-reports)
echo "Built $out and skills/market-alpha-reports-gemini.zip"
