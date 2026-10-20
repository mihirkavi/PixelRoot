#!/usr/bin/env bash
# Build the schematic figures (TikZ/circuitikz, drawn at printed size in Times)
# into figures/*.pdf. Requires pdflatex with tikz, circuitikz and standalone.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
for f in fig_architecture fig_gain_spectrum fig_m1_dcg fig_m2_coded fig_m3_stack fig_datapath; do
  pdflatex -interaction=nonstopmode -halt-on-error "$f.tex" >/dev/null
  cp "$f.pdf" "../$f.pdf"
done
rm -f ./*.aux ./*.log ./*.pdf
echo "schematic figures written to $(cd .. && pwd)"
