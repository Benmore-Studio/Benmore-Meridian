---
name: frontend-verify
description: Use when a frontend is "done" but not trusted - when a feature was built and claimed working but data does not load, one page shows stale values after another page saved, or the last 20% before launch is being burned clicking through screens by hand. Inventories every route and its data dependencies, finds the defect classes that are decidable without a browser, then drives the real app against universal runtime invariants and exits non-zero. Includes marathon mode - hours-long autonomous QA where the agent studies every feature, generates the journeys and assertions itself from source, and loops test-fix-retest until green. Triggers on "verify the frontend", "why does page B still show the old value", "half the data does not load", "QA before launch", "prove this works", "find what is broken before I click through it", "test everything", "QA marathon", "automated testing for hours". Not for visual taste (design-director), not for building UI (impeccable), not for one screen's states (ui-stress).
---

# frontend-verify

## The problem this exists for

Every other frontend tool produces an **observation**: a screenshot, a snapshot,
a console log, a probe result. None produces an **expectation**. An observation
cannot fail, so a loop built from observations terminates on "it looked right",
and the two defect classes that dominate the last 20% before launch survive it
untouched:

- **Cardinality defects** — 14 rows rendered where 17 belong. Pixel-perfect.
- **Identity defects** — page B holds a copy of what page A just changed.

Both render as beautiful pages with wrong contents. No design pass, no visual
diff, and no amount of clicking finds them reliably.

**The fix is not more test cases.** Cases are authored per feature, so coverage
grows only as fast as you write it, and the next thing you prompt into existence
is uncovered. This skill enumerates **invariants** instead: properties that hold
on every route forever, written once, applying to code that does not exist yet.

## What this is, and is not

A **supplement** to typechecking, linting, application tests, app-owned
Playwright journeys and visual regression — not their replacement. It automates
the layer none of those cover (universal runtime invariants, cross-page cache
coherence, the defect classes decidable from source), and it hands business
intent back to you as one question per entity. It does not fix bugs: it emits
file/line findings and a non-zero exit code, and the agent driving it patches
the root cause and reruns the gate — detection and repair stay separate on
purpose, because a tool that grades its own fixes is a tool that learns to
grade generously. Static rules are heuristic (regex + import graph, not an AST
— see the header of `inventory.mjs` for the trade); the runtime invariants are
measured, not inferred.

## Assert at the boundary that does not change

Types, store patterns and framework idioms are per-stack; everything asserted
above the browser gets rebuilt every time you switch. A console error, a failed
request, an `undefined` in the DOM and a stale cache entry are identical in
Next, Vite, Remix, TSX-on-a-CDN and whatever is next. Anchor there and the work
transfers at zero cost.

## Run order

Cheapest and most exhaustive first. Do not open a browser to learn something a
file read can tell you.

**Pass the repo as an absolute path.** The skill lives in `~/.claude/skills/` and
is run against many repos; nothing resolves against the current working
directory, so it cannot matter where your shell happens to be.

```bash
S=~/.claude/skills/frontend-verify

# Everything, in order, cheapest first:
bash $S/verify.sh /abs/path/to/repo                                  # static only, seconds
bash $S/verify.sh /abs/path/to/repo --base http://localhost:3000     # + the runtime sweep
```

Exit: **0** clean · **1** P0/P1 findings · **2** could not run. That exit code is
the definition of done — it is what a Stop hook, a pre-commit hook, or CI reads.

`--login user:pass` logs in through the app's own form once and saves the
state to `.verify/auth.json` (reused on every later run; delete it when
stale). `--parallel 4` sweeps four routes at once (confirm perf findings with
a serial pass — contention inflates them). `--auth state.json` to supply state
captured by hand, `--width 390` for mobile, `--quiet` for hooks, `--ratchet`
inside a fix loop, and `--mutate` (**destructive**, dev DB only) to prove sync
risks at runtime by driving real forms.

`--resume` continues an aborted sweep instead of restarting it. `--prod` says
the base URL is a production build, so timing findings grade normally — without
it they are filed P3, because against a dev server the number measured is the
compiler's. `--no-warm` skips the precompile pass; `--nav-timeout` and
`--warm-timeout` size it for a slow app.

