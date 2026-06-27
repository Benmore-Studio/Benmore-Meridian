# Typed output as a contract (pattern 8)

The extraction output is a **contract**, not an ad-hoc shape that each consumer
re-discovers. Define it once as an OpenAPI / JSON-Schema document, then
**code-generate** typed clients from it (Go structs, TypeScript types, Python
models, etc.). Every producer and consumer speaks the same generated types.

> **Core principle: type the boundary. Never emit an untyped blob**
> (`map[string]any` in Go, `dict`/`Any` in Python, `any`/`Record<string,unknown>`
> in TypeScript). An untyped value crossing a service or storage boundary is a
> value whose origin and shape nobody can check.

This pattern is the structural counterpart to provenance
([`provenance.md`](provenance.md)): provenance makes each *value* traceable; the
typed contract makes the *whole record shape* checkable and shared. The agent
harness ([`agent-and-tools.md`](agent-and-tools.md)) emits records that conform
to this contract; the verification UI ([`verification-flywheel.md`](verification-flywheel.md))
renders them by reading the same generated types.

## Contents

- The envelope vs. the payload (the critical split)
- The invariant provenance envelope (generic OpenAPI snippet)
- Codegen: from contract to typed client (Go)
- `source_ref`: the traceability link, as a first-class typed shape
- Why "type the boundary" matters in practice
- Secondary-language note (TypeScript / Python)
- Review checklist

## The envelope vs. the payload (the critical split)

There are **two layers** to the output type, and they come from different places:

| Layer | What it is | Who defines it | Stability |
|---|---|---|---|
| **Envelope** | The provenance/result wrapper: `value`, `type`/`unit`, `origin`/`method`, `source_ref`, `confidence`, `model_version` | **This skill** — invariant across every project | Fixed |
| **Payload** | The actual domain fields being extracted (the line items, the measurements, the totals — whatever *this* document yields) | **Your project** — context-dependent | Varies per project |

The skill gives you the **envelope and the discipline**, not your domain types.
A medical-form pipeline and an invoice pipeline share the *exact same* envelope;
their payloads are completely different. Do not invent a universal payload — there
isn't one. Do reuse the envelope verbatim.

```
┌──────────────────────────── ExtractedValue (ENVELOPE — fixed) ─────────────────┐
│  value · type/unit · origin(method,inputs,model_version) · source_ref · confidence │
│                                                                                    │
│        ┌──────────── payload (DOMAIN — defined per project) ────────────┐          │
│        │   e.g. { "line_item_code": ..., "qty": ..., "category": ... }   │          │
│        └────────────────────────────────────────────────────────────────┘          │
└────────────────────────────────────────────────────────────────────────────────┘
```

A practical way to wire this: the envelope is a generic schema with the domain
payload referenced as an open `object` (or a `$ref` the project fills in). The
project supplies the payload schema; the envelope schema is copied unchanged.

## The invariant provenance envelope (generic OpenAPI snippet)

This is the part the skill supplies. **Ships as a copy-paste asset:**
[`envelope.openapi.yaml`](envelope.openapi.yaml) — copy it verbatim into your
contract and fill in the payload `$ref` rather than re-typing from the snippet
below. The snippet here is the same schema, inlined for reading. It is
deliberately domain-free.

