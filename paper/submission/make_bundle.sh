#!/usr/bin/env bash
#==============================================================
# Build the submission archives from a clean copy of the sources.
#
#   dist/pixelroot_submission.zip     -> IEEE TIFS "Main Manuscript" slot
#   dist/pixelroot.pdf                -> IEEE TIFS "Main Document - PDF" slot
#   dist/pixelroot_arxiv.tar.gz       -> arXiv upload (TeX source + .bbl)
#   dist/pixelroot_supplementary.zip  -> optional supplementary material
#
# Each LaTeX bundle is compiled from scratch in its own directory, so a
# missing file fails the build here rather than on the portal.
# Requires: pdflatex, bibtex (TeX Live with IEEEtran), zip, tar.
#==============================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAPER="$(cd "$HERE/.." && pwd)"
OUT="$HERE/dist"
rm -rf "$OUT"
mkdir -p "$OUT"

stage_sources() {   # $1 = destination directory
  mkdir -p "$1/figures" "$1/contracts/src"
  cp "$PAPER/pixelroot.tex" "$PAPER/references.bib" "$1/"
  cp "$PAPER/figures/"*.pdf "$PAPER/figures/"*.png "$1/figures/"
  cp "$PAPER/contracts/src/PixelRootRegistry.sol" "$1/contracts/src/"
}

compile() {         # $1 = directory containing pixelroot.tex
  ( cd "$1"
    pdflatex -interaction=nonstopmode -halt-on-error pixelroot >/dev/null
    bibtex pixelroot >/dev/null
    pdflatex -interaction=nonstopmode -halt-on-error pixelroot >/dev/null
    pdflatex -interaction=nonstopmode -halt-on-error pixelroot >/dev/null
    for _ in 1 2; do   # floats can move labels; settle cross-references
      grep -q "Rerun to get" pixelroot.log || break
      pdflatex -interaction=nonstopmode -halt-on-error pixelroot >/dev/null
    done
    if grep -qE "(Citation|Reference) .* undefined|Rerun to get" pixelroot.log; then
      echo "LaTeX reports unresolved references in $1" >&2; exit 1
    fi )
}

#--- 1. IEEE Main Manuscript bundle ----------------------------
BUILD="$OUT/build"
stage_sources "$BUILD"
compile "$BUILD"
cp "$BUILD/pixelroot.pdf" "$OUT/pixelroot.pdf"

STAGE="$OUT/manuscript"
stage_sources "$STAGE"
cp "$BUILD/pixelroot.bbl" "$STAGE/"
( cd "$STAGE" && zip -qr "$OUT/pixelroot_submission.zip" . )
echo "Built: $OUT/pixelroot_submission.zip and $OUT/pixelroot.pdf ($(pdfinfo "$OUT/pixelroot.pdf" | awk '/Pages/ {print $2}') pages)"

#--- 2. arXiv bundle (arXiv does not run BibTeX: ship the .bbl) ---
ARX="$OUT/arxiv"
stage_sources "$ARX"
cp "$BUILD/pixelroot.bbl" "$ARX/"
rm "$ARX/references.bib"
# verify that the arXiv bundle compiles on its own with pdflatex only
CHECK="$OUT/arxiv_check"
cp -r "$ARX" "$CHECK"
( cd "$CHECK"
  for _ in 1 2 3 4; do pdflatex -interaction=nonstopmode -halt-on-error pixelroot >/dev/null; done
  if grep -qE "(Citation|Reference) .* undefined|Rerun to get" pixelroot.log; then
    echo "arXiv bundle does not compile cleanly" >&2; exit 1
  fi )
rm -rf "$CHECK"
tar -czf "$OUT/pixelroot_arxiv.tar.gz" -C "$ARX" .
echo "Built: $OUT/pixelroot_arxiv.tar.gz (verified to compile without BibTeX)"

#--- 3. Supplementary material (code, not data) -----------------
SUP="$OUT/supplementary"
mkdir -p "$SUP/experiments/tests" "$SUP/contracts/src" "$SUP/contracts/test"
cp "$PAPER/experiments/"*.py "$PAPER/experiments/"*.md \
   "$PAPER/experiments/requirements.txt" "$PAPER/experiments/fetch_data.sh" "$SUP/experiments/"
cp -r "$PAPER/experiments/results" "$SUP/experiments/"
cp "$PAPER/experiments/tests/"*.py "$SUP/experiments/tests/"
cp "$PAPER/contracts/package.json" "$PAPER/contracts/package-lock.json" \
   "$PAPER/contracts/hardhat.config.js" "$SUP/contracts/"
cp "$PAPER/contracts/src/"*.sol "$SUP/contracts/src/"
cp "$PAPER/contracts/test/"* "$SUP/contracts/test/"
( cd "$SUP" && zip -qr "$OUT/pixelroot_supplementary.zip" . )
echo "Built: $OUT/pixelroot_supplementary.zip"

rm -rf "$BUILD"
echo "Done. Archives are in: $OUT"
