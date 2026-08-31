#!/usr/bin/env node
// Feature inventory + sync graph. Static. No dependencies, no build step.
//
//   node inventory.mjs <repoRoot>            -> writes <repoRoot>/.verify/inventory.json
//   node inventory.mjs <repoRoot> --stdout   -> writes to stdout instead
//
// Output lands next to the REPO BEING ANALYSED, never in the current working
// directory. The skill is installed once and run against many repos; a relative
// output path silently drops one repo's report into whatever directory the
// shell happened to be in.
//
// Answers, without running anything:
//   - what routes exist                      (filesystem / router config)
//   - what data each route transitively reads (import graph -> query hooks)
//   - what mutations exist and what they write
//   - WHICH ROUTES GO STALE WHEN A MUTATION RUNS  <- the cross-page sync bug,
//     found before a browser is ever opened
//
// ponytail: regex + import-graph, not a TS AST. Misses computed query keys and
// re-exported hooks. Upgrade path: swap extract() for ts.createSourceFile if the
// false-negative rate ever justifies the typescript dependency. It has not yet.

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const ARGS = process.argv.slice(2).filter((a) => !a.startsWith('--'));
const ROOT = path.resolve(ARGS[0] ?? '.');
const TO_STDOUT = process.argv.includes('--stdout');
const SRC_EXT = new Set(['.ts', '.tsx', '.js', '.jsx', '.mts', '.mjs']);
const SKIP_DIR = /(^|\/)(node_modules|\.next|\.git|dist|build|out|coverage|\.turbo|\.vercel|venv|site-packages|vendor|storybook-static)(\/|$)|(^|\/)\.[^/]+\/|worktrees\/|\.(test|spec|stories)\.[tj]sx?$/;
const MAX_IMPORT_DEPTH = 12;

/* ------------------------------------------------------------------ files */

function walk(dir, acc = []) {
  let ents;
  try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch { return acc; }
  for (const e of ents) {
    const p = path.join(dir, e.name);
    if (SKIP_DIR.test(p)) continue;
    if (e.isDirectory()) walk(p, acc);
    else if (SRC_EXT.has(path.extname(e.name))) acc.push(p);
  }
  return acc;
}