```yaml
# openapi.yaml — components/schemas (the INVARIANT envelope)
components:
  schemas:
    SourceRef:
      type: object
      description: >-
        Where in the source this claim came from. Names the document (doc_id) and,
        for versioned corpora, the version; then sets one point locator
        (page+bbox / anchor / table+row) OR a span (start..end anchors) for a
        region. Anchors are stable token ids in the canonical document model
        (document-model.md), not raw character offsets.
      properties:
        doc_id:  { type: string, description: "stable (content-addressed) id of the source document" }
        version: { type: string, nullable: true, description: "document revision this ref resolves against" }
        page:    { type: integer, minimum: 1, description: 1-based page/sheet }
        bbox:
          type: array
          description: "[x1,y1,x2,y2] region on the page, canonical page coords"
          items: { type: number }
          minItems: 4
          maxItems: 4
        anchor:  { type: string, description: "stable id of a single text/table token in the canonical model" }
        table:   { type: string, description: "table/section identifier" }
        row:     { type: integer, description: "row index within table" }
        span:    { $ref: '#/components/schemas/Span' }  # start_anchor..end_anchor, may cross pages
      required: [doc_id]

    Origin:
      type: object
      description: How the value was produced — the audit trail of method + inputs.
      properties:
        method:
          type: string
          description: >-
            Producing method = a rung on the value-source ladder + a domain detail.
            Convention "<rung>:<detail>", e.g. "parse:line_item_qty", "calc:area",
            "detector:abnormal_range", "lookup:sku", "ocr:tesseract", "llm_estimate".
        inputs:
          type: array
          description: Upstream operand values or ids of upstream records this derives from.
          items: { type: string }
        model_version:
          type: string
          nullable: true
          description: Detector/model/ruleset version — for the flywheel & reproducibility.
      required: [method]

    ExtractedValue:
      type: object
      description: >-
        The invariant envelope. Every value in the output is one of these. The
        domain payload is carried under `payload` and is defined per project.
      properties:
        key:        { type: string, description: "what this value is, e.g. wall_area" }
        value:      { type: string, description: "exact value as a string (decimal-as-string / parsed token) to avoid float drift" }
        unit:       { type: string, nullable: true }
        origin:     { $ref: '#/components/schemas/Origin' }
        source_ref: { $ref: '#/components/schemas/SourceRef' }
        confidence: { type: number, minimum: 0, maximum: 1 }
        payload:
          type: object
          additionalProperties: true
          description: >-
            DOMAIN-SPECIFIC fields for this project. Replace with a $ref to your
            project's payload schema. The envelope above never changes.
      required: [key, value, origin, source_ref, confidence]
```

> The snippet above shows `SourceRef`, `Origin`, and the scalar `ExtractedValue`.
> The full [`envelope.openapi.yaml`](envelope.openapi.yaml) also defines the
> `Span` sub-object and three sibling **claim kinds** that reuse `Origin` +
> `SourceRef` verbatim: `Annotation` (a durable highlight —
> [`annotations-and-highlights.md`](annotations-and-highlights.md)), `Relation`
> (a typed link between claims), and `Change` (a version diff —
> [`comparison-and-versioning.md`](comparison-and-versioning.md)). The envelope is
> invariant across all of them; only the per-project `payload` differs.

Notes baked into the schema on purpose:
- `value` is a **string**, not a number — exact decimal-as-string avoids
  float-drift across languages and JSON parsers. The typed value is reconstructed
  on read (e.g. `decimal`/`big.Rat`).
- `source_ref.doc_id` is **required** — every claim names which document (and,
  versioned, which version) it came from, so traceability holds across a corpus.
- `source_ref` and `origin` are **required**. The contract makes it structurally
  impossible to emit a conforming value with no traceability.
- `confidence` is bounded `[0,1]` at the schema level — invalid confidence fails
  validation, not silently.

## Codegen: from contract to typed client (Go)

Generate, don't hand-write. Hand-written types drift from the schema; generated
types are the schema. With Go, `oapi-codegen` turns the snippet above into:

```go
// Code generated from openapi.yaml — DO NOT EDIT.

// SourceRef — where in the source this value came from.
type SourceRef struct {
    Page   int       `json:"page"`
    Bbox   []float64 `json:"bbox,omitempty"`
    Anchor *string   `json:"anchor,omitempty"`
    Table  *string   `json:"table,omitempty"`
    Row    *int      `json:"row,omitempty"`
}

// Origin — how the value was produced.
type Origin struct {
    Method       string   `json:"method"`
    Inputs       []string `json:"inputs,omitempty"`
    ModelVersion *string  `json:"model_version,omitempty"`
}

// ExtractedValue — the invariant envelope. Every output value is one of these.
type ExtractedValue struct {
    Key        string         `json:"key"`
    Value      string         `json:"value"` // exact decimal-as-string
    Unit       *string        `json:"unit,omitempty"`
    Origin     Origin         `json:"origin"`
    SourceRef  SourceRef      `json:"source_ref"`
    Confidence float64        `json:"confidence"`
    Payload    map[string]any `json:"payload,omitempty"` // project supplies a typed struct here
}
```

The producing tool returns this type; storage serializes it; the API hands it
out; the UI's generated TS type matches it field-for-field. One contract, many
languages, zero drift.

A producer in Go now physically cannot return an untyped result for the
envelope:

```go
// A tool returns the typed envelope, never a bare map.
func parseDimension(region Region, raw string) (ExtractedValue, error) {
    dec, err := parseImperial(raw) // deterministic parse
    if err != nil {
        return ExtractedValue{}, fmt.Errorf("parse %q: %w", raw, err)
    }
    return ExtractedValue{
        Key:   "dimension",
        Value: dec.String(), // exact, as string
        Unit:  ptr("in"),
        Origin: Origin{
            Method: "parse:dimension",
            Inputs: []string{raw},
        },
        SourceRef:  region.Ref, // the WHERE — carried, not reconstructed later
        Confidence: 0.99,
    }, nil
}
```