**Nothing else may build while the sweep runs.** A concurrent web build starves
the dev server and the run aborts as `server unreachable` — one measured
incident cost a whole pass. Same reason `--parallel` needs care.

Run a phase on its own when you want just that one:

```bash
node $S/bin/inventory.mjs "$R"                                   # routes, data deps, sync graph
node $S/bin/classify.mjs  "$R"                                   # source-decidable defects
node $S/bin/sweep.mjs --repo "$R" --base http://localhost:3000   # runtime invariants
node $S/bin/sweep.mjs --repo "$R" --base URL --routes /a,/b      # just these routes
```

`<repo>/.verifyignore` (gitignore-shaped, `*` and `?`) drops paths from the
inventory AND the classifier. Design-lab trees — `_proto/`, `playground/`,
`sandbox/`, `scratch/`, `design-lab/` — are excluded by default: committed, so
`.gitignore` does not cover them, shaped exactly like the app, so every rule
fires in them, and reachable from no route, so nothing found there can break
anything. On one real repo they were 18 of 19 static findings.

**Exit 2 is not a pass.** Zero routes, zero swept pages, or a sweep that could not
start all exit 2 rather than 0 — a run that measured nothing must never read as
green, which is the failure this whole skill exists to prevent.

### Where everything lives

| | Path | Scope |
|---|---|---|
| The tools, `SKILL.md`, `references/atlas.md` | `~/.claude/skills/frontend-verify/` | **global** — installed once, identical for every repo |
| `inventory.json`, `classify.json`, `sweep.json`, `auth*.json` | `<repo>/.verify/` | **per-repo** — written beside the repo analysed, never into your cwd |
| `verify.roles.json`, `verify.journeys.mjs`, `.verifyignore` | `<repo>/` | **per-repo, committed** — they describe the app, so they belong in its history |

The atlas is reference material for the tool, so it stays global; findings are
facts about one codebase, so they stay with it. Add `.verify/` to the repo's
`.gitignore` unless you want the reports reviewed in PRs — committing them turns
each run into a diff, which is a reasonable choice for a repo heading to launch.

Add `--stdout` (inventory) or `--json` (classify) to pipe instead of writing.

Read `.verify/inventory.json` before writing any test. `syncRisks` is the
cross-page staleness bug located statically, with its blast radius; a P1 there
names the hook, the endpoint, and every route that goes stale when it runs.

## What each phase can and cannot see

| Phase | Sees | Blind to |
|---|---|---|
| `inventory.mjs` | routes, per-route data deps, mutations, entity→route matrix, sync risks (no invalidation AND wrong-key invalidation), duplicate cache keys | anything conditional at runtime |
| `classify.mjs` | missing empty/error/loading branches, server state in client stores, stale closures, unaborted effect fetches, build-time env read at runtime, index keys, unsanitized HTML, unguarded submits | whether the code actually runs |
| `sweep.mjs` + `probe.js` | console errors, failed requests, HTTP 4xx/5xx, hydration mismatch, chunk-load failure, CSP violations, DOM value leaks, stuck spinners, empty lists with no empty state, data fetched but zero rows rendered, horizontal scroll, tap targets, unlabeled controls and fields, long tasks, CLS, LCP, layout thrash, request waterfalls, heap retained across navigation | business intent |
| `--mutate` replay | whether a real write through a real form leaves a blast-radius route stale under client-side navigation | which payload a form considers valid |
| your roles (`verify.roles.json`) | which principal owns which route tree, so each lens grades only its own half and an unclaimed tree shows up as unowned | whether the app's own gate is correct |
| your journeys (`verify.journeys.mjs`) | create/update/delete flows, dynamic routes, role gates — scripted once, then swept under every invariant above | — |
| you | "this total must equal the sum of that column" | everything above, reliably |

Router recognition is Next (app + pages), react-router/route-config literals,
and `src/routes` file conventions. Anything else inventories **zero routes and
exits 2** — inconclusive, never a pass.

## Roles: one lens per principal, and each one grades only what it owns

