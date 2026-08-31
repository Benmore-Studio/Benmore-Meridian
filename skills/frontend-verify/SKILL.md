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

`--widths 390,1440` sweeps the cell matrix rather than one width. `--states`
forces empty/500/403/malformed/slow on each route's own data and grades what it
renders (`--states empty,error` to pick). Together with `--mutate` these are the
three passes that find what a happy-path load cannot:

```bash
bash $S/verify.sh /abs/repo --base URL --prod --widths 390,1440 --states --mutate
```

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
| `--states` | what each surface renders when its own data comes back empty / 500 / 403 / malformed / slow — silent failures, stuck spinners, blank screens, missing empty states | anything behind a form or a click |
| `--widths` | every width-dependent invariant at every width, as its own cell | — |
| `--mutate` replay | whether a real write through a real form leaves a blast-radius route stale under client-side navigation, **and whether the write survives a reload at all** | which payload a form considers valid |
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

## Sweep a production build, not the dev server

The single largest cost and the single largest source of fictional findings in
every long run measured. A dev server compiles each route on first request:
8–23s each, measured (`/signature-templates` 22.3s, `/quarterly-reports` 18.3s).
Across 36 routes that is **6–12 minutes of pure compilation per sweep**. Build
once instead and the same 72-cell sweep takes **41 seconds**, routes serving in
~2ms. Build the app the way its own e2e setup does — with mocks if that is how it
runs offline — then point `--base` at it and pass `--prod` so timing findings
grade normally:

```bash
pkill -f "next dev"; rm -rf apps/web/.next     # they share .next: PageNotFoundError /_document
bun --filter web build:e2e && E2E_PORT=3000 bun --filter web start:e2e &
curl -sf --retry 90 --retry-delay 1 --retry-all-errors http://localhost:3000/login
bash $S/verify.sh /abs/repo --base http://localhost:3000 --prod
```

Compile time is not merely slow, it manufactures failures: under load the dev
server served pages in 14–20s, service-worker registration blew its budget so
**logins returned 404**, and `page.goto` hit hard timeouts — failure shapes
indistinguishable from real product bugs. The warm pass below exists for when you
cannot build; it is a mitigation, not the answer. Same reason `--parallel` needs
a re-measurement before you trust it: 88 browser processes took one box to load
25 and every number after that was about the box.

## The integrity gate: prove the run measured the app

A probe over lock screens reports **clean**. That is the failure this whole skill
exists to prevent, and it is invisible in the findings — only in the shape.
Record and check all four before reading a single finding:

```
swept == planned    ·   0 fatal-login    ·   0 bounced-to-login    ·   bytes > floor
```

The sweep now grades **itself** on exactly that, before its findings are allowed
to mean anything, and writes the verdict to `report.integrity`. A run that fails
**exits 2 — could not run — never 0.** Do not merge it, do not average it, and
never read "no findings" from it.

```
integrity  51/51 cells measured  ·  0 bounced to login  ·  0 below the text floor  ·  47 distinct surfaces
```

The load-bearing one is the last: **distinct surfaces per measured cell.** A real
app's routes do not share their first 400 characters, so when most cells
fingerprint alike, one page was measured under many names. That single check
catches both historical shapes — 45 routes that all landed on `/login`, and a
whole matrix of PASS over pages that never rendered. Measured: one sweep filed
45 `tap-target` findings across 45 routes from two selectors, because it ran
unauthenticated. 48 findings, 3 real.

The bounce and blank checks are **proportional** (`--integrity-share`, default a
quarter) and only apply from six cells up. Two gated routes out of fifty is a
coverage note, and hard-failing on it blocks the fix loop — which is the budget
burn this skill exists to stop. A quarter of the run landing on the auth wall is
a different animal: at that point "no findings" is a claim about the login page.
Both numbers print either way.

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

## Triaged once, not every run

