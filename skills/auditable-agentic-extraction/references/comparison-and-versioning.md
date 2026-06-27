# Comparison and Versioning — "git for documents"

Extraction turns documents into values. Comparison turns *pairs of versions* into **changes**: a structured account of what moved between round 7 and round 8 of a contract, where each difference is itself a traceable claim. The discipline is the same one this skill applies everywhere — a diff is a *derived* claim, so it must be attributable and navigable. Every change carries source_refs into **both** versions, so a reviewer can land on the exact clause on each side and judge whether it matters. A diff the reviewer cannot trace back to both documents is unverifiable, and an unverifiable diff is worthless in negotiation work. This file builds the comparative, versioned layer on the same provenance spine described in [provenance.md](provenance.md), reusing the canonical model and stable anchors from [document-model.md](document-model.md) and the `Change` schema from [envelope.openapi.yaml](envelope.openapi.yaml).

## Contents

- [The thesis: a diff is a derived claim](#the-thesis-a-diff-is-a-derived-claim)
- [Document identity and content addressing](#document-identity-and-content-addressing)
- [The comparison pipeline as stages](#the-comparison-pipeline-as-stages)
- [Segmentation into comparable units](#segmentation-into-comparable-units)
- [Alignment: the hard problem](#alignment-the-hard-problem)
- [Stable logical ids and blame](#stable-logical-ids-and-blame)
- [Materiality classification](#materiality-classification)
- [Three-way and base diffs](#three-way-and-base-diffs)
- [Bidirectional provenance and navigation](#bidirectional-provenance-and-navigation)
- [Amendments that edit a base contract](#amendments-that-edit-a-base-contract)
- [Replay and audit](#replay-and-audit)
- [Anti-patterns](#anti-patterns)
- [Review checklist](#review-checklist)

## The thesis: a diff is a derived claim

A `Change` is not a UI decoration; it is a claim of the form "this clause was modified between version A and version B," and it obeys the same attributability rule as an extracted value. The tool that computes the change stamps `origin.method`, both source_refs, and a `confidence`. The LLM never asserts "these clauses are the same" or "this changed" by inspection — a tool produces the change and records where, on each side, the evidence lives.

The `Change` schema (see [envelope.openapi.yaml](envelope.openapi.yaml)) is the diff unit:

```
Change {
  id, logical_id, change_type (insert|delete|modify|move|format_only),
  before: SourceRef, after: SourceRef,
  materiality (substantive|minor|cosmetic),
  summary, origin, confidence
}
```

Two structural invariants follow from "navigable to both sides":

- An **insert** has no `before` (the text exists only in B).
- A **delete** has no `after` (the text exists only in A).
- Every other change_type — `modify`, `move`, `format_only` — has **both**. A change that should have both but is missing one is a one-sided artifact and must be rejected in review.

`before`/`after` are `SourceRef`s: each carries `doc_id` (required), a `version`, and a locator (`page`+`bbox`, `anchor`, `table`+`row`, or a `span` with `start_anchor`/`end_anchor`/`regions`). The reviewer clicks a change and the UI scrolls version A to `before.span` and version B to `after.span`. That round-trip is the whole product.

## Document identity and content addressing

Treat a document the way git treats a blob: hash its canonical bytes (or canonical model) into a stable `doc_id`. Re-uploading byte-identical content yields the *same* id — idempotency, the same property staged-processing relies on so a re-run is free and safe. Identity is content, not filename or upload time.

But documents are not a linear list of commits. A contract **forks** when two counterparties edit in parallel, and **merges** when their redlines are reconciled. Versions therefore form a **DAG**:

```go
// A Version is an immutable snapshot. You never mutate one in place;
// a correction produces a NEW version with new edges.
type Version struct {
    ID        string    // content hash of the canonical model
    DocID     string    // logical document this version belongs to
    Parents   []string  // version IDs — >1 means a merge
    Round     int       // negotiation round
    Author    string
    Timestamp time.Time
}

type VersionGraph struct {
    Versions map[string]Version
    Children map[string][]string // parent ID -> child IDs
}
```

> Secondary-language note (Python): `@dataclass(frozen=True) class Version: id: str; doc_id: str; parents: tuple[str, ...]; round: int`. Freeze it so "mutate in place" is a type error, not a code-review catch.
> Secondary-language note (TypeScript): `readonly` fields plus `Object.freeze` on the snapshot; model `parents: readonly string[]`.

**Immutability is the load-bearing rule.** A version is a frozen snapshot. If round 8 had a typo and you re-OCR it, you create version 8′ with an edge from 8, never overwrite 8 — otherwise every `Change` and annotation that pointed at 8 silently changes meaning and your audit trail lies.

Be honest about where the git analogy breaks. Source code is line-oriented with a canonical text; documents are not. "Lines" here are *clauses*, and there is no canonical character stream — a PDF re-export reflows whitespace, OCR varies, and two "identical" contracts can differ byte-for-byte while being legally the same. So content addressing operates over the **canonical model** ([document-model.md](document-model.md)), not raw bytes, and equality at the clause level is a *computed alignment*, not a string compare.

## The comparison pipeline as stages

Comparison reuses the staged-processing spine. Each stage is a tool that emits attributed claims; the boundaries are where you cache, replay, and route to review:

```
segment  -> align -> diff -> classify materiality -> present
```

1. **segment** — split each version's canonical model into comparable units (clauses).
2. **align** — match each unit in A to its counterpart in B (or mark unmatched).
3. **diff** — for each matched pair, compute the `Change` (or insert/delete for unmatched units).
4. **classify materiality** — tag each `Change` substantive / minor / cosmetic.
5. **present** — render the redline and the navigable change list.

The `origin.method` rungs in this file are `segment:`, `align:`, and `diff:`. They obey the same attributability rule as every rung elsewhere: each emits a tool result with `source_ref` and `confidence`.

## Segmentation into comparable units

You cannot diff two PDFs as pixel images, and you should not diff them as one giant string — a string diff over a renumbered contract reports thousands of meaningless character moves. Instead, **segment** each version into units at a chosen granularity using the canonical model's structure:

- numbering schemes — `1`, `1.1`, `1.1.1`, `(a)`, `(i)`, roman numerals;
- defined-term blocks ("Confidential Information" means …);
- table rows and cells;
- sentence boundaries inside a clause.

Each unit is a `span` with stable anchors, so it survives reflow:

```go
type Unit struct {
    Anchor    Span   // start_anchor/end_anchor into the canonical model
    Path      string // structural address, e.g. "5.2(a)"
    Text      string // normalized text for similarity, NOT for identity
    Kind      UnitKind
}

// segment is a tool: it stamps method "segment:clause-tree@v3" and a
// source_ref per unit. The LLM may suggest boundaries for messy prose,
// but the recorded unit is a tool result anchored into the model.
func Segment(doc *CanonicalDoc, g Granularity) []Unit
```

**Granularity is a knob, and you usually want two.** Clause-level units answer "what changed substantively" and keep the change list short enough to review. Word- or token-level units drive the redline rendering (the strike-through/underline). Run coarse for triage, fine for display, and link them: a clause-level `modify` owns the word-level edits inside its span.

## Alignment: the hard problem

Alignment — deciding which unit in A corresponds to which unit in B — is where naive diffs fail. The cases:

- **Renumbering.** Insert one clause at the top and every subsequent number shifts. This is **one** insert, not fifty modifies. Alignment must match by content and structure, not by number.
- **Moves.** Section 5 becomes Section 8. This is a single `move`, detected by finding a high-similarity match at a *distant* position — never `delete` + `insert`.
- **Splits and merges.** One clause becomes two (split); two collapse into one (merge). The alignment is one-to-many or many-to-one, and the change list must say so.
- **Rewording.** Same obligation, new words → `minor` or `format_only`. Changed obligation, similar words → `substantive`. Alignment finds the pair; materiality (below) judges the meaning.

The approach is a **sequence alignment / bipartite matching** over a unit-similarity score that blends text similarity, structural hints (numbering proximity, same kind, same parent), and embeddings for semantic nearness. A tool emits `align:` claims, one per matched pair, each with both source_refs and a confidence:

```go
type Alignment struct {
    LogicalID  string      // stable id carried across versions (see below)
    Before     *SourceRef  // unit in A; nil => inserted in B
    After      *SourceRef  // unit in B; nil => deleted from A
    Relation   Relation    // one_to_one | move | split | merge
    Confidence float64
    Method     string      // e.g. "align:hungarian+embed@v2"
}

// AlignUnits returns one Alignment per matched pair plus singletons for
// inserts/deletes. It does NOT implement the matcher here — the contract is:
// every Alignment carries both source_refs (or nil for one-sided) + a
// confidence + a method. Ambiguous pairs may be PROPOSED by the LLM, but the
// returned Alignment is a recorded tool result, never a bare assertion.
func AlignUnits(a, b []Unit) []Alignment
```

> Secondary-language note (Python): `def align_units(a: list[Unit], b: list[Unit]) -> list[Alignment]`; return `Alignment(before=..., after=..., confidence=...)`. Use `scipy.optimize.linear_sum_assignment` for the bipartite step.
> Secondary-language note (TypeScript): `function alignUnits(a: Unit[], b: Unit[]): Alignment[]`; keep `before?: SourceRef` / `after?: SourceRef` optional to encode one-sided matches.

The LLM's role here is bounded. For ambiguous pairs — a heavily reworded clause that *might* be the same indemnity — the LLM may **propose** an alignment, but the system records it as a tool result with source_refs to both sides and a confidence. Low-confidence alignments do not silently ship; they route to a human, exactly as in [verification-flywheel.md](verification-flywheel.md). Confirmed alignments become training signal that lifts the matcher's confidence next round.

## Stable logical ids and blame

To follow "the indemnification clause" across nine rounds while its number drifts from 5.2 to 8.1 and its wording mutates, attach a `logical_id` to the unit and carry it on every alignment, then onto `Change.logical_id`. This is the **blame key** — the spine of a "show me the history of THIS clause" view.

Propagation rule through `align`:

- A unit matched to a prior version **inherits** that version's `logical_id`.
- A genuinely new clause (no acceptable match) gets a **fresh** `logical_id`, born at this version.
- On a `split`, the children may inherit the parent's id with a suffix, or one child keeps it and the other forks — record which, so blame stays unambiguous.

With `logical_id` stable, you can query all `Change`s for one clause across the DAG and render a log/blame timeline: round 3 inserted it, round 5 tightened the cap, round 8 moved it. That history is just a filter over the change set, which is why it is trustworthy — it is the same attributed data, grouped.

## Materiality classification

Not all changes weigh the same. A typo fix or a pure renumber is **cosmetic**. A reword that preserves the obligation is **minor**. A changed liability cap, a flipped governing-law clause, a payment term moving from net-30 to net-60 — **substantive**. Each `Change.materiality` records this judgment.

Be honest: materiality is the rung most likely to be an `llm_estimate` or a detector output, so it is **review-first**. Two rules keep it safe:

1. **`format_only` and `cosmetic` must be conservative.** When you cannot be sure a reword left the meaning intact, classify **up** — toward `substantive` — never down. The cost of a missed substantive change in a contract is unbounded; the cost of an over-flagged cosmetic one is a few seconds of reviewer time. A moved comma can be substantive in legal text; treat ambiguity as material.
2. **The classifier still cites.** Even an `llm_estimate` materiality carries the `before`/`after` source_refs, so the reviewer overturning it lands on the exact text. Their correction feeds [verification-flywheel.md](verification-flywheel.md).

## Three-way and base diffs

Reviewers rarely want "v8 vs v7." They want "everything that changed since the version *I last approved*" — a **base** that may sit several rounds back — and they want to catch whether the other side slipped a change into a clause both parties had agreed not to touch.

- **Choose a base.** Pin the approved version as the base `B0`. Diff the current version against `B0`, not against the immediate parent, so accumulated drift across rounds shows as one coherent change set.
- **N-way history.** Across rounds `B0 → B1 → … → Bn`, you can either collapse to a single base diff or render the per-round walk; the `logical_id` blame view stitches them.
- **Three-way / merge.** When the DAG **forks** — two counterparties edit `B0` in parallel into `Ba` and `Bb` — reconciling them is a three-way merge against the common ancestor `B0`. Where both sides edited the same `logical_id`, you have a **conflict**: surface it, do not auto-resolve. At minimum, flag forked clauses for human merge; never silently pick one side.

## Bidirectional provenance and navigation

Every `Change` is navigable to both sides. The UI highlights `before.span` in the old render and `after.span` in the new, scrolling both panes in lockstep. Because the spans are stable anchors, the highlight lands correctly even after reflow.

This connects to annotations. A reviewer's highlight or note attached to "Section 5.2 in v7" should **travel** to v8: re-anchor it onto the new version through the alignment that carries the clause's `logical_id`. If the underlying text was **deleted**, the annotation cannot re-anchor — it **orphans**, and the UI must say so rather than silently dropping it or attaching it to the wrong clause. See [annotations-and-highlights.md](annotations-and-highlights.md) for how an annotation re-anchors across versions and how orphans are surfaced.

## Amendments that edit a base contract

A negotiation often produces a separate instrument — an amendment that says "Section 3 is hereby deleted and replaced with the following…". This is not a side-by-side redline; it is a *document that logically edits another document*. Model it as a **version-producing operation** on the base: apply the amendment to base version `Bn` to compute a new **effective** version `Bn+1`, and record the resulting `Change`s with provenance pointing at the **amendment's instructing text** (its `before`/origin source_ref lives in the amendment, the `after` in the new effective version, the `before` content reference in the base).

This gives you a contract's effective state at any date — the base plus the chain of applied amendments — as a real version in the DAG, with every edit traceable to the amendment language that authorized it. It is distinct from a redline: the redline compares two drafts; the amendment *constructs* the next version.

## Replay and audit

A change set must be reproducible. Given the two immutable versioned snapshots plus the `model_version`s of the `segment`/`align`/`diff` tools, re-running the pipeline yields the **same** `Change`s. Because versions are content-addressed and immutable, and each stage stamps its method, replay is deterministic — the basis for the audit guarantee in [provenance.md](provenance.md) and the admissibility story in admissibility-and-security.md. If a re-run disagrees, either an input version changed (a violation — versions are frozen) or a tool's `model_version` advanced (recorded, so the divergence is explainable). The typed result of the whole comparison is shaped by [typed-contract.md](typed-contract.md).

## Anti-patterns

**Character diff as semantic diff.** A `git diff` over flattened text reports every reflowed word → segment into clause units and diff the aligned pairs, classifying meaning separately.

**Renumber as mass-change.** Inserting one clause renumbers the rest, and a position-based matcher reports fifty modifies → align by content + structure so the shift is one insert.

**Move as delete + insert.** Section 5 → Section 8 shown as a deletion and an unrelated insertion loses the fact that it is the *same* clause → detect distant high-similarity matches and emit a single `move`.

**One-sided change.** A `modify`/`move`/`format_only` missing its `before` or `after` source_ref is unverifiable → require both refs for every change_type except `insert` (no before) and `delete` (no after).

**Reword classified as format_only when meaning changed.** "shall not exceed $1M" → "shall not exceed $5M" rendered as cosmetic because the structure matched → when unsure a reword preserved meaning, classify **up** to substantive.

**Mutating a version in place.** Re-OCR'ing round 8 over the old snapshot silently rewrites the meaning of every prior change and annotation → corrections create a new version with a parent edge; snapshots are frozen.

**Diffing rendered images when a text layer exists.** Pixel-diffing two PDFs flags antialiasing and font hinting as changes → diff the canonical model; fall back to image comparison only for true scans with no recoverable text.

**LLM asserts equality without a tool.** "These two clauses are the same" with no `align:` result and no source_refs → record alignment as a tool claim with both refs and a confidence; the LLM may propose, the tool records.

## Review checklist

- [ ] Every `Change` carries `before` **and** `after` source_refs, except `insert` (no before) and `delete` (no after).
- [ ] Both source_refs include a `doc_id` and a `version`, and each resolves to a stable span in its snapshot.
- [ ] Each `Change` carries `origin.method` from `segment:` / `align:` / `diff:`, plus `confidence`.
- [ ] `doc_id`/version ids are content-addressed; re-uploading identical content yields the same id.
- [ ] Versions are immutable snapshots in a DAG; corrections create new versions, never in-place edits; merges record multiple parents.
- [ ] Segmentation produces clause-level units with stable anchors; word-level units exist for rendering and link back to their clause.
- [ ] Alignment matches by content + structure + embeddings; renumbers are single inserts; moves are `move`, not delete+insert; splits/merges are recorded as such.
- [ ] Every `Alignment` carries both source_refs (or nil for one-sided), a confidence, and a method; low-confidence alignments route to human review.
- [ ] `logical_id` is stable across versions, inherited through alignment, fresh for genuinely new clauses; blame/log view filters on it.
- [ ] Materiality is classified per change; `format_only`/`cosmetic` is conservative (classify up when unsure); estimated materiality still cites both sides.
- [ ] Base/three-way diffs are supported: a chosen base, N-way history, and fork conflicts surfaced (not auto-resolved).
- [ ] Annotations re-anchor across versions via `logical_id`; deletions orphan annotations visibly (see [annotations-and-highlights.md](annotations-and-highlights.md)).
- [ ] Amendments are modeled as version-producing operations on the base, with change provenance pointing at the amendment's instructing text.
- [ ] The change set is replayable: same snapshots + same tool `model_version`s reproduce the same `Change`s.
