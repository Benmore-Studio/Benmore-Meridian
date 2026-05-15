#!/usr/bin/env bash
# Concatenate every captures/out/*/page.gif into one tour GIF.
# Uses ffmpeg to concat frames then gifski to re-encode for size/quality.
#
# Usage:
#   bash stitch-tour.sh
#   FPS=18 GIF_WIDTH=900 bash stitch-tour.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./lib.sh
source "${SCRIPT_DIR}/lib.sh"
require_cmd ffmpeg gifski

fps=$(cfg fps); quality=$(cfg quality); gif_width=$(cfg gif_width)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

# Order: follow sitemap.json so the tour reads top-to-bottom.
if [[ -f "$SITEMAP_FILE" ]]; then
  routes=$(jq -r '.routes[] | (.name // (.path | sub("^/"; "") | sub("/"; "-")))' "$SITEMAP_FILE")
else
  routes=$(find "$OUT_DIR" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort)
fi

count=0
while IFS= read -r name; do
  gif="${OUT_DIR}/${name}/page.gif"
  [[ -f "$gif" ]] || continue
  # Expand the gif into PNG frames in the tmp dir, padded so order is preserved.
  prefix=$(printf '%03d' "$count")
  ffmpeg -hide_banner -loglevel error -y -i "$gif" \
    -vf "fps=${fps},scale=${gif_width}:-1:flags=lanczos" \
    "${tmp}/${prefix}-%04d.png"
  count=$((count + 1))
done <<< "$routes"

if (( count == 0 )); then
  echo "stitch-tour: no page.gif files found in $OUT_DIR — capture some routes first" >&2
  exit 1
fi

out="${OUT_DIR}/tour.gif"
gifski --output "$out" --fps "$fps" --quality "$quality" --width "$gif_width" "${tmp}"/*.png >/dev/null
ls -lh "$out"
