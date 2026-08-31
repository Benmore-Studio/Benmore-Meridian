#!/usr/bin/env node
// Runtime sweep. Drives every route in the inventory and applies the universal
// invariants. Exits non-zero on P0/P1 -- that exit code is the definition of done.
//
//   node sweep.mjs --repo <repoRoot> --base http://localhost:3000
//                  [--routes /,/dashboard] [--width 1280] [--auth state.json]
//                  [--leak-check] [--mutate] [--no-journeys] [--json <path>]
//
// --repo anchors everything: the inventory is read from <repo>/.verify/inventory.json
// and the report is written to <repo>/.verify/sweep.json. Nothing resolves against
// the current working directory, because this skill runs against many repos and a
// cwd-relative path drops one repo's report into another's directory.
//
// --mutate is OPT-IN and DESTRUCTIVE: it drives real forms and submits real
// writes to verify that cross-page caches actually refresh. Run it against a
// dev database only.
//
// App-owned journeys: <repo>/verify.journeys.mjs (or .verify/journeys.mjs)
// exporting [{ name, run(page, { base }) }]. Each runs under the same console/
// network listeners and gets the full probe applied to wherever it ends up.
//
// Playwright is resolved from the TARGET repo, not from here: the skill carries
// no node_modules and must not pin a version against the repo under test.

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

const argv = process.argv.slice(2);
const arg = (n, d) => { const i = argv.indexOf('--' + n); return i >= 0 ? argv[i + 1] : d; };
const flag = (n) => argv.includes('--' + n);

const BASE = (arg('base') ?? 'http://localhost:3000').replace(/\/$/, '');
const WIDTH = Number(arg('width', '1280'));
// The unit of work is a CELL -- (role, route, width) -- not a route. Half the
// invariants here are width-dependent (horizontal scroll, tap targets, covered
// elements), so a one-width run grades an app nobody uses at one width. Measured
// on a real repo: the only genuine finding in a 48-finding sweep was a 183x16px
// link that only matters at 390px. Default stays single-width so nothing gets
// slower by surprise; `--widths 390,1440` is the honest matrix.
const WIDTHS = [...new Set(String(arg('widths', String(WIDTH))).split(',')
  .map((w) => Number(w.trim())).filter((w) => w > 0))];
const HEIGHT = Number(arg('height', '900'));
const SETTLE_MS = Number(arg('settle', '1200'));
const REPO = path.resolve(arg('repo', '.'));
const INVENTORY = arg('inventory', path.join(REPO, '.verify', 'inventory.json'));
// Auth state defaults to living beside the other per-repo reports, so a state
// captured once (by hand or by auto-login below) is reused on every later run.
const AUTH = arg('auth', path.join(REPO, '.verify', 'auth.json'));
const JSON_OUT = arg('json', path.join(REPO, '.verify', 'sweep.json'));
const PROBE = path.join(path.dirname(new URL(import.meta.url).pathname), 'probe.js');
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
// Navigation and warm-up budgets. Declared with the other config, NOT beside the
// warm-up code that motivated them: auto-login navigates before that point, and
// a const in the temporal dead zone there crashed the whole sweep before it
// wrote a single line of report.
const NAV_MS = Number(arg('nav-timeout', '60000'));
const WARM_MS = Number(arg('warm-timeout', '90000'));

/* ------------------------------------------------------------- playwright */

// Both packages are CJS, so the browser launchers arrive under `.default`
// depending on the interop path. Unwrap before use -- reading `.chromium` off the
// raw namespace gives `undefined` and fails at launch() with nothing to explain it.
const unwrap = (mod) => (mod?.chromium ? mod : mod?.default?.chromium ? mod.default : null);

// Where a self-installed Playwright lives. Shared on purpose: the browser binary
// is already a global cache, so only the npm package needs a home, and putting
// that home in the skill keeps every repo's package.json and lockfile untouched.
// --install=repo opts into a real devDependency for repos that want one checked in.
const SHARED = path.join(path.dirname(path.dirname(new URL(import.meta.url).pathname)), '.playwright');

async function tryLoad(root) {
  for (const pkg of ['playwright', '@playwright/test']) {
    try {
      const req = createRequire(path.join(root, 'package.json'));
      const got = unwrap(await import(pathToFileURL(req.resolve(pkg)).href));
      if (got) return got;
    } catch { /* next package */ }
  }
  return null;
}

function run(cmd, args, cwd) {
  const r = spawnSync(cmd, args, { cwd, stdio: 'inherit', encoding: 'utf8' });
  return r.status === 0;
}

function installInto(dir) {
  fs.mkdirSync(dir, { recursive: true });
  if (!fs.existsSync(path.join(dir, 'package.json')))
    fs.writeFileSync(path.join(dir, 'package.json'), JSON.stringify({ name: 'frontend-verify-runtime', private: true }, null, 2) + '\n');
  console.error('\n  installing @playwright/test into ' + dir + ' (one time)\n');
  if (!run('npm', ['install', '--no-audit', '--no-fund', '--save-dev', '@playwright/test'], dir)) return false;
  // The browser binary lands in a shared OS cache, so this is a no-op after the
  // first ever install on the machine, whichever repo triggered it.
  console.error('\n  ensuring the chromium binary is present (shared cache)\n');
  run('npx', ['--yes', 'playwright', 'install', 'chromium'], dir);
  return true;
}

async function loadPlaywright() {
  const repo = path.resolve(arg('repo', '.'));
  const roots = [repo, SHARED, process.cwd(), ...(process.env.PLAYWRIGHT_HOME ? [path.resolve(process.env.PLAYWRIGHT_HOME)] : [])];
  for (const root of roots) { const got = await tryLoad(root); if (got) return got; }
  try { const got = unwrap(await import('playwright')); if (got) return got; } catch { /* fall through */ }

  if (flag('no-install')) {
    console.error('Playwright not found and --no-install was passed.\n  npm i -D @playwright/test && npx playwright install chromium');
    process.exit(2);
  }
  const target = arg('install') === 'repo' ? repo : SHARED;
  if (!installInto(target)) {
    console.error('Automatic install failed. Install manually:\n  npm i -D @playwright/test && npx playwright install chromium');
    process.exit(2);
  }
  const got = await tryLoad(target);
  if (got) return got;
  console.error('Installed Playwright but could not load it from ' + target);
  process.exit(2);
}

/* ----------------------------------------------------------------- routes */

