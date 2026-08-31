#!/usr/bin/env bash
# Proves the STATIC analysers fire. Builds a throwaway repo carrying one planted
# instance of each class, then asserts inventory.mjs and classify.mjs find them.
# Needs nothing but node -- no browser, no install.
#
#   bash ~/.claude/skills/frontend-verify/selftest-static.sh
set -uo pipefail

SKILL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/app/contacts" "$TMP/app/dashboard" "$TMP/src/api" "$TMP/src/store"
cat > "$TMP/tsconfig.json" <<'JSON'
{ "compilerOptions": { "baseUrl": ".", "paths": { "@/*": ["./*"] } } }
JSON

cat > "$TMP/src/api/contacts.ts" <<'TS'
import axios from 'axios'
export async function listContacts() { return axios.get('/api/contacts') }
export async function createContact(body: unknown) { return axios.post('/api/contacts', body) }
export async function updateContact(body: unknown) { return axios.put('/api/contacts', body) }
export async function renameContact(body: unknown) { return axios.patch('/api/contacts', body) }
TS

# PLANTED: a mutation that writes /api/contacts and invalidates nothing, while
# two routes render that same resource.  -> syncRisks >= 1
# PLANTED: a mutation that writes /api/contacts but invalidates ['invoices'] --
# WRONG-KEY invalidation. Must surface as partial-invalidation, not pass because
# "it invalidated something". -> syncRisks kind partial-invalidation
# NOT planted as a risk: useRenameContact invalidates ['contacts'], the right key.
cat > "$TMP/src/api/hooks.ts" <<'TS'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createContact, listContacts, updateContact, renameContact } from '@/src/api/contacts'
export function useContacts() {
  return useQuery({ queryKey: ['contacts'], queryFn: listContacts })
}
export function useCreateContact() {
  return useMutation({ mutationFn: createContact })
}
export function useUpdateContact() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: updateContact,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['invoices'] }),
  })
}
export function useRenameContact() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: renameContact,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['contacts'] }),
  })
}
TS

# PLANTED: missing-empty-state, index-as-list-key, unread-query-error
cat > "$TMP/app/contacts/page.tsx" <<'TSX'
'use client'
import { useContacts } from '@/src/api/hooks'
export default function ContactsPage() {
  const { data } = useContacts()
  return <ul>{(data ?? []).map((c: any, index: number) => <li key={index}>{c.name}</li>)}</ul>
}
TSX

# PLANTED: runtime-env-in-client-code, submit-without-pending-guard
cat > "$TMP/app/dashboard/page.tsx" <<'TSX'
'use client'
import { useContacts, useCreateContact } from '@/src/api/hooks'
export default function Dashboard() {
  const { data } = useContacts()
  const create = useCreateContact()
  const url = process.env.API_BASE_URL
  return (
    <form onSubmit={() => create.mutate({})}>
      <span>{url}</span><span>{(data ?? []).length}</span>
      <button type="submit">Save</button>
    </form>
  )
}
TSX

# PLANTED: server-state-in-client-store
cat > "$TMP/src/store/contacts.ts" <<'TS'
import { create } from 'zustand'
export const useContactStore = create((set) => ({
  items: [],
  load: async () => { const res = await fetch('/api/contacts'); set({ items: await res.json() }) },
}))
TS

# PLANTED: a GENERIC wrapper primitive (key + fn as parameters) plus a concrete
# hook built on it. Repos wrap the data layer this way, and matching only the bare
# library names reports ZERO queries on such a codebase -- so syncRisks comes back
# empty because nothing was found, not because the app is clean.
mkdir -p "$TMP/src/lib" "$TMP/app/invoices"
cat > "$TMP/src/lib/api-hooks.ts" <<'TS'
import { useMutation, useQuery } from '@tanstack/react-query'
export function useApiQuery(key: unknown[], fn: () => Promise<unknown>) {
  return useQuery({ queryKey: key, queryFn: fn })
}
export function useQueuedWrite(key: unknown[], fn: (b: unknown) => Promise<unknown>) {
  return useMutation({ mutationKey: key, mutationFn: fn })
}
TS
cat > "$TMP/app/invoices/page.tsx" <<'TSX'
'use client'
import { useApiQuery, useQueuedWrite } from '@/src/lib/api-hooks'
import { createInvoice, listInvoices } from '@/src/api/invoices'
export default function InvoicesPage() {
  const { data, isError } = useApiQuery(['invoices'], listInvoices)
  const add = useQueuedWrite(['invoices'], createInvoice)
  if (isError) return <p>failed</p>
  if (!(data as unknown[])?.length) return <p>No invoices yet</p>
  return <button onClick={() => add.mutate({})}>Add</button>
}
TSX
mkdir -p "$TMP/src/api"
cat > "$TMP/src/api/invoices.ts" <<'TS'
import axios from 'axios'
export async function listInvoices() { return axios.get('/api/invoices') }
export async function createInvoice(b: unknown) { return axios.post('/api/invoices', b) }
TS

