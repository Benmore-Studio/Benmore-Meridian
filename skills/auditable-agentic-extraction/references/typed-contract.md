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

This is the part the skill supplies. Copy it into your contract and fill in the
payload `$ref`. It is deliberately domain-free.

```yaml
# openapi.yaml — components/schemas (the INVARIANT envelope)
components:
  schemas:
    SourceRef:
      type: object
      description: >-
        Where in the source this value came from. Specific enough that a UI can
        navigate the user straight to it. Exactly one locator family is set.
      properties:
        page:    { type: integer, minimum: 1, description: 1-based page/sheet }
        bbox:
          type: array
          description: "[x1,y1,x2,y2] region on the page, source pixel coords"
          items: { type: number }
          minItems: 4
          maxItems: 4
        anchor:  { type: string, description: "stable id of a text/table anchor, e.g. OCR token id" }
        table:   { type: string, description: "table/section identifier" }
        row:     { type: integer, description: "row index within table" }
      required: [page]

    Origin:
      type: object
      description: How the value was produced — the audit trail of method + inputs.
      properties:
        method:
          type: string
          description: >-
            Producing method. Convention: "<kind>:<detail>", e.g. "detector:doorwin",
            "parse:dimension", "calc:area", "schedule_lookup", "llm_estimate".
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

Notes baked into the schema on purpose:
- `value` is a **string**, not a number — exact decimal-as-string avoids
  float-drift across languages and JSON parsers. The typed value is reconstructed
  on read (e.g. `decimal`/`big.Rat`).
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
from**. It is the single field that makes the output auditable, the verification
UI navigable, and training labels localizable. Treat it as first-class — a typed
sub-object in the contract (above), never a stringly-typed afterthought.

The link shape is a small set of locator families; pick the one the source
supports and keep it specific enough to *navigate to*:

| Source kind | `source_ref` link shape | Navigates to |
|---|---|---|
| Rendered page region | `{ "page": 4, "bbox": [120, 880, 410, 930] }` | a highlighted box on page 4 |
| Text/OCR anchor | `{ "page": 4, "anchor": "ocr_tok_8821" }` | the exact token/word |
| Table cell | `{ "page": 9, "table": "schedule_A", "row": 12 }` | a row in a parsed table |
| Multi-region (derived) | inputs reference the *records* whose own `source_ref`s point at each region | the chain of contributing regions |

Rules for a good link:
- **Specific enough to highlight.** "page 4" alone is weak; "page 4, bbox […]"
  or "page 4, anchor tok_8821" lets the UI draw a box or scroll to the word.
- **In source coordinates.** A `bbox` is in the coordinate space of the rendered
  page the user sees, so the highlight lands on the right spot.
- **Stable anchors over fragile offsets.** Prefer an OCR token id or table+row
  (stable across re-renders) to a raw character offset (shifts if the document
  is re-paginated).
- **Composable for derived values.** A computed total's `source_ref` can point at
  the calc, while its `origin.inputs` reference the operand *records*, each
  carrying its own `source_ref` — so the chain bottoms out at real source
  regions. See "composable provenance" in [`provenance.md`](provenance.md).

This is the same `source_ref` that powers the verification surface and the
training-label localization — see [`provenance.md`](provenance.md) (flow to UI &
exports) and [`verification-flywheel.md`](verification-flywheel.md) (a correction
is `source_ref` + corrected value).

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
