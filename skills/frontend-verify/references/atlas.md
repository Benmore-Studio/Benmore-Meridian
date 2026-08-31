# Frontend failure atlas

Every way a frontend fails, organised by **pipeline position** — the order is
information: a defect at L1 makes every check below it meaningless, because you
are testing a build nobody is serving.

Detection column:

| | Meaning |
|---|---|
| **S** | Static. `classify.mjs` / `inventory.mjs`. Free, exhaustive, runs on save. |
| **R** | Runtime invariant. `sweep.mjs` + `probe.js`. No per-feature authoring. |
| **G** | Generated journey. Derived from the route×entity matrix. |
| **H** | Human intent. The irreducible part — one question per entity. |
| **A** | Architecture-dependent: applies only if you chose that architecture. |

`†` = observed in this user's own session corpus (86 sessions, 532 findings).

---

## L1 — Delivery: the code under test is not the code being served

Everything below L1 is void if L1 is wrong. Check it first, always.

| # | Class | Det |
|---|---|---|
| 1.1 | Build-time env (`NEXT_PUBLIC_*`, `VITE_*`) set at runtime — never reaches the browser † | S |
| 1.2 | CDN/edge cache not invalidated after deploy; old bundle still served † | R |
| 1.3 | Two hosts serving different builds; health check green against a placeholder † | R |
| 1.4 | Service worker serving a stale app shell | R |
| 1.5 | `ChunkLoadError` — hashed chunk gone after deploy, open tabs break | R |
| 1.6 | Wrong `basePath`/`assetPrefix` → every asset 404s | R |
| 1.7 | Env var present in CI, absent in the runtime image | S |
| 1.8 | Build succeeded with a stub/fallback module aliased in | S |
| 1.9 | Verified on preview, shipped from prod — different pipeline † | H |
| 1.10 | Route's first visit failed, retry succeeded — intermittent; reported as `route.flaky`, never as a silent pass | R |

## L2 — Arrival: the data never gets there

| # | Class | Det |
|---|---|---|
| 2.10 | Request never fired (`enabled: false`, conditional hook) | R |
| 2.11 | 401/403 — token not attached, or expired mid-session | R |
| 2.12 | HTTP 200 with an empty array — wrong tenant or filter scope | G |
| 2.13 | Only page 1 rendered; pagination never wired | G |
| 2.14 | Race: the slower response overwrites the newer one | S+R |
| 2.15 | Waterfall — dependent sequential fetches; partial at every instant | R |
| 2.16 | Response applied after unmount; no `AbortController` | S |
| 2.17 | Cache-key collision — two queries share one key | S |
| 2.18 | Cache-key over-specificity — one entity cached under N key shapes | S |
| 2.19 | Retry storm → rate limit → looks like "no data" | R |
| 2.20 | CORS preflight failure — invisible behind a dev proxy | R |
| 2.21 | Parse failure returns `undefined`, treated as empty | R |
| 2.22 | Same-origin JSON array carried N>0 records; every list on the page rendered zero rows — the data arrived and was never rendered | R |

## L3 — Synchronisation: data arrives, then diverges

**The cross-page sync bug lives here.** `inventory.mjs syncRisks` finds most of
it statically, with blast radius.

| # | Class | Det |
|---|---|---|
| 3.22 | **Server entity copied into a client store** — a second source of truth the query cache cannot invalidate | S |
| 3.23 | Mutation with no invalidation → every sibling view stale | S |
| 3.24 | Invalidation targets the wrong key — nothing the written resource's readers query under; blast radius resolved | S |
| 3.25 | Optimistic update never reconciled with server truth | G |
| 3.26 | Optimistic update not rolled back on error | G |
| 3.27 | Two components own one mutation; only one invalidates | S |
| 3.28 | Derived state not recomputed — `useState(props.x)`, stale closure, dead memo | S |
| 3.29 | Tearing — external store read without `useSyncExternalStore` under concurrent rendering | S |
| 3.30 | Cross-tab divergence (no storage/broadcast sync) | A |
| 3.31 | Realtime subscription not re-established after reconnect | A |
| 3.32 | Form draft silently overwritten by a background refetch | G |
| 3.33 | Deleted entity still referenced by a cached list | G |
| 3.34 | Pagination cache not reset on filter change → mixed pages | G |
| 3.35 | Write succeeded through the real form, then client-side navigation to a blast-radius route refetched nothing and shows the old value — 3.23/3.24 confirmed live (`--mutate`) | R |