# PLANTED: unread-query-error, unread-query-loading (bare useQuery, result not
# returned, error/loading never read) and -- because this page fetches data with
# no error.tsx/loading.tsx anywhere in its segment chain -- no-error-boundary
# and no-loading-boundary.
mkdir -p "$TMP/app/widgets"
cat > "$TMP/app/widgets/page.tsx" <<'TSX'
'use client'
import { useQuery } from '@tanstack/react-query'
export default function WidgetsPage() {
  const { data } = useQuery({ queryKey: ['widgets'], queryFn: () => fetch('/api/widgets') })
  return <div>{((data as unknown[]) ?? []).length} widgets</div>
}
TSX

# PLANTED: derived-state-in-useState, stale-closure, effect-fetch-without-abort,
# unstable-context-value, unsanitized-html. One instance each.
mkdir -p "$TMP/src/components"
cat > "$TMP/src/components/widgets.tsx" <<'TSX'
import React, { useEffect, useState, createContext } from 'react'
const ThemeContext = createContext({})
export function NameBadge(props: { name: string }) {
  const [name] = useState(props.name)
  return <span>{name}</span>
}
// MUST STAY SILENT: the canonical correct []-deps effect. `online` appears ONLY
// inside string literals passed to addEventListener, and setOnline is a stable
// setter — there is no captured state here. Flagging this shape made the rule
// fire on the single most common correct use of an empty dep array.
export function OnlineBadge() {
  const [online, setOnline] = useState(true)
  useEffect(() => {
    const update = () => setOnline(navigator.onLine)
    window.addEventListener('online', update)
    window.addEventListener('offline', update)
    return () => {
      window.removeEventListener('online', update)
      window.removeEventListener('offline', update)
    }
  }, [])
  return <span>{online ? 'on' : 'off'}</span>
}
export function Ticker() {
  const [count, setCount] = useState(0)
  useEffect(() => {
    const t = setInterval(() => console.log(count), 1000)
    return () => clearInterval(t)
  }, [])
  useEffect(() => {
    fetch('/api/widgets').then((r) => r.json()).then(() => setCount((c) => c + 1))
  }, [])
  return (
    <ThemeContext.Provider value={{ mode: 'dark' }}>
      <div dangerouslySetInnerHTML={{ __html: (window as any).comment }} />
    </ThemeContext.Provider>
  )
}
// MUST STAY SILENT: verify-ignore is window-scoped -- it silences only this
// marked occurrence, not the whole file, so the unmarked sink above still fires.
export function ServerEscaped({ html }: { html: string }) {
  // verify-ignore: unsanitized-html -- escaped in api/render.go before it ships
  return <div dangerouslySetInnerHTML={{ __html: html }} />
}
// MUST STAY SILENT, and with NO marker: a <style> tag takes CSS text, not markup.
// This is shadcn/ui's chart.tsx shape verbatim, so it ships in a large share of
// real repos; flagging it was a false P0 in 2 of 2 measured.
export function ChartStyle({ css }: { css: string }) {
  return <style dangerouslySetInnerHTML={{ __html: css }} />
}
TSX

# PLANTED: external-store-without-sync, prototype-pollution-shape.
cat > "$TMP/src/lib/legacy.ts" <<'TS'
export function watch(store: { subscribe: (f: () => void) => void; getState: () => unknown }, render: (s: unknown) => void) {
  store.subscribe(() => render(store.getState()))
}
export function applyRemote(config: Record<string, unknown>, raw: string) {
  Object.assign(config, JSON.parse(raw))
}
TS

