#!/usr/bin/env bash
# One-off component crop. Doesn't require the route to be in sitemap.json.
#
# Usage:
#   bash capture-component.sh / "header nav" nav
#   bash capture-component.sh /weekly "[data-day='May 5']" may5-filter
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./lib.sh
source "${SCRIPT_DIR}/lib.sh"
require_cmd playwright-cli

path="${1:-}"; selector="${2:-}"; name="${3:-component}"
if [[ -z "$path" || -z "$selector" ]]; then
  echo "usage: capture-component.sh <path> <selector> [name]" >&2
  exit 64
fi

BASE_URL=$(cfg base_url)
SESSION=$(cfg session_name)
out_dir="${OUT_DIR}/$(slugify "$path")/components"
mkdir -p "$out_dir"

trap 'pw_close "$SESSION"' EXIT
pw_open "$SESSION" "${BASE_URL%/}${path}"
sleep "$(awk "BEGIN{print $(cfg wait_ms_after_nav)/1000}")"
playwright-cli -s="$SESSION" screenshot "$selector" \
  --filename="${out_dir}/${name}.png" >/dev/null
echo "✓ ${out_dir}/${name}.png"
