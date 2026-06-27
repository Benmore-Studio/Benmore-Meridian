# Durable annotations & highlights (pattern)

An **annotation** is a span of *meaning* a human or model marks on a document — a
highlighted clause, a defined term, a risk flag, a reviewer note. It must survive
re-OCR, re-pagination, and new document versions. A highlight that vanishes when
the document is re-rendered is a correctness and trust failure (a lawyer's risk
flag silently gone), so annotations are first-class, long-lived objects — not
transient UI decoration.

Annotations are adjacent to provenance's `source_ref`
([`provenance.md`](provenance.md)) — both locate a region via `span`/anchors — but
they are their own concern. A `source_ref` is born with a value and dies with it;
an annotation is an independently stored object with its own lifecycle, often
user-authored, frequently overlapping, and authoritative across versions. The
locked shapes (`Annotation`, `SourceRef`, `Span`) live in
[`envelope.openapi.yaml`](envelope.openapi.yaml) — this file is the discipline for
using them.

## Contents

- Annotation vs provenance `source_ref`
- Why pixel/offset anchoring breaks (and the fix)
- The re-anchoring algorithm (the core)
- Orphaning — never silently drop
- Overlapping & nested annotations
- Categories & semantics
- Collaboration & multi-user
- Round-trip export
- Annotations across versions
- Storage note
- Anti-patterns
- Review checklist

## Annotation vs provenance `source_ref`

Both reference a region through a `Span` of stable anchors, so it is tempting to
treat them as the same thing. They are not:

| | `source_ref` (on a value) | `Annotation` |
|---|---|---|
| Lifetime | born with the value, dies with it | durable, independently stored |
| Audience | audit trail / internal | user-facing highlight |
| Lifecycle | none (immutable fact) | created → re-anchored → orphaned/resolved |
| Overlap | one per value | many, freely overlapping |
| Author | the producing tool | a human **or** a model |

An annotation carries `origin` exactly like a value does, because **a model can
author one**: a detector that flags unusual indemnity language emits an
`Annotation{category: "risk", origin.method: "detector:indemnity", author:
<model_version>}` the same way it emits a value. A reviewer highlighting a clause
emits `Annotation{author: <human id>, origin.method: "human"}`. Both are
first-class; the difference is authority (see Categories below), not type.

## Why pixel/offset anchoring breaks (and the fix)

Two tempting representations both rot:

- **Page + pixel bbox.** Store the highlight as `{page: 4, bbox: [...]}` and it
  breaks the moment the document is re-rendered at a new DPI, or a new version
  reflows the text — the box now covers the wrong words (or whitespace).
- **Character offset.** Store it as `chars: [1840, 1902]` into the normalized
  text and it breaks the moment text is *inserted above it* — every offset
  downstream shifts.

The fix: anchor annotations to **stable token-id spans** in the canonical document
model (see [`document-model.md`](document-model.md)). `span.start_anchor` /
`span.end_anchor` are ids of tokens, not positions, so inserting text elsewhere
does not move them. This is the *whole reason* highlights survive edits.

`regions[]` (the per-page bboxes on the `Span`) are a **derived, cached rendering**
of the anchor span — what the UI draws. They are recomputed from the anchors
whenever the document is rendered; they are never the source of truth. `chars` is
a convenience hint only (fast text slicing), explicitly marked FRAGILE in the
schema — re-anchor on read if it drifts.

> Secondary-language note: in TS the `Span` is an `interface` with
> `regions?: Region[]`; in Python a pydantic model with
> `anchor_confidence: confloat(ge=0, le=1)`. The rule is identical everywhere:
> anchors are truth, `regions[]` and `chars` are derived/hint.

## The re-anchoring algorithm (the core)

When a document is re-OCR'd or a new version arrives, token ids may not resolve
verbatim. **Re-anchoring** relocates the span and scores the result. The classic
robust-anchoring approach: store the annotated *text* plus a little surrounding
context, and relocate by best match.

1. **Exact** — try the stored `start_anchor`/`end_anchor` token ids directly. If
   they still resolve in the new model, confidence ≈ 1.0. Done.
2. **Content fallback** — they didn't resolve. Match the span's *normalized text*
   (the quote) against the new model using prefix/suffix context windows: find the
   location where the quote, bracketed by its remembered before/after context,
   best matches. Fuzzy/contextual, tolerant of minor OCR noise.