# PLANTED: the generated-client shapes. Every one of these silently produced a
# WRONG-BUT-GREEN inventory before it was covered here, and none of them fails
# loudly -- they just make findings disappear, which is the worst shape of bug
# this suite exists to catch.
#
#  1. UPPERCASE http verbs (openapi-fetch and every generated client). A
#     lowercase-only endpoint matcher resolved the endpoint of NONE of them, so
#     resourceMatrix came back with 1 entry on a 145-query app and every sync
#     risk downgraded itself to "could not determine what goes stale".
#  2. A GET wrapped in useMutation (open-a-pdf, start-a-download). It writes
#     nothing, so it has no blast radius and must not be filed as a sync risk.
#  3. An AMBIENT resource -- one that most routes read. `auth` read by 30 of 57
#     routes is not an entity, and "this write leaves 30 routes stale" is a
#     denominator failure, not a finding.
# The two hook families live in SEPARATE modules on purpose. The import walk
# attributes every hook in a module to every route that imports it, so one
# grab-bag module would make all 13 routes read both entities -- and the narrow
# blast radius this fixture exists to assert would become ambient by accident.
mkdir -p "$TMP/src/hooks"
cat > "$TMP/src/hooks/use-taxdocs.ts" <<'TS'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/src/api/client'
export function useTaxDocs() {
  return useQuery({ queryKey: ['taxdocs'], queryFn: async () => {
    const { data } = await apiClient.GET('/v1/taxdocs'); return data } })
}
export function useCreateTaxDoc() {
  return useMutation({ mutationKey: ['taxdocs'], mutationFn: async (body: unknown) => {
    const { data } = await apiClient.POST('/v1/taxdocs', { body }); return data } })
}
export function useOpenTaxDocPdf() {
  return useMutation({ mutationKey: ['taxdocs', 'pdf'], mutationFn: async ({ id }: { id: string }) => {
    const { data } = await apiClient.GET('/v1/taxdocs/{id}/pdf', { params: { path: { id } } }); return data } })
}
export function usePutTaxDocLimit() {
  const qc = useQueryClient()
  return useMutation({ mutationKey: ['taxdocs', 'limit'], mutationFn: async ({ id }: { id: string }) => {
      const { data } = await apiClient.PUT('/v1/taxdocs/{id}/limit/{year}', { params: { path: { id } } }); return data },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['limit', 'board'] }) } })
}
TS
# The ambient-by-SHARE plant. Its resource is deliberately NOT one of the
# ambient-by-NAME spellings, so the two demotions stay separately provable: if
# this used `session`, the name rule would carry it and the share rule could rot
# undetected.
cat > "$TMP/src/hooks/use-session.ts" <<'TS'
import { useMutation, useQuery } from '@tanstack/react-query'
import { apiClient } from '@/src/api/client'
export function useSession() {
  return useQuery({ queryKey: ['workspace'], queryFn: async () => {
    const { data } = await apiClient.GET('/v1/workspace/me'); return data } })
}
export function useRefreshSession() {
  return useMutation({ mutationKey: ['workspace'], mutationFn: async () => {
    const { data } = await apiClient.POST('/v1/workspace/refresh'); return data } })
}
// PLANTED: ambient by NAME on TWO readers, far under the share threshold. A sign-in
// does not leave a view stale, it replaces the principal and the tree remounts.
// Measured: 4 of 7 P1 sync risks on a real repo were exactly this shape.
export function useSignIn() {
  return useMutation({ mutationFn: async () => {
    const { data } = await apiClient.POST('/v1/auth/login'); return data } })
}
// PLANTED, MUST BE WAIVED: a genuine-looking risk the repo has already triaged.
export function usePushSegment() {
  // verify-ignore: sync-risk -- pushes to Mailchimp; no segment list exists here
  return useMutation({ mutationFn: async () => {
    const { data } = await apiClient.POST('/v1/segments/push'); return data } })
}
TS
# One route that renders the taxdocs entity (a real, narrow blast radius) ...
mkdir -p "$TMP/app/taxdocs"
cat > "$TMP/app/taxdocs/page.tsx" <<'TSX'
'use client'
import { useTaxDocs, useCreateTaxDoc, useOpenTaxDocPdf } from '@/src/hooks/use-taxdocs'
export default function TaxDocsPage() {
  const { data, isError, isLoading } = useTaxDocs()
  const add = useCreateTaxDoc(); const open = useOpenTaxDocPdf()
  if (isLoading) return <p>Loading</p>
  if (isError) return <p>failed</p>
  if (!(data as unknown[])?.length) return <p>No tax documents yet</p>
  return <div><button onClick={() => add.mutate({})}>Add</button>
    <button onClick={() => open.mutate({ id: 'x' })}>PDF</button></div>
}
TSX
# ... and TWELVE routes that all read the session, making it ambient.
for n in 1 2 3 4 5 6 7 8 9 10 11 12; do
  mkdir -p "$TMP/app/amb$n"
  cat > "$TMP/app/amb$n/page.tsx" <<'TSX'
