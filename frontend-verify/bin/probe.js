// frontend-verify in-page probe. Deterministic runtime invariants.
//
// Returns { findings: [{kind, severity, detail, at}], metrics: {...} }.
//
// HARD CONSTRAINT: no backticks, no dollar signs anywhere in this file. It is
// passed through a double-quoted shell argument by playwright-cli; the shell
// eats both. Use string concatenation. (Same rule as ui-stress/probe.js.)
//
// Everything here is decidable without vision. Screenshots are for the residual.

async page => {
  const out = await page.evaluate(async () => {
    const V = [];
    const add = (kind, severity, detail, at) => V.push({ kind, severity, detail, at: at || '(page)' });

    const sel = el => {
      if (!el || el.nodeType !== 1) return '(page)';
      const t = el.getAttribute && el.getAttribute('data-testid');
      if (t) return '[data-testid=' + t + ']';
      if (el.id) return '#' + el.id;
      const c = (el.className && String(el.className).split(/\s+/)[0]) || '';
      return el.tagName.toLowerCase() + (c ? '.' + c : '');
    };
    const vis = el => {
      if (!el || el.nodeType !== 1) return false;
      const s = getComputedStyle(el);
      if (s.display === 'none' || s.visibility === 'hidden' || Number(s.opacity) < 0.02) return false;
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0;
    };
    // Screen-reader-only elements are 1x1 by design. Measuring them as tap
    // targets is how a ticket claims 103 failures and a browser finds one.
    const srOnly = el => {
      const s = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      return (r.width <= 2 && r.height <= 2) || s.clip === 'rect(0px, 0px, 0px, 0px)' || s.clipPath === 'inset(50%)';
    };

    /* -- L5: values that leaked through formatting ------------------------ */

    const LEAKS = [
      [/\[object Object\]/, '[object Object] rendered as text'],
      [/\bNaN\b/, 'NaN rendered as text'],
      [/\bundefined\b/, 'undefined rendered as text'],
      [/\bInvalid Date\b/, 'Invalid Date rendered as text'],
      [/\bnull\b/, 'the string "null" rendered as text'],
      [/\bTypeError\b|\bReferenceError\b|is not a function|Cannot read propert/, 'raw JS error text in the DOM'],
      [/\{\{[\w.]+\}\}|\$\{[\w.]+\}/, 'unresolved template variable in the DOM'],
    ];
    const bodyText = (document.body && document.body.innerText) || '';
    for (const pair of LEAKS) {
      const hit = bodyText.match(pair[0]);
      if (!hit) continue;
      const at = Math.max(0, (hit.index || 0) - 50);
      add('value.leak', 'P1', pair[1] + ' -- ...' + bodyText.slice(at, at + 140).replace(/\s+/g, ' ') + '...');
    }

    /* -- L4: states that were never built --------------------------------- */

    const root = document.querySelector('#root,#__next,[data-reactroot],main') || document.body;
    if (!root || (root.innerText || '').trim().length < 2)
      add('render.empty', 'P0', 'page root rendered with no text content');

    // A spinner still mounted after the settle loop is a query that never
    // resolved -- the other half of "the data did not load".
    const spinners = [...document.querySelectorAll('[aria-busy="true"],[role="progressbar"],.spinner,.loading,.skeleton,[class*="skeleton" i],[class*="animate-pulse"]')].filter(vis);
    if (spinners.length)
      add('render.stuck-loading', 'P1', spinners.length + ' loading indicator(s) still visible after settle', sel(spinners[0]));

    // An empty list with no empty state is indistinguishable from a failed fetch.
    // NOT filtered by vis(): an empty list is zero-height by definition, so a
    // visibility filter excludes precisely the case this rule exists to catch.
    // Layout participation (offsetParent, or a fixed/sticky ancestor) is the
    // right test -- it excludes display:none subtrees and keeps empty lists.
    const inLayout = el => el.offsetParent !== null || getComputedStyle(el).position === 'fixed';
    const lists = [...document.querySelectorAll('ul,ol,tbody,[role="list"],[role="table"],[role="grid"]')].filter(inLayout);
    for (const l of lists) {
      const rows = [...l.children].filter(vis);
      if (rows.length) continue;
      const near = ((l.parentElement && l.parentElement.innerText) || '').toLowerCase();
      if (!/no |empty|none |nothing|0 result|get started|add your first/.test(near))
        add('render.empty-list-no-state', 'P1', 'list rendered with zero rows and no empty-state message', sel(l));
    }

    /* -- L8: layout under the real viewport ------------------------------- */

    if (document.documentElement.scrollWidth > window.innerWidth + 1) {
      const wide = [...document.querySelectorAll('body *')].filter(el => {
        const r = el.getBoundingClientRect();
        return r.width > 0 && (r.right > window.innerWidth + 1 || r.left < -1) && vis(el);
      });
      add('layout.h-scroll', 'P1',
        'page scrolls horizontally at ' + window.innerWidth + 'px (content ' + document.documentElement.scrollWidth + 'px)',
        wide.length ? sel(wide[0]) : '(page)');
    }

    const INTERACTIVE = 'a[href],button,input,select,textarea,summary,[role="button"],[role="link"],[role="tab"],[role="menuitem"]';
    const small = [...document.querySelectorAll(INTERACTIVE)].filter(el => {
      if (!vis(el) || srOnly(el)) return false;
      const r = el.getBoundingClientRect();
      return Math.min(r.width, r.height) < 24;
    });
    if (small.length)
      add('a11y.tap-target', 'P2', small.length + ' interactive element(s) under 24px (sr-only excluded)', sel(small[0]));

    /* -- L6: a control that cannot be clicked ------------------------------ */

    // elementFromPoint at the control's center must return the control or one
    // of its own descendants/ancestors; anything else is sitting on top and
    // eats the click. elementFromPoint already skips pointer-events:none, so a
    // deliberate click-through overlay never fires this. An OPEN dialog
    // legitimately occludes everything behind it, so any modal signal
    // suppresses the whole rule for this capture rather than flagging the
    // entire background surface.
    const modalOpen = !!document.querySelector('dialog[open],[role="dialog"],[aria-modal="true"]');
    if (!modalOpen) {
      const occluded = [];
      for (const el of document.querySelectorAll('a[href],button,input,select,textarea,summary,[role="button"],[role="link"],[role="tab"],[role="menuitem"]')) {
        if (!vis(el) || srOnly(el)) continue;
        const r = el.getBoundingClientRect();
        const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
        if (cx < 0 || cy < 0 || cx > window.innerWidth || cy > window.innerHeight) continue;
        // Scrolled out of its own clipping ancestor is NOT occluded. A nav with
        // overflow-y:auto still reports a layout rect for items below the fold,
        // so elementFromPoint at that coordinate returns whatever is PAINTED
        // there -- typically the footer sitting under the scroll box. The user
        // scrolls and clicks the control fine.
        //
        // Measured, not theorised: a sidebar nav item one row past its
        // container's bottom edge produced this on 37 of 51 routes in one run,
        // every one reading "clicks land on span.block instead" -- the account
        // name in the sign-out block below the nav. 37 P1s that are all one
        // scrollable list is exactly the noise that stops a report being read.
        let clipped = false;
        for (let a = el.parentElement; a && a !== document.body; a = a.parentElement) {
          const s = getComputedStyle(a);
          if (!/auto|scroll|hidden|clip/.test(s.overflowY + s.overflowX)) continue;
          const ar = a.getBoundingClientRect();
          if (cx < ar.left || cx > ar.right || cy < ar.top || cy > ar.bottom) { clipped = true; break; }
        }
        if (clipped) continue;
        const hit = document.elementFromPoint(cx, cy);
        if (!hit || hit === el || el.contains(hit) || hit.contains(el)) continue;
        // A label wrapping its input is how custom checkboxes are built.
        if (hit.closest && hit.closest('label') && hit.closest('label').contains(el)) continue;
        occluded.push([el, hit]);
      }
      if (occluded.length)
        add('interact.click-occluded', 'P1', occluded.length + ' interactive element(s) whose center is covered by another element -- clicks land on '
          + sel(occluded[0][1]) + ' instead', sel(occluded[0][0]));
    }

    const noAria = el => !el.getAttribute('aria-label') && !el.getAttribute('aria-labelledby') && !el.getAttribute('title');
    const unlabeled = [...document.querySelectorAll('button,[role="button"],a[href]')].filter(el =>
      vis(el) && !(el.innerText || '').trim() && noAria(el));
    // Form fields get a name from a <label> (wrapping or for=), aria, or title.
    // A placeholder is accepted here only because browsers fall back to it in
    // accname computation -- it is still bad practice, but not nameless.
    const unlabeledFields = [...document.querySelectorAll('input,select,textarea')].filter(el =>
      vis(el) && el.type !== 'hidden' && noAria(el)
      && !(el.labels && el.labels.length) && !el.closest('label') && !el.getAttribute('placeholder'));
    const nameless = unlabeled.concat(unlabeledFields);
    if (nameless.length)
      add('a11y.unlabeled-control', 'P2', nameless.length + ' control(s) with no accessible name', sel(nameless[0]));

    /* -- L5: data arrived, page rendered none of it ------------------------ */

    // The cardinality defect's strongest decidable form. The in-page network
    // recorder captured a same-origin JSON array; if EVERY list on the page has
    // zero visible rows, the data arrived and was never rendered. Requiring all
    // lists empty (a populated nav suppresses it) keeps this near zero noise.
    const net = (window.__fv_net || []).filter(r =>
      r.method === 'GET' && r.ok && typeof r.arrayLen === 'number'
      && (!/^https?:/.test(r.url) || r.url.indexOf(location.origin) === 0));
    const maxLen = net.reduce((n, r) => Math.max(n, r.arrayLen), 0);
    const totalRows = lists.reduce((n, l) => n + [...l.children].filter(vis).length, 0);
    if (maxLen > 0 && lists.length && totalRows === 0)
      add('data.rendered-zero-of-n', 'P1', 'a same-origin API response carried ' + maxLen
        + ' record(s) but every list on the page rendered zero rows -- the data arrived and was never rendered');

    /* -- L10: what the main thread actually did --------------------------- */

    const metrics = { longTasks: 0, longestTaskMs: 0, cls: 0, lcpMs: null, forcedReflows: 0, resources: 0, transferKB: 0, perfObserved: false };

    // longtask / layout-shift / LCP are ONLY visible to observers installed
    // before navigation (the sweep's init script fills window.__fv_perf);
    // performance.getEntriesByType returns nothing for them in Chromium. When
    // the init script is absent (probe run standalone), the perf gates are
    // marked unmeasured rather than silently reporting clean zeros.
    const P = window.__fv_perf;
    if (P) {
      if (P.flush) try { P.flush(); } catch (e) { /* drained what we could */ }
      metrics.perfObserved = true;
      metrics.longTasks = P.longTasks; metrics.longestTaskMs = P.longestTaskMs;
      metrics.cls = P.cls; metrics.lcpMs = P.lcpMs; metrics.forcedReflows = P.thrashReads;
    }
    try { performance.getEntriesByType('resource').forEach(e => { metrics.resources++; metrics.transferKB += (e.transferSize || 0) / 1024; }); } catch (e) { /* unsupported */ }
    metrics.cls = Math.round(metrics.cls * 1000) / 1000;
    metrics.transferKB = Math.round(metrics.transferKB);

    // Thresholds are the published Core Web Vitals "needs improvement" line, so
    // a finding here means something a real user feels, not a preference. All
    // gated on perfObserved: an unmeasured metric must never read as a clean one.
    if (metrics.perfObserved) {
      if (metrics.longestTaskMs > 200)
        add('perf.long-task', 'P2', 'longest main-thread task ' + metrics.longestTaskMs + 'ms (' + metrics.longTasks + ' over 50ms) -- input is blocked for that whole window');
      if (metrics.cls > 0.1)
        add('perf.layout-shift', 'P2', 'cumulative layout shift ' + metrics.cls + ' (over the 0.1 threshold) -- content moves under the cursor');
      if (metrics.lcpMs !== null && metrics.lcpMs > 2500)
        add('perf.lcp', 'P2', 'largest contentful paint at ' + metrics.lcpMs + 'ms (over 2500ms)');
      // Forced synchronous layout, counted since before app JS ran: a geometry
      // read after a DOM write in the same frame makes the browser lay out again.
      if (metrics.forcedReflows > 20)
        add('perf.layout-thrash', 'P2', metrics.forcedReflows + ' geometry reads interleaved with DOM writes in one frame -- forced synchronous layout');
    }

    /* -- L4: hydration and boundaries ------------------------------------- */

    // React marks a hydration-mismatched root; the visible symptom is content
    // that renders then silently swaps or disappears.
    if (document.querySelector('[data-nextjs-error],[data-nextjs-dialog]'))
      add('render.dev-overlay', 'P0', 'a framework error overlay is present on the page');

    return { findings: V, metrics };
  });
  return out;
}