An app with two principals — a staff session and a customer-portal session —
refuses each other's routes **in both directions on purpose**. One lens can
therefore never reach more than its own half, and the half it cannot reach is
not broken. Drop `verify.roles.json` at the repo root:

```json
{ "staff":  { "auth": ".verify/auth.json",        "owns": ["/"], "excludes": ["/portal"] },
  "portal": { "auth": ".verify/auth-portal.json", "owns": ["/portal"] },
  "proxy":  { "auth": ".verify/auth.json",        "owns": ["/portal"],
              "headers": { "X-Profectus-Proxy-Customer": "cust-1" } } }
```

A principal is **not always a cookie jar**. The third role above is a staff user
acting *through* the customer portal: same storage state as `staff`, different
authority, different expected surface, distinguished only by a request header.
`headers` makes that lens expressible; without it it gets misfiled as `portal`
and its distinct behaviour is never measured. Two roles may own the same tree —
that is the point, and each sweeps it under its own identity.

Count the principals from the app's own test helpers, not from the login screen:
one real repo had **ten** (nine staff roles plus a portal producer) where the UI
suggested two.

Each role sweeps only the routes it owns (prefix match), under its own storage
state, and every record carries its `role`. Without a roles file the sweep runs
one `default` role owning everything, which is the previous behaviour exactly.

**`owns` is the load-bearing half, not `auth`.** Two auth states without
ownership do not produce two half-reports, they produce two full reports in
which each role files every route it does not own as a defect: measured, the
portal lens produced 45 `landed on /login` P1s, none of them a bug.

A route matching **no** role is never visited, and is counted as
`summary.routesUnowned` and listed in `report.unowned` — a route nobody claims
must show up as a gap, not vanish.

### Not reached is a coverage gap, not a finding

A route the sweep never reached goes to `report.unreached` with the role that
tried and where it landed, **never into the finding list**. The tool refuses to
grade a route it did not reach; it does not pretend the route is broken. This
was worth changing: in one run 10 of 13 P1s were the tool reporting on the
caller's cookie jar in the same list as the app's bugs.

Which is also why `PASS` now carries its denominator — "no P0/P1 findings over
41 of 51 routes" and "over 51 of 51" are different claims, and printing them
identically is how a partial run gets read as a clean one.

That last row is the only part a human must supply, and it is **one question per
entity**, not per feature.

## The invariants the sweep enforces

Every route, every run, no authoring:

1. Zero console errors, page errors, unhandled rejections
2. Zero failed same-origin requests; zero unexpected 4xx/5xx. A **4xx the page
   handled** — the surface still renders, nothing crashed, nothing stayed blank
   or spinning — is P2, not P1: a deliberate negative fixture is coverage, not a
   defect, and the repos that get flagged hardest for it are the ones testing
   their error paths properly. 5xx is exempt; a server fault is a defect whoever
   caught it