function routesToSweep() {
  const explicit = arg('routes');
  if (explicit) return explicit.split(',').map((s) => s.trim()).filter(Boolean);
  if (fs.existsSync(INVENTORY)) {
    const inv = JSON.parse(fs.readFileSync(INVENTORY, 'utf8'));
    // Dynamic segments need a real id; without one the route 404s and the sweep
    // reports a false failure. Skip them here; app-owned journeys (which have a
    // seeded record to address) are the honest way to cover them.
    return inv.routes.map((r) => r.path).filter((p) => !/[:[]/.test(p));
  }
  return ['/'];
}

// route -> how many query hooks the inventory found reachable from it. This turns
// "no data requests observed" from a heuristic into an assertion: a route the
// import graph says reads nothing SHOULD show no traffic, and flagging it is the
// tool complaining that a static page is static. Measured on a real repo, all 6
// hits were genuinely static routes (an install page, a magic-link callback).
// Only a route with data dependencies AND no traffic is evidence of anything.
function routeQueryCounts() {
  const m = new Map();
  try {
    const inv = JSON.parse(fs.readFileSync(INVENTORY, 'utf8'));
    for (const r of inv.routes) m.set(r.path, (r.queries ?? []).length);
  } catch { /* no inventory: every route is unknown, and unknown never accuses */ }
  return m;
}
const ROUTE_QUERIES = routeQueryCounts();

// ...and the join is only as good as the walk that fed it. The same import-graph
// blind spots that once reported `modules: 1` on every route also undercount
// query hooks, and an undercounting walk turns this P1 into "N hooks are
// reachable and none fired" with N invented. So the rule carries its own
// denominator check: if the walk found data dependencies on fewer than a third
// of routes, it did not resolve the app, and one route's entry is not evidence.
const QUERY_JOIN_TRUSTED = ROUTE_QUERIES.size > 0
  && [...ROUTE_QUERIES.values()].filter((n) => n > 0).length >= ROUTE_QUERIES.size / 3;

// The dev server WILL hiccup over an hours-long run. Any HTTP response at all
// means it is up; only a connection-level failure means it is not.
//
// The 5s timeout this used to carry was not a liveness check, it was a load
// check: a dev server busy compiling another route answers `/` in 30s, and the
// sweep aborted the whole run calling it dead. Give it room, and require two
// consecutive failures before believing them.
async function serverAlive() {
  for (const attempt of [0, 1]) {
    try { await fetch(BASE + '/', { signal: AbortSignal.timeout(20000) }); return true; } catch { if (!attempt) await wait(2000); }
  }
  return false;
}

/* ------------------------------------------------------------------ sweep */

const playwright = await loadPlaywright();
const routes = routesToSweep();
// Zero routes is not a clean sweep, it is a sweep that did not happen: an empty
// or unrecognised inventory, or a --routes list that filtered to nothing. Exiting
// 0 here would report PASS for an app nobody looked at.
if (!routes.length) {
  console.error('sweep: no routes to visit. Run inventory.mjs first, or pass --routes /,/dashboard.');
  process.exit(2);
}
const probeSrc = fs.readFileSync(PROBE, 'utf8').replace(/^\s*\/\/[^\n]*\n/gm, '').trim();
const probeFn = eval('(' + probeSrc + ')');

// Timing measured against a dev server is the COMPILER's, not the app's. On a
// real run 16 of 53 findings were perf.lcp, the worst reading 14,864ms against
// `next dev` -- a number with no relationship to anything a user will ever
// experience, filed at the same severity as a page that crashed. Without --prod
// these stay in the report (the reading is real) but as P3, labelled. Pass
// --prod when the base URL is a production build and they grade normally.
// perf.unused-preload and perf.memory-leak are build-independent and unaffected.
const PROD = flag('prod');
const COMPILE_SENSITIVE = /^perf\.(lcp|long-task|layout-shift|layout-thrash)$/;
function graded(probe) {
  if (PROD) return probe;
  for (const f of probe.findings ?? []) {
    if (!COMPILE_SENSITIVE.test(f.kind)) continue;
    f.severity = 'P3';
    f.detail += ' -- measured without --prod; against a dev server this is the compiler, not the app';
  }
  return probe;
}

// A launch failure is "could not run", never "found problems": exit 1 here would
// let a missing browser binary read as an app defect.
let browser;
try {
  browser = await playwright.chromium.launch();
} catch (e) {
  console.error('sweep: could not launch chromium -- ' + String(e).split('\n')[0]);
  console.error('  npx playwright install chromium');
  process.exit(2);
}
// One context per ROLE. An app with two principals (a staff session and a
// customer-portal session) refuses each other's routes by design, so a single
// context can never reach more than its own half -- and the half it cannot reach
// reports as findings unless the caller knows to ignore them. Everything below
// installs identically into every role's context.
// `headers` exists because a principal is not always a cookie jar. A staff user
// acting THROUGH the customer portal is a third lens over the same routes,
// distinguished only by a request header (`X-Profectus-Proxy-Customer`) -- same
// storage state as staff, different authority, different expected surface.
// Without it that lens is inexpressible and gets misfiled as the portal role.
async function makeContext(authPath, headers) {
  const ctx = await browser.newContext({
    viewport: { width: WIDTH, height: HEIGHT },
    ...(authPath && fs.existsSync(authPath) ? { storageState: authPath } : {}),
    ...(headers && Object.keys(headers).length ? { extraHTTPHeaders: headers } : {}),
  });
  for (const script of INIT_SCRIPTS) await ctx.addInitScript(script);
  return ctx;
}
const INIT_SCRIPTS = [];

// Playwright's network events only see traffic that reaches the browser's network
// stack. A service worker (MSW and every mock-first setup) answers fetches INSIDE
// the page, so page.on('response') fires zero times and every network invariant
// silently passes -- the tool reports clean on an app it never measured. Patching
// window.fetch and XHR before app JS runs is the only vantage point that sees both
// real and intercepted traffic.
INIT_SCRIPTS.push(() => {
  const log = [];
  Object.defineProperty(window, '__fv_net', { get: () => log, configurable: true });
  const captureArray = (entry, text) => {
    if (typeof text !== 'string' || text.length > 2_000_000) return;
    try {
      const j = JSON.parse(text);
      const arr = Array.isArray(j) ? j
        : ['data', 'items', 'results', 'rows', 'records'].map((k) => j && j[k]).find(Array.isArray);
      if (arr) entry.arrayLen = arr.length;
    } catch { /* not JSON after all */ }
  };
  const realFetch = window.fetch;
  window.fetch = async function (...args) {
    const url = String(args[0]?.url ?? args[0] ?? '');
    const method = (args[1]?.method ?? args[0]?.method ?? 'GET').toUpperCase();
    const start = performance.now();
    try {
      const res = await realFetch.apply(this, args);
      const entry = { url, method, status: res.status, ok: res.ok, start, end: performance.now(), via: 'fetch' };
      log.push(entry);
      if (res.ok && (res.headers.get('content-type') ?? '').includes('json'))
        res.clone().text().then((t) => captureArray(entry, t)).catch(() => {});
      return res;
    } catch (e) {
      log.push({ url, method, status: 0, ok: false, error: String(e), start, end: performance.now(), via: 'fetch' });
      throw e;
    }
  };
  const RealXHR = window.XMLHttpRequest;
  if (RealXHR) {
    const open = RealXHR.prototype.open, send = RealXHR.prototype.send;
    RealXHR.prototype.open = function (m, u, ...rest) { this.__fv = { url: String(u), method: String(m).toUpperCase() }; return open.call(this, m, u, ...rest); };
    RealXHR.prototype.send = function (...a) {
      const meta = this.__fv;
      if (meta) {
        meta.start = performance.now();
        this.addEventListener('loadend', () => {
          const entry = { ...meta, status: this.status, ok: this.status >= 200 && this.status < 400, end: performance.now(), via: 'xhr' };
          log.push(entry);
          try { if (entry.ok && (this.responseType === '' || this.responseType === 'text')) captureArray(entry, this.responseText); } catch { /* opaque */ }
        });
      }
      return send.apply(this, a);
    };
  }
});

// Performance instrumentation must be installed BEFORE navigation. Reading
// performance.getEntriesByType() after the fact returns nothing for longtask /
// layout-shift / LCP in Chromium (deprecated for those types), so the perf gates
// would report clean numbers for pages they never measured. Buffered observers
// from an init script are the supported vantage point; same for layout thrash,
// which happens during load -- instrumenting it after settle watches an empty frame.
INIT_SCRIPTS.push(() => {
  const perf = { longTasks: 0, longestTaskMs: 0, cls: 0, lcpMs: null, thrashReads: 0 };
  Object.defineProperty(window, '__fv_perf', { get: () => perf, configurable: true });
  // Observer callbacks are delivered asynchronously; a reader that does not
  // drain the pending queue first can race a just-finished entry and miss it.
  const pending = [];
  perf.flush = () => pending.forEach(([o, fn]) => o.takeRecords().forEach(fn));
  const observe = (type, fn) => {
    try {
      const o = new PerformanceObserver((l) => l.getEntries().forEach(fn));
      o.observe({ type, buffered: true });
      pending.push([o, fn]);
    } catch { /* unsupported */ }
  };
  observe('longtask', (e) => { perf.longTasks++; perf.longestTaskMs = Math.max(perf.longestTaskMs, Math.round(e.duration)); });
  observe('layout-shift', (e) => { if (!e.hadRecentInput) perf.cls += e.value; });
  observe('largest-contentful-paint', (e) => { perf.lcpMs = Math.round(e.startTime); });
  // Layout thrash: a geometry read after a DOM write in the same frame forces a
  // synchronous reflow. Writes are detected synchronously (a MutationObserver
  // delivers at the microtask checkpoint, AFTER a sync write/read loop has
  // already finished, so it would count zero on exactly the code this catches).
  let wrote = false;
  const markWrite = (proto, name) => {
    const real = proto[name];
    if (!real) return;
    proto[name] = function (...a) { wrote = true; return real.apply(this, a); };
  };
  ['setAttribute', 'appendChild', 'insertBefore', 'removeChild', 'remove'].forEach((n) => markWrite(Element.prototype, n));
  const realRect = Element.prototype.getBoundingClientRect;
  Element.prototype.getBoundingClientRect = function (...a) {
    if (wrote) { perf.thrashReads++; wrote = false; }
    return realRect.apply(this, a);
  };
  const frame = () => { wrote = false; requestAnimationFrame(frame); };
  requestAnimationFrame(frame);
});

/* ------------------------------------------------------------------ roles */

// <repo>/verify.roles.json (or .verify/roles.json):
//
//   { "staff":  { "auth": ".verify/auth.json",        "owns": ["/"], "excludes": ["/portal"] },
//     "portal": { "auth": ".verify/auth-portal.json", "owns": ["/portal"] } }
//
// OWNERSHIP is the load-bearing half, not the auth state. An app that refuses a
// staff principal on /portal/* and a portal principal on /* is behaving
// correctly in BOTH directions, so a role swept over routes it does not own
// reports every one of them as a defect. Measured on a real repo: the portal
// lens produced 45 "requested X, landed on /login" P1s, none of them a bug.
// Owning a route is a prefix match -- route trees are prefix-shaped, and a glob
// language here would be machinery for a case nobody has.
function loadRoles() {
  const file = [path.join(REPO, 'verify.roles.json'), path.join(REPO, '.verify', 'roles.json')]
    .find((f) => fs.existsSync(f));
  if (!file) return [{ name: 'default', auth: AUTH, headers: null, owns: ['/'], excludes: [] }];
  const raw = JSON.parse(fs.readFileSync(file, 'utf8'));
  return Object.entries(raw).map(([name, r]) => ({
    name,
    auth: r.auth ? path.resolve(REPO, r.auth) : AUTH,
    headers: r.headers ?? null,
    owns: r.owns ?? ['/'],
    excludes: r.excludes ?? [],
  }));
}
const underPrefix = (route, p) => route === p || route.startsWith(p.replace(/\/$/, '') + '/');
const roleOwns = (role, route) =>
  role.owns.some((p) => underPrefix(route, p)) && !role.excludes.some((p) => underPrefix(route, p));

/* -------------------------------------------------------------- auto-login */

// A gated app without auth state sweeps 6 of 49 routes and honestly reports
// the rest unmeasured -- honest, but useless. Given credentials (flags or
// FV_LOGIN_USER / FV_LOGIN_PASS), log in through the app's real form once and
// persist the storage state beside the other reports. Delete the state file
// when it goes stale. Failure here is loud and non-fatal: the sweep proceeds
// unauthenticated and every unreached route says so.
async function autoLogin(user, pass) {
  const page = await context.newPage();
  try {
    const loginPath = arg('login-path', '/login');
    await page.goto(BASE + loginPath, { waitUntil: 'domcontentloaded', timeout: NAV_MS }).catch(() => {});
    let pw = await page.$('input[type="password"]');
    if (!pw) {
      // The app may put login elsewhere; follow its own redirect from /.
      await page.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: NAV_MS }).catch(() => {});
      await page.waitForTimeout(1500);
      pw = await page.$('input[type="password"]');
    }
    if (!pw) { console.error('sweep: auto-login found no password field at ' + loginPath + ' or / -- pass --login-path, or capture state by hand'); return false; }
    const id = await page.$('input[type="email"], input[autocomplete="username"], form input[type="text"]');
    if (id) await id.fill(user);
    await pw.fill(pass);
    const before = await page.evaluate(() => location.pathname).catch(() => '/login');
    await page.evaluate(() => {
      const f = document.querySelector('input[type="password"]')?.closest('form');
      if (f) (f.requestSubmit ? f.requestSubmit() : f.submit());
    }).catch(() => {});
    for (let t = 0; t < 30; t++) {
      await page.waitForTimeout(500);
      const now = await page.evaluate(() => location.pathname).catch(() => before);
      if (now !== before) break;
    }
    const landed = await page.evaluate(() => location.pathname).catch(() => before);
    if (landed === before) { console.error('sweep: auto-login submitted but never left ' + before + ' -- wrong credentials or an unusual form'); return false; }
    fs.mkdirSync(path.dirname(AUTH), { recursive: true });
    await context.storageState({ path: AUTH });
    console.error('  auto-login ok, state saved -> ' + AUTH);
    return true;
  } finally { await page.close(); }
}

