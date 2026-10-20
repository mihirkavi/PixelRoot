#!/usr/bin/env bash
# Download the public Kodak True Color image suite (24 images) used by the
# PixelRoot real-image experiments.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)/data/kodak"
mkdir -p "$DIR"
# Primary source: r0k.us. Fallback: a public GitHub mirror of the same 24 PNGs
# (PhotoCD_PCD0992/NN.png), verified to reproduce results/e1_robustness.txt
# byte for byte.
MIRROR="https://github.com/MohamedBakrAli/kodak-lossless-true-color-image-suite"
for i in $(seq -w 1 24); do
  out="$DIR/kodim${i}.png"
  if [ ! -f "$out" ]; then
    if curl -fsSL -o "$out" "https://r0k.us/graphics/kodak/kodak/kodim${i}.png"; then
      echo "fetched kodim${i}.png"
    else
      rm -f "$out"
      if [ ! -d "$DIR/.mirror" ]; then
        git clone --depth 1 "$MIRROR" "$DIR/.mirror"
      fi
      cp "$DIR/.mirror/PhotoCD_PCD0992/${i}.png" "$out"
      echo "copied kodim${i}.png from mirror"
    fi
  fi
done
echo "Kodak suite ready in $DIR ($(ls -1 "$DIR"/*.png | wc -l) images)."
