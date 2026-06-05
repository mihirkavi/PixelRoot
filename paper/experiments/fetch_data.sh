#!/usr/bin/env bash
# Download the public Kodak True Color image suite (24 images) used by the
# PixelRoot real-image experiments.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)/data/kodak"
mkdir -p "$DIR"
for i in $(seq -w 1 24); do
  out="$DIR/kodim${i}.png"
  if [ ! -f "$out" ]; then
    curl -fsSL -o "$out" "https://r0k.us/graphics/kodak/kodak/kodim${i}.png"
    echo "fetched kodim${i}.png"
  fi
done
echo "Kodak suite ready in $DIR ($(ls -1 "$DIR"/*.png | wc -l) images)."