## `source_ref`: the traceability link, as a first-class typed shape

`source_ref` is the link from a value **back to where in the document it came
from** — the single field that makes the output auditable. In the *contract* it
is a first-class typed sub-object (above), never a stringly-typed afterthought:
the schema makes it `required`, so a conforming value cannot exist without a link
to its source.

The locator families it carries (page+bbox / anchor / table+row / derived), the
rules for a good link (specific enough to highlight, in source coordinates,
stable anchors over fragile offsets, composable for derived values), and how it
powers verification and training labels are defined once in
[`provenance.md`](provenance.md) — the canonical home for the `source_ref`
concept. This file only fixes its *typed shape*; that file governs its *content*.

One contract-level note: `required: [page]` on `SourceRef` assumes a paginated
source. If your inputs are not paginated (a stream, a single image, a transcript
with timestamps), relax that constraint and add the locator your source supports
(e.g. an offset or timestamp) — the *envelope* is invariant, but which locator
family is mandatory is yours to set.

## Why "type the boundary" matters in practice

An untyped blob (`map[string]any`, `dict`, `any`) crossing a boundary defeats the
whole methodology:

- **It hides missing provenance.** A blob can omit `source_ref` and nothing
  complains until an auditor asks "where did this come from?" — too late. A typed
  envelope with `required: [source_ref, origin]` fails fast.
- **It hides type/unit drift.** `value: 1240` (a number) vs `value: "1240.00"`
  (exact string) vs `value: "1,240"` (formatted) are indistinguishable in a blob
  and silently corrupt downstream math.
- **It pushes shape-discovery onto every consumer.** Each consumer re-guesses the
  keys; they disagree; bugs follow. Codegen makes the producer and all consumers
  share one definition.
- **It can't be reviewed mechanically.** You can grep a codebase for
  `map[string]any` / `: dict` / `: any` at boundaries and treat each hit as a
  finding (see checklist). You cannot grep for "this dict was missing a field."

The boundary to type is anywhere a value is **serialized, stored, or sent**: the
tool→harness return, the harness→storage write, the API response, the
WebSocket/event payload.

## Secondary-language note (TypeScript / Python)

The same contract generates other languages — the envelope is identical, only the
syntax differs. Briefly:

- **TypeScript** (e.g. `openapi-typescript`): `ExtractedValue` becomes an
  `interface` with `origin: Origin; source_ref: SourceRef; confidence: number`.
  Ban `any`/`Record<string, unknown>` at boundaries via `tsc` + lint; the
  generated interface is what API responses are typed against.
- **Python** (e.g. `datamodel-code-generator` → pydantic): `ExtractedValue`
  becomes a `BaseModel` with required `origin`, `source_ref`, `confidence` and
  validation (`confidence: confloat(ge=0, le=1)`). Pydantic rejects a blob that
  omits a required field at parse time — the boundary is enforced at runtime.

In all three, the rule is the same: **the generated envelope type is the only
thing allowed to cross the boundary; raw maps/dicts/`any` are a review finding.**

## External references

- OpenAPI Specification — <https://spec.openapis.org/oas/latest.html>
- JSON Schema — <https://json-schema.org/specification>

## Review checklist

- [ ] Is the output defined as an OpenAPI / JSON-Schema **contract**, not an
      ad-hoc shape per consumer?
- [ ] Are typed clients **code-generated** from the contract (not hand-written
      and prone to drift)?
- [ ] Is the **envelope** (`value`, `unit`, `origin`, `source_ref`, `confidence`,
      `model_version`) reused verbatim from this skill, with only the **payload**
      defined per project?
- [ ] Are `source_ref` and `origin` **required** in the schema (impossible to emit
      a conforming value with no traceability)?
- [ ] Is `value` an exact string (decimal-as-string), not a float, to avoid drift?
- [ ] Is `confidence` bounded `[0,1]` at the schema level?
- [ ] Does any boundary (tool return, storage write, API/event payload) carry an
      untyped blob (`map[string]any` / `dict` / `any`)? → finding; type it.
- [ ] Is `source_ref` specific enough to navigate to (page+bbox / anchor /
      table+row), in source coordinates, with stable anchors?
