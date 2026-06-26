# Structured provenance on every derived value (pattern 2)

Provenance is a **structured field that travels with the value**, not a log
line. It answers, for any value in the output: *where in the source did this
come from, how was it produced, from what inputs, and how confident are we?*

If you build only one thing from this methodology, build this — and build it
first. Retrofitting provenance after the extraction code exists means revisiting
every value-producing path. Stamping it from day one (even on a pure-LLM v1)
means the audit surface always exists.

Provenance is the *value-level* discipline; the typed contract
([`typed-contract.md`](typed-contract.md)) is the *shape-level* discipline that
makes the provenance envelope a shared, generated type. Read them together — the
fields named here (`source_ref`, `origin`/`method`, `confidence`, `model_version`)
are exactly the envelope fields the contract codegens.

## Contents

- The origin record (what to capture)
- `source_ref`: the traceability link (first-class)
- A language-neutral record sketch (Go)
- Where provenance comes from (the source)
- How provenance flows to UI and exports
- Replay: the test that provenance is real
- Review checklist

## The origin record

Minimum viable origin record for a derived value:

| Field | Meaning | Example |
|---|---|---|
| `method` | how the value was produced | `"detector:doorwin"`, `"parse:dimension"`, `"calc:area"`, `"schedule_lookup"`, `"llm_estimate"` |
| `source_ref` | *where* in the source — the traceability link, specific enough to navigate to | `{"page": 4, "bbox": [x1,y1,x2,y2]}` or `{"page": 9, "table": "schedule_A", "row": 12}` |
| `inputs` | the upstream values/operands this was derived from | `["12.0", "8.5"]` or `[<id of another record>]` |
| `confidence` | 0–1, from the producing tool/model | `0.92` |
| `model_version` | which detector/model/ruleset produced it (for the flywheel + reproducibility) | `"doorwin-v3"` |

`method` is the single most useful field for triage: it lets you filter "show me
every value that came from an `llm_estimate`" — i.e. exactly the values that are
*not* fully grounded and deserve scrutiny.

Keep provenance **composable**: a calculated total's `inputs` point at the
records of its operands, each of which has its own provenance (and its own
`source_ref`). Tracing a wrong total walks the chain down to the wrong leaf,
which bottoms out at a real source region.

> The illustrative `method` values above (`detector:doorwin`, etc.) come from a
> construction takeoff pipeline — they are examples only; your domain supplies
> its own method names.

## `source_ref`: the traceability link (first-class)

`source_ref` is the field that earns the word *auditable*. It is the link from a
value **back to the exact place in the document it came from**, so an auditor (or
the verification UI, or a training-label) can go look. Everything else in
provenance describes *how*; `source_ref` answers *where* — and "where" is what a
human checks first.

Make it specific enough to **navigate to**. The link is a small set of locator
families; pick the one the source supports:

| Source kind | `source_ref` link shape | Navigates to |
|---|---|---|
| Rendered page region | `{ "page": 4, "bbox": [120, 880, 410, 930] }` | a highlighted box on page 4 |
| Text / OCR anchor | `{ "page": 4, "anchor": "ocr_tok_8821" }` | the exact token/word |
| Table cell | `{ "page": 9, "table": "schedule_A", "row": 12 }` | a row in a parsed table |
| Derived / multi-region | `inputs` reference the *records* whose own `source_ref`s point at each contributing region | the chain of source regions |

Rules for a good link:
- **Specific enough to highlight.** "page 4" alone is weak; add a `bbox` or
  `anchor` so the UI can draw a box or scroll to the word.
- **In source coordinates.** A `bbox` is in the coordinate space of the rendered
  page the user actually sees, so the highlight lands correctly.
- **Stable anchors over fragile offsets.** Prefer an OCR token id or `table`+`row`
  (stable across re-renders) to a raw character offset (shifts on re-pagination).
- **It is emitted by the producing tool**, at the moment it knows the region —
  never reconstructed later (see below).

The same `source_ref` is reused by three other patterns: it powers the
verification surface and exports (below), and it is what makes a human correction
a *localized* training label (see
[`verification-flywheel.md`](verification-flywheel.md)). Its typed shape is
defined once in the contract ([`typed-contract.md`](typed-contract.md)).

## A language-neutral record sketch (Go)

Provenance is a typed nested object stored alongside the value (serialized to a
JSON column in a relational DB, or a JSON field in a document store). These are
the generated envelope types from the contract
([`typed-contract.md`](typed-contract.md)) — shown here in Go as the lead example:

