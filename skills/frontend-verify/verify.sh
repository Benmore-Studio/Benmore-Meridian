#!/usr/bin/env bash
# One command. Inventory -> classify -> sweep, in that order, cheapest first.
#
#   verify.sh <repoRoot> [--base URL] [--auth state.json] [--width N] [--quiet]
#                        [--mutate] [--ratchet] [--resume] [--prod] [--no-warm]
#                        [--widths 390,1440] [--states [empty,error,...]]
#
#   verify.sh /path/to/repo                          static only, seconds, no install
#   verify.sh /path/to/repo --base http://localhost:3000   + the runtime sweep
#
#   --mutate   DESTRUCTIVE, opt-in: drives real forms to prove sync risks at
#              runtime. Dev database only.
#   --ratchet  fix-loop guard: total findings may never exceed the best run seen
#              (.verify/ratchet.json); the baseline tightens automatically.
#   --resume   continue an aborted sweep instead of restarting it; already
#              measured routes are kept, unmeasured ones are re-visited.
#   --prod     the base URL is a PRODUCTION build, so timing findings grade
#              normally. Without it they are P3: against a dev server the number
#              measured is the compiler's, not the app's.
#   --no-warm  skip the precompile pass. The warm pass exists because a dev
#              server compiles a route on first request (measured: 30.5s) and a
#              mock service worker does not intercept until it controls a page.
#
#   Multiple principals: put <repo>/verify.roles.json beside the repo and each
#   role sweeps only the routes it OWNS. See "Roles" in SKILL.md.
#
#   Nothing else may build while the sweep runs -- a concurrent web build starves
#   the dev server and the whole run aborts as "server unreachable".
#
# Exit: 0 clean · 1 P0/P1 findings (or ratchet regression) · 2 could not run.
# That exit code is the definition of done -- it is what a Stop hook, a
# pre-commit hook or CI reads. Everything else here is reporting.
set -uo pipefail

SKILL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO=""; BASE=""; AUTH=""; WIDTH=""; QUIET=0; MUTATE=0; RATCHET=0; LOGIN=""; PARALLEL=""; PASSTHRU=()
while [ $# -gt 0 ]; do
  case "$1" in
    --base)  BASE="${2:-}"; shift 2 ;;
    --auth)  AUTH="${2:-}"; shift 2 ;;
    --width) WIDTH="${2:-}"; shift 2 ;;
    --login) LOGIN="${2:-}"; shift 2 ;;          # user:pass -> auto-login, state saved to .verify/auth.json
    --parallel) PARALLEL="${2:-}"; shift 2 ;;
    --quiet) QUIET=1; shift ;;
    --mutate) MUTATE=1; shift ;;
    --ratchet) RATCHET=1; shift ;;
    # Straight through to sweep.mjs. --resume continues an aborted sweep instead
    # of restarting it, --prod says the base URL is a production build so timing
    # findings grade normally, --no-warm skips the precompile pass.
    --resume|--prod|--no-warm|--leak-check) PASSTHRU+=( "$1" ); shift ;;
    --nav-timeout|--warm-timeout|--settle) PASSTHRU+=( "$1" "${2:-}" ); shift 2 ;;
    # --widths 390,1440   the cell matrix: every route at every width. Half the
    #                     invariants here are width-dependent, so a one-width run
    #                     grades an app nobody uses at one width.
    # --states [kinds]    force empty/error/forbidden/malformed/slow on the data
    #                     each route actually fetches, and grade what it renders.
    #                     Bare --states runs all five.
    --widths|--text-floor|--integrity-share) PASSTHRU+=( "$1" "${2:-}" ); shift 2 ;;
    --states) PASSTHRU+=( "$1" ); case "${2:-}" in ''|--*) ;; *) PASSTHRU+=( "$2" ); shift ;; esac; shift ;;
    -h|--help) sed -n '2,31p' "$0"; exit 0 ;;
    *) [ -z "$REPO" ] && REPO="$1" || true; shift ;;
  esac
done

[ -z "$REPO" ] && REPO="$PWD"
REPO="$(cd "$REPO" 2>/dev/null && pwd)" || { echo "verify: no such directory" >&2; exit 2; }
command -v node >/dev/null || { echo "verify: node not found" >&2; exit 2; }

OUT="$REPO/.verify"
mkdir -p "$OUT"
say() { [ "$QUIET" -eq 1 ] || printf '%s\n' "$*"; }
rc=0

say ""
say "  frontend-verify  $REPO"

# --- 1. inventory (always; also the route list the sweep uses) --------------
if ! node "$SKILL/bin/inventory.mjs" "$REPO" >"$OUT/inventory.log" 2>&1; then
  cat "$OUT/inventory.log" >&2; echo "verify: inventory failed" >&2; exit 2
fi
[ "$QUIET" -eq 1 ] || sed -n '2,5p' "$OUT/inventory.log"

# A sync risk that names the routes it breaks is a real defect, and the only one
# of the three phases that does not already exit non-zero on its own.
if [ "$QUIET" -eq 1 ]; then
  node -e 'try { process.exit(require(process.argv[1]).syncRisks.some((r) => r.severity === "P1") ? 1 : 0) } catch { process.exit(0) }' "$OUT/inventory.json" || rc=1
else
  node -e '
    let p1 = [];
    try { p1 = require(process.argv[1]).syncRisks.filter((r) => r.severity === "P1") } catch { process.exit(0) }
    if (!p1.length) process.exit(0);
    console.log("");
    console.log("  " + p1.length + " P1 sync risk(s) -- a write with no invalidation, on routes that render it:");
    for (const r of p1.slice(0, 12)) console.log("    " + r.detail);
    if (p1.length > 12) console.log("    ... and " + (p1.length - 12) + " more in .verify/inventory.json");
    process.exit(1);
  ' "$OUT/inventory.json" || rc=1