'use client'
import { useSession, useRefreshSession, useSignIn, usePushSegment } from '@/src/hooks/use-session'
export default function AmbientPage() {
  const { data, isError, isLoading } = useSession()
  const refresh = useRefreshSession(); const login = useSignIn(); const push = usePushSegment()
  void login; void push;
  if (isLoading) return <p>Loading</p>
  if (isError) return <p>failed</p>
  if (!data) return <p>No session</p>
  return <button onClick={() => refresh.mutate()}>Refresh</button>
}
TSX
done
cat > "$TMP/src/api/client.ts" <<'TS'
export const apiClient = {
  GET: async (_p: string, _o?: unknown) => ({ data: [] as unknown[] }),
  POST: async (_p: string, _o?: unknown) => ({ data: {} }),
  PUT: async (_p: string, _o?: unknown) => ({ data: {} }),
}
TS

# PLANTED, MUST STAY SILENT: a design-lab tree. Committed, shaped exactly like the
# app, reachable from no route. On a real repo these produced 18 of 19 findings.
mkdir -p "$TMP/src/_proto"
cat > "$TMP/src/_proto/lab.jsx" <<'JSX'
export function Lab({ rows }) {
  return <ul>{rows.map((r, index) => <li key={index}>{r.name}</li>)}</ul>
}
JSX

# PLANTED, MUST BE WAIVED (not merely absent): the same defect the triage of a
# real repo proved harmless, marked at the line. Proves the waiver reaches a rule
# it was not written for, and that a waived finding is still counted and reported.
mkdir -p "$TMP/src/components"
cat > "$TMP/src/components/legend.jsx" <<'JSX'
export function Legend({ swatches }) {
  // verify-ignore: index-as-list-key -- fixed-length constant, never reordered
  return <ul>{swatches.map((s, index) => <li key={index}>{s}</li>)}</ul>
}
JSX

fail=0
INV="$TMP/inventory.json"
node "$SKILL/bin/inventory.mjs" "$TMP" --stdout > "$INV" || { echo "FAIL: inventory.mjs crashed"; exit 1; }
node "$SKILL/bin/classify.mjs" "$TMP" --json > "$TMP/classify.json" || true

echo "--- inventory"
node -e '
const j = require(process.argv[1]); let bad = 0;
const check = (label, ok, got) => { console.log((ok ? "  ok    " : "  MISS  ") + label + "  (" + got + ")"); if (!ok) bad = 1; };
check("routes found",           j.counts.routes >= 2,        j.counts.routes);
check("queries found",          j.counts.queries >= 1,       j.counts.queries);
check("mutations found",        j.counts.mutations >= 1,     j.counts.mutations);
check("resource matrix built",  Object.keys(j.resourceMatrix).includes("contacts"), Object.keys(j.resourceMatrix).join(","));
check("sync risk detected",     j.syncRisks.length >= 1,     j.syncRisks.length);
const wrongKey = j.syncRisks.find((r) => r.kind === "partial-invalidation");
check("wrong-key invalidation caught", !!wrongKey && wrongKey.invalidates.includes("invoices"),
      wrongKey ? wrongKey.detail.slice(0, 90) : "none");
check("right-key invalidation NOT flagged",
      !j.syncRisks.some((r) => (r.hook || "") === "useRenameContact"),
      j.syncRisks.map((r) => r.hook).join(",") || "none");
check("wrapper query counted",  j.routes.some((r) => r.queries.some((x) => x.via === "useApiQuery")),
      j.routes.flatMap((r) => r.queries).filter((x) => x.via).map((x) => x.via).join(",") || "none");
check("wrapper mutation counted", j.routes.some((r) => r.mutations.some((x) => x.via === "useQueuedWrite")),
      j.routes.flatMap((r) => r.mutations).filter((x) => x.via).map((x) => x.via).join(",") || "none");
check("blast radius resolved",  (j.syncRisks[0] && j.syncRisks[0].staleRoutes || []).length >= 2,
      JSON.stringify((j.syncRisks[0] || {}).staleRoutes));
