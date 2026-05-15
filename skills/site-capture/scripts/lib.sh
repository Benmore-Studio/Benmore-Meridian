#!/usr/bin/env bash
# Shared helpers for site-capture scripts. Sourced by every other script.
# Provides:
#   - cfg <key> [default]    — read from captures/config.json with override
#   - cfg_for_route <name> <key> [default]
#                            — same, but with per-route override fallback
#   - slugify <string>
#   - require_cmd <name…>
#   - probe_url <url>
#   - pw_open / pw_close / pw_eval / pw_screenshot
# Conventions:
#   - All paths resolved against $CAPTURES_DIR (defaults to ./captures).
#   - Per-call env vars (e.g. FPS=24) win over config.json.

set -euo pipefail

CAPTURES_DIR="${CAPTURES_DIR:-$(pwd)/captures}"
CONFIG_FILE="${CONFIG_FILE:-${CAPTURES_DIR}/config.json}"
SITEMAP_FILE="${SITEMAP_FILE:-${CAPTURES_DIR}/sitemap.json}"
OUT_DIR="${OUT_DIR:-${CAPTURES_DIR}/out}"

require_cmd() {
  local missing=()
  for c in "$@"; do
    command -v "$c" >/dev/null 2>&1 || missing+=("$c")
  done
  if [[ ${#missing[@]} -gt 0 ]]; then
    echo "site-capture: missing required command(s): ${missing[*]}" >&2
    echo "  install hints:" >&2
    for m in "${missing[@]}"; do
      case "$m" in
        playwright-cli) echo "    npm install -g @playwright/cli@latest" >&2 ;;
        gifski)         echo "    brew install gifski" >&2 ;;
        ffmpeg)         echo "    brew install ffmpeg" >&2 ;;
        jq)             echo "    brew install jq" >&2 ;;
      esac
    done
    exit 127
  fi
}

slugify() {
  local s="$1"
  s="${s#/}"; s="${s%/}"
  s="${s//\//-}"
  s="${s// /-}"
  echo "${s:-home}" | tr '[:upper:]' '[:lower:]'
}

# Default values when neither env nor config provide one.
declare -A SITE_CAPTURE_DEFAULTS=(
  [base_url]="http://localhost:3000"
  [browser]="chrome"
  [session_name]="site-capture"
  [viewport_width]="1280"
  [viewport_height]="800"
  [device_scale_factor]="2"
  [theme]="dark"
  [frames_per_page]="30"
  [scroll_step_px]="0"
  [fps]="12"
  [quality]="85"
  [gif_width]="1100"
  [wait_ms_after_nav]="1200"
  [wait_ms_between_frames]="80"
  [strict_console]="0"
)

# cfg <key> [default]
# Lookup order: env (uppercase) → captures/config.json → SITE_CAPTURE_DEFAULTS → caller default.
cfg() {
  local key="$1"
  local env_name
  env_name="$(echo "$key" | tr '[:lower:]' '[:upper:]')"
  if [[ -n "${!env_name:-}" ]]; then
    echo "${!env_name}"
    return 0
  fi
  if [[ -f "$CONFIG_FILE" ]]; then
    # support both flat keys and viewport.width nested form
    local value
    case "$key" in
      viewport_width)  value=$(jq -r '.viewport.width // empty'  "$CONFIG_FILE" 2>/dev/null || true) ;;
      viewport_height) value=$(jq -r '.viewport.height // empty' "$CONFIG_FILE" 2>/dev/null || true) ;;
      *) value=$(jq -r --arg k "$key" '(.[$k] // empty) | tostring' "$CONFIG_FILE" 2>/dev/null || true) ;;
    esac
    if [[ -n "$value" && "$value" != "null" ]]; then
      echo "$value"; return 0
    fi
  fi
  if [[ -n "${SITE_CAPTURE_DEFAULTS[$key]:-}" ]]; then
    echo "${SITE_CAPTURE_DEFAULTS[$key]}"; return 0
  fi
  echo "${2:-}"
}

# cfg_for_route <route_index_or_name> <key> [default]
# Falls back to the global cfg() if the route doesn't override.
cfg_for_route() {
  local route_idx="$1" key="$2" fallback="${3:-}"
  if [[ -f "$SITEMAP_FILE" ]]; then
    local value
    case "$key" in
      viewport_width)  value=$(jq -r --argjson i "$route_idx" '.routes[$i].viewport.width // empty'  "$SITEMAP_FILE" 2>/dev/null || true) ;;
      viewport_height) value=$(jq -r --argjson i "$route_idx" '.routes[$i].viewport.height // empty' "$SITEMAP_FILE" 2>/dev/null || true) ;;
      *) value=$(jq -r --argjson i "$route_idx" --arg k "$key" '(.routes[$i][$k] // empty) | tostring' "$SITEMAP_FILE" 2>/dev/null || true) ;;
    esac
    if [[ -n "$value" && "$value" != "null" ]]; then
      echo "$value"; return 0
    fi
  fi
  cfg "$key" "$fallback"
}

probe_url() {
  local url="$1"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "$url" || echo "000")
  if [[ "$code" != "200" && "$code" != "301" && "$code" != "302" && "$code" != "307" ]]; then
    echo "site-capture: $url returned HTTP $code — is the dev server running?" >&2
    return 1
  fi
}

# Open a named playwright-cli session and apply viewport + theme + dev console silencing.
# Idempotent: if the session is already open, leaves it alone.
pw_open() {
  local session="$1" url="$2"
  local browser; browser=$(cfg browser)
  local vw vh dsf theme
  vw=$(cfg viewport_width); vh=$(cfg viewport_height)
  dsf=$(cfg device_scale_factor); theme=$(cfg theme)

  # Try to navigate; if the session is dead, open fresh.
  if ! playwright-cli -s="$session" goto "$url" >/dev/null 2>&1; then
    playwright-cli -s="$session" open "$url" --browser="$browser" >/dev/null
  fi
  playwright-cli -s="$session" resize "$vw" "$vh" >/dev/null
  playwright-cli -s="$session" eval \
    "() => { document.documentElement.setAttribute('data-theme','${theme}'); try{localStorage.setItem('theme','${theme}')}catch{} }" \
    >/dev/null
}

pw_close() {
  local session="$1"
  playwright-cli -s="$session" close >/dev/null 2>&1 || true
}

pw_eval() {
  local session="$1"; shift
  playwright-cli -s="$session" eval "$@"
}

pw_screenshot() {
  local session="$1" filename="$2"; shift 2
  playwright-cli -s="$session" screenshot --filename="$filename" "$@" >/dev/null
}

# Map a route entry from sitemap.json by index to (path, name) globals.
route_at() {
  local idx="$1"
  ROUTE_PATH=$(jq -r --argjson i "$idx" '.routes[$i].path' "$SITEMAP_FILE")
  ROUTE_NAME=$(jq -r --argjson i "$idx" '.routes[$i].name // empty' "$SITEMAP_FILE")
  if [[ -z "$ROUTE_NAME" || "$ROUTE_NAME" == "null" ]]; then
    ROUTE_NAME=$(slugify "$ROUTE_PATH")
  fi
}

route_count() {
  jq -r '.routes | length' "$SITEMAP_FILE"
}
