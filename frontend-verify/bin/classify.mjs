#!/usr/bin/env node
// Static defect classifier. No browser, no build, no dependencies.
//
//   node classify.mjs <repoRoot>          -> prints a report, writes <repoRoot>/.verify/classify.json
//   node classify.mjs <repoRoot> --json   -> JSON to stdout instead
//
// Output lands next to the REPO BEING ANALYSED, never in the current working
// directory: this skill is installed once and run against many repos.
//
// Each rule below is a NAMED FAILURE CLASS, not a lint preference: every one of
// them has shipped a real bug. Rules are keyed to references/atlas.md so a finding
// carries its own explanation. Precision over recall throughout — a false positive
// costs more than a miss, because it is what makes a report stop being read.

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const ROOT = path.resolve(process.argv[2]?.startsWith('--') ? '.' : (process.argv[2] ?? '.'));
const JSON_OUT = process.argv.includes('--json');
const SKIP = /(^|\/)(node_modules|\.next|\.git|dist|build|out|coverage|\.turbo|\.vercel|venv|site-packages|vendor|storybook-static|__tests__|__mocks__)(\/|$)|(^|\/)\.[^/]+\/|worktrees\/|\.(test|spec|stories|d)\.[tj]sx?$/;

function walk(dir, acc = []) {
  let ents; try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch { return acc; }
  for (const e of ents) {
    const p = path.join(dir, e.name);
    if (SKIP.test(p)) continue;
    if (e.isDirectory()) walk(p, acc);
    else if (/\.[jt]sx?$/.test(e.name)) acc.push(p);
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

// Design-lab trees: committed (so .gitignore does not cover them), shaped like
// the app (so every rule fires in them), reachable from no route (so nothing
// found there can break anything). On a real repo these produced 18 of 19
// findings -- a report that is 95% noise is a report nobody opens twice.
// Add repo-specific trees to <repo>/.verifyignore, one substring or glob per line.
const LAB = /(^|\/)(_proto|proto|design-lab|playground|sandbox|scratch)(\/|$)/;

// Deliberately glob-lite: `*` and `?` only, matched against the repo-relative
// path. A full matcher would be a dependency, and this file has none by design.
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
  .filter((f) => /\.[jt]sx?$/.test(f) && !SKIP.test(f) && !ignored(path.relative(ROOT, f)));
const rel = (f) => path.relative(ROOT, f);
const lineAt = (src, i) => src.slice(0, i).split('\n').length;

// Comments and string bodies produce most false positives in a regex classifier.
const decomment = (s) => s.replace(/\/\*[\s\S]*?\*\//g, (m) => ' '.repeat(m.length))
  .replace(/(^|[^:])\/\/[^\n]*/g, (m) => ' '.repeat(m.length));

// Brace/paren-matched argument text from an opening delimiter.
function block(src, open, cap = 8000) {
  let depth = 0;
  for (let i = open; i < Math.min(src.length, open + cap); i++) {
    const c = src[i];
    if ('([{'.includes(c)) depth++;
    else if (')]}'.includes(c)) { depth--; if (depth === 0) return src.slice(open, i + 1); }
  }
  return src.slice(open, open + cap);
}

const findings = [];
const add = (rule, sev, file, line, detail, atlas) =>
  findings.push({ rule, severity: sev, file: rel(file), line, detail, atlas });

for (const file of FILES) {
  let raw; try { raw = fs.readFileSync(file, 'utf8'); } catch { continue; }
  const src = decomment(raw);
  // Server files legitimately read any env var. instrumentation.ts, middleware,
  // *.config.*, route handlers and anything importing next/server or server-only
  // never ship to the browser, so the build-time-inlining rule does not apply.
  // e2e specs, build scripts and tooling run in Node and never reach a browser,
  // so the build-time-inlining rule does not apply to them either.
  const isServerFile = /(^|\/)(instrumentation|middleware)\.[jt]s|\.config\.[jtm]s|(^|\/)(app|pages)\/api\/|\.server\.[jt]s|(^|\/)sentry\.(server|edge)\.|(^|\/)(e2e|scripts|tools|tests?|cypress|playwright)\//.test(rel(file))
    || /from\s+["'](next\/server|server-only)["']/.test(src);
  const isClient = !isServerFile && (/^\s*["']use client["']/m.test(src) || !/(^|\/)app\//.test(file));
  const isTSX = /\.[jt]sx$/.test(file);

  /* L4 — states that were never built ------------------------------------- */

  // A list with no zero-length branch renders identically whether the data is
  // empty or the fetch failed. This is the single most common reason "half the
  // data didn't load" looks fine on screen.

  // Server data reaches a component through a WRAPPER hook far more often than
  // through a useQuery call in the same file, so requiring useQuery here misses
  // the normal case entirely. The real signal is: something destructured from a
  // use*() call is being mapped over. Static arrays (nav links, legal copy)
  // legitimately have no empty state and must not be flagged.
  const hookData = [...src.matchAll(/const\s*\{([^}]*)\}\s*=\s*use[A-Z]\w*\s*\(/g)]
    .flatMap((m) => m[1].split(',').map((x) => x.split(':').pop().trim()).filter(Boolean));
  const mapsHookData = hookData.some((n) => new RegExp('\\b' + n + '\\b[^\\n]{0,40}\\.map\\s*\\(').test(src))
    || /use(?:Suspense)?(?:Infinite)?Query|useSWR|await\s+fetch/.test(src);
  if (isTSX && /\.map\s*\(/.test(src) && mapsHookData) {
    const hasEmptyBranch = /\.length\s*===?\s*0|\.length\s*[?>]|!\w+\.length|\.length\s*<\s*1|isEmpty|EmptyState|NoResults|no-results/i.test(src);
    if (!hasEmptyBranch) {
      const m = src.match(/\.map\s*\(/);
      add('missing-empty-state', 'P1', file, lineAt(src, m.index),
        'renders a list with no zero-length branch — an empty list and a failed fetch look identical', 'L4.36');
    }
  }

  for (const m of src.matchAll(/\buse(?:Suspense)?(?:Infinite)?Query\s*\(/g)) {
    const b = block(src, m.index + m[0].length - 1);
    const after = src.slice(Math.max(0, m.index - 300), m.index + b.length + 1200);
    // A wrapper hook that RETURNS the query result is not ignoring the error —
    // its caller reads it. Flagging those buries the real findings under the
    // repo's entire data layer, which is how a report stops being read.
    const returned = /\breturn\s*$/.test(src.slice(Math.max(0, m.index - 20), m.index).trim() ? src.slice(Math.max(0, m.index - 20), m.index) : '')
      || /(?:return|=>)\s*$/.test(src.slice(Math.max(0, m.index - 12), m.index));
    if (returned) continue;
    if (!/\b(isError|error|isLoadingError|failureReason)\b/.test(after))
      add('unread-query-error', 'P1', file, lineAt(src, m.index),
        'useQuery result never reads isError/error — a failed fetch renders as empty, silently', 'L4.35');
    if (!/\b(isLoading|isPending|isFetching|Suspense|skeleton|Skeleton)\b/.test(after))
      add('unread-query-loading', 'P2', file, lineAt(src, m.index),
        'useQuery result never reads isLoading/isPending — no loading state, so empty renders first', 'L4.34');
  }

  /* L3 — two sources of truth --------------------------------------------- */

  // Server data copied into a client store is a second source of truth that the
  // query cache cannot invalidate. This is the structural cause of "page B still
  // shows the old value after page A saved".
  if (/\bcreate\s*(?:<[^>]*>)?\s*\(\s*(?:\(set|\(\)|set|persist|immer|devtools|subscribeWithSelector)/.test(src)
      && /zustand/.test(raw)) {
    const holdsServer = /\b(data|items|list|results|rows|records|entities|byId)\b\s*:/.test(src)
      && /\b(fetch|axios|api|await\s+\w+\()/.test(src);
    if (holdsServer) {
      const m = src.match(/\bcreate\s*(?:<[^>]*>)?\s*\(/);
      add('server-state-in-client-store', 'P0', file, lineAt(src, m.index),
        'client store fetches and holds server data — the query cache can never invalidate it; page B goes stale', 'L3.22');
    }
  }

  // useState seeded from a prop never updates when the prop changes.
  // Only props.X: useState(SomeEnum.Value) is a constant initialiser, not
  // derived state, and matching any dotted identifier flags all of them.
  for (const m of src.matchAll(/useState\s*(?:<[^>]*>)?\s*\(\s*props\.(\w+)/g))
    add('derived-state-in-useState', 'P2', file, lineAt(src, m.index),
      `useState seeded from props.${m[1]} — will not update when that prop changes`, 'L3.28');

  /* L3/L6 — effects, closures, aborts ------------------------------------- */

  for (const m of src.matchAll(/useEffect\s*\(\s*(?:async\s*)?\(\s*\)\s*=>\s*\{/g)) {
    const b = block(src, src.indexOf('{', m.index + m[0].length - 1));
    const depsAt = src.indexOf('}', m.index + b.length - 1);
    const deps = (src.slice(depsAt, depsAt + 200).match(/\}\s*,\s*(\[[^\]]*\])/) ?? [])[1];

    if (/\b(fetch|axios)\s*[.(]/.test(b) && !/AbortController|signal|cancelled|ignore|isMounted/.test(b))
      add('effect-fetch-without-abort', 'P1', file, lineAt(src, m.index),
        'fetch in an effect with no AbortController — a late response lands on an unmounted or navigated view', 'L2.16');

    // Empty deps + referenced state/props = the stale closure. Reads the value
    // captured on first render, forever.
    if (deps === '[]') {
      // Strip string/template literals and comments before looking for identifier
      // reads. Without this, addEventListener("online", ...) inside an effect
      // counts as a read of a state variable named `online` — a false positive on
      // the single most common shape of a correct []-deps effect (subscribe on
      // mount, unsubscribe on unmount), which is exactly the code this rule must
      // stay silent on to be worth reading.
      const scannable = b
        .replace(/\/\*[\s\S]*?\*\//g, ' ')
        .replace(/\/\/[^\n]*/g, ' ')
        .replace(/"(?:[^"\\]|\\.)*"/g, '""')
        .replace(/'(?:[^'\\]|\\.)*'/g, "''")
        .replace(/`(?:[^`\\]|\\.)*`/g, '``');
      const reads = [...scannable.matchAll(/\b([a-z][\w]*)\b(?!\s*[:(])/g)].map((x) => x[1]);
      const stateNames = [...src.matchAll(/const\s*\[\s*([a-z][\w]*)\s*,\s*set[A-Z]/g)].map((x) => x[1]);
      const captured = [...new Set(reads.filter((r) => stateNames.includes(r)))];
      if (captured.length)
        add('stale-closure', 'P1', file, lineAt(src, m.index),
          `effect has [] deps but reads state (${captured.slice(0, 3).join(', ')}) — sees the first-render value forever`, 'L3.28');
    }
  }

  /* L4 — reconciliation ---------------------------------------------------- */

  for (const m of src.matchAll(/key\s*=\s*\{\s*(?:index|i|idx)\s*\}/g))
    add('index-as-list-key', 'P2', file, lineAt(src, m.index),
      'key={index} — on reorder or delete, React updates the wrong row and keeps the wrong local state', 'L4.40');

  // A new object identity every render busts every consumer's memo.
  for (const m of src.matchAll(/<(\w+)\.Provider\s+value=\{\s*[{[]/g))
    if (!/useMemo/.test(src.slice(Math.max(0, m.index - 500), m.index)))
      add('unstable-context-value', 'P2', file, lineAt(src, m.index),
        'Provider value is a fresh literal each render — every consumer re-renders, memoization downstream is dead', 'L10.92');

  // An external store read without useSyncExternalStore can tear under
  // concurrent rendering: two components render the same store in one paint
  // with different values.
  if (/subscribe\s*\(/.test(src) && /getSnapshot|getState/.test(src) && !/useSyncExternalStore/.test(src))
    add('external-store-without-sync', 'P2', file, lineAt(src, src.search(/subscribe\s*\(/)),
      'external store read without useSyncExternalStore — tearing risk under concurrent rendering', 'L3.29');

  /* L1 — delivery ---------------------------------------------------------- */

  // Bundlers inline NEXT_PUBLIC_/VITE_ at BUILD time. Any other env var read in
  // client code is undefined in the browser no matter what the runtime sets.
  if (isClient)
    for (const m of src.matchAll(/process\.env\.([A-Z][A-Z0-9_]*)/g))
      if (!/^(NEXT_PUBLIC_|NODE_ENV$|STORYBOOK_)/.test(m[1]))
        add('runtime-env-in-client-code', 'P0', file, lineAt(src, m.index),
          `process.env.${m[1]} in client code — inlined at build time, so it is undefined in the browser however the runtime is configured`, 'L1.1');

  for (const m of src.matchAll(/import\.meta\.env\.([A-Z][A-Z0-9_]*)/g))
    if (!/^(VITE_|MODE$|DEV$|PROD$|SSR$|BASE_URL$)/.test(m[1]))
      add('runtime-env-in-client-code', 'P0', file, lineAt(src, m.index),
        `import.meta.env.${m[1]} is not VITE_-prefixed — Vite strips it from the client bundle`, 'L1.1');

  /* L5 / L7 — value and trust boundaries ----------------------------------- */

  for (const m of src.matchAll(/dangerouslySetInnerHTML|\.innerHTML\s*=/g)) {
    if (/DOMPurify|sanitize/i.test(src)) continue;
    // JSON-LD / structured-data blocks are a serialized object, not markup, and
    // are the most common legitimate use of this API. Flagging them trains the
    // reader to ignore the rule that catches the real sink.
    const around = src.slice(Math.max(0, m.index - 200), m.index + 200);
    if (/application\/ld\+json|JSON\.stringify/.test(around)) continue;
    // A sink can be sanitized upstream of this file entirely (e.g. the server
    // escapes before the value ever reaches the client) -- undecidable from
    // this file alone. `verify-ignore: unsanitized-html` is a deliberate,
    // window-scoped escape hatch: it silences only the matched occurrence, not
    // the whole file, so it can't accidentally mask a second, real sink placed
    // elsewhere in the same file. The comment must say WHERE the sanitization
    // happens, so the claim stays checkable. `decomment` blanks comment text out
    // of `src` (same length, so indices still line up) -- the marker lives in a
    // comment, so it has to be read from `raw`, not the decommented window. Wider
    // than the 200-char default window: this marker routinely stacks above an
    // existing biome-ignore, which biome requires to sit immediately adjacent to
    // the sink -- pushing the marker itself further back than a single comment.
    const rawAround = raw.slice(Math.max(0, m.index - 400), m.index + 200);
    if (/verify-ignore:\s*unsanitized-html/.test(rawAround)) continue;
    add('unsanitized-html', 'P0', file, lineAt(src, m.index),
      'raw HTML injection with no sanitizer in the file — XSS sink', 'L7.74');
  }

  // Merging a parsed payload into an existing object is the prototype-pollution
  // shape; a payload carrying __proto__ rewrites Object.prototype.
  for (const m of src.matchAll(/Object\.assign\s*\(\s*(?!\{)\w+\s*,\s*(?:JSON\.parse|await|res|data|body|payload|params)/g))
    add('prototype-pollution-shape', 'P1', file, lineAt(src, m.index),
      'Object.assign into an existing object from untrusted data — __proto__ in the payload rewrites Object.prototype', 'L7.75');

  /* L6 — idempotency ------------------------------------------------------- */

  // A submit path with no pending guard produces duplicate records on a
  // double-click or a slow network. Idempotent UI actions, in their list.
  if (isTSX && /onSubmit|handleSubmit/.test(src) && /useMutation|mutate\s*\(/.test(src)
      && !/isPending|isLoading|isSubmitting|disabled=/.test(src)) {
    const m = src.match(/onSubmit|handleSubmit/);
    add('submit-without-pending-guard', 'P1', file, lineAt(src, m.index),
      'submit path with no pending/disabled guard — a double click writes the record twice', 'L6.59');
  }
}

/* --------------------------------------------------------- route-level gaps */

// Next app router: a route segment with data and no error.tsx has no boundary,
// so a thrown render error blanks the whole subtree instead of that panel.
const appRoutes = FILES.filter((f) => /(^|\/)app\/(.*\/)?page\.[jt]sx?$/.test(f));
for (const p of appRoutes) {
  const dir = path.dirname(p);
  const src = (() => { try { return fs.readFileSync(p, 'utf8'); } catch { return ''; } })();
  if (!/useQuery|useSWR|fetch\s*\(|await\s/.test(src)) continue;
  const upTo = (name) => {
    for (let d = dir; d.startsWith(ROOT); d = path.dirname(d))
      if (['tsx', 'ts', 'jsx', 'js'].some((e) => fs.existsSync(path.join(d, `${name}.${e}`)))) return true;
    return false;
  };
  if (!upTo('error')) add('no-error-boundary', 'P1', p, 1, 'data route with no error.tsx in its segment chain — a render throw blanks the subtree', 'L4.38');
  if (!upTo('loading')) add('no-loading-boundary', 'P2', p, 1, 'data route with no loading.tsx — the empty shell paints before data arrives', 'L4.34');
}

/* ---------------------------------------------------------------- report */

const order = { P0: 0, P1: 1, P2: 2, P3: 3 };
findings.sort((a, b) => order[a.severity] - order[b.severity] || a.rule.localeCompare(b.rule) || a.file.localeCompare(b.file));
const byRule = findings.reduce((a, f) => ((a[f.rule] = (a[f.rule] ?? 0) + 1), a), {});
const bySev = findings.reduce((a, f) => ((a[f.severity] = (a[f.severity] ?? 0) + 1), a), {});

const payload = JSON.stringify({ root: ROOT, files: FILES.length, counts: { total: findings.length, ...bySev }, byRule, findings }, null, 2) + '\n';

if (JSON_OUT) {
  process.stdout.write(payload);
} else {
  const outDir = path.join(ROOT, '.verify');
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, 'classify.json'), payload);
  console.log(`\n  ${FILES.length} source files scanned in ${ROOT}`);
  console.log(`  ${findings.length} findings  ${Object.entries(bySev).map(([k, v]) => `${k}:${v}`).join('  ')}\n`);
  for (const [rule, n] of Object.entries(byRule).sort((a, b) => b[1] - a[1])) {
    const first = findings.find((f) => f.rule === rule);
    console.log(`  ${String(n).padStart(4)}  ${first.severity}  ${rule}  [${first.atlas}]`);
    console.log(`        ${first.detail}`);
    for (const f of findings.filter((x) => x.rule === rule).slice(0, 3)) console.log(`        ${f.file}:${f.line}`);
    if (n > 3) console.log(`        ... and ${n - 3} more`);
    console.log('');
  }
  console.log(`  -> ${path.join(ROOT, '.verify', 'classify.json')}\n`);
}
process.exit(bySev.P0 || bySev.P1 ? 1 : 0);