`verify-ignore: <rule-id>` in a comment on, or within 6 lines above, a flagged
line drops that one rule at that one line — every static rule, plus `sync-risk`
for the inventory's own P1s. Not the file, not the rule globally. Say WHERE the
guarantee comes from in the same comment, so the waiver stays checkable at
review, and note that waived findings are **counted and listed** in the report
(`waived`, `syncRisksWaived`), never silently dropped.

```ts
// verify-ignore: sync-risk -- pushes to Mailchimp; no segment list exists in this app
export function usePushAudienceSegment() { ... }
```

This is the difference between a gate and a chore. Without it a finding proved
false in a written triage comes back at full severity on the very next run, with
nowhere to record the verdict — measured, a marathon spent roughly **a quarter of
its budget** re-triaging findings and hand-tuning the classifier mid-run instead
of fixing the app. It lives in the source rather than in a central ignore file
for the same reason the design-lab exclusion does not: a waiver next to the code
moves with it and dies with it, while a path in a list outlives the line it was
written for.

Waive only what you have *proved*, with the proof in the comment. `.verifyignore`
is still the right tool for whole trees; the ledger is still the right place for
"open, unexplained".

## Playwright: the library, not the CLI

The sweep drives `playwright.chromium.launch()` directly, from a copy vendored in
the skill. Use the `playwright-cli` skill for what it is good at — poking at a
live page to **discover selectors** while writing `verify.journeys.mjs` — and not
as the sweep's engine. Its `run-code` sandbox has gaps that each cost a real run:

- no `process` — bake values into a generated per-role script instead
- no `URL` — `page.url().replace(/^https?:\/\/[^/]+/, "").split("?")[0]`
- no backticks and no `$` in any string passed as a shell argument, including
  inside a comment that lands in a generator's template literal. This bit **three
  separate times**.

The durable output of a browsing session is the journey file, never the session.

## Forced states — `--states`

The highest-yield pass, and the one nothing else reaches. What each surface does
on **empty / 500 / 403 / malformed / slow** is written once and then executed by
nobody: a mock layer always serves a populated happy path, so those branches rot
invisibly. `--states` runs all five; `--states empty,error` picks.

It forces **only the URLs the baseline sweep watched that route fetch** — guessing
at "things that look like an API" breaks RSC payloads and asset loads, and the
page then reports the wreckage as its own defect. Three measured facts shape it:

- **`page.route()` does not intercept an app with a mock service worker.**
  `page.on('request')` saw 10 `/v1/*` calls on a route where `page.route("**/v1/**")`
  saw **zero** — the worker answers inside the page, and unregistering it does not
  help because the app re-registers on mount. So the forcing is a
  `page.addInitScript` that patches `window.fetch` *and* `XMLHttpRequest` before
  the app's JS runs, which is the only vantage point earlier than the worker.
- **Auth paths are never forced.** Breaking auth logs the session out, and every
  later cell measures a login page while reporting clean.
- **Identical columns mean the experiment never ran.** Measured in the wild as six
  **byte-identical** forced-state columns. When it happens the pass files
  `state.not-intercepted` and *withholds* that route's other findings rather than
  reporting them as clean.

Everything is read from the **rendered text**, never the response: a 500 that
renders a blank screen and a 500 that says "something went wrong" are the same
HTTP status and opposite products. `state.silent-failure` is the one that matters
most — the request failed and the surface says nothing, so it renders as though
the data arrived and the user acts on values that are not there.

## The cell matrix — `--widths`

The unit of work is a **cell**: `(role, route, width)`. Half the invariants here
are width-dependent — horizontal scroll, tap targets, covered elements — so a
one-width run grades an app nobody uses at one width. `--widths 390,1440` sweeps
both; the destination-already-measured dedup is per width, so the narrow pass
cannot inherit the wide one's verdict. Measured: the single genuine finding in a
48-finding sweep was a 183×16px link that only matters at 390px.

## `--mutate` also asks whether the write survived a reload