// Enumerate through git when the root is a repo. This is the only enumeration
// that respects .gitignore for free, and gitignored trees are where the noise
// lives: agent worktrees under .claude/, prototype scratch dirs, vendored
// builds. Each such tree is a near-copy of the app, so every finding in it is a
// duplicate -- one real repo reported 357 findings of which 335 came from copies
// of itself. A 94% noise rate is indistinguishable from a broken tool.
function gitFiles(root) {
  const r = spawnSync('git', ['-C', root, 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
    { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
  if (r.status !== 0 || !r.stdout) return null;
  return r.stdout.split('\0').filter(Boolean).map((f) => path.join(root, f));
}

// Same design-lab exclusion and same <repo>/.verifyignore as classify.mjs -- an
// ignore file that applies to only one phase is a trap, because the route list
// and the findings would then disagree about what the app is.
const LAB = /(^|\/)(_proto|proto|design-lab|playground|sandbox|scratch)(\/|$)/;
function ignoreMatcher(root) {
  let lines = [];
  try {
    lines = fs.readFileSync(path.join(root, '.verifyignore'), 'utf8')
      .split('\n').map((l) => l.replace(/#.*/, '').trim()).filter(Boolean);
  } catch { /* no ignore file, defaults only */ }
  const res = lines.map((l) => new RegExp(
    l.replace(/[.+^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '[^\\0]*').replace(/\?/g, '.')));
  return (relPath) => LAB.test(relPath) || res.some((r) => r.test(relPath));
}
const ignored = ignoreMatcher(ROOT);

const FILES = (gitFiles(ROOT) ?? walk(ROOT))
  .filter((f) => SRC_EXT.has(path.extname(f)) && !SKIP_DIR.test(f) && !ignored(path.relative(ROOT, f)));
const read = (f) => { try { return fs.readFileSync(f, 'utf8'); } catch { return ''; } };
const SOURCE = new Map(FILES.map((f) => [f, read(f)]));
const rel = (f) => path.relative(ROOT, f);

/* ----------------------------------------------------------------- routes */

// Next app router: app/**/page.tsx -> /a/[id]/b  (groups and parallel segments dropped)
function nextAppRoutes() {
  return FILES.filter((f) => /(^|\/)app\/.*\/page\.(t|j)sx?$/.test(f) || /(^|\/)app\/page\.(t|j)sx?$/.test(f))
    .map((f) => {
      const after = rel(f).replace(/^.*?(^|\/)app\//, '');
      const url = '/' + after
        .replace(/\/page\.(t|j)sx?$/, '')
        .split('/')
        .filter((s) => s && !/^\(.*\)$/.test(s) && !s.startsWith('@'))
        .join('/');
      return { path: url === '/' ? '/' : url.replace(/\/$/, ''), file: rel(f), kind: 'next-app' };
    });
}

// Next pages router: pages/**/*.tsx, minus _app/_document/api
function nextPagesRoutes() {
  return FILES.filter((f) => /(^|\/)pages\/.*\.(t|j)sx?$/.test(f) && !/\/(_app|_document|_error)\./.test(f) && !/(^|\/)pages\/api\//.test(f))
    .map((f) => {
      const after = rel(f).replace(/^.*?(^|\/)pages\//, '');
      let url = '/' + after.replace(/\.(t|j)sx?$/, '').replace(/\/index$/, '').replace(/^index$/, '');
      return { path: url === '/' ? '/' : url.replace(/\/$/, ''), file: rel(f), kind: 'next-pages' };
    });
}

// react-router / tanstack-router: <Route path="x" element={<Y/>}/> and { path: 'x', element: <Y/> }
function configRoutes() {
  const out = [];
  for (const [f, src] of SOURCE) {
    for (const m of src.matchAll(/<Route\s+[^>]*path=["'`]([^"'`]+)["'`][^>]*?(?:element=\{\s*<([A-Z][\w]*)|component=\{\s*([A-Z][\w]*))/gs)) {
      out.push({ path: m[1].startsWith('/') ? m[1] : '/' + m[1], file: rel(f), component: m[2] ?? m[3], kind: 'react-router' });
    }
    for (const m of src.matchAll(/\{\s*path:\s*["'`]([^"'`]+)["'`][\s\S]{0,220}?(?:element:\s*<([A-Z][\w]*)|component:\s*([A-Z][\w]*)|lazy)/g)) {
      out.push({ path: m[1].startsWith('/') ? m[1] : '/' + m[1], file: rel(f), component: m[2] ?? m[3], kind: 'route-config' });
    }
  }
  return out;
}

// TanStack Router (and any src/routes file convention): src/routes/**/*.tsx.
// A repo on this router reports ZERO routes without it, which makes the whole
// inventory silently empty rather than wrong — the worst failure shape.
//   _auth/       pathless layout segment, contributes nothing to the URL
//   $id          dynamic param
//   route.tsx    the segment's layout, not a page
//   -components/ the leading dash means "not a route"
function fileRouterRoutes() {
  return FILES.filter((f) => /(^|\/)src\/routes\/.*\.[jt]sx$/.test(f))
    .filter((f) => !/(^|\/)__|(^|\/)-|\/route\.[jt]sx$|\.lazy\.[jt]sx$/.test(rel(f)))
    .map((f) => {
      const after = rel(f).replace(/^.*?(^|\/)src\/routes\//, '');
      const segs = after.replace(/\.[jt]sx$/, '').split('/')
        .filter((s) => s && !s.startsWith('_'))          // pathless layouts
        .map((s) => (s.startsWith('$') ? ':' + s.slice(1) : s))
        .filter((s) => s !== 'index');
      return { path: '/' + segs.join('/'), file: rel(f), kind: 'file-router' };
    })
    .map((r) => ({ ...r, path: r.path === '/' ? '/' : r.path.replace(/\/$/, '') }));
}

const routes = [...nextAppRoutes(), ...nextPagesRoutes(), ...configRoutes(), ...fileRouterRoutes()]
  // A path with a file extension is a source filename that leaked into the route
  // list; sweeping it makes the tool request a URL that cannot exist and then
  // report its own 404 as a finding.
  .filter((r) => !/\.[a-z]{2,4}$/i.test(r.path))
  .filter((r, i, a) => a.findIndex((x) => x.path === r.path) === i)
  .sort((a, b) => a.path.localeCompare(b.path));

/* ---------------------------------------------------- imports (local only) */

// Try EVERY matching alias, not just the first: with several candidate roots
// configured, stopping at the first prefix match resolves nothing when that
// root happens to be the wrong one.
function resolveImport(fromFile, spec, aliases) {
  const bases = [];
  if (spec.startsWith('.')) bases.push(path.resolve(path.dirname(fromFile), spec));
  else for (const [pre, target] of aliases) {
    if (spec === pre || spec.startsWith(pre + '/')) bases.push(path.resolve(target, spec.slice(pre.length + 1)));
  }
  for (const base of bases) {
    const cands = [base, ...['.ts', '.tsx', '.js', '.jsx'].flatMap((e) => [base + e, path.join(base, 'index' + e)])];
    const hit = cands.find((c) => SOURCE.has(c));
    if (hit) return hit;
  }
  return null;
}

// tsconfig paths -> [["@", "."], ...]; falls back to the conventional ones.
//
// Do NOT strip /* */ before parsing: the alias keys THEMSELVES contain "/*"
// ("@/*": ["./*"]), so a block-comment stripper eats the paths map and every
// import silently fails to resolve. Line comments and trailing commas only.
function parseJsonc(text) {
  try { return JSON.parse(text); } catch { /* fall through to the tolerant pass */ }
  try { return JSON.parse(text.replace(/^\s*\/\/.*$/gm, '').replace(/,(\s*[}\]])/g, '$1')); } catch { return null; }
}

// Alias scopes, one per tsconfig in the tree, NOT just the repo root. In a
// monorepo the paths map lives in apps/web/tsconfig.json ("@/*": ["./src/*"])
// and the root has no tsconfig at all -- so a root-only reader resolves nothing,
// every import fails silently, and the walk stops at the entry file with
// modules:1. That looks like an app with no data rather than a broken traversal,
// which is the failure shape worth the most care to avoid.
function readAliasScopes() {
  const scopes = [];
  const seen = new Set();
  const load = (p, into, depth = 0) => {
    if (depth > 4 || seen.has(p) || !fs.existsSync(p)) return;
    seen.add(p);
    const json = parseJsonc(read(p));
    if (!json) return;
    const baseDir = path.dirname(p);
    const baseUrl = json?.compilerOptions?.baseUrl ?? '.';
    for (const [k, v] of Object.entries(json?.compilerOptions?.paths ?? {})) {
      const pre = k.replace(/\/\*$/, '');
      const target = String(v?.[0] ?? '').replace(/\/\*$/, '');
      if (pre && target) into.push([pre, path.resolve(baseDir, baseUrl, target)]);
    }
    if (typeof json.extends === 'string' && json.extends.startsWith('.')) load(path.resolve(baseDir, json.extends), into, depth + 1);
  };

  const configs = new Set([path.join(ROOT, 'tsconfig.json'), path.join(ROOT, 'jsconfig.json')]);
  for (const f of FILES) {                       // every package dir that ships source
    for (let d = path.dirname(f); d.startsWith(ROOT) && d !== ROOT; d = path.dirname(d))
      for (const n of ['tsconfig.json', 'jsconfig.json'])
        if (fs.existsSync(path.join(d, n))) configs.add(path.join(d, n));
  }
  for (const cfg of configs) {
    const entries = [];
    load(cfg, entries);
    if (entries.length) scopes.push({ dir: path.dirname(cfg), entries });
  }
  // Longest dir first, so the nearest tsconfig to a file wins.
  scopes.sort((a, b) => b.dir.length - a.dir.length);
  if (!scopes.length) scopes.push({ dir: ROOT, entries: [['@', ROOT], ['@', path.join(ROOT, 'src')], ['~', path.join(ROOT, 'src')]] });
  return scopes;
}
const ALIAS_SCOPES = readAliasScopes();

// The alias map governing a given file: nearest enclosing tsconfig, then any
// other scope as a fallback (a shared package imported across workspaces).
function aliasesFor(file) {
  const own = ALIAS_SCOPES.filter((s) => file.startsWith(s.dir + path.sep) || file === s.dir);
  return [...own, ...ALIAS_SCOPES.filter((s) => !own.includes(s))].flatMap((s) => s.entries);
}

function importsOf(file) {
  const src = SOURCE.get(file) ?? '';
  const specs = [
    ...src.matchAll(/(?:^|\n)\s*import\s+(?:[\s\S]*?\s+from\s+)?["'`]([^"'`]+)["'`]/g),
    ...src.matchAll(/import\(\s*["'`]([^"'`]+)["'`]\s*\)/g),
    ...src.matchAll(/(?:^|\n)\s*export\s+[\s\S]*?\s+from\s+["'`]([^"'`]+)["'`]/g),
  ].map((m) => m[1]);
  const aliases = aliasesFor(file);
  return [...new Set(specs)].map((s) => resolveImport(file, s, aliases)).filter(Boolean);
}

function reachable(entry) {
  const seen = new Set([entry]);
  let frontier = [entry];
  for (let d = 0; d < MAX_IMPORT_DEPTH && frontier.length; d++) {
    const next = [];
    for (const f of frontier) for (const i of importsOf(f)) if (!seen.has(i)) { seen.add(i); next.push(i); }
    frontier = next;
  }
  return seen;
}

/* -------------------------------------------------- queries and mutations */

// The entity a query key names. Two shapes in the wild, both common:
//   ['contacts', id]                  -> contacts   (literal array)
//   QUERY_KEYS.adminSettings.list()   -> adminSettings   (key factory)
// Mature repos overwhelmingly use the factory, so handling only the literal
// finds almost nothing. Namespace matters: a mutation's invalidateQueries uses
// the SAME factory, which is what lets writes and reads be matched at all.
function keyEntity(expr) {
  const lit = expr.match(/^\s*\[\s*["'`]([\w.:-]+)["'`]/);
  if (lit) return lit[1];
  const factory = expr.match(/\b[A-Za-z_$][\w$]*\s*\.\s*([A-Za-z_$][\w$]*)/);
  if (factory) return factory[1];
  const bare = expr.match(/^\s*["'`]([\w.:/-]+)["'`]/);
  if (bare) return bare[1].replace(/^\//, '').split('/')[0];
  return null;
}

// The endpoint a hook body talks to — used for blast radius and, later, for
// DOM-count-vs-API parity.
//
// The verb alternation is case-INSENSITIVE on purpose. openapi-fetch, openapi-typescript
// and every generated client built on them spell the method in caps
// (`apiClient.POST("/v1/accounts")`), and a lowercase-only matcher resolves the
// endpoint of exactly none of them. That is not a partial miss: `endpoint` feeds
// `resource()`, which feeds `resourceMatrix`, which is the blast radius of every
// sync risk AND the target list for --mutate. On a real 145-query app it produced
// ONE resourceMatrix entry and 7 syncRisks all marked unresolved — the headline
// finding silently reduced to "could not determine what goes stale" everywhere.
// If you tighten this regex, check resourceMatrix's size against a grep of the
// repo's HTTP calls before believing the result (see "Structural tells" in SKILL.md).
const ENDPOINT_CALL = /\.(?:get|post|put|patch|delete)\s*\(\s*[`"']([^`"']+)/i;
// Typed wrappers pass the path as a bare argument rather than as a method name
// (`useApiQuery(queryKeys.health(), "/v1/portal/health")`). Requiring an
// `/api/` or `/v1/` style prefix keeps this from matching an href or a CSS path.
const ENDPOINT_LITERAL = /[`"'](\/(?:api|v\d+|rest|graphql)\/[^`"'\s]+)[`"']/;
const endpointOf = (body) => (body.match(ENDPOINT_CALL)
  ?? body.match(/fetch\s*\(\s*[`"']([^`"']+)/)
  ?? body.match(ENDPOINT_LITERAL) ?? [])[1] ?? null;

// The HTTP method, same case-insensitivity for the same reason. A GET wrapped in
// useMutation (opening a PDF, kicking off a download) writes nothing, so it has no
// blast radius and must not be filed as a sync risk.
const verbOf = (body) => ((body.match(/\.(get|post|put|patch|delete)\s*\(/i) ?? [])[1] ?? '').toUpperCase() || null;

// The REST resource an endpoint addresses: /admin-panel/settings/?x -> settings.
// Leading api/v1/admin-panel style prefixes carry no entity information, and
// treating them as the entity collapses every route onto one bucket.
const PREFIX = /^(api|v\d+|admin-panel|admin|rest|graphql|public|internal)$/;
// Every meaningful segment of an endpoint, outermost first. `{id}` is a path
// parameter exactly like `:id` and `$id` -- leaving it in made it a "resource"
// and shifted every nested endpoint's segments by one.
function segments(endpoint) {
  if (!endpoint) return [];
  return endpoint.split('?')[0].split('/').filter(Boolean)
    .filter((s) => !s.startsWith('$') && !s.startsWith(':') && !/^\{.*\}$/.test(s) && !/^\d+$/.test(s))
    .filter((s) => !PREFIX.test(s));
}
function resource(endpoint) {
  if (!endpoint) return null;
  const all = endpoint.split('?')[0].split('/').filter(Boolean);
  return segments(endpoint)[0] ?? all[0] ?? null;
}

// `mutationFn: postLogout` hides the URL one module away. Without following it,
// every such mutation reports "affected routes undetermined" — which is most of
// them in any repo with an api/ layer, i.e. the report says nothing.
const fnEndpointCache = new Map();
function resolveFnEndpoint(name) {
  if (!name) return null;
  if (fnEndpointCache.has(name)) return fnEndpointCache.get(name);
  fnEndpointCache.set(name, null);                       // cycle guard
  const decl = new RegExp(`(?:export\\s+)?(?:async\\s+)?function\\s+${name}\\s*\\(|(?:export\\s+)?const\\s+${name}\\s*=`);
  for (const src of SOURCE.values()) {
    const m = src.match(decl);
    if (!m) continue;
    const found = endpointOf(src.slice(m.index, m.index + 1500));
    if (found) { fnEndpointCache.set(name, found); return found; }
  }
  return null;
}

// A call's argument text, brace-matched from the opening paren. Regex windows
// truncate real hook bodies (a queryFn is routinely 40 lines), which silently
// drops the invalidations that decide whether a mutation is a sync risk.
function callBody(src, openParenIdx, cap = 6000) {
  let depth = 0;
  for (let i = openParenIdx; i < Math.min(src.length, openParenIdx + cap); i++) {
    const c = src[i];
    if (c === '(' || c === '{' || c === '[') depth++;
    else if (c === ')' || c === '}' || c === ']') { depth--; if (depth === 0) return src.slice(openParenIdx, i + 1); }
  }
  return src.slice(openParenIdx, openParenIdx + cap);
}

const lineAt = (src, idx) => src.slice(0, idx).split('\n').length;

// The '(' of a call, skipping a generic argument list. `useQuery<A<B>, C>({...})`
// is routine in typed data layers, and `<[^>]*>` stops at the FIRST '>' -- so a
// naive matcher silently misses every generically-typed call while matching the
// untyped ones beside it. Returns -1 when what follows is not a call.
function callParen(src, after) {
  let i = after;
  while (i < src.length && /\s/.test(src[i])) i++;
  if (src[i] === '<') {
    let depth = 0;
    for (; i < src.length && i < after + 400; i++) {
      if (src[i] === '<') depth++;
      else if (src[i] === '>') { depth--; if (depth === 0) { i++; break; } }
      else if (src[i] === ';' || src[i] === '{') return -1;   // not a generic list
    }
    while (i < src.length && /\s/.test(src[i])) i++;
  }
  return src[i] === '(' ? i : -1;
}

// The hook or function a call sits inside. "useDeleteContact" is a finding a
// human can act on; "hook.ts:61" is a coordinate they have to go look up.
function enclosingName(src, idx) {
  const before = src.slice(0, idx);
  const decls = [...before.matchAll(/(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)|(?:export\s+)?const\s+([A-Za-z_$][\w$]*)\s*=/g)]
    .map((d) => d[1] ?? d[2]);
  // The nearest declaration is often a local inside the hook (const qc =
  // useQueryClient()); the enclosing HOOK is what a reader can act on.
  return decls.reverse().find((n) => /^use[A-Z]/.test(n)) ?? decls[0] ?? null;
}


// Repos wrap the data layer: useApiQuery / useQueuedWrite / useResource rather
// than bare useQuery / useMutation. Matching only the library names then reports
// ZERO queries on a codebase with forty hooks -- and syncRisks, the headline
// output, comes back empty because nothing was found to correlate, not because
// the app is clean. Silently empty is the worst failure shape a tool has.
function collectWrappers() {
  const q = new Set(), m = new Set();
  const DECL = /(?:export\s+)?(?:async\s+)?function\s+(use[A-Z]\w*)\s*[(<]|(?:export\s+)?const\s+(use[A-Z]\w*)\s*=/g;
  for (const src of SOURCE.values()) {
    for (const d of src.matchAll(DECL)) {
      const name = d[1] ?? d[2];
      if (!name) continue;
      // Brace-match the actual body. A fixed character window spills into the
      // NEXT declaration, so in a hooks file of many small hooks nearly every
      // one gets marked a wrapper -- which inflated one repo from 320 mutations
      // to 1620 and made syncRisks meaningless.
      const brace = src.indexOf('{', d.index);
      const body = brace < 0 ? '' : callBody(src, brace, 4000);
      // A wrapper RETURNS the query/mutation. A hook that merely calls one
      // somewhere in its body is a consumer, not a wrapper.
      const retQ = /return\s+use(?:Suspense)?(?:Infinite)?Query\s*[(<]|=>\s*use(?:Suspense)?(?:Infinite)?Query\s*[(<]/.test(body);
      const retM = /return\s+useMutation\s*[(<]|=>\s*useMutation\s*[(<]/.test(body);
      if (!retQ && !retM) continue;
      // Only GENERIC primitives get expanded at their call sites. useApiQuery(key, fn)
      // passes a PARAMETER through as the key, so its call sites carry the entity and
      // must be read. useCreateHouseholdMember() hardcodes its own key -- it was
      // already counted at this definition, and counting its call sites too inflated
      // one repo from 320 mutations to 991 and buried the real sync risks.
      const params = (src.slice(d.index, brace < 0 ? d.index : brace).match(/\(([^)]*)\)/) ?? [])[1] ?? '';
      const names = params.split(',').map((x) => x.trim().split(/[:=\s]/)[0]).filter((x) => /^[A-Za-z_$][\w$]*$/.test(x));
      const passesThrough = names.some((n) => new RegExp('(queryKey|mutationKey|mutationFn|queryFn)\\s*:\\s*' + n + '\\b').test(body));
      if (!passesThrough) continue;
      if (retQ) q.add(name);
      if (retM) m.add(name);
    }
  }
  for (const n of m) q.delete(n);   // wraps both -> the write is what matters
  return { queryWrappers: q, mutationWrappers: m };
}
const { queryWrappers, mutationWrappers } = collectWrappers();

// A wrapper takes its key as the FIRST ARGUMENT, not a queryKey: field, and its
// fetcher as the second. Split on top-level commas.
function splitArgs(callText) {
  const inner = callText.slice(1, -1);
  const out = [];
  let depth = 0, start = 0;
  for (let i = 0; i < inner.length; i++) {
    const c = inner[i];
    if ('([{'.includes(c)) depth++;
    else if (')]}'.includes(c)) depth--;
    else if (c === ',' && depth === 0) { out.push(inner.slice(start, i)); start = i + 1; }
  }
  out.push(inner.slice(start));
  return out.map((x) => x.trim());
}
const firstArg = (t) => splitArgs(t)[0] ?? '';

function extractWrapped(file, names, kind) {
  if (!names.size) return [];
  const src = SOURCE.get(file) ?? '';
  const out = [];
  const re = new RegExp('\\b(' + [...names].join('|') + ')\\b', 'g');
  for (const m of src.matchAll(re)) {
    const open = callParen(src, m.index + m[0].length);
    if (open < 0) continue;
    // Skip the wrapper's OWN declaration -- `function useApiQuery(key, fn)`
    // matches the call pattern, and counting it yields phantom queries whose
    // key is the parameter list.
    if (/\b(function|const|let|var)\s+$/.test(src.slice(Math.max(0, m.index - 24), m.index))) continue;
    const body = callBody(src, open);
    const key = firstArg(body);
    // The fetcher is the SECOND argument, positionally. Matching it by name
    // pattern (…Fetch/…Get/…Api) misses the ordinary spellings — listAccounts,
    // createInvoice — which is most of them, leaving the endpoint unresolved and
    // the blast radius undetermined.
    const args = splitArgs(body);
    const fnRef = (args[1] ?? '').match(/^([A-Za-z_$][\w$]*)$/)?.[1] ?? '';
    const rec = {
      entity: keyEntity(key), key: key.trim().slice(0, 120),
      endpoint: endpointOf(body) ?? resolveFnEndpoint(fnRef),
      file: rel(file), line: lineAt(src, m.index), via: m[1],
    };
    if (kind !== 'mutation') { out.push(rec); continue; }
    const invalidates = [...body.matchAll(/invalidateQueries\s*\(\s*\{?\s*(?:queryKey:\s*)?([^\n,)]+)/g)].map((x) => keyEntity(x[1])).filter(Boolean);
    const called = [...body.matchAll(/\b([A-Za-z_$][\w$]*)\s*\(/g)].map((x) => x[1]);
    const hook = enclosingName(src, m.index);
    out.push({
      ...rec, hook,
      // What it writes is the ENDPOINT'S resource, never the invalidation key:
      // deriving writes from what it invalidates makes wrong-key invalidation
      // definitionally impossible to detect -- the mutation that writes
      // /api/contacts but invalidates ['invoices'] would read as "writes
      // invoices, invalidates invoices" and pass.
      writes: (rec.endpoint ? resource(rec.endpoint) : null) ?? rec.entity ?? invalidates[0],
      verb: verbOf(body),
      invalidates: [...new Set(invalidates)],
      clearsCache: CACHE_OP.test(body) || called.some((n) => INVALIDATOR_NAMES.has(n)),
      clearsIndirectly: called.some((n) => INVALIDATOR_NAMES.has(n)),
      nonWrite: isNonWrite(rec.via, hook, rec.endpoint) || verbOf(body) === 'GET',
    });
  }
  return out;
}

function extractQueries(file) {
  const src = SOURCE.get(file) ?? '';
  const out = [...extractWrapped(file, queryWrappers, 'query')];
  for (const m of src.matchAll(/\buse(?:Suspense)?(?:Infinite)?Query\b/g)) {
    const open = callParen(src, m.index + m[0].length);
    if (open < 0) continue;
    const body = callBody(src, open);
    const key = (body.match(/queryKey:\s*([^\n,]+)/) ?? [])[1];
    if (!key) continue;
    const qFn = (body.match(/queryFn:\s*([A-Za-z_$][\w$]*)/) ?? [])[1] ?? '';
    out.push({
      entity: keyEntity(key), key: key.trim().slice(0, 120), endpoint: endpointOf(body) ?? resolveFnEndpoint(qFn),
      file: rel(file), line: lineAt(src, m.index),
    });
  }
  for (const m of src.matchAll(/\buseSWR\s*(?:<[^>]*>)?\s*\(\s*(["'`][^"'`]+["'`]|\[[\s\S]{0,120}?\])/g)) {
    out.push({ entity: keyEntity(m[1]), key: m[1].replace(/\s+/g, ' ').slice(0, 120), endpoint: null, file: rel(file), line: lineAt(src, m.index), hook: 'swr' });
  }
  return out;
}

/* --------------------------------------------- who actually clears the cache */

// Any call that refreshes cached server state, not just invalidateQueries.
const CACHE_OP = /(?:invalidate|reset|remove|refetch)Queries\s*\(|set(?:Query|Queries)Data\s*\(|(?:query|mutation)(?:Cache|Client)\s*\.\s*clear\s*\(/;

// Repos wrap cache resets in a helper (`const { resetQuery } = useResetQuery()`)
// and call THAT from onSuccess. Matching only the literal invalidateQueries call
// reports every such mutation as a sync risk — a false positive rate that makes
// the whole report unusable. So: collect the names of functions that clear the
// cache, and treat a call to one of them as an invalidation.
// Precision is the priority here: a missed risk surfaces later, a false alarm
// burns the reader's trust the first time they open the file and find nothing.
function collectInvalidatorNames() {
  const names = new Set();
  const DECL = /(?:function\s+([A-Za-z_$][\w$]*)\s*\(|(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\(|function)|([A-Za-z_$][\w$]*)\s*:\s*(?:async\s*)?\()/g;
  for (const src of SOURCE.values()) {
    for (const m of src.matchAll(DECL)) {
      const name = m[1] ?? m[2] ?? m[3];
      if (!name || names.has(name)) continue;
      if (CACHE_OP.test(src.slice(m.index, m.index + 1200))) names.add(name);
    }
  }
  return names;
}
const INVALIDATOR_NAMES = collectInvalidatorNames();

// Not every useMutation writes server state: exports, downloads, analytics pings
// and GET-backed "mutations" have nothing to invalidate and must not be flagged.
// Match on WORDS, after splitting camelCase and paths: a plain \b regex misses
// both "useCreateRecordExport" (no boundary inside camelCase) and "/exports/"
// (the boundary lands after the plural s), which is most real-world spellings.
const NON_WRITE_STEMS = /^(exports?|downloads?|prints?|tracks?|analytics?|telemetry|logs?|reports?|previews?|validates?|checks?|searches|search|verify|verifies)$/i;
const words = (s) => String(s ?? '').replace(/([a-z\d])([A-Z])/g, '$1 $2').split(/[^A-Za-z\d]+/).filter(Boolean);
const isNonWrite = (...parts) => parts.some((p) => words(p).some((w) => NON_WRITE_STEMS.test(w)));

function extractMutations(file) {
  const src = SOURCE.get(file) ?? '';
  const out = [...extractWrapped(file, mutationWrappers, 'mutation')];
  for (const m of src.matchAll(/\buseMutation\b/g)) {
    const open = callParen(src, m.index + m[0].length);
    if (open < 0) continue;
    const body = callBody(src, open);
    const invalidates = [...body.matchAll(/invalidateQueries\s*\(\s*\{?\s*(?:queryKey:\s*)?([^\n,)]+)/g)].map((x) => keyEntity(x[1])).filter(Boolean);
    const setQuery = [...body.matchAll(/set(?:Query|Queries)Data\s*\(\s*([^\n,]+)/g)].map((x) => keyEntity(x[1])).filter(Boolean);
    const fnName = (body.match(/mutationFn:\s*([A-Za-z_$][\w$]*)/) ?? [])[1] ?? '';
    const endpoint = endpointOf(body) ?? resolveFnEndpoint(fnName);
    const hook = enclosingName(src, m.index);
    // Does the body clear the cache directly, or by calling a known invalidator?
    const clearsDirectly = CACHE_OP.test(body);
    const calledNames = [...body.matchAll(/\b([A-Za-z_$][\w$]*)\s*\(/g)].map((x) => x[1]);
    const clearsIndirectly = calledNames.some((n) => INVALIDATOR_NAMES.has(n));
    out.push({
      // Endpoint resource first -- see the identical note in extractWrapped.
      writes: (endpoint ? resource(endpoint) : null) ?? setQuery[0] ?? invalidates[0],
      verb: verbOf(body),
      endpoint, fnName, hook,
      invalidates: [...new Set([...invalidates, ...setQuery])],
      clearsCache: clearsDirectly || clearsIndirectly,
      clearsIndirectly,
      nonWrite: isNonWrite(fnName, hook, endpoint) || verbOf(body) === 'GET'
        || (body.match(/\.(get|post|put|patch|delete)\s*\(/) ?? [])[1] === 'get',
      file: rel(file), line: lineAt(src, m.index),
    });
  }
  return out;
}

/* ------------------------------------------------------- assemble + graph */

const routeReport = routes.map((r) => {
  const entry = path.resolve(ROOT, r.file);
  const tree = reachable(entry);
  const queries = [...tree].flatMap(extractQueries);
  const mutations = [...tree].flatMap(extractMutations);
  return {
    ...r,
    modules: tree.size,
    entities: [...new Set(queries.map((q) => q.entity).filter(Boolean))].sort(),
    queries, mutations,
  };
});

// entity -> the routes that render it. This IS the sync graph.
const matrix = {};
for (const r of routeReport) for (const e of r.entities) (matrix[e] ??= []).push(r.path);
for (const e of Object.keys(matrix)) matrix[e] = [...new Set(matrix[e])].sort();

// The same graph keyed by API resource. Query keys and mutation targets are named
// in different vocabularies (a `QUERY_KEYS.getConversations()` factory vs a POST to
// /messages/), so key-name matching alone connects almost nothing. The endpoint is
// the vocabulary both sides actually share.
const resourceMatrix = {};
// resource -> the query-key entities that READ it. A mutation's invalidation is
// written in the readers' key vocabulary (QUERY_KEYS.crm covers a query keyed
// 'crm' that fetches /api/contacts), so "did it invalidate the right thing" must
// be judged against these, not against the endpoint's spelling.
const resourceReaders = {};
for (const r of routeReport) {
  for (const q of r.queries) {
    const res = resource(q.endpoint);
    if (!res) continue;
    (resourceMatrix[res] ??= []).push(r.path);
    if (q.entity) (resourceReaders[res] ??= new Set()).add(q.entity);
  }
}
for (const k of Object.keys(resourceMatrix)) resourceMatrix[k] = [...new Set(resourceMatrix[k])].sort();

const allMutations = routeReport.flatMap((r) => r.mutations.map((m) => ({ ...m, route: r.path })));
const byLoc = new Map(allMutations.map((m) => [`${m.file}:${m.line}`, m]));

// THE FINDING. Two shapes, both meaning "a write happened and some view still
// shows the old value" — the cross-page sync bug, located before a browser opens.
const syncRisks = [];
// Share of all routes past which a resource counts as ambient, not as an entity.
// The absolute floor matters as much as the share: in a 3-route app every
// resource clears 40%, and demoting there would blind the tool on exactly the
// small repos where the blast radius is easiest to state precisely.
const AMBIENT_SHARE = 0.4;
const AMBIENT_MIN_READERS = 10;
// Loose spelling match: 'contact-list' covers 'contacts', 'contacts' covers
// 'contact'. Prefer a miss to a false positive -- 'people' vs 'persons' is a
// miss, and that is the right trade.
const norm = (s) => String(s ?? '').toLowerCase().replace(/[-_./]/g, '').replace(/s$/, '');
for (const m of byLoc.values()) {
  if (m.nonWrite) continue;                    // nothing to go stale
  // A: writes something and invalidates NOTHING. Every reader of it is stale.
  // staleRoutes null means "blast radius not determined" — the entity could not
  // be resolved. That is NOT the same as zero affected routes, and reporting it
  // as an empty list would understate the finding.
  const res = resource(m.endpoint);
  const readersRaw = (res ? resourceMatrix[res] : null) ?? (m.writes ? matrix[m.writes] : null) ?? null;
  // A resource that most of the app reads is not an entity, it is an ambient
  // concern -- `auth`, `session`, `me`, `config`, `settings`. "This write leaves
  // 30 of 57 routes stale" is the denominator failure SKILL.md warns about: the
  // number is large because the resource is everywhere, not because the write is
  // dangerous. Measured on a real repo, /v1/auth/magic-link/request (which sends
  // an email and mutates no rendered collection) claimed 30 stale routes and
  // outranked four genuine findings. So: past the threshold the blast radius is
  // reported as undetermined rather than as evidence -- a weaker claim, honestly
  // labelled, which is the trade this tool makes everywhere else.
  const ambient = readersRaw && readersRaw.length >= AMBIENT_MIN_READERS && readersRaw.length > routeReport.length * AMBIENT_SHARE;
  const readers = ambient ? null : readersRaw;
  const name = m.hook ? `${m.hook}()` : `${m.file}:${m.line}`;
  if (!m.invalidates.length) {
    // Clears the cache through a helper or setQueryData whose keys we cannot
    // see: assume handled. Only the no-visible-keys case gets this benefit --
    // a mutation with LITERAL keys is judged on them, below.
    if (m.clearsCache) continue;
    // Three distinct claims, three severities. "This write leaves route X stale"
    // is evidence; "I could not work out what goes stale" is an admission, and
    // filing them at the same severity makes the strong finding look as soft as
    // the weak one. unresolved:true says so in the record, not just in the prose.
    const severity = readers?.length ? 'P1' : (m.writes ? 'P2' : 'P3');
    syncRisks.push({
      severity, kind: 'no-invalidation', unresolved: !readers?.length,
      route: m.route, entity: m.writes ?? res, hook: m.hook, mutation: `${m.file}:${m.line}`, verb: m.verb, endpoint: m.endpoint,
      invalidates: [], staleRoutes: readers,
      detail: `${name} writes ${m.endpoint ?? m.writes ?? 'server state'} and invalidates no query`
        + (readers?.length ? `; ${readers.length} route(s) render it`
          : ambient ? `; "${res}" is read by ${readersRaw.length} of ${routeReport.length} routes, so it is an ambient concern and the blast radius is not meaningful`
          : m.writes ? `; nothing found rendering "${m.writes}"` : '; could not determine what goes stale'),
    });
    continue;
  }
  // B: invalidates something, but nothing that covers what it writes. Covered
  // means: an invalidated key matches the written resource's spelling OR any
  // key the readers of that resource actually query under. An indirect clear
  // (helper function) may invalidate keys we cannot see, so those are skipped
  // rather than guessed at.
  if (m.clearsIndirectly) continue;
  const readerKeys = res ? [...(resourceReaders[res] ?? [])] : [];
  const covers = (k, w) => norm(k) === norm(w) || norm(k).includes(norm(w)) || norm(w).includes(norm(k));
  // Judge the invalidation against EVERY segment of the endpoint, not only the
  // outermost one. A PUT to /v1/accounts/{id}/budget/{year} that invalidates
  // ["budget", "board"] has covered what it wrote; calling that a wrong-key
  // invalidation because the outermost segment is "accounts" is the nesting,
  // not a defect. Spot-checked as a false positive on a real repo before it
  // reached anyone.
  const written = [...new Set([m.writes, ...segments(m.endpoint)].filter(Boolean))];
  const covered = m.invalidates.some((k) =>
    written.some((w) => covers(k, w)) || readerKeys.some((e) => covers(k, e)));
  if (m.writes && !covered && readers?.length) {
    syncRisks.push({
      severity: 'P1', kind: 'partial-invalidation',
      route: m.route, entity: m.writes ?? res, hook: m.hook, mutation: `${m.file}:${m.line}`, verb: m.verb, endpoint: m.endpoint,
      invalidates: m.invalidates, staleRoutes: readers,
      detail: `${name} writes "${m.writes}" but invalidates only [${m.invalidates.join(', ')}] -- none of which any reader of "${m.writes}" queries under; ${readers.length} route(s) render it stale`,
    });
  }
}
syncRisks.sort((a, b) => a.severity.localeCompare(b.severity) || (b.staleRoutes?.length ?? -1) - (a.staleRoutes?.length ?? -1));

// An entity read under two shapes of key is two sources of truth for one thing.
// Two sources of truth for ONE resource, not a key hierarchy. TanStack keys are
// deliberately hierarchical -- ["accounts", id, "orders"] and ["accounts", id,
// "order-favorites"] are CHILDREN of ["accounts"], and invalidating the parent
// covers both. That is the idiom, not a defect. The real defect is two different
// key shapes that fetch THE SAME ENDPOINT, which genuinely gives one resource two
// caches that can disagree. Grouping by entity alone flagged every correctly
// keyed hierarchy in a repo.
const byEndpoint = {};
for (const q of routeReport.flatMap((r) => r.queries)) {
  if (!q.entity || !q.endpoint) continue;
  // An endpoint with unresolved interpolation is not a comparable literal:
  // "${BASE}/analytics/" is three different URLs in three modules, and treating
  // the raw string as one collapses them into a phantom duplicate.
  if (/\$\{|\$\w/.test(q.endpoint)) continue;
  const res = resource(q.endpoint);
  if (!res) continue;
  ((byEndpoint[q.endpoint] ??= { entity: q.entity, keys: new Set() })).keys.add(q.key.replace(/\s/g, ''));
}
const duplicateSources = Object.entries(byEndpoint)
  .filter(([, v]) => v.keys.size > 1)
  .map(([endpoint, v]) => ({
    entity: v.entity, endpoint, keys: [...v.keys],
    detail: `${endpoint} is cached under ${v.keys.size} different key shapes -- one resource, two caches that can disagree`,
  }));

const payload = JSON.stringify({
  root: ROOT,
  generated: new Date().toISOString(),
  counts: {
    files: FILES.length,
    routes: routeReport.length,
    entities: Object.keys(matrix).length,
    // Unique call SITES. Summing per-route counts multiplies every shared hook by
    // the number of routes that reach it, which reads as 4000 queries in a repo
    // that has 300 — a count nobody can sanity-check is a count nobody should cite.
    queries: new Set(routeReport.flatMap((r) => r.queries.map((q) => `${q.file}:${q.line}`))).size,
    queryUsages: routeReport.reduce((n, r) => n + r.queries.length, 0),
    mutations: byLoc.size,
    syncRisks: syncRisks.length,
    duplicateSources: duplicateSources.length,
  },
  routes: routeReport,
  matrix,
  resourceMatrix,
  syncRisks,
  duplicateSources,
}, null, 2) + '\n';

if (TO_STDOUT) {
  process.stdout.write(payload);
} else {
  const outDir = path.join(ROOT, '.verify');
  fs.mkdirSync(outDir, { recursive: true });
  const outFile = path.join(outDir, 'inventory.json');
  fs.writeFileSync(outFile, payload);
  const c = JSON.parse(payload).counts;
  const p1 = JSON.parse(payload).syncRisks.filter((r) => r.severity === 'P1').length;
  console.log('\n  ' + ROOT);
  console.log('  ' + c.routes + ' routes  ' + c.queries + ' queries  ' + c.mutations + ' mutations');
  console.log('  ' + c.syncRisks + ' sync risks (' + p1 + ' with a resolved blast radius)  ' + c.duplicateSources + ' duplicate cache keys');
  console.log('  -> ' + outFile + '\n');
}
