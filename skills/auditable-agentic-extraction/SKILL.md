---
name: auditable-agentic-extraction
description: >-
  Methodology for building auditable, agent-orchestrated systems that turn
  documents (PDFs, scans, forms, images, contracts, statements) into verifiable
  structured data — where every derived value is traceable to its source and
  no value is invented by the LLM. Use when designing or reviewing a pipeline
  that extracts quantities, totals, line items, measurements, or other
  structured fields from documents and needs to be trustworthy: when the
  requirement involves "auditable", "verifiable", "provenance", "traceability",
  "no hallucinated numbers", human review/correction loops, ML-assisted
  extraction with fallbacks, OCR gating, typed extraction-output contracts
  (OpenAPI/JSON-Schema with codegen, "type the boundary"), or staged document
  processing with progress reporting. Domain-agnostic; language-neutral
  (Go-first examples); distilled from a production document-to-structured-data
  takeoff pipeline.
---

# Auditable Agentic Extraction

A methodology for turning documents into structured data you can **defend**:
every number traces back to a place in the source, and the language model
never authors a value out of thin air.

## The core thesis

> **The agent is the brain; tools are the hands. The LLM decides _where to
> look_ and _what to do_ — a tool produces the _value_ and records how it got
> it. The model never writes a value straight into the output.**

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
- The output is structured values someone will **act on or be billed against**
  (quantities, prices, totals, measurements, dates, identifiers).
- Being wrong is expensive, so the output must be **auditable and correctable**.

If you just need a rough summary and nobody audits the numbers, this is
overkill — let the LLM summarize directly.

## The eight patterns

This methodology is a set of patterns that reinforce each other. Read the
reference for whichever ones you're implementing — each file is self-contained
with code templates.

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

Staged processing (pattern 7) is the spine that runs the agent loop over the
whole document; degradation + gating (5, 6) decide which tools are available and
when to fall back at each stage. The typed contract (pattern 8) is the shape
every record, tool result, and API/event payload conforms to — the envelope
that carries provenance (pattern 2) across every boundary.

## Recommended build order

When building a new pipeline from scratch, implement in this order — each step
is usable on its own and de-risks the next:

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

External specifications referenced by this skill:
[OpenAPI Specification](https://spec.openapis.org/oas/latest.html) ·
[JSON Schema](https://json-schema.org/specification).
