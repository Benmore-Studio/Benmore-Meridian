#!/usr/bin/env bash
# Iterate every route in captures/sitemap.json and call capture-page.sh for each.
# Keeps a single playwright-cli session alive across routes for speed.
#
# Usage:
#   BASE_URL=http://localhost:5001 bash capture-all.sh
#   FILTER=weekly bash capture-all.sh        # only routes whose name matches
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./lib.sh
source "${SCRIPT_DIR}/lib.sh"
require_cmd playwright-cli gifski jq

[[ -f "$SITEMAP_FILE" ]] || { echo "no sitemap at $SITEMAP_FILE — run init.sh first" >&2; exit 64; }

BASE_URL=$(cfg base_url)
probe_url "$BASE_URL" || exit 1

filter="${FILTER:-}"
total=$(route_count)
ok=0; failed=0

echo "site-capture: ${total} route(s) against ${BASE_URL}"
for i in $(seq 0 $((total - 1))); do
  route_at "$i"
  if [[ -n "$filter" && "$ROUTE_NAME" != *"$filter"* && "$ROUTE_PATH" != *"$filter"* ]]; then
    continue
  fi
  echo "  → $ROUTE_NAME ($ROUTE_PATH)"
  if ROUTE_NAME="$ROUTE_NAME" bash "${SCRIPT_DIR}/capture-page.sh" "$ROUTE_PATH"; then
    ok=$((ok + 1))
  else
    failed=$((failed + 1))
    echo "    ✗ $ROUTE_NAME failed; continuing" >&2
  fi
done

echo
echo "site-capture: ${ok} ok, ${failed} failed"
echo "  outputs in: ${OUT_DIR}/"
(( failed == 0 ))
