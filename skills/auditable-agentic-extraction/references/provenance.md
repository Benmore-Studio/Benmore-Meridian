# Structured provenance on every derived value (pattern 2)

Provenance is a **structured field that travels with the value**, not a log
line. It answers, for any value in the output: *where in the source did this
come from, how was it produced, from what inputs, and how confident are we?*

If you build only one thing from this methodology, build this — and build it
first. Retrofitting provenance after the extraction code exists means revisiting
every value-producing path. Stamping it from day one (even on a pure-LLM v1)
means the audit surface always exists.

The unit that carries provenance is not only a scalar value. The same
`origin` + `source_ref` envelope attaches to every **claim kind**: an
`ExtractedValue` (a number), an `Annotation` (a highlighted span/clause — see
[`annotations-and-highlights.md`](annotations-and-highlights.md)), a `Relation`
(a cross-reference or defined-term link), and a `Change` (a diff between two
versions — see [`comparison-and-versioning.md`](comparison-and-versioning.md)).
Everything below is written for a "value", but read "claim": a clause boundary
and a redline are produced by tools and stamped with provenance exactly as a
number is, and the LLM authors none of them directly.

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

> The `method` values below name a *rung on the value-source ladder* (`calc:`,
> `parse:`, `lookup:`, `detector:`, `ocr:`, `llm_estimate`) plus a domain detail.
> The rungs are fixed by the methodology; the detail is yours. Examples are shown
> across domains so nothing here is construction-specific. See the ladder in
> [`agent-and-tools.md`](agent-and-tools.md).

| Field | Meaning | Example (varies by domain) |
|---|---|---|
| `method` | which rung produced the value (`<rung>:<detail>`) | `"parse:line_item_qty"` (invoice), `"calc:area"` (takeoff), `"detector:abnormal_range"` (lab), `"lookup:sku"`, `"llm_estimate"` |
| `source_ref` | *where* in the source — names the `doc_id` (+ `version`) and a locator specific enough to navigate to | `{"doc_id":"d9…","page": 4, "bbox": [x1,y1,x2,y2]}` or `{"doc_id":"d9…","span":{"start_anchor":"tok_8821","end_anchor":"tok_8907"}}` |
| `inputs` | the upstream values/operands this was derived from | `["12.0", "8.5"]` or `[<id of another record>]` |
| `confidence` | 0–1, sourced per rung (see below) | `0.92` |
| `model_version` | which detector/model/ruleset produced it (for the flywheel + reproducibility) | `"detector-v3"` |

`method` is the single most useful field for triage: it lets you filter "show me
every value at rung ≥4 (`detector`/`ocr`/`llm_estimate`)" — i.e. exactly the
values that are *not* fully grounded and deserve scrutiny.

Keep provenance **composable**: a calculated total's `inputs` point at the
records of its operands, each of which has its own provenance (and its own
`source_ref`). Tracing a wrong total walks the chain down to the wrong leaf,
which bottoms out at a real source region. Keep chains shallow and acyclic —
`inputs` reference *prior* records only, so the graph is a DAG you can walk
without looping; if a leaf is later corrected, recompute its dependents rather
than leaving them stale.

## Where `confidence` comes from (and how to combine it)

`confidence` is only meaningful if it is sourced consistently — otherwise sorting
by it is theatre. Set it **per rung**, and combine it **conservatively** when a
value derives from others:

- **Leaf values** take the producing rung's confidence: a detector's own score
  (rung 4), an OCR engine's score (rung 5), a fixed-high constant for an exact
  parse (rung 2), or the *measured* accuracy of a lookup path (rung 3) — never a
  number plucked from the air. An `llm_estimate` (rung 6) is low by construction.
- **Derived values** (rung 1, `calc:`) inherit `min(operand confidences)`: exact
  math adds no error, so a result is only as sure as its shakiest input. (Use
  `min` for a conservative floor; a product of confidences is defensible if your
  inputs are independent — pick one rule and apply it everywhere.)
- **The tool's score and the record's confidence are distinct.** A detector
  returns an internal score in its `ToolResult`; the harness maps that into the
  record's `confidence`. Document the mapping; don't conflate them.
- **Human verification does not set `confidence = 1.0`.** A confirmed value keeps
  its automation confidence and gains a separate `status = verified` (see
  [`verification-flywheel.md`](verification-flywheel.md)) — so you can still
  measure how good the automation *was*.

## `source_ref`: the traceability link (first-class)

`source_ref` is the field that earns the word *auditable*. It is the link from a
value **back to the exact place in the document it came from**, so an auditor (or
the verification UI, or a training-label) can go look. Everything else in
provenance describes *how*; `source_ref` answers *where* — and "where" is what a
human checks first.

A `source_ref` always names **which document** (`doc_id`) and, in a versioned
corpus, **which version** (`version`) — so a value is traceable even when many
documents and revisions coexist (see
[`comparison-and-versioning.md`](comparison-and-versioning.md)). Then it sets a
locator. Make it specific enough to **navigate to**. The link is a small set of
locator families; pick the one the source supports:

| Source kind | `source_ref` link shape | Navigates to |
|---|---|---|
| Rendered page region | `{ "doc_id": "d9…", "page": 4, "bbox": [120, 880, 410, 930] }` | a highlighted box on page 4 |
| Text / token anchor | `{ "doc_id": "d9…", "page": 4, "anchor": "tok_8821" }` | the exact token/word |
| Table cell | `{ "doc_id": "d9…", "page": 9, "table": "schedule_A", "row": 12 }` | a row in a parsed table |
| **Span** (a region of text) | `{ "doc_id": "d9…", "span": { "start_anchor": "tok_8821", "end_anchor": "tok_8907" } }` | a whole clause/phrase, possibly multi-page |
| Derived / multi-region | `inputs` reference the *records* whose own `source_ref`s point at each contributing region | the chain of source regions |

`anchor`/`span` ids are stable token ids in the **canonical document model**
([`document-model.md`](document-model.md)) — *not* raw character offsets, which
shift on re-pagination and re-OCR. The canonical model is what makes a
`source_ref` survive a re-render or a new version; build it before you stamp
anchors.

Rules for a good link:
- **Specific enough to highlight.** "page 4" alone is weak; add a `bbox`,
  `anchor`, or `span` so the UI can draw a box or scroll to the word.
- **In canonical coordinates.** A `bbox` is in the canonical page coordinate
  space ([`document-model.md`](document-model.md)), not raw render pixels at an
  arbitrary DPI, so the highlight lands correctly after any re-render.
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
    DocID   string    `json:"doc_id"`            // REQUIRED — which document
    Version *string   `json:"version,omitempty"` // which revision, in a versioned corpus
    Page    int       `json:"page,omitempty"`    // 1-based page/sheet (point locators)
    Bbox    []float64 `json:"bbox,omitempty"`    // [x1,y1,x2,y2] in CANONICAL page coords
    Anchor  *string   `json:"anchor,omitempty"`  // stable token id (canonical model)
    Table   *string   `json:"table,omitempty"`
    Row     *int      `json:"row,omitempty"`
    Span    *Span     `json:"span,omitempty"`    // a region of text (clause/phrase), may cross pages
}

// Span — a contiguous range delimited by stable anchors (see document-model.md).
type Span struct {
    StartAnchor string `json:"start_anchor"`
    EndAnchor   string `json:"end_anchor"`
    // chars[] and per-page regions[] are carried in the wire envelope
    // (envelope.openapi.yaml); chars are a fragile HINT, re-anchor on read.
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