3. No hydration mismatch, no chunk-load failure, no CSP violation
4. Root renders non-empty text
5. No loading indicator still mounted after settle
6. No list with zero rows and no empty state
7. No API response whose records exist while every list renders zero rows
7b. No route with data dependencies that fires **no request at all** — joined
    against the inventory, so a genuinely static page is never accused. Before
    that join it was a P2 shrug ("either this route needs none, or the sweep is
    measuring nothing"); scoped, it is one claim: N query hooks are reachable
    from here and not one of them fired
8. No `undefined` / `NaN` / `[object Object]` / `Invalid Date` / unresolved template var in the DOM
9. No horizontal scroll at the tested width
10. Interactive elements >= 24px (screen-reader-only elements excluded)
11. Every control has an accessible name (buttons, links, AND form fields)
12. Longest task < 200ms, CLS < 0.1, LCP < 2500ms — measured by observers
    installed **before navigation**; unmeasured is reported as unmeasured, never
    as clean. Filed **P3 unless `--prod`**: against a dev server these measure
    the compiler, not the app. One real run produced 16 perf findings of 53, the
    worst reading 14,864ms, every one of them a `next dev` compile
13. No interactive element whose center another element covers — clicks that
    land on an invisible overlay (open dialogs and `pointer-events:none`
    excluded)
14. No `SameSite=None` cookie without `Secure` — the browser rejects it, auth
    silently vanishes
15. No resource preloaded and never used (Chrome's own diagnostic, exact-matched)
16. No dependent request chain 3 deep
17. (opt-in `--leak-check`) heap returns after GC across repeated navigation
18. (opt-in `--mutate`) after a successful write, every blast-radius route either
    refetches or shows the new value under client-side navigation

The sweep is hardened for long runs: it liveness-checks the dev server before
every route (a dead server is one exit-2, not forty fake findings), retries a
dropped route once and marks a pass-on-retry `route.flaky` instead of clean, and
writes `sweep.json` incrementally so hour three cannot destroy hours one and two.

## Journeys: the app's flows, the skill's harness

A universal journey generator is brittle over-engineering — inventing what a
form "should" accept is guessing at intent. So the split is: **you script the
flow once, the harness supplies everything else.** Drop `verify.journeys.mjs`
at the repo root (committed, unlike `.verify/`):

```js
export default [
  { name: 'create-invoice', start: '/invoices', run: async (page, { base }) => {
      await page.fill('[name=amount]', '42');
      await page.click('button[type=submit]');
      await page.click('a[href="/invoices"]');
  }},
];
```

Each journey runs under the full console/network listeners, and wherever it
ends up gets the whole probe — so a journey is three lines of clicks, and the
fourteen invariants above are asserted for free at every step's destination.
This is how dynamic routes (`/invoices/:id`), role gates and CRUD flows get
covered: the journey knows a real id; the sweep never guesses one. A journey
that throws is a P0 (`journey.failed`), not a skipped test.

`--mutate` is the zero-authoring fallback for sync risks specifically: it fills
the mutation route's form with sentinel values, submits, client-side navigates
to each statically-computed stale route, and files `sync.stale-after-write` P0
only when the write succeeded AND no refetch happened AND the sentinel is
absent. A validation-rejected submit is reported as unverified, never as a
defect — the app's reaction to synthetic input is not a finding.

## Warm before you measure

Two races manufacture findings about the harness rather than the app, and the
warm pass closes both. It runs by default; `--no-warm` opts out.

- **Cold compile.** A dev server compiles a route on its first request. Measured:
  `✓ Compiled /tasks in 30.5s` against a 30s navigation timeout — the route lost
  by 500ms and was filed unreachable. The warm pass GETs every route over plain
  HTTP first, which triggers the same compile at a fraction of a navigation's
  cost. Nav timeout is now 60s (`--nav-timeout`).
- **Service-worker claim.** A mock service worker does not intercept until it
  *controls* the page, so the first navigation of a run goes to the real origin
  and 404s. Measured: first load `GET /v1/auth/me -> 404`; second load, 20
  requests, all 200. Every 404 in that run was the harness. `serviceWorker.ready`
  resolves at activation, which is **earlier** than control — that gap is where
  an earlier warm-up attempt failed silently, so an uncontrolled page is reloaded
  once and the outcome is reported either way.

Both report what they achieved (`report.warm`, `report.serviceWorker`:
`claimed` / `registered-not-controlling` / `none`). That is the difference
between this warm-up and the one that was reverted: an unproven fix that says so
is worth keeping, one that stays silent is not.

Liveness is checked with a 20s budget and two consecutive failures, not one 5s
probe — a dev server busy compiling another route is loaded, not dead, and
aborting the run on it throws away everything measured so far. When a run does
abort, `--resume` picks up from the routes that were never measured.

## Readiness, not networkidle

`domcontentloaded` fires before client-rendered content exists, and a gate that
captures there measures nothing while still occupying the verification slot —
worse than no gate, because it reports green. `networkidle` never arrives under
long polling, websockets or background refetch. The sweep waits for the root to
have text, then settles. Keep it that way.

## Precision is the product

Every rule here was tuned against real repos until its false-positive rate hit
roughly zero, because a report with noise in it stops being read, and a tool
that is not read is worse than no tool. When adding a rule:

- Run it on a real repo before committing it. Open the top three hits and
  confirm each is genuinely a defect.
- A wrapper hook that returns its query is not ignoring the error — its caller
  reads it. Follow one level of indirection before flagging.
- Screen-reader-only elements are 1x1 by design. Measuring them as tap targets
  is how a ticket claims 103 failures and a browser finds one.
- JSON-LD blocks are serialized data, not markup.
- Prefer a miss to a false positive. A miss surfaces later; a false alarm costs
  the reader's trust the first time they open the file and find nothing wrong.
- Say how strong the claim is. "This write leaves route X stale" and "I could not
  determine what goes stale" are different assertions; filing both at one severity
  makes the strong one look as soft as the weak one. `unresolved: true` marks it.
- A finding repeated across N routes is usually one finding about the surface all
  N of them landed on. Check the denominator counts routes, not cells.
- **A blast radius that covers most of the app is a denominator failure, not a
  big finding.** A resource read by 30 of 57 routes is not an entity, it is an
  ambient concern (`auth`, `session`, `me`, `config`), and "this write leaves 30
  routes stale" outranks four genuine findings while being wrong. Past 40% of
  routes (and at least 10 of them) the blast radius is reported as undetermined
  instead — a weaker claim, honestly labelled.
- A wrapper's method name may be **uppercase**. Generated clients spell it
  `GET`/`POST`; a case-sensitive matcher silently resolves none of them, and
  silent is the whole problem — the report stays green and says less.
- A read wrapped in a write primitive (a `GET` inside `useMutation`, to open a
  PDF or start a download) mutates nothing and has no blast radius.

## Structural tells that a run is an artifact

The costliest failures are not wrong rows, they are confident numbers produced by
a harness that never measured the thing. Every one of these was caught by shape,
not by reading any individual finding:

| Tell | What it means |
|---|---|
| Identical output across deliberately different inputs | The experiment never ran. The differential check in `selftest.sh` exists for exactly this. |
| One selector or surface repeated across N routes | N routes landed on the same page — auth redirect, not-found shell — and got measured under their own names. |
| `modules: 1` on every route in the inventory | The import walk resolved nothing at hop 1. Aliases are wrong; the app is not "clean". |
| `resourceMatrix` with a handful of keys on a repo with a hundred queries | The endpoint matcher missed the client's spelling, so no blast radius resolves and every sync risk demotes itself to "could not determine what goes stale". Caught in the wild: a lowercase-only verb regex resolved the endpoint of **zero** `apiClient.POST(...)` calls, leaving 1 matrix entry on a 145-query app. Grep the repo's HTTP calls and compare. |
| Every sync risk marked `unresolved: true` | Same failure, seen from the other end. A detector that resolves 0 of 7 is not a tuned heuristic, it is a broken one. |
| A count that is a multiple of the file count | Per-route sums counting shared modules once per route. |
| Zero of something a grep finds hundreds of | The matcher missed a wrapper, a generic, or a path alias. Grep before believing a zero. |

When a number looks decisive, check its denominator before publishing it.

## Prove the probes fire

```bash
bash ~/.claude/skills/frontend-verify/selftest-static.sh   # no browser needed
bash ~/.claude/skills/frontend-verify/selftest.sh          # needs Playwright in reach
```

The static selftest plants one instance of **all 16 classifier rules** (a meta
check fails the suite if a 17th rule is added without a plant), the wrong-key
and no-invalidation sync risks, the wrapper/monorepo/generics traversal shapes,
the generated-client shapes (uppercase verbs resolving to a blast radius, a
`GET` inside `useMutation` staying silent, an ambient resource refusing to file
P1), the design-lab exclusion (and the same rule still firing in real source),
and the known false positives that must stay silent. The runtime selftest plants
20 finding kinds in the fixture, asserts the dedup invariants (one 404 = one
finding; classified console texts do not double as `console.error`), runs a
differential check (distinct inputs must yield distinct output), drives the
journey and `--mutate` engines against a two-variant SPA — the stale variant
must be flagged, the fixed one must not — and asserts role ownership end to end:
each lens sweeps only its own subtree, an unreached route lands in `unreached`
and **not** in the findings, and a route no role claims is counted as unowned.

One assertion there is about the suite itself: a run that wrote **no report** used
to make every following `grep` return non-zero, which reads as "the bad string is
absent" and passes. The suite now fails loudly on a missing report — it caught a
crash on the first run after it was added. Not planted (still trust-but-unproven):
real hydration/chunk/CSP events (their console *classification* is tested via
planted text, not provoked browser events), LCP-over-threshold, redirects/auth,
and the leak check. **Run both after any edit to a rule.** A rule that silently
stops matching keeps reporting green.

## Wiring the gate

Done is an exit code, not a sentence — **and the exit code must survive the
wiring.** `verify.sh ... || echo BLOCKED` returns echo's 0 and waves every
failure through; that exact bug shipped in an earlier version of this section.
A Stop hook blocks on exit 2, so re-exit explicitly:

```json
{ "hooks": { "Stop": [{ "hooks": [{ "type": "command",
  "command": "bash ~/.claude/skills/frontend-verify/verify.sh \"$CLAUDE_PROJECT_DIR\" --quiet || { echo 'BLOCKED: frontend-verify found P0/P1 findings — run it without --quiet to see them' >&2; exit 2; }" }] }] } }
```

In CI and pre-commit hooks, run `verify.sh` bare — its own exit status is the
gate; anything appended after `||` must end in `exit 1` or the pipeline reads
green. Pass `--base` against the preview deployment in CI so the runtime half
runs too.

The agent cannot end a turn claiming done while that exits non-zero.

## Marathon mode: hours of testing, zero authoring from the user

The user starts it and confirms two facts (dev database; auth credentials if
gated). Everything else — including the journeys and the business assertions —
**the agent derives from the repo**. The build already encodes the intent: a
form's fields say what the feature accepts, its mutation says what it writes,
the entity matrix says where the result must appear, and a server-computed
`total`/`count` field says what the UI number must equal. Asking the user to
restate any of that in sentences is transcription, not intent.

**Phase 0 — preconditions (refuse to skip).** App reachable at `--base`, dev
DB confirmed (`--mutate` submits real forms). Clean branch — one commit per
fix, revertible. If any route redirects to login, ask the user for dev
credentials ONCE and pass `--login user:pass` — the sweep logs in through the
app's real form and persists the state, so this never comes up again. A sweep
that reaches 6/49 routes is a lap of the parking lot. Both selftests pass —
calibrate the instruments before the flight. Big app? `--parallel 4`.

Then **count the principals before the first sweep, not after the first
confusing report.** If the app has more than one (a staff console and a customer
portal; an admin area; anything behind a different login), write
`verify.roles.json` now — auth state *and* `owns` — because a role sweep without
ownership is not a partial report, it is a report where most of the P1s are the
tool describing your cookie jar. `summary.routesUnowned > 0` at the end of a run
means a route tree nobody claimed and nobody looked at.

Two operational rules that each cost a full run when they were learned:
**nothing else may build while the sweep runs** (a concurrent web build starves
the dev server and the sweep aborts as `server unreachable`), and when a run does
abort, **rerun with `--resume`** rather than from the top.

**Phase 1 — study.** Run the inventory, then read the source of every route
with a mutation. Write `.verify/ledger.md`, one row per route:
`| route | entities | mutations | journey | swept | status |` with status
`untested → journeyed → swept → clean | bug:<id> → fixed`. Ledger rows must
equal `inventory.counts.routes` — state both numbers; a ledger built from a
truncated list tests a sample and reports a total. Dynamic routes get a seed
note: which record the journey creates so the sweep's `:id` blind spot closes.

**Phase 1b — if the app has a mock layer, diff it against the generated one.**
This is the highest-yield thing in the whole marathon that no DOM invariant can
reach, and it is mechanical. A mock fixture and a generated API schema are two
copies of one contract; they drift the moment a migration lands and nobody
mirrors it, and the drift is invisible to typecheck, lint and every unit test
because the mocks *are* the test data. Both of these were found that way, and
neither is findable any other way:

- a field REQUIRED in the generated schema, absent from the mock payloads →
  the page threw `Cannot read properties of undefined` on load.
- a permission granted to 8 roles in a migration, present in neither mock role
  catalog → one route unreachable by **every** persona, plus 7 more missing
  grants found from the same diff.

So: find the pair (`mocks/payloads.ts` vs `lib/api/generated/schema.ts`, a role
catalog vs `migrations/*.up.sql`) and diff the key sets. The sweep will land you
on the page that crashes; only this tells you why. Corollary: **a run against
mocks tests the mocks.** Note it in the exit report rather than letting a green
sweep imply the real backend agrees.

**Phase 2 — the agent writes the journeys.** For every row with a form or
mutation, generate the journey in `verify.journeys.mjs` from what Phase 1
read: fill the form's actual fields, submit, client-side-navigate to each
route the entity matrix says renders the result, assert the new record is
there. Derive assertions from code, in this order of confidence:
1. **Free** (no authoring at all): the 18 sweep invariants plus
   `data.rendered-zero-of-n` — DOM rows vs API array length is already checked
   on every route.
2. **Derived**: the API response carries `total`, `sum`, `count`, `balance`,
   or a field computed from a list in server code → assert the rendered number
   equals the recomputation from the rendered rows.
3. **Residue**: only a rule invisible in code (a legal threshold, a domain
   convention) earns a question to the user — expect a handful per app, not
   hours. If unanswered, ship the derived assertions and mark the ledger row
   `clean*` (consistency-checked, intent unconfirmed) — never block on it.
Use `playwright-cli` to discover selectors; the durable output is the journey
file, not the browsing session.

**Phase 3 — the loop.** This is the hours part:

```
run verify.sh <repo> --base <url> --auth .verify/auth.json --mutate --ratchet
  exit 0? → done.
  → pick the TOP finding (P0, then P1, then count) → fix the ROOT CAUSE
    (grep every caller first; one guard in the shared function beats N at
    N call sites) → commit that one fix → update the ledger row
  → selftests still pass → rerun → repeat
  RATCHET failure → revert the last commit, take the next finding instead
```

Pace with `/loop` or scheduled wakeups, never sleep-polling; long sweeps run
in the background and deserve one check when they finish. Checkpoint every ~45
minutes: commit plus a one-line ledger summary ("31/49 clean, 3 fixed, 2
open") — numbers, not adjectives. A finding judged a false positive is not
ignored: it goes through the rule loop below (counter-example planted,
selftest green) or stays on the ledger as open; there is no third bucket.
Independent bugs on disjoint routes may fan out to parallel agents — one
ledger row each, full gate before reporting, commit hash or "blocked" and
nothing else; never two agents on one store or hook.

**Exit report.** Routes total / clean / fixed (commit hashes) / open (finding
ids), the ratchet trajectory, and the gate's exit code quoted verbatim. If the
gate is red at hand-off, the first word is FAIL.

Two rules keep the loop honest, and both are enforced, not aspirational:

- **The detectors are not the patient.** After any edit to `classify.mjs`,
  `probe.js` or `sweep.mjs`, both selftests must pass — a "fix" that blinds a
  rule is caught by its planted instance. And prefer not to edit them mid-run
  at all: one marathon spent roughly a quarter of its budget tuning the
  classifier instead of the app. A false positive during the loop goes to
  `.verifyignore` or to the ledger as open; the rule change is its own task,
  afterwards, with its own planted counter-example.
- **`--ratchet`: total findings never increase.** A fix that trades one finding
  for two exits 1 with `RATCHET`, and the right response is revert-and-retry,
  not argue. The baseline (`.verify/ratchet.json`) tightens itself on every
  improvement; delete it only to knowingly accept a regression.

## The loop that ends the clicking

Every bug you still find by hand becomes a rule **once**:

1. Reproduce it.
2. Add the rule to `classify.mjs` (static) or `probe.js` (runtime) — or, if it
   is a flow bug, three lines in `verify.journeys.mjs`.
3. Plant an instance in the matching fixture and confirm the selftest catches it.
4. Fix the bug.

Clicking hours currently produce nothing durable, which is why they recur on
every project. Under this rule each one permanently retires a defect class
across every repo you own, and the manual pass asymptotes toward zero.

## References

- `references/atlas.md` — the full failure taxonomy, 11 layers, each class keyed
  to its detection method. Rule IDs in tool output (`L4.36`) index into it.
