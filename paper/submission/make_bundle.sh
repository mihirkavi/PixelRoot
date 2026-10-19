#!/usr/bin/env bash
#==============================================================
# Build the submission archives from a clean copy of the sources.
#
# Two versions come from one source (pixelroot.tex, switch \ifshort):
#   - TIFS submission  : pixelroot_tifs.tex  (<= 13 pages incl. references)
#   - Full version     : pixelroot.tex       (arXiv preprint; TIFS supplement)
#
# Outputs in dist/:
#   pixelroot_tifs.pdf               -> IEEE "Main Document - PDF" slot
#   pixelroot_tifs_submission.zip    -> IEEE "Main Manuscript" (LaTeX) slot
#   pixelroot_supplementary.zip      -> IEEE "Supplementary Material": the full
#                                       version PDF + code, contract, results
#   pixelroot_full.pdf               -> the arXiv preprint, as it will render
#   pixelroot_arxiv.tar.gz           -> arXiv upload (TeX + .bbl, no .bib)
#
# Each LaTeX bundle is compiled from scratch, so a missing file fails here
# rather than on the portal. Requires: pdflatex, bibtex (TeX Live with
# IEEEtran), pdfinfo, zip, tar.
#==============================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAPER="$(cd "$HERE/.." && pwd)"
OUT="$HERE/dist"
TIFS_MAX_PAGES=13
rm -rf "$OUT"
mkdir -p "$OUT"

stage_sources() {   # $1 = destination directory
  mkdir -p "$1/figures" "$1/contracts/src"
  cp "$PAPER/pixelroot.tex" "$PAPER/pixelroot_tifs.tex" "$PAPER/references.bib" "$1/"
  cp "$PAPER/figures/"*.pdf "$PAPER/figures/"*.png "$1/figures/"
  cp "$PAPER/contracts/src/PixelRootRegistry.sol" "$1/contracts/src/"
}

compile() {         # $1 = directory, $2 = job name
  ( cd "$1"
    pdflatex -interaction=nonstopmode -halt-on-error "$2" >/dev/null
    bibtex "$2" >/dev/null
    for _ in 1 2 3 4; do   # floats can move labels; settle cross-references
      pdflatex -interaction=nonstopmode -halt-on-error "$2" >/dev/null
      grep -q "Rerun to get" "$2.log" || break
    done
    if grep -qE "(Citation|Reference) .* undefined|Rerun to get" "$2.log"; then
      echo "LaTeX reports unresolved references in $1/$2" >&2; exit 1
    fi )
}

pages() { pdfinfo "$1" | awk '/^Pages:/ {print $2}'; }

BUILD="$OUT/build"
stage_sources "$BUILD"
compile "$BUILD" pixelroot_tifs
compile "$BUILD" pixelroot
cp "$BUILD/pixelroot_tifs.pdf" "$OUT/pixelroot_tifs.pdf"
cp "$BUILD/pixelroot.pdf" "$OUT/pixelroot_full.pdf"
NT=$(pages "$OUT/pixelroot_tifs.pdf")
if [ "$NT" -gt "$TIFS_MAX_PAGES" ]; then
  echo "TIFS version is $NT pages; the limit is $TIFS_MAX_PAGES" >&2; exit 1
fi

#--- 1. IEEE TIFS Main Manuscript bundle ------------------------
STAGE="$OUT/tifs"
stage_sources "$STAGE"
cp "$BUILD/pixelroot_tifs.bbl" "$STAGE/"
( cd "$STAGE" && zip -qr "$OUT/pixelroot_tifs_submission.zip" . )
echo "Built: pixelroot_tifs.pdf ($NT pages) and pixelroot_tifs_submission.zip"

#--- 2. arXiv bundle: full version, .bbl instead of .bib ---------
ARX="$OUT/arxiv"
stage_sources "$ARX"
rm "$ARX/references.bib" "$ARX/pixelroot_tifs.tex"
cp "$BUILD/pixelroot.bbl" "$ARX/"
CHECK="$OUT/arxiv_check"
cp -r "$ARX" "$CHECK"
( cd "$CHECK"
  for _ in 1 2 3 4; do pdflatex -interaction=nonstopmode -halt-on-error pixelroot >/dev/null; done
  if grep -qE "(Citation|Reference) .* undefined|Rerun to get" pixelroot.log; then
    echo "arXiv bundle does not compile cleanly" >&2; exit 1
  fi )
rm -rf "$CHECK"
tar -czf "$OUT/pixelroot_arxiv.tar.gz" -C "$ARX" .
echo "Built: pixelroot_arxiv.tar.gz ($(pages "$OUT/pixelroot_full.pdf") pages; verified to compile with pdfLaTeX alone)"

#--- 3. Supplementary material: extended version + code ---------
SUP="$OUT/supplementary"
mkdir -p "$SUP/experiments/tests" "$SUP/contracts/src" "$SUP/contracts/test"
cp "$OUT/pixelroot_full.pdf" "$SUP/PixelRoot_extended_version.pdf"
cp "$PAPER/experiments/"*.py "$PAPER/experiments/EXPERIMENT_PLAN.md" "$PAPER/experiments/MANUFACTURING.md" \
   "$PAPER/experiments/requirements.txt" "$PAPER/experiments/fetch_data.sh" "$SUP/experiments/"
mkdir -p "$SUP/experiments/results"
cp "$PAPER/experiments/results/"*.txt "$PAPER/experiments/results/"*.csv \
   "$PAPER/experiments/results/"*.json "$SUP/experiments/results/"
cp "$PAPER/experiments/tests/"*.py "$SUP/experiments/tests/"
cp "$PAPER/contracts/package.json" "$PAPER/contracts/package-lock.json" \
   "$PAPER/contracts/hardhat.config.js" "$SUP/contracts/"
cp "$PAPER/contracts/src/"*.sol "$SUP/contracts/src/"
cp "$PAPER/contracts/test/"* "$SUP/contracts/test/"
cat > "$SUP/README.txt" <<'TXT'
PixelRoot -- supplementary material

PixelRoot_extended_version.pdf  Full version of the paper: manufacturing feasibility
                                analysis (M1-M3), per-pixel localization (E3), PRNU
                                baseline (E4), full related work and threat
                                catalogue, micro-benchmarks, and the contract listing.
experiments/                    Evaluation code and measured results (E1-E6); see
                                EXPERIMENT_PLAN.md to reproduce. Image data are not
                                included: fetch_data.sh downloads the public Kodak set.
contracts/                      PixelRootRegistry.sol and its Hardhat test suite
                                (npm ci && npm test).
TXT
( cd "$SUP" && zip -qr "$OUT/pixelroot_supplementary.zip" . )
echo "Built: pixelroot_supplementary.zip"

rm -rf "$BUILD"
echo "Done. Archives are in: $OUT"
