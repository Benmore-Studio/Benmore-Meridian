---
name: auditable-agentic-extraction
description: >-
  Methodology for building auditable, agent-orchestrated systems that turn
  documents (PDFs, scans, forms, images, contracts, statements, blueprints) into
  verifiable structured data, comparisons, and annotations — where every derived
  claim is traceable to its source and no value, clause boundary, or change is
  invented by the LLM. Use when designing or reviewing a pipeline that extracts
  quantities/totals/line items/measurements/fields, OR compares and version-tracks
  documents (legal redlines, contract negotiation across rounds, "git for
  documents"), OR maintains durable highlights/annotations — and needs to be
  trustworthy. Triggers: "auditable", "verifiable", "provenance", "traceability",
  "no hallucinated numbers", "document comparison/diff/redline", "version
  tracking", "highlights/annotations", "blueprint/takeoff extraction", human
  review/correction loops, ML-assisted extraction with fallbacks, OCR gating,
  typed extraction-output contracts (OpenAPI/JSON-Schema with codegen, "type the
  boundary"), staged document processing with progress reporting, admissibility /
  chain-of-custody / privileged documents. Domain-agnostic (legal, construction,
  finance, medical); language-neutral (Go-first examples); distilled from a
  production document-to-structured-data takeoff pipeline.
---

# Auditable Agentic Extraction

A methodology for turning documents into structured outputs you can **defend**:
every claim traces back to a place in the source, and the language model never
authors one out of thin air. The output may be a **value** (a number you bill
against), a **comparison** (what changed between two contract versions), or an
**annotation** (a durable highlight on a clause) — the discipline is the same for
all three.

## The core thesis

> **The agent is the brain; tools are the hands. The LLM decides _where to
> look_ and _what to do_ — a tool produces the _claim_ and records how it got
> it. The model never writes a value, a clause boundary, or a change straight
> into the output.**

The unit of output is an **attributed claim**, and it comes in four kinds, all
carrying the same provenance envelope (`origin` + `source_ref`):

- **value** — a scalar read/measured/computed from the document (the core).
- **annotation** — a durable highlight/span over a region of meaning (a clause,
  a defined term, a risk flag). → [`references/annotations-and-highlights.md`](references/annotations-and-highlights.md)
- **relation** — a typed link between claims (a cross-reference, a defined-term
  use → its definition).
- **change** — a diff between two document versions, the unit of the "git for
  documents" comparison. → [`references/comparison-and-versioning.md`](references/comparison-and-versioning.md)

When an LLM both reads a document and produces a final number, you get plausible
but unverifiable output: it will confidently emit `1,240 sq ft` (or `$1,240.00`
on an invoice, or `12.5 mg/dL` on a lab report) with no way to check whether it
measured, read, estimated, or guessed. The fix is a division of labor:

- The model **perceives, locates, classifies, and orchestrates**.
- A **tool produces every value that ends up in the output**, and stamps *how*
  it was produced (`method`), *where* from (`source_ref`), and *how sure*
  (`confidence`).

**The real invariant is _attributability_, not determinism.** Determinism is the
*best* way to produce a value (a calculator, an exact parser — replayable), but
not the only legitimate one: a detector, an OCR read, even an LLM transcription
or estimate are allowed — *as long as each enters through a tool call that stamps
its method, source_ref, and an honest confidence.* These methods form a ranked
ladder (see [`references/agent-and-tools.md`](references/agent-and-tools.md)):
deterministic at the top, `llm_estimate` at the bottom. The bottom rung is not a
loophole — it is the explicitly-labeled, review-first tier, and the LLM still
never *silently* authors a number. Every value, however produced, has an origin
you can trace, triage by confidence, and (for the deterministic tiers) replay.

A second rule makes the output *checkable*: **type the boundary — never emit an
untyped blob** (`map[string]any` / `dict` / `any`). The extraction output is a
contract defined once (OpenAPI / JSON-Schema) and code-generated into typed
clients. The skill supplies the invariant provenance/result *envelope* (value,
type/unit, origin/method, source_ref, confidence, model_version); the *domain
payload* is defined per project. See
[`references/typed-contract.md`](references/typed-contract.md).

Code throughout is **language-neutral with Go as the lead example**, with brief
secondary-language notes (TypeScript / Python). Nothing here is tied to a
framework — "a tool", "a persisted record", "a background stage" are described
generically.

## When to apply this

Apply when **all** of these hold:
- The input is a document (or set of documents) — not already-structured data.
- The output is something someone will **act on, be billed against, or rely on
  in a dispute**: extracted values (quantities, prices, totals, measurements,
  dates, identifiers), a **comparison** of versions (what changed, and does it
  matter), or **annotations** a reviewer trusts to persist.
- Being wrong is expensive, so the output must be **auditable and correctable**.

Representative fits: construction takeoff/blueprints (quantities billed to a
client), invoice/statement extraction (finance), lab/medical forms, and
**legal/contract work** — redlining dense agreements across many negotiation
rounds, tracking which clause changed and whether it's substantive, and keeping
durable highlights on risk language. The methodology is one spine; the domain
payload differs.

If you just need a rough summary and nobody audits the result, this is
overkill — let the LLM summarize directly.

## The patterns

This methodology is a set of patterns that reinforce each other. Read the
reference for whichever ones you're implementing — each file is self-contained
with code templates. Patterns 1–8 are the **core** (any auditable extraction
pipeline needs them); 9–12 **extend** the spine to a canonical substrate,
comparison/versioning, durable annotations, and admissibility — reach for them
when the work involves messy real-world inputs, legal/redline comparison,
highlights, or third-party-defensible output.

### Core (1–8)

1. **Agent-brain / deterministic-hands** — the LLM orchestrates; tools compute.
   The LLM never writes a final value. → [`references/agent-and-tools.md`](references/agent-and-tools.md)

2. **Structured provenance on every derived value** — each value carries an
   origin record (`source_ref` location, method, inputs, confidence,
   model_version) so it can be traced and replayed.
   → [`references/provenance.md`](references/provenance.md)

3. **Perception/computation split** — a vision model decides *where* the
   relevant region is; a deterministic tool reads/measures/computes the value
   from that region. → [`references/agent-and-tools.md`](references/agent-and-tools.md)

4. **Human verification + correction flywheel** — humans confirm or correct
   values; corrections are captured as labeled training data that improves the
   detectors/models over time. → [`references/verification-flywheel.md`](references/verification-flywheel.md)

5. **Graceful degradation** — a missing model or tool narrows capability
   instead of crashing; the system falls back to a lower-confidence source and
   says so. → [`references/degradation-and-gating.md`](references/degradation-and-gating.md)

6. **Capability-based gating (not result-based)** — decide whether to run a
   fallback (e.g. OCR) by inspecting the input's *capability* (does this page
   have a text layer?), never by waiting to see if the primary path returned
   empty. → [`references/degradation-and-gating.md`](references/degradation-and-gating.md)

7. **Document-wide staged processing with progress events** — process the whole
   document through named stages, emit a progress event per stage, and make
   each stage idempotent and resumable. → [`references/staged-processing.md`](references/staged-processing.md)

8. **Typed output as a contract** — define the extraction output once as an
   OpenAPI / JSON-Schema contract and code-generate typed clients; reuse the
   invariant provenance *envelope* and define only the domain *payload* per
   project. *Type the boundary — never emit an untyped blob.*
   → [`references/typed-contract.md`](references/typed-contract.md)

### Extended (9–12)

9. **Canonical document model & robust ingestion** — build one normalized
   representation (pages → blocks → lines → tokens, with stable anchor ids and a
   canonical coordinate space) that every `source_ref`, bbox, highlight, and diff
   resolves against, and handle the messy real world (encrypted/corrupt/rotated
   PDFs, scanned-vs-vector, garbage text layers, redactions, strikethrough,
   watermarks, locale-sensitive numbers/dates, DoS limits). This is what makes
   anchors survive re-OCR and re-pagination.
   → [`references/document-model.md`](references/document-model.md)

10. **Comparison & versioning ("git for documents")** — content-address each
    document, treat versions as immutable snapshots in a DAG, then
    `segment → align → diff → classify materiality` to produce `Change` claims
    that point into **both** versions. Handles renumbering, moved/split/merged
    clauses, "what changed since the version I approved", and amendments that
    modify a base. → [`references/comparison-and-versioning.md`](references/comparison-and-versioning.md)

11. **Durable annotations & highlights** — highlights anchored to canonical text
    spans (not pixels or character offsets) so they survive re-OCR and new
    versions; overlapping/nested annotations; re-anchoring with a confidence, and
    explicit *orphaning* (never silent loss) when the marked text is gone.
    → [`references/annotations-and-highlights.md`](references/annotations-and-highlights.md)

12. **Admissibility, tamper-evidence & sensitive content** — make the trail
    defensible to an outside party: hash the original bytes, an append-only
    hash-chained audit log / chain of custody, pinned model+prompt versions for
    reproducibility, signed exports, and redaction-aware / privilege-aware
    handling of sensitive documents. → [`references/admissibility-and-security.md`](references/admissibility-and-security.md)

## How the patterns fit together

```
                    ┌───────────────────────────────────────────┐
                    │  AGENT (LLM): classify · locate · decide    │
                    └───────────────┬─────────────────────────────┘
                                    │ calls tools, never writes values
            ┌───────────────────────┼───────────────────────┐
            ▼                       ▼                       ▼
     ┌────────────┐         ┌──────────────┐        ┌──────────────┐
     │ detector / │         │  parser /    │        │  calculator  │
     │ perception │         │  reader      │        │  (math)      │
     └─────┬──────┘         └──────┬───────┘        └──────┬───────┘
     └──── each returns the TYPED ENVELOPE: value + source_ref + origin ────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │  structured records   │  ← typed contract; every value
                         │  (typed contract)     │     has an origin + source_ref
                         └──────────┬────────────┘
                                    ▼
                         ┌──────────────────────┐         corrections
                         │  HUMAN VERIFICATION    │───────────────┐
                         └──────────┬────────────┘               │
                                    ▼                            ▼
                         ┌──────────────────────┐      ┌──────────────────┐
                         │  trusted output       │      │  training labels │
                         └──────────────────────┘      │  (flywheel)      │
                                                        └──────────────────┘
```

The **canonical document model** (pattern 9) is the substrate underneath this
diagram: every `source_ref` the tools emit is an anchor into it, which is what
lets a highlight (pattern 11) or a diff (pattern 10) stay attached after re-OCR
or a new version. Staged processing (pattern 7) is the spine that runs the agent
loop over the whole document; degradation + gating (5, 6) decide which tools are
available and when to fall back at each stage. The typed contract (pattern 8) is
the shape every record, tool result, and API/event payload conforms to — the
envelope that carries provenance (pattern 2) across every boundary. Admissibility
(pattern 12) wraps the whole trail so an outside party can trust it.

## Recommended build order

When building a new pipeline from scratch, implement in this order — each step
is usable on its own and de-risks the next:

0. **Canonical document model** (pattern 9) if your inputs are messy or you'll do
   comparison/annotation. Stable anchors are the foundation every `source_ref`
   stands on; pixel/offset refs you retrofit later will not survive re-OCR or a
   new version. For a single-source, born-digital, extract-only v1 you can defer
   this — but decide deliberately.
1. **Typed contract + provenance envelope first** (patterns 8 & 2). Define the
   output as an OpenAPI / JSON-Schema contract and codegen the typed envelope
   (`value`, `unit`, `origin`/`method`, `source_ref`, `confidence`,
   `model_version`) *before* writing any extraction code — both are painful to
   retrofit. Even a v1 that does pure LLM extraction should emit the typed
   envelope and stamp provenance (`method="llm_estimate"`, with a real
   `source_ref`), so the audit surface and the shared types exist from day one.
2. **Staged spine** (pattern 7) with one trivial stage and a progress event, so
   you can watch the document move through the pipeline.
3. **Agent + one deterministic tool** (patterns 1, 3) — e.g. locate-then-parse —
   producing real provenanced values that conform to the contract.
4. **Gating + degradation** (patterns 5, 6) so the one tool can be absent or the
   input can lack a capability without crashing.
5. **Verification UI + flywheel** (pattern 4) once values are flowing, so humans
   can correct (via each value's `source_ref`) and those corrections are captured
   as localized training labels.

## Anti-patterns to watch for (during design or review)

- **LLM authors the number.** A prompt that returns `{"area": 1240}` with no
  tool call and no source citation. → Route the value through a tool that
  measures/computes, and attach provenance.
- **Free-form LLM arithmetic.** Asking the model to "calculate the total." LLMs
  do arithmetic unreliably and untraceably. → Hand the operands to a
  deterministic calculator tool.
- **Result-based fallback.** "If extraction returned nothing, run OCR." This
  fires OCR on genuinely-empty pages and misses scanned pages that *did* return
  garbage. → Gate on capability (text layer present?), see pattern 6.
- **Provenance as a logging afterthought.** Origin stuffed into a log line
  instead of a structured field on the record. → It must travel *with* the
  value so the UI and audits can read it.
- **Untyped blob at a boundary.** Returning/storing/sending `map[string]any`,
  `dict`, or `any`. → Type the boundary with the generated envelope; a blob hides
  a missing `source_ref` and silent type/unit drift. See pattern 8.
- **A value with no `source_ref` (or a vague one).** "page 4" with no
  bbox/anchor/row. → The reviewer can't find it and a correction can't be
  localized into a training label. Make `source_ref` navigable.
- **Hand-written types that drift from the schema.** → Code-generate clients from
  the OpenAPI/JSON-Schema contract so producer and all consumers share one shape.
- **A missing model is a crash.** → It should be a narrower capability + an
  honest lower-confidence fallback.
- **Corrections thrown away.** Human fixes that only patch one record. →
  Capture every correction as a labeled example for the flywheel.
- **Wall-clock processing timeouts.** Killing a long document by elapsed time.
  → Track *activity/progress*; only kill when a stage stops making progress.
- **Pixel- or offset-anchored highlights.** A bbox or character offset as the
  source of truth for a highlight/source_ref → it breaks on re-render or a text
  edit. Anchor to canonical token-id spans; treat bboxes as a derived, recomputed
  rendering. See pattern 9 & 11.
- **Text/character diff sold as semantic diff.** A renumber shown as 50 changes,
  a moved clause shown as delete+insert, a reworded-but-changed-meaning clause
  labelled "cosmetic". → Segment + align first, classify materiality
  conservatively (when unsure, *up* to substantive). See pattern 10.
- **Trusting a text layer's presence, not its quality.** A broken-ToUnicode PDF
  yields selectable garbage that passes a length check. → Gate on text *quality*,
  and OCR + stamp degradation when it fails. See pattern 9.
- **Seeing through a redaction.** Reading text still present under a black-box
  redaction, or hallucinating past it. → Redactions are first-class facts; strip
  hidden text, never invent covered content. See patterns 9 & 12.
- **Silently dropping an un-anchorable annotation.** A reviewer's risk flag
  vanishes when the clause moves. → Re-anchor; if it can't, *orphan* it visibly
  for re-review. See pattern 11.
- **Mutating a document version in place.** A correction overwrites the snapshot.
  → Versions are immutable; a change creates a new version. See pattern 10.
- **Un-pinned model/prompt versions.** Output that can't be reproduced for an
  auditor. → Record `model_version` + prompt/template version on every claim. See
  pattern 12.

## Reference files

- [`references/agent-and-tools.md`](references/agent-and-tools.md) — patterns 1 &
  3: the agent/tools harness, the perception/computation split, the typed
  tool-result contract, and a deterministic calculator tool (Go-first).
- [`references/provenance.md`](references/provenance.md) — pattern 2: the origin
  record, `source_ref` as the first-class traceability link, a Go record sketch,
  replay tests, and how provenance flows to exports and the UI.
- [`references/typed-contract.md`](references/typed-contract.md) — pattern 8:
  output as an OpenAPI/JSON-Schema contract, the invariant provenance envelope vs.
  the per-project domain payload, codegen to Go/TS/Python, and "type the boundary".
  Ships [`references/envelope.openapi.yaml`](references/envelope.openapi.yaml) — the
  invariant envelope as a copy-paste schema.
- [`references/verification-flywheel.md`](references/verification-flywheel.md) —
  pattern 4: the verify loop and turning `source_ref`-localized corrections into
  training labels.
- [`references/degradation-and-gating.md`](references/degradation-and-gating.md) —
  patterns 5 & 6: graceful degradation when a model/tool is missing, and
  capability-based gating.
- [`references/staged-processing.md`](references/staged-processing.md) — pattern 7:
  the document-wide staged spine, progress events, idempotency, and activity-based
  reaping.
- [`references/document-model.md`](references/document-model.md) — pattern 9: the
  canonical document model (stable anchors, canonical coordinates, reading order,
  text normalization) and robust ingestion of messy/adversarial inputs.
- [`references/comparison-and-versioning.md`](references/comparison-and-versioning.md) —
  pattern 10: content-addressed identity, the version DAG, segment/align/diff,
  move detection, materiality, base/three-way diff, and amendments — "git for
  documents".
- [`references/annotations-and-highlights.md`](references/annotations-and-highlights.md) —
  pattern 11: durable span-anchored highlights, re-anchoring with confidence,
  orphaning, overlapping annotations, and round-trip export.
- [`references/admissibility-and-security.md`](references/admissibility-and-security.md) —
  pattern 12: source-byte hashing, tamper-evident audit log / chain of custody,
  reproducibility (pinned model+prompt versions), signed exports, and
  redaction-/privilege-aware handling.

External specifications referenced by this skill:
[OpenAPI Specification](https://spec.openapis.org/oas/latest.html) ·
[JSON Schema](https://json-schema.org/specification).