## L4 — Rendering and lifecycle

| # | Class | Det |
|---|---|---|
| 4.34 | Missing loading state → empty shell paints first | S+R |
| 4.35 | Missing error state → failure renders as empty, silently | S |
| 4.36 | **Missing empty state → an empty list and a failed fetch are indistinguishable** | S+R |
| 4.37 | Suspense boundary converts an error into a permanent spinner | R |
| 4.38 | Error boundary catches and renders nothing | S |
| 4.39 | Hydration mismatch — SSR output ≠ first client render | R |
| 4.40 | List key collision (`key={index}`) → wrong row updates on reorder | S |
| 4.41 | Effect dependency bug → infinite render, or never runs | S |
| 4.42 | Conditional hook order violation | S |
| 4.43 | Portal/modal escapes its theme or stacking context | R |
| 4.44 | Virtualised list renders zero rows at certain heights | R |
| 4.45 | Layout shift on data arrival (no reserved space) | R |

## L5 — Value and serialisation: the leaks

Cheapest class to detect, highest hit rate, almost nobody checks it.

| # | Class | Det |
|---|---|---|
| 5.46 | `undefined` rendered as text † (this one reached a live API in prod) | R |
| 5.47 | `NaN` rendered | R |
| 5.48 | `[object Object]` rendered | R |
| 5.49 | `Invalid Date` rendered | R |
| 5.50 | The string `"null"` rendered | R |
| 5.51 | Unresolved template variable † | R |
| 5.52 | Timezone — the date shifts by a day | H |
| 5.53 | Currency — cents/dollars confusion, float rounding | H |
| 5.54 | Locale/number formatting inconsistent between views | H |
| 5.55 | Unescaped HTML or raw markdown shown | S |
| 5.56 | Truncation with no ellipsis or title | R |
| 5.57 | Enum rendered raw (`in_progress`, not "In progress") | R |
| 5.58 | Precision loss on large IDs (JS number vs int64) | H |

## L6 — Interaction and control flow

| # | Class | Det |
|---|---|---|
| 6.59 | **Double submit** — no pending guard → duplicate records | S |
| 6.60 | Navigation during a pending mutation → lost write | G |
| 6.61 | Back button does not restore list state, scroll, or filters | G |
| 6.62 | Refresh on a deep link loses required state | G |
| 6.63 | Unsaved-changes guard missing | S |
| 6.64 | Interactive element covered by another element — clicks land on the occluder (`interact.click-occluded`; open dialogs and `pointer-events:none` overlays excluded) | R |
| 6.65 | Focus lost after an action → keyboard user stranded | R |
| 6.66 | Client validation passes; server rejects with an unhandled error shape | G |
| 6.67 | Disabled state not conveyed — looks clickable, does nothing | R |
| 6.68 | Async action with no feedback → the user clicks again | S |

## L7 — Access and identity

| # | Class | Det |
|---|---|---|
| 7.69 | Role-gated route reachable by deep link | G |
| 7.70 | UI hides an action the API allows — or shows one it denies | G |
| 7.71 | Tenant scope missing from a query → cross-tenant leak | G |
| 7.72 | Session expiry → redirect loop, or silent empty data | R |
| 7.73 | Stale permissions cached after a role change | G |
| 7.74 | XSS sink — unsanitised HTML injection | S |
| 7.75 | Prototype pollution — merging untrusted payload into an object | S |
| 7.76 | DOM clobbering — a named element shadowing a global | S |
| 7.77 | CSP violation blocking a real resource | R |
| 7.78 | `SameSite=None` cookie without `Secure` — the browser rejects it; auth silently absent (`security.cookie-samesite-none-insecure`) | R |

## L8 — Responsive and layout