// Generated-client shapes. Each of these was a silent green before it was planted.
const risk = (h) => j.syncRisks.find((r) => (r.hook || "") === h);
check("UPPERCASE verb endpoint resolved",
      Object.keys(j.resourceMatrix).includes("taxdocs"),
      Object.keys(j.resourceMatrix).slice(0, 8).join(",") || "none");
check("uppercase-POST write flagged with its blast radius",
      !!risk("useCreateTaxDoc") && (risk("useCreateTaxDoc").staleRoutes || []).length >= 1,
      risk("useCreateTaxDoc") ? risk("useCreateTaxDoc").severity + " " + JSON.stringify(risk("useCreateTaxDoc").staleRoutes) : "none");
check("GET wrapped in useMutation NOT a sync risk", !risk("useOpenTaxDocPdf"),
      risk("useOpenTaxDocPdf") ? risk("useOpenTaxDocPdf").detail.slice(0, 70) : "absent");
check("nested write that invalidates its INNER segment NOT flagged",
      !risk("usePutTaxDocLimit"),
      risk("usePutTaxDocLimit") ? risk("usePutTaxDocLimit").detail.slice(0, 90) : "absent");
check("ambient by SHARE not filed as P1",
      !!risk("useRefreshSession") && risk("useRefreshSession").severity !== "P1" && risk("useRefreshSession").unresolved === true,
      risk("useRefreshSession") ? risk("useRefreshSession").severity + " stale=" + JSON.stringify(risk("useRefreshSession").staleRoutes) : "none");
// A session write on TWO readers clears neither share threshold. The share rule
// alone let 4 of the 7 P1s on a real repo through as auth false positives.
check("ambient by NAME not filed as P1, even on few readers",
      !!risk("useSignIn") && risk("useSignIn").severity !== "P1" && risk("useSignIn").unresolved === true,
      risk("useSignIn") ? risk("useSignIn").severity + " stale=" + JSON.stringify(risk("useSignIn").staleRoutes) : "none");
check("verify-ignore waives a sync risk, and says it did",
      !risk("usePushSegment")
        && (j.syncRisksWaived || []).some((r) => r.hook === "usePushSegment")
        && j.counts.syncRisksWaived === 1,
      "waived=" + JSON.stringify((j.syncRisksWaived || []).map((r) => r.hook)));
process.exit(bad);
' "$INV" || fail=1

echo "--- classifier (every rule it defines, one planted instance each)"
for rule in missing-empty-state index-as-list-key runtime-env-in-client-code \
            server-state-in-client-store submit-without-pending-guard \
            unread-query-error unread-query-loading derived-state-in-useState \
            effect-fetch-without-abort stale-closure unstable-context-value \
            external-store-without-sync unsanitized-html prototype-pollution-shape \
            no-error-boundary no-loading-boundary; do
  if grep -q "\"rule\": \"$rule\"" "$TMP/classify.json"; then echo "  ok    $rule"
  else echo "  MISS  $rule  <- planted, rule did not fire"; fail=1; fi
done
# The list above must BE the rule set: a rule added to classify.mjs without a
# plant here is a rule nobody has watched fail.
nrules=$(grep -oE "add\('[a-zA-Z-]+'" "$SKILL/bin/classify.mjs" | sort -u | wc -l | tr -d ' ')
if [ "$nrules" = "16" ]; then echo "  ok    16 rules defined, 16 asserted"
else echo "  FAIL  classify.mjs defines $nrules distinct rules but this selftest asserts 16 -- plant the new one"; fail=1; fi

# Known false positives that must stay silent. A rule is only worth reading if
# it is quiet on correct code; each entry here is a shape that once fired.
if grep -q '"file": "src/components/widgets.tsx"' "$TMP/classify.json" && \
   node -e '
     const f = require("'"$TMP"'/classify.json").findings || [];
     const bad = f.filter((x) => x.rule === "stale-closure" && /OnlineBadge/.test(x.message || ""));
     process.exit(bad.length ? 1 : 0);
   ' 2>/dev/null; then :; fi
if node -e '
  const f = require("'"$TMP"'/classify.json").findings || [];
  const hits = f.filter((x) => x.rule === "stale-closure");
  // Exactly ONE stale-closure: the planted Ticker. The OnlineBadge counter-example
  // must not add a second.
  process.exit(hits.length === 1 ? 0 : 1);