A 2xx is not persistence. Measured on a real repo: the mock service worker's last
branch is `if (POST||PUT||PATCH||DELETE) return ok({ok:true})`, so **every write
it does not explicitly route reports success and silently discards the data** —
the request succeeded, the cache updated optimistically, the UI showed the new
value, and it was gone. Neither typecheck, lint, unit tests, nor any DOM
invariant on a happy page can see it. So after the staleness checks (which need
the un-reloaded cache, and therefore go first), `--mutate` reloads the page and
reads the sentinel back: absent ⇒ `mutate.write-lost`, P0. It is claimed only
when the value visibly rendered before the reload — otherwise its absence
afterwards says nothing.

## Not built yet, and the traps that will eat the session that builds them

Two passes remain manual. Both were attempted by hand and both cost a run to a
harness bug rather than an app bug, so the method below is the deliverable —
build them against it, not from first principles.

**Control exercising** (clicking every control on a surface, ~1,500 of them on a
real app, to find inert affordances):

- **Never report "control not found" without having waited.** A bare `.click()`
  races hydration and times out on a control that provably exists; the failure
  reads `waiting for getByRole(...)`, which is indistinguishable from a missing
  control. One measured near-miss filed a working "New task" button as broken.
  Wait for `visible` first, and report "never appeared" and "appeared but was not
  clickable" as different findings — they need different fixes.
- **`.first()` grabs a hidden duplicate.** Responsive surfaces ship the desktop
  and mobile renderings *both in the DOM*, one CSS-hidden. Measured: Playwright
  reported `43 × locator resolved to hidden` on `main input[type=number]`. Every
  locator must be `:visible`-scoped. (`probe.js` already filters this way, which
  is why the `--widths` cells measure different nodes and not one node twice.)
- An inert control and a lost write look identical on screen and need opposite
  fixes. `--mutate`'s reload check is what separates them.

**Dark mode.** The trap is the theme library, not the CSS. Under next-themes with
`enableSystem={false}` — a common setup:

- `emulateMedia({ colorScheme: 'dark' })` does **nothing**, because
  `prefers-color-scheme` is never consulted. A pass that only emulates the media
  query reports "dark renders identically to light" and is wrong about why.
- Injecting a `.dark` class around hydration is **stripped**: the library
  reapplies from storage after mount.
- What works: seed `localStorage.theme` in an init script **before first
  navigation** — the same lever `--states` uses. Better still, click the app's own
  theme control when it has one, and fall back to seeding storage on chrome-less
  routes (public token pages) that ship no toggle.
- Grade it as **two** findings, never one. "Dark tokens apply" (html carries the
  class, `color-scheme: dark`, body/background colours inverted) is inheritance
  only; it does not prove per-element contrast or the absence of hardcoded light
  values. Reporting the first as "dark is correct" is the same overclaim as
  reporting a swept login wall as a clean app.

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
- **Group by `(rule, selector)` before reading any count.** A finding repeated
  across N routes is usually one finding about the surface all N of them landed
  on, or one shared component. Three tools in one session each produced a
  headline that was mostly artifact — 320 findings that were 28 distinct pairs
  and then 6 real classes; 357 that were 335 duplicate copies of the repo; 48
  that were 45 repeats of the login page — and in every case the tell was the
  same one selector or one path repeated down the rows. Check the denominator
  counts routes, not cells.
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
- **Vendored UI primitives ship the same false positive to every repo that has
  them.** `<style dangerouslySetInnerHTML>` injects CSS text — there is no parser
  to smuggle a `<script>` past, so "raw HTML injection, XSS sink" is a false
  claim. That is shadcn/ui's `chart.tsx` verbatim, and it was a false **P0** in
  2 of 2 real repos, same file, same line. Before adding a rule, run it on a repo
  that ran `npx shadcn add` and look at what it says about `components/ui/`.
- **Ambient by name, not only by share.** A session write does not leave a view
  stale; it replaces the principal and the tree remounts. The share threshold
  only catches that on a large app: on a 21-route repo `auth` is read by 5
  routes, clears neither threshold, and files a P1 per auth mutation — measured,
  **4 of that repo's 7 P1 sync risks** were `/auth/login`, `/auth/mfa/enroll` and
  the two `/auth/reset/*` calls, and they outranked the one finding on the list
  worth reading.