// The primary context: the default role's, and the one the journey, mutate and
// leak phases run under after the route loop.
let context = await makeContext(AUTH);

const LOGIN_USER = arg('login-user') ?? process.env.FV_LOGIN_USER;
const LOGIN_PASS = arg('login-pass') ?? process.env.FV_LOGIN_PASS;
if (LOGIN_USER && LOGIN_PASS && !fs.existsSync(AUTH)) await autoLogin(LOGIN_USER, LOGIN_PASS);

const report = { base: BASE, width: WIDTH, started: new Date().toISOString(), routes: [], unreached: [], roles: [], summary: {} };
let currentRole = 'default';
const sevOf = (f) => f.severity ?? 'P2';

// Written after every route, not once at the end: hour three of a long run must
// not be able to take hours one and two with it.
function writeReport() {
  fs.mkdirSync(path.dirname(JSON_OUT), { recursive: true });
  fs.writeFileSync(JSON_OUT, JSON.stringify(report, null, 2));
}

// Destinations already probed. An unauthenticated sweep of a gated app redirects
// every route to /login, and probing each one attributes the login page's contents
// to 50 routes it never reached -- 45 copies of one finding, reading as app-wide.
// Worse, it reports coverage of routes nobody saw. Measure each destination once.
const measured = new Set();