'; then echo "  ok    stale-closure quiet on the correct subscribe/unsubscribe shape"
else echo "  FAIL  stale-closure fired on a correct []-deps effect (string literal read as an identifier)"; fail=1; fi

if node -e '
  const f = require("'"$TMP"'/classify.json").findings || [];
  const hits = f.filter((x) => x.rule === "unsanitized-html");
  // Exactly ONE: the unmarked window.comment sink. Neither the marked
  // ServerEscaped sink (verify-ignore, window-scoped -- not a whole-file bypass)
  // nor the unmarked ChartStyle <style> tag may add a second.
  process.exit(hits.length === 1 ? 0 : 1);
'; then echo "  ok    verify-ignore is window-scoped, and <style> CSS is not an HTML sink"
else echo "  FAIL  unsanitized-html: waiver leaked to the whole file, or <style> CSS was flagged as markup"; fail=1; fi

# The waiver has to work for EVERY rule, not just the one it was born in: a
# finding proved false in a written triage that comes back at P1 on the next run
# is how a marathon spends its budget re-litigating instead of fixing.
if node -e '
  const r = require("'"$TMP"'/classify.json");
  const w = r.waived || [];
  process.exit(w.length === 2
    && w.some((x) => x.rule === "unsanitized-html")
    && w.some((x) => x.rule === "index-as-list-key")
    && (r.findings || []).every((x) => !x.waived) ? 0 : 1);
'; then echo "  ok    verify-ignore waives any rule, and waived findings are reported, not vanished"
else echo "  FAIL  the generic verify-ignore waiver did not cover both planted rules"; fail=1; fi

