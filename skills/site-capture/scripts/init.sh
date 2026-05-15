#!/usr/bin/env bash
# Initialise a capture project in the current directory.
# Creates captures/{config.json, sitemap.json} with sensible defaults
# and adds captures/out/ to .gitignore if a git repo is present.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./lib.sh
source "${SCRIPT_DIR}/lib.sh"

mkdir -p "${CAPTURES_DIR}/out"

if [[ ! -f "$CONFIG_FILE" ]]; then
  cat > "$CONFIG_FILE" <<'JSON'
{
  "base_url": "http://localhost:3000",
  "viewport": { "width": 1280, "height": 800 },
  "device_scale_factor": 2,
  "theme": "dark",
  "frames_per_page": 30,
  "scroll_step_px": 0,
  "fps": 12,
  "quality": 85,
  "gif_width": 1100,
  "wait_ms_after_nav": 1200,
  "wait_ms_between_frames": 80,
  "browser": "chrome",
  "session_name": "site-capture"
}
JSON
  echo "wrote $CONFIG_FILE"
fi

if [[ ! -f "$SITEMAP_FILE" ]]; then
  cat > "$SITEMAP_FILE" <<'JSON'
{
  "routes": [
    { "path": "/",         "name": "home" },
    { "path": "/about",    "name": "about" },
    { "path": "/projects", "name": "projects" },
    { "path": "/weekly",   "name": "weekly-index" }
  ]
}
JSON
  echo "wrote $SITEMAP_FILE"
fi

# Add captures/out/ to .gitignore if this is a git repo and the entry is missing.
if [[ -d .git ]]; then
  if ! grep -qxF "captures/out/" .gitignore 2>/dev/null; then
    printf "\n# site-capture skill output\ncaptures/out/\n" >> .gitignore
    echo "added captures/out/ to .gitignore"
  fi
fi

echo
echo "Next:"
echo "  1. Edit ${SITEMAP_FILE} with the routes you want to capture."
echo "  2. BASE_URL=http://localhost:5001 bash ${SCRIPT_DIR}/capture-all.sh"