```go
// SourceRef — the traceability link. Specific enough that a UI can navigate to it.
type SourceRef struct {
    Page   int       `json:"page"`             // 1-based page/sheet
    Bbox   []float64 `json:"bbox,omitempty"`   // [x1,y1,x2,y2] in source pixel coords
    Anchor *string   `json:"anchor,omitempty"` // stable token/anchor id
    Table  *string   `json:"table,omitempty"`
    Row    *int      `json:"row,omitempty"`
}

// Origin — how the value was produced.
type Origin struct {
    Method       string   `json:"method"`                 // "calc:area", "parse:dimension", "llm_estimate", ...
    Inputs       []string `json:"inputs,omitempty"`       // operand values or upstream record ids
    ModelVersion *string  `json:"model_version,omitempty"`
}

// ExtractedValue — value and its origin are INSEPARABLE. You cannot construct
// one without a SourceRef and an Origin.
type ExtractedValue struct {
    Key        string    `json:"key"`               // what this is, e.g. "wall_area"
    Value      string    `json:"value"`             // exact (decimal-as-string / parsed token)
    Unit       *string   `json:"unit,omitempty"`
    Origin     Origin    `json:"origin"`            // REQUIRED
    SourceRef  SourceRef `json:"source_ref"`        // REQUIRED — no value without a link to source
    Confidence float64   `json:"confidence"`        // 0..1
}
```

Storage note (language-/engine-agnostic): persist the whole envelope as JSON, but
promote to first-class **indexed columns** the two things you'll *query and filter
on* — typically `method` (to filter ungrounded values) and `model_version` (for
the flywheel and per-version accuracy). Everything else lives in the JSON.

```sql
-- illustrative; any relational engine
ALTER TABLE extracted_value
  ADD COLUMN provenance        JSON     NOT NULL,   -- the full envelope
  ADD COLUMN provenance_method VARCHAR  NOT NULL,   -- indexed; filter ungrounded
  ADD COLUMN model_version     VARCHAR  NULL;       -- indexed; flywheel / reproducibility
```

> Secondary-language note: TypeScript generates the same fields as an `interface`;
> Python as a pydantic `BaseModel` with `confidence: confloat(ge=0, le=1)` and
> required `origin`/`source_ref`. The discipline is identical: the value is
> inseparable from its origin and its `source_ref`.

## Where provenance comes from

Provenance is **emitted by the producing tool**, not assembled later by the agent
or a post-processor (see the `ToolResult` envelope in
[`agent-and-tools.md`](agent-and-tools.md)). This is why "the value can only enter
through a tool call" matters: the same call site that computes the value is the
only place that knows its true origin and its `source_ref`. Assembling provenance
after the fact reintroduces guesswork — the exact thing provenance exists to
eliminate. In particular, a `source_ref` reconstructed after the fact is a
*guess* at where the value came from; a `source_ref` emitted by the tool that read
the region is a *fact*.

## How provenance flows to UI and exports

Provenance is not just for audits — it powers the product, and `source_ref` is the
field doing most of the work:

- **Verification UI**: each value links back to its `source_ref` — highlight the
  region on the page, jump to the schedule row, scroll to the token. Confidence +
  method are shown so reviewers triage low-confidence / `llm_estimate` values
  first. Without `source_ref`, a reviewer has to hunt the document by hand.
- **Exports**: annotated outputs (e.g. a PDF with numbered boxes drawn over the
  cited regions, a spreadsheet with a "source page / location" column) are
  generated *from* `source_ref`. The export is only as auditable as the
  `source_ref` behind each value.
- **Filtering / triage**: "show only values whose method is `llm_estimate` or
  whose confidence < 0.7" is the reviewer's first query.

## Replay: the test that provenance is real

Provenance is only meaningful if it is **sufficient to reproduce the value**.
Write a replay test: given a stored record's provenance, re-run the producing
method against the source — using `source_ref` to find the region — and assert
you get the same value. (Go, lead example.)

```go
func TestProvenanceReplays(t *testing.T, rec ExtractedValue, src Source) {
    switch {
    case strings.HasPrefix(rec.Origin.Method, "calc:"):
        op := strings.TrimPrefix(rec.Origin.Method, "calc:")
        got := calculator(op, rec.Origin.Inputs, rec.Unit)
        require.Equal(t, rec.Value, got.Value) // same op + operands → same answer

    case strings.HasPrefix(rec.Origin.Method, "parse:"):
        token := readRegion(src, rec.SourceRef) // crop/OCR the CITED region
        require.Equal(t, rec.Value, parse(token).Value)

    case rec.Origin.Method == "llm_estimate":
        // Cannot replay deterministically — that is the POINT.
        // These are exactly the values that need human verification.
    }
}
```

If a value's provenance does not let you replay it (and it isn't an explicit
`llm_estimate`), the provenance is incomplete — most often because `source_ref`
is too vague to re-read the region, or `inputs` are missing.

## Review checklist

- [ ] Does **every** derived value carry a provenance envelope (never null)?
- [ ] Is `source_ref` present on every value and **specific enough for a UI to
      navigate to** (page+bbox / anchor / table+row), in source coordinates?
- [ ] Is `source_ref` (and the rest of provenance) **emitted by the producing
      tool**, not reconstructed afterward?
- [ ] Can deterministic values be replayed from their provenance, using
      `source_ref` to find the region?
- [ ] Is `method` (or equivalent) queryable/indexed, so you can filter ungrounded
      values?
- [ ] Do calculated values' `inputs` reference their operands' records, so the
      chain bottoms out at real `source_ref` regions?
- [ ] Are stable anchors (token id / table+row) preferred over fragile character
      offsets?