- **A file:line that points at the wrong line is worse than no finding.** The
  reader opens it, finds nothing, and stops opening the report. Blanking a
  multi-line `/* */` to spaces once collapsed its newlines, so every finding
  below a JSDoc header was reported N lines early — silently, on every rule at
  once. The static selftest now checks reported lines against the file on disk.

## Structural tells that a run is an artifact

The costliest failures are not wrong rows, they are confident numbers produced by
a harness that never measured the thing. Every one of these was caught by shape,
not by reading any individual finding:

| Tell | What it means |
|---|---|
| Identical output across deliberately different inputs | The experiment never ran. The differential check in `selftest.sh` exists for exactly this. Seen in the wild as six **byte-identical** forced-state columns: the interception never reached the app. |
| Every page in the run weighs about the same | They are the same page. A login wall measured under N route names. |
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
P1 by share **and** by name, on few readers), the design-lab exclusion (and the
same rule still firing in real source), the `verify-ignore` waiver on two
different rules plus a sync risk (waived, counted, and not leaking to the rest of
the file), the reported `file:line` checked against the file on disk, and the
known false positives that must stay silent — `<style>` CSS among them.

The runtime selftest plants 20 finding kinds in the fixture, asserts the dedup
invariants (one 404 = one finding; classified console texts do not double as
`console.error`), runs a differential check (distinct inputs must yield distinct
output), drives the journey and `--mutate` engines against a two-variant SPA —
the stale variant must be flagged, the fixed one must not — and asserts role
ownership end to end: each lens sweeps only its own subtree, an unreached route
lands in `unreached` and **not** in the findings, and a route no role claims is
counted as unowned. It then proves the three newest passes, each differentially:

- **`--widths`** — 2 routes × 2 widths is 4 cells, each carrying its width, and
  none of them skipped. The dedup is per width or the narrow pass inherits the
  wide one's verdict and measures nothing.
- **`--states`** — two variants of one page, identical on the happy path and
  opposite when their data fails. The honest one renders an error and an empty
  state and must stay silent; the mute one must be flagged for both. Every forced
  response must change the page **from its own baseline render** — asserted that
  way rather than against the other columns, because a page that fails identically
  for 500/403/malformed is being consistent, which is not the same as an
  interception that never fired.
- **the integrity gate** — seven routes that all serve one page must come back
  `ok: false`, name the reason, and **exit 2**. That is the same artifact as 45
  routes that all landed on `/login`, and the suite fails if it reads as 0.

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

**Phase 0 — preconditions (refuse to skip).** Serve a **production build**, not
the dev server (see above — this is 41 seconds against 6–12 minutes, and it is
the difference between measuring the app and measuring the compiler). App
reachable at `--base`, dev DB confirmed (`--mutate` submits real forms). Clean
branch — one commit per fix, revertible. If any route redirects to login, ask
the user for dev credentials ONCE and pass `--login user:pass` — the sweep logs
in through the app's real form and persists the state, so this never comes up
again. Better still, **log in with the repo's own mechanism** if it has one: port
the session helper its e2e suite already uses rather than inventing a second one.
A sweep that reaches 6/49 routes is a lap of the parking lot, and one that
reaches 45 login pages is worse — run the integrity gate before believing any of
it. Both selftests pass — calibrate the instruments before the flight. Big app?
`--parallel 4`, then confirm the finding count against a serial pass.

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
run verify.sh <repo> --base <url> --auth .verify/auth.json \
      --prod --widths 390,1440 --states --mutate --ratchet
  exit 2? → INVALID. Fix the harness, not the app. Nothing below is real.
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
  classifier instead of the app. A false positive during the loop gets a
  `verify-ignore: <rule>` comment carrying its proof, or `.verifyignore` for a
  whole tree, or a ledger row as open — there is no fourth bucket, and none of
  the three is editing a detector. The rule change is its own task, afterwards,
  with its own planted counter-example.
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
