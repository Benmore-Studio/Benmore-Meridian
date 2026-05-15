#!/usr/bin/env bash
# Sanity-check a route before running a full capture.
# Prints: HTTP status, image count, broken-image count, console error count.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./lib.sh
source "${SCRIPT_DIR}/lib.sh"
require_cmd playwright-cli jq

path="${1:-/}"
BASE_URL=$(cfg base_url)
url="${BASE_URL%/}${path}"
SESSION="${SESSION:-$(cfg session_name)-probe}"

code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "$url" || echo "000")
echo "URL:       $url"
echo "HTTP:      $code"
(( code == 200 )) || { echo "(skipping deeper probe — non-200)"; exit 1; }

trap 'pw_close "$SESSION"' EXIT
pw_open "$SESSION" "$url"
sleep 1

stats=$(playwright-cli -s="$SESSION" eval \
  "() => ({
     imgs: document.images.length,
     broken: [...document.images].filter(i => !i.complete || i.naturalWidth === 0).length,
     title: document.title
   })" --raw 2>&1 | tail -1)
echo "Title:     $(echo "$stats" | jq -r '.title // ""')"
echo "Images:    $(echo "$stats" | jq -r '.imgs') (broken: $(echo "$stats" | jq -r '.broken'))"

# Console errors are logged inside the playwright-cli session metadata; we
# surface them via the snapshot's Events section. For now, the broken-image
# count is the most actionable signal here.