3. **Score** — set `anchor_confidence` from match quality (exact text + exact
   context → high; fuzzy text or shifted context → lower). Stamp the *new* span
   (fresh anchors + recomputed `regions[]`) and the confidence.

```go
// reanchor relocates an annotation's span onto doc (a freshly re-OCR'd model or
// a new version). Returns the new span and how confident the match is.
func reanchor(ann Annotation, doc Doc) (Span, float64) {
    old := ann.SourceRef.Span

    // (a) exact token-id match — cheap, and ~1.0 when it works.
    if s, ok := doc.ResolveAnchors(old.StartAnchor, old.EndAnchor); ok {
        s.Regions = doc.RenderRegions(s) // recompute cached boxes
        return s, 1.0
    }

    // (b) content fallback: relocate by the quoted text + surrounding context.
    quote := doc.NormalizeText(old)                    // the annotated text
    pre, suf := ann.Context.Prefix, ann.Context.Suffix // remembered windows
    hit := doc.BestMatch(quote, pre, suf)              // fuzzy/contextual search

    s := Span{StartAnchor: hit.Start, EndAnchor: hit.End}
    s.Regions = doc.RenderRegions(s)
    return s, hit.Score // (c) match quality → anchor_confidence
}
```

Re-anchoring runs on every re-OCR and on every new version (below). It never
mutates the *original* recorded span in place without keeping the prior value —
you want the history of where the highlight has lived.

## Orphaning — never silently drop

If re-anchoring confidence falls below a threshold, the annotated text was deleted
or changed too much to relocate honestly. **Do not drop the annotation.** Set
`status = orphaned`, preserve the original span and the last-known text, and
surface it for human re-review.

A silently-dropped highlight is a correctness/trust failure: the reviewer believes
their risk flag is still on the document. Orphaning makes the loss *visible and
actionable* instead.

Critically, orphaning is **information, not an error to hide**. Cross-reference
[`comparison-and-versioning.md`](comparison-and-versioning.md): when a new version
deletes the very clause a reviewer flagged, the annotation *should* orphan — that
tells the reviewer "the thing you flagged was removed," which is exactly what they
need to know. The orphaned annotation, with its preserved text, is the evidence of
what used to be there.

## Overlapping & nested annotations

One sentence routinely carries several overlapping highlights: a `defined_term`
inside an `obligation` inside a `risk`-flagged clause. The model **must** support
arbitrary overlap. This is why annotations are independent objects keyed by span —
**not** a single-layer markup over the text. Do not force a tree; overlaps are not
strictly nested (a defined term can straddle two obligations), and a tree cannot
represent partial overlap.

- **Rendering.** Stack by z-order; blend highlight colors by category so an
  overlapped region reads as "more than one thing here." A subtle left-edge bar
  per category, or progressively darker tint per layer, both work.
- **Resolution.** Clicking an overlapped region offers *all* annotations covering
  that point (a small list/popover), not just the topmost — the user picks which
  one to read or act on.

Because each annotation re-anchors independently, an edit that splits a sentence
re-anchors each overlapping highlight on its own; they don't have to move together.

## Categories & semantics

`category` drives color and behavior:

- `defined_term` — links the use to its definition. This is the same target as a
  `Relation` claim of `rel_type: term_use`; the annotation is the *visible* layer
  over that logical link (cross-ref logical ids in
  [`comparison-and-versioning.md`](comparison-and-versioning.md)).
- `cross_reference` — links to the target it points at ("as defined in §2.1").
- `obligation` — a duty owed; often paired with a `Relation` to the bound party.
- `risk` — a flag for scrutiny.
- `user_note` — a free reviewer comment.

**Authority differs by author.** Model-authored annotations (the indemnity
detector) are *review-first*: shown as suggestions, carrying the detector's
`anchor_confidence` and its `origin`. Human annotations are *authoritative*. When
a human confirms or dismisses a model-suggested highlight, that decision is a
label — it feeds the same loop as every other verification
([`verification-flywheel.md`](verification-flywheel.md)). The flywheel turns "the
risk detector's suggestions" into measured precision over time.

## Collaboration & multi-user

Multiple reviewers annotate the same version concurrently. Because annotations are
independent objects, concurrent creates **do not conflict** — there is no shared
document buffer to merge. Each carries `author`, so the UI attributes every
highlight. Replies and resolution form a small thread hung off the annotation
(`note` plus child notes); `status: resolved` closes it.