fi

# --- 2. classify (always) ---------------------------------------------------
node "$SKILL/bin/classify.mjs" "$REPO" >"$OUT/classify.log" 2>&1
cls=$?
[ "$QUIET" -eq 1 ] || sed -n '2,40p' "$OUT/classify.log"
[ "$cls" -ne 0 ] && rc=1

# --- 3. sweep (only with --base; needs the app running) ---------------------
if [ -n "$BASE" ]; then
  args=( --repo "$REPO" --base "$BASE" )
  [ -n "$AUTH" ]  && args+=( --auth "$AUTH" )
  [ -n "$WIDTH" ] && args+=( --width "$WIDTH" )
  [ -n "$PARALLEL" ] && args+=( --parallel "$PARALLEL" )
  [ -n "$LOGIN" ] && args+=( --login-user "${LOGIN%%:*}" --login-pass "${LOGIN#*:}" )
  [ "$MUTATE" -eq 1 ] && args+=( --mutate )
  [ ${#PASSTHRU[@]} -gt 0 ] && args+=( "${PASSTHRU[@]}" )
  node "$SKILL/bin/sweep.mjs" "${args[@]}" >"$OUT/sweep.log" 2>&1
  sw=$?
  [ "$QUIET" -eq 1 ] || sed -n '2,40p' "$OUT/sweep.log"
  # 2 means the sweep could not run at all. Never let that read as clean.
  [ "$sw" -eq 2 ] && { echo "verify: sweep could not run -- see $OUT/sweep.log" >&2; exit 2; }
  [ "$sw" -ne 0 ] && rc=1
else
  say ""
  say "  runtime sweep skipped (no --base). Static analysis cannot see whether the"
  say "  code runs -- pass --base http://localhost:3000 with the app up to cover that."
fi

# PASS must mean "measured, and clean" -- never "measured nothing". A repo with no
# routes is one the tool did not understand, and reporting it green is the exact
# failure this whole skill exists to prevent.
ROUTES=$(node -e 'try { console.log(require(process.argv[1]).counts.routes) } catch { console.log(0) }' "$OUT/inventory.json")
if [ "${ROUTES:-0}" -eq 0 ]; then
  echo "" >&2
  echo "  INCONCLUSIVE  0 routes found in $REPO" >&2
  echo "  Nothing was measured, so this is not a pass. Either this is not a frontend" >&2
  echo "  repo, or its router is not one inventory.mjs recognises (Next app/pages," >&2
  echo "  react-router config, or a src/routes file convention)." >&2
  exit 2
fi

# --- ratchet (opt-in): a fix loop that trades one finding for two is going
# backwards, and an agent mid-loop will not notice on its own. Total findings
# (every severity, all phases) may never exceed the best run seen; the baseline
# tightens itself on every improvement. Static-only and runtime runs measure
# different things, so a mode switch resets the baseline instead of comparing them.
if [ "$RATCHET" -eq 1 ]; then
  ROUT=/dev/stdout; [ "$QUIET" -eq 1 ] && ROUT=/dev/null
  node -e '
    const fs = require("fs");
    const out = process.argv[1], mode = process.argv[2];
    const j = (f) => { try { return JSON.parse(fs.readFileSync(out + "/" + f, "utf8")); } catch { return null; } };
    const inv = j("inventory.json"), cls = j("classify.json"), sw = mode === "runtime" ? j("sweep.json") : null;
    const total = (inv?.syncRisks?.length ?? 0) + (cls?.counts?.total ?? 0) + (sw?.summary?.findings ?? 0);
    const file = out + "/ratchet.json";
    const prev = j("ratchet.json");
    if (prev && prev.mode === mode && total > prev.best) {
      console.error("  RATCHET  " + total + " findings, best was " + prev.best + " -- this change went backwards; fix or revert it (delete .verify/ratchet.json only to accept a known regression)");
      process.exit(1);
    }
    const best = prev && prev.mode === mode ? Math.min(prev.best, total) : total;
    fs.writeFileSync(file, JSON.stringify({ mode, best, last: total, at: new Date().toISOString() }, null, 2));
    console.log("  ratchet  " + total + " findings (best " + best + ")");
  ' "$OUT" "$([ -n "$BASE" ] && echo runtime || echo static)" >"$ROUT" || rc=1
fi

# PASS must carry the DENOMINATOR. "No P0/P1 findings" over 41 of 51 routes and
# over 51 of 51 are different claims, and printing them identically is how a
# partial run gets read as a clean one -- the exact failure this skill exists for.
COVER=""
if [ -n "$BASE" ]; then
  COVER=$(node -e '
    try {
      const s = require(process.argv[1]).summary ?? {};
      if (s.routesRequested == null) process.exit(0);
      const un = s.routesUnreached ?? 0, uo = s.routesUnowned ?? 0;
      process.stdout.write("  ·  swept " + s.routesReached + "/" + s.routesRequested + " routes"
        + (un ? ", " + un + " NOT MEASURED (redirected)" : "")
        + (uo ? ", " + uo + " unowned" : ""));
    } catch {}
  ' "$OUT/sweep.json" 2>/dev/null)
fi

say ""
if [ "$rc" -eq 0 ]; then say "  PASS  $ROUTES routes analysed, no P0/P1 findings$COVER"
else say "  FAIL  P0/P1 findings above  ·  reports in $OUT/$COVER"; fi
exit "$rc"