function attachListeners(page) {
  const findings = [];
  const requests = [];
  // Keyed method+path+status, so the same failure seen at BOTH the network layer
  // and in-page is reported once. Without this every network finding doubles on
  // any app where both vantage points can see the traffic.
  const reported = new Set();
  const netKey = (method, pathname, status) => method + ' ' + pathname + ' ' + status;
  const push = (kind, severity, detail, at) => findings.push({ kind, severity, detail, at: at ?? '(page)' });

  page.on('console', (m) => {
    const t = m.text();
    // Warnings are dropped EXCEPT exact engine-authored diagnostics, which are
    // zero-noise by construction. A blanket warning capture would bury the report.
    if (m.type() === 'warning' && /preloaded using link preload but not used/.test(t))
      return push('perf.unused-preload', 'P3', t.slice(0, 200));
    if (m.type() !== 'error') return;
    // The browser logs its own line for every failed request; the network layer
    // already reports that failure, so counting the log line too doubles it.
    if (/Failed to load resource/.test(t)) return;
    // ResizeObserver's loop warning is a real signal (an observer callback that
    // writes layout, re-triggering itself) and belongs in its own class.
    if (/ResizeObserver loop/.test(t)) return push('render.resize-observer-loop', 'P2', t.slice(0, 200));
    if (/ChunkLoadError|Loading chunk \d+ failed/.test(t)) return push('delivery.chunk-load', 'P0', t.slice(0, 200));
    if (/Hydration failed|did not match|Text content does not match|#418|#423|#425/.test(t))
      return push('render.hydration-mismatch', 'P0', t.slice(0, 250));
    if (/Content Security Policy|Refused to (load|execute|connect)|Trusted Types?|TrustedHTML/.test(t))
      return push('security.csp-violation', 'P1', t.slice(0, 200));
    push('console.error', 'P1', t.slice(0, 250));
  });
  page.on('pageerror', (e) => push('console.pageerror', 'P0', String(e).slice(0, 250)));
  page.on('requestfailed', (r) => {
    const u = new URL(r.url());
    const same = u.origin === new URL(BASE).origin;
    push(same ? 'network.requestfailed' : 'network.requestfailed.external', same ? 'P1' : 'P3',
      r.method() + ' ' + u.pathname + ' -- ' + (r.failure()?.errorText ?? 'unknown'));
  });
  page.on('request', (r) => requests.push({ url: r.url(), type: r.resourceType(), start: Date.now(), end: null }));
  const badCookies = new Set();
  page.on('response', async (res) => {
    const rec = requests.find((x) => x.url === res.url() && x.end === null);
    if (rec) rec.end = Date.now();
    const u = new URL(res.url());
    if (u.origin !== new URL(BASE).origin) return;
    if (res.status() >= 400) {
      reported.add(netKey(res.request().method(), u.pathname, res.status()));
      push('network.http-' + res.status(), res.status() >= 500 ? 'P0' : 'P1', res.request().method() + ' ' + u.pathname + ' -> ' + res.status());
    }
    // SameSite=None without Secure is not a style nit: browsers REJECT the
    // cookie, so the guaranteed outcome is auth silently absent. This is a hard
    // browser rule, not a judgment call -- zero noise when it fires.
    try {
      const sc = (await res.allHeaders())['set-cookie'];
      if (!sc) return;
      for (const line of sc.split('\n')) {
        if (!/samesite=none/i.test(line) || /;\s*secure/i.test(line)) continue;
        const name = line.split('=')[0].trim();
        if (badCookies.has(name)) continue;
        badCookies.add(name);
        push('security.cookie-samesite-none-insecure', 'P1',
          'cookie "' + name + '" set with SameSite=None and no Secure on ' + u.pathname + ' -- browsers reject it; whatever it carries is silently absent');
      }
    } catch { /* response gone */ }
  });
  return { findings, requests, reported, netKey, push };
}

// Merge what the page itself saw. On a service-worker app this is the ONLY
// source with anything in it; on a normal app it agrees with Playwright and
// the dedupe keeps findings from doubling.
async function mergeInPage(page, L) {
  let inPage = [];
  try { inPage = await page.evaluate(() => (window.__fv_net ?? []).map((r) => ({ ...r }))); } catch { /* page closed */ }
  const seen = new Set(L.requests.map((r) => r.url));
  for (const r of inPage) {
    let abs = r.url, pathname = r.url;
    try { const u = new URL(r.url, BASE); abs = u.href; pathname = u.pathname; } catch { /* keep raw */ }
    const key = L.netKey(r.method, pathname, r.status);
    if (!L.reported.has(key)) {
      if (r.status >= 400) {
        L.reported.add(key);
        L.push('network.http-' + r.status, r.status >= 500 ? 'P0' : 'P1', r.method + ' ' + pathname + ' -> ' + r.status + ' (seen in-page)');
      } else if (!r.ok && r.status === 0) {
        L.reported.add(key);
        L.push('network.requestfailed', 'P1', r.method + ' ' + pathname + ' -- ' + (r.error ?? 'failed') + ' (seen in-page)');
      }
    }
    if (!seen.has(abs)) L.requests.push({ url: abs, type: 'fetch', start: r.start, end: r.end, inPageOnly: true });
  }
  return inPage;
}

// KNOWN BLIND SPOT -- a mock-API service worker (MSW and hand-rolled
// equivalents) does not intercept until it has CLAIMED the page, so the FIRST
// route of a sweep issues its requests straight to the origin and they 404.
// They surface as network.http-404 P1s on a route that is fine.
//
// Measured on one app (2026-08-29): first load `GET /v1/auth/me -> 404`; second
// load, 20 requests, all 200. Journeys hit it too -- their start route is a
// first navigation for that page.
//
// A warm-up navigation before the route loop was written and REVERTED: it did
// not change the finding count, and an unproven fix in a shared tool is worse
// than a documented gap. Whoever picks this up: verify
// navigator.serviceWorker.controller actually becomes non-null at BASE under
// --auth before assuming the warm-up ran at all -- that is where the first
// attempt failed silently.

const settleAndLand = async (page, route) => {
  // Readiness is NOT networkidle: long polling, websockets and background
  // refetches keep the network busy forever, and a capture taken before the
  // client renders measures nothing at all.
  await page.waitForLoadState('load', { timeout: 15000 }).catch(() => {});
  await page.waitForFunction(
    () => { const r = document.querySelector('#root,#__next,[data-reactroot],main') || document.body; return r && (r.innerText || '').trim().length > 1; },
    { timeout: 8000 },
  ).catch(() => {});
  await page.waitForTimeout(SETTLE_MS);
  let landedPath = route;
  try { landedPath = new URL(page.url()).pathname.replace(/\/$/, '') || '/'; } catch { /* keep */ }
  return landedPath;
};

async function sweepRoute(route, width = WIDTHS[0]) {
  const page = await context.newPage();
  if (width !== WIDTH) await page.setViewportSize({ width, height: HEIGHT }).catch(() => {});
  const L = attachListeners(page);
  const { push } = L;

  let probe = { findings: [], metrics: {} };
  let redirectedTo = null;
  let unreachable = false;
  let surface = null;
  try {
    const resp = await page.goto(BASE + route, { waitUntil: 'domcontentloaded', timeout: NAV_MS });
    if (resp && resp.status() >= 400) push('route.status-' + resp.status(), 'P0', 'route returned HTTP ' + resp.status());
    const landedPath = await settleAndLand(page, route);

    const wanted = route.replace(/\/$/, '') || '/';
    // NOT a finding. A route the sweep never reached is a gap in COVERAGE, and
    // filing it beside real defects is the tool reporting on its own cookie jar
    // in the same list as the app's bugs -- on a real run, 10 of 13 P1s were
    // "landed on /portal/login". Coverage gaps go to report.unreached, get their
    // own line in the summary, and keep PASS from ever meaning "everything was
    // measured". The tool refuses to grade a route it did not reach; it does not
    // pretend the route is broken.
    if (landedPath !== wanted) {
      redirectedTo = landedPath;
      report.unreached.push({ route: wanted, width, landedOn: landedPath, role: currentRole,
        reason: /\b(login|signin|sign-in|auth)\b/.test(landedPath)
          ? 'redirected to auth -- no role in verify.roles.json reached this route'
          : 'redirected' });
    }
    // A not-found shell is not the route's surface either. A sweep that
    // substitutes a synthetic :id which exists in no fixture measures the
    // not-found page under every detail route's name -- same family as a
    // redirect, and just as good at manufacturing a confident wrong number.
    if (!redirectedTo) {
      const notFound = await page.evaluate(() => {
        const t = ((document.body && document.body.innerText) || '').slice(0, 600).toLowerCase();
        return /\b(404|not found|page not found|does(n't| not) exist|no such|couldn't find|could not find)\b/.test(t);
      }).catch(() => false);
      if (notFound) {
        push('route.not-found-shell', 'P1', 'route rendered a not-found surface -- if this path has a dynamic segment, the sweep used an id that exists in no fixture, so nothing below measures the real route');
        redirectedTo = landedPath + ' (not-found)';
      }
    }

    // Probe a destination once PER WIDTH. Everything found on /login belongs to
    // /login -- but a surface measured at 1440 has not been measured at 390.
    if (!measured.has(landedPath + '@' + width)) {
      measured.add(landedPath + '@' + width);
      probe = graded(await probeFn(page));
    } else {
      probe = { findings: [], metrics: {}, skipped: 'destination already measured at this width: ' + landedPath };
    }
    // The surface's own fingerprint, for the integrity gate below. A run in which
    // most cells render the SAME text measured one page under many names -- the
    // shape that filed 45 tap-target findings from two selectors on a login wall,
    // and the shape that produced six byte-identical forced-state columns. No
    // individual finding shows it; only the distribution does.
    surface = await page.evaluate(() => {
      const t = ((document.body && document.body.innerText) || '').replace(/\s+/g, ' ').trim();
      let h = 5381; const head = t.slice(0, 400);
      for (let i = 0; i < head.length; i++) h = ((h * 33) ^ head.charCodeAt(i)) >>> 0;
      return { textLen: t.length, fingerprint: h.toString(36) };
    }).catch(() => null);
  } catch (e) {
    push('route.unreachable', 'P0', String(e).split('\n')[0].slice(0, 200));
    unreachable = true;
  }

  const inPage = await mergeInPage(page, L);

  // A non-2xx the app RENDERS A DESIGNED STATE FOR is not a defect, and the
  // repos that get flagged hardest for it are the ones testing their error paths
  // properly. Measured: a fixture literally named `mock-report-stale-filter`,
  // returning 422 "this saved filter needs updating" to exercise a documented
  // contract, was filed as a P1 on a page that rendered perfectly.
  //
  // The discriminator needs no per-repo config: did the page still satisfy its
  // invariants afterwards? If nothing crashed, nothing stayed blank and nothing
  // stayed spinning, the app handled the response -- that is what "handled"
  // means. 5xx is exempt: a server fault is a defect whoever caught it.
  const HANDLED = /^(render\.empty|render\.stuck-loading|render\.hydration|console\.pageerror|delivery\.chunk-load|value\.leak)/;
  const surfaceBroke = [...L.findings, ...(probe.findings ?? [])].some((f) => HANDLED.test(f.kind));
  if (!surfaceBroke && !redirectedTo && !unreachable) {
    for (const f of L.findings) {
      const code = Number((f.kind.match(/^network\.http-(\d+)$/) ?? [])[1]);
      if (!code || code >= 500) continue;
      f.severity = 'P2';
      f.detail += ' -- the page still rendered and satisfied every invariant afterwards, so the app handled this; P1 only if a surface actually broke';
    }
  }
  // Only for routes actually reached: a redirected route already carries
  // route.not-reached, and 43 copies of "no traffic" on a gated app are 43
  // restatements of that one finding.
  // ...and only for routes the inventory says HAVE data dependencies. Scoped
  // that way the finding stops being "either this route needs none, or the sweep
  // is measuring nothing" and becomes one claim: the import graph found N query
  // hooks reachable from here and not one of them fired.
  if (!redirectedTo && !unreachable && QUERY_JOIN_TRUSTED && (ROUTE_QUERIES.get(route) ?? 0) > 0
      && !L.requests.some((r) => r.type === 'xhr' || r.type === 'fetch') && inPage.length === 0)
    push('verify.no-data-traffic', 'P1', ROUTE_QUERIES.get(route) + ' query hook(s) are reachable from this route and none of them fired -- no request at the network layer or in-page');

  // Request waterfall: B starting right after A finished, repeatedly, is a
  // dependent chain. Every link is a full round trip added to time-to-data, and
  // the page is partially populated at every step of it.
  const api = L.requests.filter((r) => (r.type === 'xhr' || r.type === 'fetch') && r.end);
  api.sort((a, b) => a.start - b.start);
  let chain = 1, worst = 1;
  for (let i = 1; i < api.length; i++) {
    if (api[i].start >= api[i - 1].end - 5 && api[i].start - api[i - 1].end < 400) { chain++; worst = Math.max(worst, chain); }
    else chain = 1;
  }
  if (worst >= 3) push('network.waterfall', 'P2', worst + ' data requests fired in a dependent chain -- each one is a round trip before the page is complete');

  await page.close();
  return {
    record: {
      route, width, redirectedTo, findings: [...L.findings, ...(probe.findings ?? [])], metrics: probe.metrics ?? {},
      apiRequests: api.length,
      // The exact data URLs this route fetched. The forced-state pass replays
      // ONLY these: guessing at "what looks like an API call" breaks RSC payloads
      // and asset loads and then reports the wreckage as app defects.
      apiPaths: [...new Set(api.map((r) => { try { return new URL(r.url, BASE).pathname; } catch { return null; } }).filter(Boolean))],
      ...(surface ?? {}), ...(probe.skipped ? { skipped: probe.skipped } : {}),
    },
    unreachable,
  };
}

// --parallel N sweeps N routes at once in one browser. Big time win on big
// apps; CPU contention can inflate the perf metrics (long tasks, CLS), so
// confirm any perf finding from a parallel run with a serial pass before
// filing it as truth.
const PARALLEL = Math.max(1, Math.min(8, Number(arg('parallel', '1')) || 1));

/* --------------------------------------------------------------- warm-up */

// Two races, both of which manufacture findings about the harness rather than
// the app, and both of which a warm pass closes.
//
// 1. COLD COMPILE. A dev server compiles a route on its first request. Measured:
//    `✓ Compiled /tasks in 30.5s` against a 30000ms goto timeout -- the route
//    lost the race by 500ms and was filed as unreachable. A plain HTTP GET
//    triggers the same compile at a fraction of the cost of a browser navigation.
// 2. SERVICE-WORKER CLAIM. A mock service worker does not intercept until it
//    CONTROLS the page, so the first navigation of a run issues its requests to
//    the real origin and 404s. Measured: first load `GET /v1/auth/me -> 404`;
//    second load, 20 requests, all 200. Every 404 in that run was the harness.
//
// A previous warm-up attempt was reverted for being unproven. So this one
// REPORTS what it achieved -- report.warm and report.serviceWorker -- and the
// service-worker state is one of 'claimed' / 'registered-not-controlling' /
// 'none'. An unproven fix that says so is worth keeping; one that stays silent
// is not, which is the whole disagreement that reverted the last attempt.

async function httpWarm(list) {
  const t0 = Date.now();
  let ok = 0;
  for (const r of list) {
    try {
      const res = await fetch(BASE + r, { signal: AbortSignal.timeout(WARM_MS) });
      await res.arrayBuffer();
      ok++;
    } catch { /* a route that will not warm is measured cold, and says so below */ }
  }
  report.warm = { requested: list.length, compiled: ok, seconds: Math.round((Date.now() - t0) / 1000) };
}

// Drive one real navigation so a service worker can install AND claim. `ready`
// resolves at activation, which is EARLIER than control of the current page --
// that gap is exactly where the previous attempt failed silently, so an
// uncontrolled page is reloaded once (a controlled load is what claims it) and
// the outcome is reported either way.
async function swWarm(ctx) {
  const page = await ctx.newPage();
  try {
    await page.goto(BASE + '/', { waitUntil: 'load', timeout: NAV_MS }).catch(() => {});
    const check = () => page.evaluate(async () => {
      if (!('serviceWorker' in navigator)) return 'none';
      try { await Promise.race([navigator.serviceWorker.ready, new Promise((r) => setTimeout(r, 8000))]); } catch { return 'none' }
      const regs = await navigator.serviceWorker.getRegistrations().catch(() => []);
      if (!regs.length) return 'none';
      return navigator.serviceWorker.controller ? 'claimed' : 'registered-not-controlling';
    }).catch(() => 'unknown');
    let state = await check();
    if (state === 'registered-not-controlling') {
      await page.reload({ waitUntil: 'load', timeout: NAV_MS }).catch(() => {});
      state = await check();
    }
    return state;
  } finally { await page.close(); }
}

/* ----------------------------------------------------------------- resume */

// An hours-long sweep that dies at route 40 should not restart at route 1. Keeps
// every record that was actually measured; drops the ones that were not, so a
// resumed run cannot inherit a gap and report it as covered.
function resumeRecords() {
  if (!flag('resume') || !fs.existsSync(JSON_OUT)) return new Map();
  try {
    const prev = JSON.parse(fs.readFileSync(JSON_OUT, 'utf8'));
    const keep = new Map();
    for (const r of prev.routes ?? []) {
      if (r.route.startsWith('(')) continue;
      if (r.findings?.some((f) => f.kind === 'route.unreachable')) continue;
      keep.set((r.role ?? 'default') + ' ' + r.route + ' @' + (r.width ?? WIDTHS[0]), r);
    }
    return keep;
  } catch { return new Map(); }
}

/* ------------------------------------------------------------- role sweep */

const ROLES = loadRoles();
report.roles = ROLES.map((r) => ({ name: r.name, owns: r.owns, excludes: r.excludes, auth: path.relative(REPO, r.auth), headers: r.headers ? Object.keys(r.headers) : undefined }));
const RESUMED = resumeRecords();

if (!flag('no-warm')) await httpWarm(routes);

let records = [];
let nextIdx = 0;
let roleRoutes = [];
async function sweepWorker() {
  for (;;) {
    const idx = nextIdx++;
    if (idx >= roleRoutes.length) return;
    const { route, width } = roleRoutes[idx];
    // Liveness first: when the dev server has died, every remaining route would
    // report route.unreachable -- 40 copies of one infrastructure failure dressed
    // up as app defects. One retry covers a restart-in-progress.
    if (!(await serverAlive())) {
      report.aborted = 'server unreachable at cell ' + (idx + 1) + '/' + roleRoutes.length + ' (' + route + ' @' + width + 'px, role ' + currentRole + ') -- partial results kept; rerun with --resume to continue from here';
      report.routes = records.concat(roleRecords.filter(Boolean));
      writeReport();
      console.error('sweep: ' + report.aborted);
      process.exit(2);
    }
    let { record, unreachable } = await sweepRoute(route, width);
    // One retry for a route that timed out or dropped: a transient hiccup that
    // passes on retry is FLAKY, which is a fact worth keeping, not a pass.
    if (unreachable) {
      const again = await sweepRoute(route, width);
      if (!again.unreachable) {
        record = again.record;
        record.flaky = true;
        record.findings.push({ kind: 'route.flaky', severity: 'P2', at: '(page)', detail: 'first visit failed, retry succeeded -- intermittent' });
      }
    }
    record.role = currentRole;
    roleRecords[idx] = record;
    report.routes = records.concat(roleRecords.filter(Boolean));   // inventory order, however workers finish
    writeReport();
  }
}

let roleRecords = [];
for (const role of ROLES) {
  currentRole = role.name;
  // The matrix: every route this role owns, at every width. One cell each.
  const owned = routes.filter((r) => roleOwns(role, r)).flatMap((r) => WIDTHS.map((w) => ({ route: r, width: w })));
  const key = (c) => role.name + ' ' + c.route + ' @' + c.width;
  const already = owned.filter((c) => RESUMED.has(key(c)));
  roleRoutes = owned.filter((c) => !RESUMED.has(key(c)));
  records.push(...already.map((c) => RESUMED.get(key(c))));
  if (!owned.length) {
    console.error('sweep: role "' + role.name + '" owns no routes -- check `owns` in verify.roles.json');
    continue;
  }
  if (!roleRoutes.length) continue;

  // Reuse the primary context for the default/first role so the auto-login
  // state captured above is not thrown away.
  const roleCtx = role.auth === AUTH && !role.headers ? context : await makeContext(role.auth, role.headers);
  const prevCtx = context;
  context = roleCtx;
  // Same path under two principals renders two different pages, so the
  // measured-once dedup is per role. Sharing it across roles would silently
  // skip the portal's version of a path the staff lens already visited.
  measured.clear();
  const sw = await swWarm(roleCtx);
  (report.serviceWorker ??= {})[role.name] = sw;

  roleRecords = new Array(roleRoutes.length);
  nextIdx = 0;
  await Promise.all(Array.from({ length: Math.min(PARALLEL, roleRoutes.length) }, sweepWorker));
  records.push(...roleRecords.filter(Boolean));
  roleRecords = [];
  report.routes = records;
  writeReport();

  context = prevCtx;
  if (roleCtx !== prevCtx) await roleCtx.close();
}
currentRole = 'default';
report.routes = records;

/* -------------------------------------------------- app-owned journeys */

// A universal journey generator is brittle over-engineering; the app's own
// critical flows are the app's to script. What the skill supplies is the harness:
// each journey runs under the full console/network listeners, and wherever it
// ends up gets the whole probe. Interaction coverage without inventing intent.
const journeyFiles = [path.join(REPO, 'verify.journeys.mjs'), path.join(REPO, '.verify', 'journeys.mjs')];
const journeyFile = journeyFiles.find((f) => fs.existsSync(f));
if (journeyFile && !flag('no-journeys')) {
  let journeys = [];
  try {
    const mod = await import(pathToFileURL(journeyFile).href);
    journeys = mod.default ?? mod.journeys ?? [];
  } catch (e) {
    report.routes.push({ route: '(journeys)', metrics: {}, findings: [{ kind: 'journey.load-failed', severity: 'P1', at: journeyFile, detail: String(e).split('\n')[0].slice(0, 200) }] });
  }
  for (const j of journeys) {
    const page = await context.newPage();
    const L = attachListeners(page);
    let probe = { findings: [], metrics: {} };
    try {
      await page.goto(BASE + (j.start ?? '/'), { waitUntil: 'domcontentloaded', timeout: NAV_MS });
      await settleAndLand(page, j.start ?? '/');
      await j.run(page, { base: BASE, settle: () => page.waitForTimeout(SETTLE_MS) });
      await page.waitForTimeout(SETTLE_MS);
      probe = graded(await probeFn(page));
    } catch (e) {
      L.push('journey.failed', 'P0', (j.name ?? 'journey') + ': ' + String(e).split('\n')[0].slice(0, 200));
    }
    await mergeInPage(page, L);
    report.routes.push({ route: '(journey: ' + (j.name ?? 'unnamed') + ')', findings: [...L.findings, ...probe.findings], metrics: probe.metrics });
    writeReport();
    await page.close();
  }
}

/* ------------------------------------------------ forced states (opt-in) */

// The branches nothing in normal development ever renders. A mock layer always
// serves a populated happy path, so empty / 500 / 403 / malformed / slow are
// written once and then never executed again by anyone -- which is why they rot,
// and why this is the highest-yield pass that no DOM invariant on a happy page
// can reach.
//
// Three measured facts shape the whole implementation:
//
// 1. `page.route()` DOES NOT WORK against an app with a mock service worker.
//    Measured: `page.on('request')` saw 10 /v1/* calls on a route where
//    `page.route("**/v1/**")` saw ZERO -- the worker answers inside the page, so
//    nothing reaches Playwright's network layer. Unregistering it does not help
//    either; the app re-registers on mount. Patching window.fetch/XHR in an init
//    script runs BEFORE the app's JS and therefore before the worker sees
//    anything, which is the only vantage point that works for both.
// 2. NEVER force an auth endpoint. Breaking auth logs the session out and every
//    later cell measures a login page while reporting clean.
// 3. Force only the URLs the baseline sweep OBSERVED this route fetching.
//    Pattern-matching "things that look like an API" breaks RSC payloads and
//    asset loads, and the page then reports the wreckage as its own defect.
//
// The finding is read from the RENDERED TEXT, never from the response: a 500 that
// paints a blank screen and a 500 that says "something went wrong" are the same
// HTTP status and opposite products.
const STATE_KINDS = {
  empty:     { status: 200, body: '[]' },
  error:     { status: 500, body: '{"error":"internal"}' },
  forbidden: { status: 403, body: '{"error":"forbidden"}' },
  malformed: { status: 200, body: '{"unexpected":true}' },
  slow:      { status: 200, body: null, delayMs: 6000 },
};
// `--states` alone runs all five; `--states empty,error` picks. The next argv
// entry is only a value if it is not itself a flag.
const STATES = (() => {
  if (!flag('states')) return [];
  const v = arg('states');
  const list = !v || v.startsWith('--') ? Object.keys(STATE_KINDS) : v.split(',').map((s) => s.trim());
  return list.filter((s) => STATE_KINDS[s]);
})();

if (STATES.length) {
  // Anything under an auth/session path stays untouched (fact 2 above), as does
  // anything the app needs to boot.
  const AUTH_PATH = /(^|\/)(auth|login|logout|session|sessions|signin|sign-in|token|refresh|csrf|me)(\/|$|\?)/i;
  const baseline = report.routes.filter((r) => !r.route.startsWith('(') && !r.redirectedTo
    && (r.apiPaths ?? []).some((p) => !AUTH_PATH.test(p)));
  const seenRoute = new Set();
  const cells = [];
  for (const r of baseline) {
    if (seenRoute.has(r.route)) continue;          // one width is enough for a state test
    seenRoute.add(r.route);
    cells.push(r);
  }
  report.states = { routes: cells.length, kinds: STATES, cells: cells.length * STATES.length };

  for (const cell of cells) {
    const targets = (cell.apiPaths ?? []).filter((p) => !AUTH_PATH.test(p));
    const columns = [];
    for (const kind of STATES) {
      const spec = STATE_KINDS[kind];
      const page = await context.newPage();
      await page.addInitScript(({ targets, spec }) => {
        const hit = (u) => { try { return targets.includes(new URL(u, location.origin).pathname); } catch { return false; } };
        const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
        const of = () => new Response(spec.body, { status: spec.status, headers: { 'content-type': 'application/json' } });
        const origFetch = window.fetch.bind(window);
        window.fetch = async (input, init) => {
          const url = typeof input === 'string' ? input : (input && input.url) || '';
          if (!hit(url)) return origFetch(input, init);
          if (spec.delayMs) { await sleep(spec.delayMs); return origFetch(input, init); }
          return of();
        };
        // XHR too: generated clients and older libraries still use it, and a state
        // pass that only patches fetch silently measures the happy path for them.
        const XO = XMLHttpRequest.prototype.open, XS = XMLHttpRequest.prototype.send;
        XMLHttpRequest.prototype.open = function (m, u, ...rest) { this.__fv_forced = hit(u); return XO.call(this, m, u, ...rest); };
        XMLHttpRequest.prototype.send = function (...a) {
          if (!this.__fv_forced || spec.delayMs) return XS.apply(this, a);
          Object.defineProperty(this, 'status', { get: () => spec.status });
          Object.defineProperty(this, 'responseText', { get: () => spec.body ?? '' });
          Object.defineProperty(this, 'response', { get: () => spec.body ?? '' });
          Object.defineProperty(this, 'readyState', { get: () => 4 });
          setTimeout(() => { this.onreadystatechange?.(); this.onload?.(); this.dispatchEvent(new Event('load')); }, 0);
        };
      }, { targets, spec });

      let read = null;
      try {
        await page.goto(BASE + cell.route, { waitUntil: 'domcontentloaded', timeout: NAV_MS });
        await settleAndLand(page, cell.route);
        if (spec.delayMs) await page.waitForTimeout(1500);   // measure DURING the wait, not after
        read = await page.evaluate(() => {
          const t = ((document.body && document.body.innerText) || '').replace(/\s+/g, ' ').trim();
          const low = t.toLowerCase();
          let h = 5381; for (let i = 0; i < Math.min(t.length, 400); i++) h = ((h * 33) ^ t.charCodeAt(i)) >>> 0;
          return {
            textLen: t.length, fingerprint: h.toString(36),
            saysError: /\b(error|went wrong|failed|unable to|try again|couldn.t load|problem)\b/.test(low),
            saysEmpty: /\b(no |none|empty|nothing|0 results|not found yet|get started|add your first)\b/.test(low),
            saysDenied: /\b(denied|forbidden|not authoriz|no access|permission)\b/.test(low),
            hasSpinner: !!document.querySelector('[role=progressbar],[aria-busy=true],.animate-spin,[data-loading=true],[class*=skeleton i]'),
            leaksRaw: /\{"(error|unexpected)"|\bTypeError\b|\bundefined is not\b|at [A-Za-z]+ \(http/.test(t),
          };
        });
      } catch (e) {
        read = { crashed: String(e).split('\n')[0].slice(0, 160) };
      }
      columns.push({ kind, ...read });
      await page.close();
    }

    // Judge the columns together, because the interesting failures are relational.
    const findings = [];
    const ok = columns.filter((c) => !c.crashed);
    for (const c of ok) {
      if (c.kind === 'slow') {
        if (!c.hasSpinner && c.textLen < 40)
          findings.push({ kind: 'state.slow-blank', severity: 'P1', at: c.kind, detail: 'while its data was in flight this route rendered neither content nor a loading indicator -- a blank screen is what a slow network looks like to the user' });
        continue;
      }
      if (c.textLen < 40)
        findings.push({ kind: 'state.blank', severity: 'P1', at: c.kind, detail: 'forcing ' + c.kind + ' left the page blank (' + c.textLen + ' chars of text) -- a broken API renders nothing at all, with no way for the user to tell what happened' });
      else if (c.hasSpinner && (c.kind === 'error' || c.kind === 'forbidden'))
        findings.push({ kind: 'state.stuck-spinner', severity: 'P1', at: c.kind, detail: 'a loading indicator is still mounted after the request failed with ' + STATE_KINDS[c.kind].status + ' -- the page spins forever instead of reporting the failure' });
      else if ((c.kind === 'error' || c.kind === 'malformed') && !c.saysError)
        findings.push({ kind: 'state.silent-failure', severity: 'P1', at: c.kind, detail: 'the request failed and the surface says nothing about it -- it renders as though the data arrived, which is how a user acts on values that are not there' });
      else if (c.kind === 'forbidden' && !c.saysDenied && !c.saysError)
        findings.push({ kind: 'state.silent-failure', severity: 'P1', at: c.kind, detail: '403 rendered with no denial or error message -- the user cannot tell an empty result from one they are not allowed to see' });
      else if (c.kind === 'empty' && !c.saysEmpty)
        findings.push({ kind: 'state.no-empty-state', severity: 'P2', at: c.kind, detail: 'an empty response renders no empty state -- an empty list and a failed fetch look identical to the user' });
      if (c.leaksRaw)
        findings.push({ kind: 'state.leaks-raw', severity: 'P2', at: c.kind, detail: 'raw payload or stack text is visible in the DOM under ' + c.kind });
    }
    // THE integrity tell, and the reason this pass reports columns rather than a
    // verdict: identical output across deliberately different inputs means the
    // experiment never ran. Measured in the wild as six byte-identical columns --
    // the interception was defeated by a service worker and every "PASS" in that
    // table was about nothing.
    const prints = new Set(ok.map((c) => c.fingerprint));
    if (ok.length >= 3 && prints.size === 1) {
      findings.length = 0;
      findings.push({ kind: 'state.not-intercepted', severity: 'P2', at: 'all', detail: STATES.length + ' deliberately different responses produced byte-identical pages -- the forced state never reached the app, so nothing here was measured. Findings for this route are withheld rather than reported as clean.' });
    }
    report.routes.push({ route: '(states: ' + cell.route + ')', metrics: {}, findings, columns });
    writeReport();
  }
}

/* ------------------------------------------- mutation replay (opt-in, writes!) */

// The runtime half of the syncRisks finding. Static analysis says "this write
// invalidates nothing, these routes render it"; this proves it in a real browser:
// fill the form, submit, client-side navigate to a blast-radius route, and check
// whether ANY refetch of the written resource happened or the new value shows.
// Direct API calls cannot test this -- the app's cache only invalidates inside
// its own mutation callbacks, so the write must go through the app's own UI.
if (flag('mutate') && fs.existsSync(INVENTORY)) {
  const inv = JSON.parse(fs.readFileSync(INVENTORY, 'utf8'));
  const risks = (inv.syncRisks ?? []).filter((r) => r.endpoint && r.route && (r.staleRoutes ?? []).length && !/[:[]/.test(r.route));
  const lastSeg = (ep) => ep.split('?')[0].split('/').filter((s) => s && !/^(api|v\d+)$/.test(s)).pop() ?? '';
  for (const risk of risks) {
    const page = await context.newPage();
    // No invariant listeners here on purpose: a form filled with sentinel data
    // legitimately provokes validation errors, and reporting the app's reaction
    // to synthetic input as findings would be noise. This phase reports only
    // what it exists to prove: staleness after a successful write.
    const sentinel = 'fv-probe-' + Date.now();
    const findings = [];
    try {
      await page.goto(BASE + risk.route, { waitUntil: 'domcontentloaded', timeout: NAV_MS });
      await settleAndLand(page, risk.route);
      const hasForm = await page.evaluate(() => !!document.querySelector('form input, form textarea'));
      if (!hasForm) { report.routes.push({ route: '(mutate: ' + risk.route + ')', metrics: {}, findings: [], skipped: 'no form on the mutation route -- cover this risk with a journey' }); await page.close(); continue; }

      for (const h of await page.$$('form input:not([type=hidden]):not([type=checkbox]):not([type=radio]):not([type=submit]):not([type=file]), form textarea')) {
        const type = ((await h.getAttribute('type')) ?? 'text').toLowerCase();
        const value = type === 'email' ? sentinel + '@example.com'
          : type === 'number' ? '2'
          : type === 'url' ? 'https://example.com/' + sentinel
          : type === 'date' ? '2026-01-02'
          : type === 'password' ? sentinel
          : sentinel;
        await h.fill(value).catch(() => {});
      }
      const tMark = await page.evaluate(() => performance.now());
      await page.evaluate(() => { const f = document.querySelector('form'); if (f.requestSubmit) f.requestSubmit(); else f.submit(); });

      // Wait for the write to show up in the in-page log.
      let write = null;
      for (let t = 0; t < 25 && !write; t++) {
        await page.waitForTimeout(200);
        write = await page.evaluate((mark) =>
          (window.__fv_net ?? []).find((r) => ['POST', 'PUT', 'PATCH', 'DELETE'].includes(r.method) && r.start > mark) ?? null, tMark);
      }
      if (!write) {
        report.routes.push({ route: '(mutate: ' + risk.route + ')', metrics: {}, findings: [], skipped: 'submit produced no write (validation? different trigger?) -- cover this risk with a journey' });
        await page.close(); continue;
      }
      if (write.status >= 400) {
        findings.push({ kind: 'mutate.write-rejected', severity: 'P2', at: risk.route, detail: write.method + ' ' + write.url + ' -> ' + write.status + ' from a generically filled form -- not proof of a defect, but the risk stays unverified' });
      } else {
        const seg = lastSeg(risk.endpoint);
        // Whether the app RENDERED the written value at all, captured now, before
        // anything navigates. It is the precondition for the persistence check
        // below: if the value never appeared, its absence after a reload says
        // nothing, and a P0 nobody can reproduce costs more than the bug it was
        // guessing at.
        const renderedTheWrite = await page.evaluate((s) => ((document.body && document.body.innerText) || '').includes(s), sentinel);

        for (const staleRoute of risk.staleRoutes.filter((p) => !/[:[]/.test(p)).slice(0, 4)) {
          // Client-side navigation only: a full page load rebuilds every cache
          // and proves nothing about invalidation.
          const link = await page.$('a[href="' + staleRoute + '"], a[href="' + staleRoute + '/"]');
          if (!link) continue;
          await link.click().catch(() => {});
          await page.waitForTimeout(SETTLE_MS);
          const { refetched, sentinelSeen } = await page.evaluate(({ after, seg, sentinel }) => ({
            refetched: (window.__fv_net ?? []).some((r) => r.method === 'GET' && r.end > after && r.url.includes(seg)),
            sentinelSeen: ((document.body && document.body.innerText) || '').includes(sentinel),
          }), { after: write.end, seg, sentinel });
          if (!refetched && !sentinelSeen) {
            findings.push({ kind: 'sync.stale-after-write', severity: 'P0', at: staleRoute,
              detail: write.method + ' ' + risk.endpoint + ' succeeded on ' + risk.route + ', then client-side navigation to ' + staleRoute
                + ' refetched nothing and does not show the new value -- the cross-page cache is stale (static finding ' + (risk.hook ?? risk.mutation) + ' confirmed at runtime)' });
          }
        }

        // DID THE WRITE SURVIVE A RELOAD? Asked LAST, because a reload rebuilds
        // every cache and would destroy the staleness measurement above -- but
        // asked, because a 2xx is not persistence. Measured on a real repo: the
        // mock service worker's final branch is
        // `if (POST||PUT||PATCH||DELETE) return ok({ok:true})`, so every write it
        // does not explicitly route reports success and silently discards the
        // data. The request succeeded, the cache updated optimistically, the UI
        // showed the new value, and it was gone. Neither typecheck, lint, unit
        // tests, nor any DOM invariant on a happy page can see that -- only
        // reading the value back through a full reload can, because the app's own
        // cache is precisely the thing that must not be trusted here.
        if (renderedTheWrite) {
          await page.goto(BASE + risk.route, { waitUntil: 'domcontentloaded', timeout: NAV_MS }).catch(() => {});
          await settleAndLand(page, risk.route);
          await page.reload({ waitUntil: 'domcontentloaded', timeout: NAV_MS }).catch(() => {});
          await settleAndLand(page, risk.route);
          const survived = await page.evaluate((s) => ((document.body && document.body.innerText) || '').includes(s), sentinel);
          if (!survived) {
            findings.push({ kind: 'mutate.write-lost', severity: 'P0', at: risk.route,
              detail: write.method + ' ' + risk.endpoint + ' returned ' + write.status + ' and the new value rendered, but after a full reload it is gone -- the write was accepted and never stored. A 2xx is not persistence.' });
          }
        }
      }
    } catch (e) {
      findings.push({ kind: 'mutate.failed', severity: 'P2', at: risk.route, detail: String(e).split('\n')[0].slice(0, 200) });
    }
    report.routes.push({ route: '(mutate: ' + risk.route + ')', metrics: {}, findings });
    writeReport();
    await page.close();
  }
}

/* ----------------------------------------------------- leak check (opt-in) */

if (flag('leak-check') && routes.length >= 2) {
  const page = await context.newPage();
  const cdp = await context.newCDPSession(page);
  const heap = async () => {
    await cdp.send('HeapProfiler.collectGarbage');
    const { usedSize } = await cdp.send('Runtime.getHeapUsage');
    return usedSize;
  };
  await page.goto(BASE + routes[0], { waitUntil: 'load' }).catch(() => {});
  const before = await heap();
  for (let i = 0; i < 5; i++) {
    for (const r of routes.slice(0, 4)) await page.goto(BASE + r, { waitUntil: 'load' }).catch(() => {});
  }
  await page.goto(BASE + routes[0], { waitUntil: 'load' }).catch(() => {});
  const after = await heap();
  const growthMB = Math.round(((after - before) / 1048576) * 10) / 10;
  report.leak = { beforeMB: Math.round(before / 1048576), afterMB: Math.round(after / 1048576), growthMB };
  // Heap that does not come back after GC across repeated navigation is retained
  // by something the unmount did not release: a listener, a timer, a subscription.
  if (growthMB > 8) {
    report.routes.push({
      route: '(navigation loop)', metrics: {},
      findings: [{ kind: 'perf.memory-leak', severity: 'P1', at: '(page)',
        detail: growthMB + 'MB retained after GC across 20 navigations -- detached nodes or un-removed listeners' }],
    });
  }
  await page.close();
}

await browser.close();

/* ---------------------------------------------------------------- report */

const all = report.routes.flatMap((r) => r.findings.map((f) => ({ ...f, route: r.route })));
const bySev = all.reduce((a, f) => ((a[sevOf(f)] = (a[sevOf(f)] ?? 0) + 1), a), {});
const byKind = all.reduce((a, f) => ((a[f.kind] = (a[f.kind] ?? 0) + 1), a), {});
const reached = report.routes.filter((r) => !r.redirectedTo && !r.route.startsWith('(')).length;
const swept = report.routes.filter((r) => !r.route.startsWith('(')).length;
// Every summary field is set BEFORE the final serialize; fields added after a
// write exist only in this process's memory and never reach the report.
// Coverage is reported beside the findings, never inside them. A run that
// measured 41 of 51 routes and found nothing is not the same claim as a run that
// measured 51 of 51 and found nothing, and only one of those is "clean".
const ownedByNoRole = routes.filter((r) => !ROLES.some((role) => roleOwns(role, r)));
report.summary = {
  routes: report.routes.length, routesRequested: swept, routesReached: reached,
  routesUnreached: report.unreached.length, routesUnowned: ownedByNoRole.length,
  roles: ROLES.map((r) => r.name),
  findings: all.length, ...bySev,
};
if (ownedByNoRole.length) report.unowned = ownedByNoRole;

/* ------------------------------------------------------- integrity gate */

// A probe over lock screens reports CLEAN. That is the failure this whole tool
// exists to prevent, and no individual finding shows it -- only the shape of the
// run does. So the run grades ITSELF before its findings are allowed to mean
// anything, and a run that fails here exits 2 (could not run), never 0.
//
// Measured, all three of these happened on real runs:
//   - 45 tap-target findings across 45 routes, from two selectors, because the
//     sweep ran unauthenticated and measured /login 45 times under 45 names.
//   - a whole matrix of "PASS" over pages that had never rendered.
//   - six byte-identical columns from an interception that never fired.
const cells = report.routes.filter((r) => !r.route.startsWith('('));
const measuredCells = cells.filter((r) => !r.redirectedTo && !r.skipped && r.textLen != null);
const TEXT_FLOOR = Number(arg('text-floor', '40'));
const bounced = report.unreached.filter((u) => /\b(login|signin|sign-in|auth)\b/.test(u.landedOn)).length;
const belowFloor = measuredCells.filter((r) => r.textLen < TEXT_FLOOR).length;
const prints = new Set(measuredCells.map((r) => r.fingerprint));
// Distinct surfaces per measured cell. One page measured under many names is the
// classic artifact; a real app's routes do not share their first 400 characters.
// Deliberately loose (a third) and floored at 6 cells, because the cost of a
// false INVALID is a blocked run and the cost of a miss is one noisy report.
const distinctRatio = measuredCells.length ? prints.size / measuredCells.length : 1;
const sameSurface = measuredCells.length >= 6 && distinctRatio < 0.34;
// Proportional, not absolute. The source rule was "bounced == 0", written for a
// run that held an auth state for all ten principals -- but two gated routes out
// of fifty is a coverage note, and hard-failing on it blocks the fix loop, which
// is the exact budget burn this skill keeps trying to stop. A quarter of the run
// landing on the auth wall is a different animal: at that point "no findings"
// is a claim about the login page. Both numbers are always printed either way.
const SHARE = Number(arg('integrity-share', '0.25'));
// Every check below is about a DISTRIBUTION, and a distribution needs a sample.
// Under six cells these are spot checks (`--routes /a,/b`), where one blank page
// is a finding to read, not grounds to void the run.
const SAMPLE = 6;
const mostlyBounced = cells.length >= SAMPLE && bounced > cells.length * SHARE;
const mostlyBlank = measuredCells.length >= SAMPLE && belowFloor > measuredCells.length * SHARE;
report.integrity = {
  cellsPlanned: cells.length, cellsMeasured: measuredCells.length,
  bouncedToLogin: bounced, cellsBelowTextFloor: belowFloor,
  distinctSurfaces: prints.size, distinctRatio: Number(distinctRatio.toFixed(2)),
  aborted: !!report.aborted, share: SHARE,
  ok: !report.aborted && measuredCells.length > 0 && !mostlyBounced && !mostlyBlank && !sameSurface,
  failed: [
    report.aborted ? 'run aborted before every cell was swept' : null,
    measuredCells.length === 0 ? 'zero cells were measured' : null,
    mostlyBounced ? bounced + ' of ' + cells.length + ' cells bounced to a login page -- this run graded the auth wall, not the app' : null,
    mostlyBlank ? belowFloor + ' of ' + measuredCells.length + ' measured cells rendered under ' + TEXT_FLOOR + ' characters of text -- the app was not up, or never rendered' : null,
    sameSurface ? measuredCells.length + ' cells rendered only ' + prints.size + ' distinct surfaces -- one page measured under many names' : null,
  ].filter(Boolean),
};

report.finished = new Date().toISOString();
writeReport();

console.log('\n  ' + BASE + '  ' + swept + ' routes at ' + WIDTH + 'px'
  + (ROLES.length > 1 ? '  as ' + ROLES.map((r) => r.name).join(', ') : ''));
if (report.warm) console.log('  warm-up: ' + report.warm.compiled + '/' + report.warm.requested + ' routes precompiled in ' + report.warm.seconds + 's');
if (report.serviceWorker) console.log('  service worker: ' + Object.entries(report.serviceWorker).map(([r, s]) => r + '=' + s).join(', '));
// Coverage first and separately: these are not defects, they are the routes this
// run declines to grade, and mixing them into the finding list is how a report
// spends 10 of its 13 P1s describing the caller's cookie jar.
if (report.unreached.length) {
  console.log('\n  NOT MEASURED  ' + report.unreached.length + ' of ' + swept + ' routes -- redirected, so nothing below covers them:');
  for (const u of report.unreached.slice(0, 8)) console.log('    ' + u.route + '  -> ' + u.landedOn + '  (as ' + u.role + ')');
  if (report.unreached.length > 8) console.log('    ... and ' + (report.unreached.length - 8) + ' more in ' + JSON_OUT);
  console.log('    Give each one an owning role in verify.roles.json, or accept them as out of scope.');
}
if (ownedByNoRole.length)
  console.log('\n  UNOWNED  ' + ownedByNoRole.length + ' route(s) match no role in verify.roles.json and were never visited: ' + ownedByNoRole.slice(0, 6).join(', '));
console.log('\n  ' + all.length + ' findings  ' + Object.entries(bySev).map(([k, v]) => k + ':' + v).join('  ') + '\n');
for (const [kind, n] of Object.entries(byKind).sort((a, b) => b[1] - a[1])) {
  const first = all.find((f) => f.kind === kind);
  console.log('  ' + String(n).padStart(4) + '  ' + sevOf(first) + '  ' + kind);
  for (const f of all.filter((x) => x.kind === kind).slice(0, 3))
    console.log('        ' + f.route + '  ' + f.detail.slice(0, 130));
  if (n > 3) console.log('        ... and ' + (n - 3) + ' more');
}
console.log('  -> ' + JSON_OUT);
if (report.leak) console.log('\n  heap after GC across navigation: ' + report.leak.beforeMB + 'MB -> ' + report.leak.afterMB + 'MB (+' + report.leak.growthMB + 'MB)');

const g = report.integrity;
console.log('\n  integrity  ' + g.cellsMeasured + '/' + g.cellsPlanned + ' cells measured  ·  '
  + g.bouncedToLogin + ' bounced to login  ·  ' + g.cellsBelowTextFloor + ' below the text floor  ·  '
  + g.distinctSurfaces + ' distinct surfaces');
if (!g.ok) {
  console.error('\n  INVALID  this run did not measure the app:');
  for (const f of g.failed) console.error('    - ' + f);
  console.error('  Do not merge it, do not average it, and do not read "no findings" from it.\n');
  process.exit(2);
}
console.log('');

process.exit((bySev.P0 ?? 0) + (bySev.P1 ?? 0) > 0 ? 1 : 0);
