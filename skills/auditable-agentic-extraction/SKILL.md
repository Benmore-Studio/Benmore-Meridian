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
  extraction with fallbacks, OCR gating, or staged document processing with
  progress reporting. Domain-agnostic; distilled from a production
  document-to-structured-data takeoff pipeline.
---

# Auditable Agentic Extraction

A methodology for turning documents into structured data you can **defend**:
every number traces back to a place in the source, and the language model
never authors a value out of thin air.

## The core thesis

> **The agent is the brain; deterministic tools are the hands. The LLM
> decides _where to look_ and _what to do_ — a deterministic tool computes
> the _value_.**

When an LLM both reads a document and produces a final number, you get plausible
but unverifiable output: it will confidently emit `1,240 sq ft` with no way to
check whether it measured, estimated, or guessed. The fix is a division of labor:

- The model **perceives, locates, classifies, and orchestrates**.
- Deterministic code (Python, a calculator, a parser, a detector) **produces
  every value that ends up in the output**, and records *how* it was produced.

This single rule is what makes the rest of the methodology possible. If a value
can only enter the output through a tool call, then every value automatically
has an origin you can attach provenance to, replay, and verify.

## When to apply this

Apply when **all** of these hold:
- The input is a document (or set of documents) — not already-structured data.
- The output is structured values someone will **act on or be billed against**
  (quantities, prices, totals, measurements, dates, identifiers).
- Being wrong is expensive, so the output must be **auditable and correctable**.

If you just need a rough summary and nobody audits the numbers, this is
overkill — let the LLM summarize directly.

## The seven patterns

This methodology is a set of patterns that reinforce each other. Read the
reference for whichever ones you're implementing — each file is self-contained
with code templates.

1. **Agent-brain / deterministic-hands** — the LLM orchestrates; tools compute.
   The LLM never writes a final value. → `references/agent-and-tools.md`

2. **Structured provenance on every derived value** — each value carries an
   origin record (source location, method, inputs, confidence) so it can be
   traced and replayed. → `references/provenance.md`

3. **Perception/computation split** — a vision model decides *where* the
   relevant region is; a deterministic tool reads/measures/computes the value
   from that region. → `references/agent-and-tools.md`

4. **Human verification + correction flywheel** — humans confirm or correct
   values; corrections are captured as labeled training data that improves the
   detectors/models over time. → `references/verification-flywheel.md`

5. **Graceful degradation** — a missing model or tool narrows capability
   instead of crashing; the system falls back to a lower-confidence source and
   says so. → `references/degradation-and-gating.md`

6. **Capability-based gating (not result-based)** — decide whether to run a
   fallback (e.g. OCR) by inspecting the input's *capability* (does this page
   have a text layer?), never by waiting to see if the primary path returned
   empty. → `references/degradation-and-gating.md`

7. **Document-wide staged processing with progress events** — process the whole
   document through named stages, emit a progress event per stage, and make
   each stage idempotent and resumable. → `references/staged-processing.md`

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
           └────────── each returns value + PROVENANCE ─────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │  structured records   │  ← every value has an origin
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
when to fall back at each stage.

## Recommended build order

When building a new pipeline from scratch, implement in this order — each step
is usable on its own and de-risks the next:

1. **Provenance model first** (pattern 2). Decide the origin record before
   writing any extraction code. It is painful to retrofit. Even a v1 that does
   pure LLM extraction should stamp provenance (`method="llm_estimate"`), so the
   audit surface exists from day one.
2. **Staged spine** (pattern 7) with one trivial stage and a progress event, so
   you can watch the document move through the pipeline.
3. **Agent + one deterministic tool** (patterns 1, 3) — e.g. locate-then-parse —
   producing real provenanced values.
4. **Gating + degradation** (patterns 5, 6) so the one tool can be absent or the
   input can lack a capability without crashing.
5. **Verification UI + flywheel** (pattern 4) once values are flowing, so humans
   can correct and those corrections are captured.

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
- **A missing model is a crash.** → It should be a narrower capability + an
  honest lower-confidence fallback.
- **Corrections thrown away.** Human fixes that only patch one record. →
  Capture every correction as a labeled example for the flywheel.
- **Wall-clock processing timeouts.** Killing a long document by elapsed time.
  → Track *activity/progress*; only kill when a stage stops making progress.

## Reference files

- `references/agent-and-tools.md` — patterns 1 & 3: the agent/tools harness, the
  perception/computation split, the tool-result contract, and a calculator tool.
- `references/provenance.md` — pattern 2: the origin record, a framework-light
  model-field sketch, and how provenance flows to exports and the UI.
- `references/verification-flywheel.md` — pattern 4: the verify loop and turning
  corrections into training labels.
- `references/degradation-and-gating.md` — patterns 5 & 6: graceful degradation
  when a model/tool is missing, and capability-based gating.
- `references/staged-processing.md` — pattern 7: the document-wide staged spine,
  progress events, idempotency, and activity-based reaping.