| # | Class | Det |
|---|---|---|
| 8.79 | Horizontal scroll at 320/390 | R |
| 8.80 | Overlap or clipping at a breakpoint | R |
| 8.81 | Tap target < 24px — **excluding sr-only elements** † | R |
| 8.82 | Long content (400-char name) breaks the layout | R |
| 8.83 | Broken image with no fallback dimension | R |
| 8.84 | Dark-mode override missed † | R |
| 8.85 | Font swap shift | R |
| 8.86 | Fixed height clips content at large text size or zoom | R |

## L9 — Accessibility

| # | Class | Det |
|---|---|---|
| 9.87 | Contrast below threshold | R |
| 9.88 | Control with no accessible name | R |
| 9.89 | Keyboard trap, or unreachable control | R |
| 9.90 | Focus order does not follow visual order | R |
| 9.91 | No visible focus ring | R |
| 9.92 | Async result with no live region | S |

## L10 — Performance

| # | Class | Det |
|---|---|---|
| 10.93 | Long task > 200ms — input blocked for that window (INP) | R |
| 10.94 | CLS > 0.1 — content moves under the cursor | R |
| 10.95 | LCP > 2500ms | R |
| 10.96 | Layout thrash — geometry read after DOM write, in a loop | R |
| 10.97 | Memory leak — heap retained after GC across navigation | R |
| 10.98 | Unstable context value → re-render storm, memoisation dead | S |
| 10.99 | Unbounded list render | S |
| 10.100 | Bundle size regression | S |
| 10.101 | Preloaded resource never used — Chrome's own diagnostic, exact-matched (`perf.unused-preload`) | R |

## L11 — The check itself

**The highest-leverage layer and the one nobody writes down.** Every class here
makes the layers above report green while broken.

| # | Class | Det |
|---|---|---|
| 11.101 | Capture fires before render → the gate measures nothing † *"worse than no gate — it consumes the verification slot without occupying it"* | H |
| 11.102 | Baseline captured from the buggy build → locks the bug in as correct | H |
| 11.103 | An assertion that cannot fail (empty selector, truthy on undefined) | H |
| 11.104 | The check ran against the wrong host or build † | R |
| 11.105 | Test skipped or filtered, reported green | H |
| 11.106 | Claim inflation — report says 103, reality is 1 † | H |
| 11.107 | **Verified at the wrong layer — API green, UI broken** † | G |
| 11.108 | Fixture regenerated from actual output → the test becomes a screenshot of the bug † | H |
| 11.109 | Gate returns "inconclusive" and is read as pass | H |
| 11.110 | Route absent from the sweep because the route list is hardcoded | S |

11.107 is the mechanism behind "Claude said it was built": the API was checked,
it answered correctly, and the UI had no password field because the env var was
inlined at build time. Verification at one layer says nothing about the layer
above it.

---

## The advanced concept list, sorted by what you can do with it

Concepts split three ways. Only the middle column is testable — but the first
column is what tells you **where to place the probe**, so it is not wasted.

### Mechanisms — explain why a class exists; not themselves testable

Reconciliation · Fiber · virtual DOM diffing · structural sharing · referential
equality · immutable data patterns · event loop (macro/microtasks) · scheduler
priorities · time slicing · concurrent rendering · critical rendering path ·
paint vs composite vs layout · browser compositing layers · GPU acceleration ·
subpixel rendering · tree shaking internals · garbage collection timing ·
accessibility tree · virtual DOM complexity · priority inversion

Read these to know *why* `key={index}` corrupts rows (reconciliation), why a new
object literal kills memoisation (referential equality), why a geometry read
after a write stalls (layout → paint → composite ordering).

### Observable — these ARE the runtime probes