# Every finding's file:line must point at the line the defect is ON. Blanking a
# multi-line /* */ down to spaces once collapsed its newlines and reported every
# finding below a JSDoc header N lines early. Checked against the file on disk, so
# it cannot be satisfied by a matching-but-wrong index. Waived findings included:
# the waiver reads a window around `line`, so a drifting line silently un-waives.
if node -e '
  const fs = require("fs"), path = require("path");
  const r = require("'"$TMP"'/classify.json");
  const NEEDLE = { "unsanitized-html": /dangerouslySetInnerHTML|\.innerHTML\s*=/,
                   "index-as-list-key": /key=\{\s*(index|i)\b/ };
  let bad = [];
  for (const f of [...(r.findings || []), ...(r.waived || [])]) {
    const re = NEEDLE[f.rule]; if (!re) continue;
    const L = fs.readFileSync(path.join(r.root, f.file), "utf8").split("\n");
    if (!re.test(L[f.line - 1] ?? "")) bad.push(f.file + ":" + f.line + " (" + f.rule + ")");
  }
  if (bad.length) { console.error("      " + bad.join("  ")); process.exit(1); }
'; then echo "  ok    reported file:line lands on the defect, under block comments"
else echo "  FAIL  file:line drifted -- decomment is eating newlines again"; fail=1; fi

# Design-lab trees are committed, so .gitignore does not cover them, and they are
# shaped exactly like the app, so every rule fires in them. Reachable from no
# route, though, so nothing found there can break anything. On a real repo they
# were 18 of 19 findings -- a report that is 95% noise is one nobody opens twice.
if node -e '
  const f = require("'"$TMP"'/classify.json").findings || [];
  const lab = f.filter((x) => /(^|\/)_proto(\/|$)/.test(x.file));
  if (lab.length) { console.error("      " + lab.length + " finding(s) inside _proto/: " + lab[0].file); process.exit(1); }
  // ...and the identical defect in real source must STILL be reported, or this
  // is not an exclusion, it is the rule having quietly stopped working.
  process.exit(f.some((x) => x.rule === "index-as-list-key") ? 0 : 1);
'; then echo "  ok    design-lab tree excluded, index-key rule still fires in real source"
else echo "  FAIL  _proto/ leaked into findings, or the index-key rule stopped firing entirely"; fail=1; fi

# ---------------------------------------------------------------------------
# MONOREPO regression. Reproduces the exact shape that reported modules:1 and
# zero queries on a real app: no tsconfig at the repo root, paths declared in
# apps/web/tsconfig.json, the route three hops from its data, and the wrapper
# typed with NESTED generics between the identifier and the paren.
MONO="$(mktemp -d)"
trap 'rm -rf "$TMP" "$MONO"' EXIT
mkdir -p "$MONO/apps/web/src/app/(app)/accounts" "$MONO/apps/web/src/components/accounts" "$MONO/apps/web/src/hooks" "$MONO/apps/web/src/lib"
cat > "$MONO/package.json" <<'JSON'
{ "name": "mono-root", "private": true, "workspaces": ["apps/*"] }
JSON
cat > "$MONO/apps/web/tsconfig.json" <<'JSON'
{ "compilerOptions": { "baseUrl": ".", "paths": { "@/*": ["./src/*"] } } }
JSON
cat > "$MONO/apps/web/src/lib/api-hooks.ts" <<'TS'
import { useQuery } from '@tanstack/react-query'
type GetResponse<P> = { data: P }
export function useApiQuery<Path, Data>(key: unknown[], fn: () => Promise<Data>) {
  return useQuery<GetResponse<Path>, Error, Data, unknown[]>({ queryKey: key, queryFn: fn })
}
TS
cat > "$MONO/apps/web/src/hooks/use-accounts.ts" <<'TS'
import axios from 'axios'
import { useApiQuery } from '@/lib/api-hooks'
export const listAccounts = async () => axios.get('/v1/accounts')
export function useAccounts() { return useApiQuery(['accounts'], listAccounts) }
TS
cat > "$MONO/apps/web/src/components/accounts/accounts-route.tsx" <<'TSX'
import { useAccounts } from '@/hooks/use-accounts'
export function AccountsRoute() { const { data } = useAccounts(); return <div>{String(data)}</div> }
TSX
cat > "$MONO/apps/web/src/app/(app)/accounts/page.tsx" <<'TSX'
'use client'
import { AccountsRoute } from '@/components/accounts/accounts-route'
export default function Page() { return <AccountsRoute /> }
TSX

cat >> "$TMP/src/api/hooks.ts" <<'TS'
// Hierarchical children of ['contacts'] -- idiomatic TanStack, NOT duplicates:
// invalidating the parent covers them.
export function useContactOrders(id: string) {
  return useQuery({ queryKey: ['contacts', id, 'orders'], queryFn: () => fetch('/api/contacts/' + id + '/orders') })
}
export function useContactFavorites(id: string) {
  return useQuery({ queryKey: ['contacts', id, 'order-favorites'], queryFn: () => fetch('/api/contacts/' + id + '/favorites') })
}
TS
node "$SKILL/bin/inventory.mjs" "$TMP" --stdout > "$INV"
echo "--- key hierarchy vs duplicate source"
node -e '
const j = require(process.argv[1]);
const hits = j.duplicateSources.map((d) => d.endpoint).join(",");
if (j.duplicateSources.length === 0) console.log("  ok    hierarchical keys not flagged as duplicate sources");
else { console.log("  FALSE-POSITIVE  key hierarchy flagged: " + hits); process.exit(1); }
' "$INV" || fail=1

echo "--- monorepo traversal"
node "$SKILL/bin/inventory.mjs" "$MONO" --stdout > "$MONO/inv.json" || { echo "  FAIL: crashed"; fail=1; }
node -e '
const j = require(process.argv[1]); let bad = 0;
const check = (l, ok, got) => { console.log((ok ? "  ok    " : "  MISS  ") + l + "  (" + got + ")"); if (!ok) bad = 1; };
const r = j.routes.find((x) => x.path === "/accounts");
check("route found under apps/web",  !!r,                 j.routes.map((x) => x.path).join(",") || "none");
check("import walk left the page",   (r?.modules ?? 0) > 1, r?.modules ?? 0);
check("query found 3 hops out",      (r?.queries.length ?? 0) >= 1, r?.queries.length ?? 0);
check("generic wrapper matched",     r?.queries.some((q) => q.via === "useApiQuery"), (r?.queries ?? []).map((q) => q.via ?? "bare").join(","));
check("entity resolved",             r?.entities.includes("accounts"), (r?.entities ?? []).join(",") || "none");
check("endpoint resolved",           r?.queries.some((q) => q.endpoint === "/v1/accounts"), (r?.queries ?? []).map((q) => q.endpoint).join(","));
process.exit(bad);
' "$MONO/inv.json" || fail=1

echo
if [ "$fail" -eq 0 ]; then echo "STATIC SELFTEST PASS"; else echo "STATIC SELFTEST FAIL"; fi
exit "$fail"