Access control is real but light here: who may see or edit which annotations
(privileged legal notes vs shared highlights) is an authorization concern —
forward-ref [`admissibility-and-security.md`](admissibility-and-security.md).

## Round-trip export

Highlights must export back onto a shareable artifact:

- **Burned-in PDF** — colored highlights + margin notes rendered *from*
  `regions[]` directly onto the page.
- **Sidecar** — a W3C Web Annotation document, or PDF annotation objects, kept
  alongside the file.

The export is only as accurate as the anchor→region computation: garbage
`regions[]` produce misplaced boxes. And exported, burned-in highlights are
**flattened** — they lose their anchors, so they can no longer re-anchor when the
document changes. Always keep the live, anchored copy as the source of truth; the
burned PDF is a snapshot for sharing, never the system of record.

## Annotations across versions

This is the payoff of content-anchoring and the comparison layer working
together. When a new version arrives
([`comparison-and-versioning.md`](comparison-and-versioning.md)), carry every
annotation forward by re-anchoring it onto the new version:

- **Clause moved.** The highlight *follows the moved text* — because it anchors to
  content, the content fallback (or the alignment's `logical_id`) relocates it to
  wherever the clause went. The reviewer's flag stays on the right clause.
- **Clause edited slightly.** Re-anchors with a lower `anchor_confidence`,
  flagging it for a glance.
- **Clause deleted.** Re-anchoring fails → `status = orphaned`, surfacing "the
  thing you flagged was removed."

Without content-anchoring this is impossible; without the comparison/alignment
layer it is guesswork. Together they make a reviewer's work durable across the
document's whole revision history.

## Storage note

Annotations are their own table/store (language-/engine-agnostic), keyed by
`(doc_id, version-range, anchor span)` and independently queryable by `category`,
`author`, and `status`. Promote to indexed columns the fields you filter on —
`doc_id`, `category`, `status`, `author` — and keep the full `Annotation` envelope
(span, regions, note, anchor_confidence, origin) as JSON. This mirrors the
provenance storage note ([`provenance.md`](provenance.md)): index what you query,
JSON the rest. "Show every active `risk` annotation on this doc authored by a
model with `anchor_confidence < 0.8`" is a routine triage query.

## Anti-patterns

**Pixel bbox as truth.** Highlight stored as page+bbox → breaks on re-render/new
DPI/reflow → store anchors; treat `regions[]` as a derived cache recomputed from
them.

**Character-offset anchoring.** Highlight stored as `chars` offsets → breaks when
text is inserted above → anchor to stable token ids; keep `chars` as a hint only.

**Silent drop.** An annotation that won't re-anchor just disappears → the
reviewer's flag is gone without trace → set `status = orphaned`, preserve original
span + last-known text, surface for re-review.

**Single-layer markup.** Overlapping highlights forced into one non-overlapping
layer (or a tree) → can't represent a term inside an obligation inside a risk
clause → keep annotations as independent objects keyed by span; allow arbitrary
overlap.

**Burned-in-only export.** Highlights exist only as flattened boxes in a shared
PDF → re-anchoring is lost forever → keep the live anchored copy as source of
truth; export is a snapshot.

**No `anchor_confidence`.** Re-anchored spans stamped without a score → can't tell
solid anchors from fuzzy guesses → always record match quality, and let it drive
orphaning and triage.

## Review checklist

- [ ] Are annotations stored as **independent, durable objects** (their own
      store), not transient UI state or value-bound `source_ref`s?
- [ ] Is every annotation anchored to **stable token-id spans**, with `regions[]`
      treated as a derived cache and `chars` as a hint only?
- [ ] Does re-anchoring try **exact token match, then content+context fallback**,
      and stamp a fresh span?
- [ ] Is `anchor_confidence` recorded from match quality on every re-anchor?
- [ ] Do low-confidence re-anchors **orphan** (preserving original span + text)
      rather than silently drop?
- [ ] Can annotations **overlap arbitrarily**, with stacked rendering and
      click-to-resolve-all, and no forced tree?
- [ ] Do model-authored annotations carry `origin` + `author` and feed the
      flywheel as suggestions, with human annotations authoritative?
- [ ] Do annotations **carry forward across versions** — following moved clauses,
      orphaning on deletion?
- [ ] Is the **live anchored copy** the source of truth, with burned-in/sidecar
      exports treated as snapshots?
- [ ] Is the annotation store **queryable by `category` / `status` / `author`**
      via indexed columns?