| Concept | Becomes | Atlas |
|---|---|---|
| Hydration / selective hydration | React #418/#423/#425 in console; click before hydrate is dropped | 4.39 |
| Tearing in concurrent UI | external store read without `useSyncExternalStore` | 3.29 |
| Stale closure problem | effect with `[]` deps reading state | 3.28 |
| Memoisation pitfalls | Provider value is a fresh literal each render | 10.98 |
| Layout thrashing | geometry reads interleaved with writes in one frame | 10.96 |
| Long tasks API / FID / INP | longest task > 200ms | 10.93 |
| CLS / LCP | PerformanceObserver, buffered | 10.94-95 |
| Detached DOM nodes / leak detection | heap retained after GC across navigation | 10.97 |
| `ResizeObserver` loop limit | its own console error — free once console is a gate | 4.41 |
| `MutationObserver` cost | forced-reflow counter | 10.96 |
| Render waterfalls | dependent request chain ≥ 3 | 2.15 |
| `AbortController` | fetch in effect without a signal | 2.16 |
| Backpressure / streaming fetch | unconsumed reader → stalled render | 2.21 |
| Task starvation | long task + no yield | 10.93 |
| Service Worker lifecycle traps | stale app shell; buildId mismatch | 1.4 |
| Cache invalidation / SWR / ETag vs Cache-Control | response headers on the sweep | 1.2 |
| Code splitting / dynamic import chunking | `ChunkLoadError` | 1.5 |
| CORS preflight | failed OPTIONS | 2.20 |
| CSP / Trusted Types | `securitypolicyviolation` | 7.77 |
| SameSite cookie modes | cookie attributes after login | 7.78 |
| XSS / CSRF / DOM clobbering / prototype pollution | static sink detection | 7.74-76 |
| Race conditions in UI state | two fetches, slower wins | 2.14 |
| Optimistic UI rollback | mutate → force error → assert revert | 3.26 |
| Idempotent UI actions | double-submit guard | 6.59 |
| Deterministic rendering | render twice, diff | 11.103 |
| Preload / prefetch / preconnect, priority hints | resource timing on the sweep | 10.95 |
| IndexedDB | quota + upgrade failure paths | A |
| ARIA live regions | async result with no announcement | 9.92 |
| Pointer events | tap target + hit testing | 8.81 |
| Speculative prerendering | double-fired effects on prerender | A |

### Architecture — change which classes apply, not what you check

Islands · partial hydration · streaming SSR · server components · edge rendering
· micro-frontend orchestration · module federation · Shadow DOM · custom
elements · Web Components interop · Web Workers vs Service Workers ·
`SharedArrayBuffer` · transferable objects · `OffscreenCanvas` · WebAssembly ·
WebRTC · CRDTs · event sourcing · finite state modelling · offline conflict
resolution · CSS containment

Pick one and a whole column of classes switches on. Islands and partial
hydration make 4.39 and "click before hydrate" primary. Micro-frontends and
module federation make 1.3 (two hosts, different builds) a weekly event. CRDTs
and offline make 3.30-3.31 the dominant risk. **Configuration, not new code.**

---

## Evaluated and deliberately not implemented

Each of these was specced far enough to know why it must not ship yet. A rule
that fires on healthy apps costs more than the class it catches.

| Check | Why not |
|---|---|
| duplicate-in-flight-request (2.14's runtime half) | needs a proven guard separating React StrictMode's double-invoke from a real race; ship only with a StrictMode fixture asserted silent |
| bundle-size-regression (10.100's runtime half) | needs a per-repo build-output path; no universal baseline location in monorepos |
| render-blocking-head-script | fires on deliberately synchronous analytics snippets — "verify this is intentional" is not a defect claim |
| missing-live-region-for-async-status (9.92) | scoping unresolved: a live region far from the toast is still a live region; the conservative gate leaves mostly misses |
| indexeddb-open-error | too narrow — apps touch IndexedDB through libraries that already handle it |
| deterministic-rendering (render twice, diff) | the noisiest possible rule: timestamps, counters, carousels and A/B buckets are legitimately non-deterministic |
| CSRF-token-presence | token-auth and SameSite-cookie architectures are both healthy without one; the absence proves nothing |

## Adding a class

1. Reproduce it once, by hand.
2. Add the rule to `classify.mjs` (S) or `probe.js` (R).
3. Plant an instance in `references/fixture.html` or `selftest-static.sh`.
4. Confirm the selftest **fails without the fix and passes with it**.
5. Give it a number here.

Step 4 is the one people skip, and skipping it produces 11.103 — a rule that
occupies the verification slot while asserting nothing.
