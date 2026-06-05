#!/usr/bin/env bash
#==============================================================
# Build the IEEE TIFS submission archives.
#
#   pixelroot_submission.zip    -> Main Manuscript slot (LaTeX bundle)
#   pixelroot_supplementary.zip -> Supplementary Material slot (optional)
#
# Run from the repo root or anywhere; paths are resolved relative to
# this script's location (paper/submission/).
#==============================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAPER="$(cd "$HERE/.." && pwd)"
OUT="$HERE/dist"
rm -rf "$OUT"
mkdir -p "$OUT"

#--- 1. Main Manuscript bundle ---------------------------------
STAGE="$OUT/manuscript"
mkdir -p "$STAGE/figures"
cp "$PAPER/pixelroot.tex"   "$STAGE/"
cp "$PAPER/references.bib"  "$STAGE/"
cp "$PAPER/registry.sol"    "$STAGE/"
cp "$PAPER/figures/"*.pdf   "$STAGE/figures/"

( cd "$STAGE" && zip -qr "$OUT/pixelroot_submission.zip" . )
echo "Built: $OUT/pixelroot_submission.zip"
unzip -l "$OUT/pixelroot_submission.zip"

#--- 2. Supplementary material (optional) ----------------------
SUP="$OUT/supplementary"
mkdir -p "$SUP"
# Experiment scripts, plan, and manufacturing deep-dive — NOT data.
cp "$PAPER/experiments/"*.py            "$SUP/" 2>/dev/null || true
cp "$PAPER/experiments/"*.md            "$SUP/" 2>/dev/null || true
cp "$PAPER/experiments/requirements.txt" "$SUP/" 2>/dev/null || true
cp "$PAPER/experiments/fetch_data.sh"   "$SUP/" 2>/dev/null || true

( cd "$SUP" && zip -qr "$OUT/pixelroot_supplementary.zip" . )
echo "Built: $OUT/pixelroot_supplementary.zip"

echo "Done. Archives are in: $OUT"
