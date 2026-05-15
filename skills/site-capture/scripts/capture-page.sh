#!/usr/bin/env bash
# Capture a single route: full-page PNG + N scroll-position frames + per-page GIF.
# Optionally crops each named component from sitemap.json.
#
# Usage:
#   bash capture-page.sh /weekly
#   FPS=18 FRAMES_PER_PAGE=45 bash capture-page.sh /weekly
#   ROUTE_NAME=hero-shot bash capture-page.sh /
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./lib.sh
source "${SCRIPT_DIR}/lib.sh"
require_cmd playwright-cli gifski jq

ROUTE_PATH_INPUT="${1:-}"
if [[ -z "$ROUTE_PATH_INPUT" ]]; then
  echo "usage: capture-page.sh <path>  (e.g. capture-page.sh /weekly)" >&2
  exit 64
fi

BASE_URL=$(cfg base_url)
SESSION=$(cfg session_name)
ROUTE_NAME="${ROUTE_NAME:-$(slugify "$ROUTE_PATH_INPUT")}"
ROUTE_DIR="${OUT_DIR}/${ROUTE_NAME}"
FRAMES_DIR="${ROUTE_DIR}/frames"
COMPONENTS_DIR="${ROUTE_DIR}/components"
FULL_URL="${BASE_URL%/}${ROUTE_PATH_INPUT}"

probe_url "$FULL_URL" || exit 1

mkdir -p "$FRAMES_DIR" "$COMPONENTS_DIR"
rm -f "${FRAMES_DIR}"/f-*.png

# Look up the route's index in sitemap (for per-route overrides + components).
ROUTE_IDX="-1"
if [[ -f "$SITEMAP_FILE" ]]; then
  ROUTE_IDX=$(jq -r --arg p "$ROUTE_PATH_INPUT" \
    '[.routes[] | .path] | index($p) // -1' "$SITEMAP_FILE")
fi

frames=$( [[ "$ROUTE_IDX" -ge 0 ]] && cfg_for_route "$ROUTE_IDX" frames_per_page || cfg frames_per_page )
wait_nav=$( [[ "$ROUTE_IDX" -ge 0 ]] && cfg_for_route "$ROUTE_IDX" wait_ms_after_nav || cfg wait_ms_after_nav )
wait_frame=$( cfg wait_ms_between_frames )
step_override=$( [[ "$ROUTE_IDX" -ge 0 ]] && cfg_for_route "$ROUTE_IDX" scroll_step_px || cfg scroll_step_px )
fps=$(cfg fps); quality=$(cfg quality); gif_width=$(cfg gif_width)

trap 'pw_close "$SESSION"' EXIT
pw_open "$SESSION" "$FULL_URL"

# Wait for the page to settle.
sleep "$(awk "BEGIN{print ${wait_nav}/1000}")"

# Full-page screenshot first — let playwright-cli scroll itself.
playwright-cli -s="$SESSION" eval "() => window.scrollTo(0, 0)" >/dev/null
pw_screenshot "$SESSION" "${ROUTE_DIR}/full.png"

# Compute scroll step.
range=$(pw_eval "$SESSION" \
  "() => Math.max(0, document.body.scrollHeight - window.innerHeight)" --raw \
  | tr -d '\r' | tail -1)
if (( step_override > 0 )); then
  step="$step_override"
else
  if (( range == 0 )); then
    step=0
  else
    step=$(( range / (frames - 1) ))
    (( step < 1 )) && step=1
  fi
fi

for i in $(seq 0 $((frames - 1))); do
  y=$(( i * step ))
  pw_eval "$SESSION" "() => window.scrollTo(0, ${y})" >/dev/null
  sleep "$(awk "BEGIN{print ${wait_frame}/1000}")"
  pw_screenshot "$SESSION" "${FRAMES_DIR}/f-$(printf '%03d' "$i").png"
done

# Per-page GIF.
gifski \
  --output "${ROUTE_DIR}/page.gif" \
  --fps "$fps" \
  --quality "$quality" \
  --width "$gif_width" \
  "${FRAMES_DIR}"/f-*.png >/dev/null

# Component crops (if any).
if [[ "$ROUTE_IDX" -ge 0 ]]; then
  comp_count=$(jq -r --argjson i "$ROUTE_IDX" \
    '(.routes[$i].components // []) | length' "$SITEMAP_FILE")
  for j in $(seq 0 $((comp_count - 1))); do
    sel=$(jq -r --argjson i "$ROUTE_IDX" --argjson j "$j" \
      '.routes[$i].components[$j].selector' "$SITEMAP_FILE")
    name=$(jq -r --argjson i "$ROUTE_IDX" --argjson j "$j" \
      '.routes[$i].components[$j].name' "$SITEMAP_FILE")
    if [[ -n "$sel" && "$sel" != "null" ]]; then
      playwright-cli -s="$SESSION" screenshot "$sel" \
        --filename="${COMPONENTS_DIR}/${name}.png" >/dev/null 2>&1 || \
        echo "  (component '$name' / '$sel' not found on $ROUTE_PATH_INPUT)" >&2
    fi
  done
fi

# Session is closed by the EXIT trap on success or failure.
echo "✓ ${ROUTE_NAME}  (${frames} frames, page.gif → ${ROUTE_DIR}/page.gif)"
