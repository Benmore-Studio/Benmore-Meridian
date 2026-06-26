# Structured provenance on every derived value (pattern 2)

Provenance is a **structured field that travels with the value**, not a log
line. It answers, for any value in the output: *where in the source did this
come from, how was it produced, from what inputs, and how confident are we?*

If you build only one thing from this methodology, build this — and build it
first. Retrofitting provenance after the extraction code exists means revisiting
every value-producing path. Stamping it from day one (even on a pure-LLM v1)
means the audit surface always exists.

## Contents

- The origin record (what to capture)
- A framework-light model-field sketch
- Where provenance comes from (the source)
- How provenance flows to UI and exports
- Replay: the test that provenance is real
- Review checklist

## The origin record

Minimum viable origin record for a derived value:

| Field | Meaning | Example |
|---|---|---|
| `method` | how the value was produced | `"detector:doorwin"`, `"parse:dimension"`, `"calc:area"`, `"schedule_lookup"`, `"llm_estimate"` |
| `source_ref` | *where* in the source — must be specific enough to navigate to | `{"page": 4, "bbox": [x1,y1,x2,y2]}` or `{"table": "schedule_A", "row": 12}` |
| `inputs` | the upstream values/operands this was derived from | `["12.0", "8.5"]` or `[<id of another record>]` |
| `confidence` | 0–1, from the producing tool/model | `0.92` |
| `model_version` | which detector/model/ruleset produced it (for the flywheel + reproducibility) | `"doorwin-v3"` |

`method` is the single most useful field: it lets you filter "show me every
value that came from an `llm_estimate`" — i.e. exactly the values that are *not*
fully grounded and deserve scrutiny.

Keep provenance **composable**: a calculated total's `inputs` point at the
records of its operands, each of which has its own provenance. Tracing a wrong
total walks the chain down to the wrong leaf.

## A framework-light model-field sketch

Provenance is a typed nested object stored as JSON on the record. The sketch
below is plain dataclasses (serialize to a JSON column in any ORM / a JSON field
in any document store):

```python
from dataclasses import dataclass, asdict, field
from typing import Any

@dataclass
class SourceRef:
    """Specific enough that a UI can navigate the user to it."""
    locator: dict[str, Any]   # {"page": 4, "bbox": [..]} or {"table": .., "row": ..}

@dataclass
class Provenance:
    method: str                          # how (see table above)
    source_ref: SourceRef
    inputs: list[str] = field(default_factory=list)   # operand values or upstream record ids
    confidence: float = 0.0              # 0..1
    model_version: str | None = None

@dataclass
class DerivedValue:
    """A value as stored in the structured output. The value and its origin are
    inseparable — you cannot construct one without the other."""
    key: str                  # what this is, e.g. "wall_area"
    value: str                # store exact (Decimal-as-str / parsed token)
    unit: str | None
    provenance: Provenance    # REQUIRED — no value without an origin

    def to_row(self) -> dict:
        return {"key": self.key, "value": self.value, "unit": self.unit,
                "provenance": asdict(self.provenance)}
```

ORM note (illustrative, framework-agnostic): add a `provenance = JSONField()`
column on the record table, plus first-class columns for the two things you'll
*query and index* — typically `method` (to filter ungrounded values) and
`model_version` (for the flywheel and reproducibility). Everything else can live
inside the JSON.

```
# pseudo-migration
ALTER TABLE extracted_value
  ADD COLUMN provenance        JSON     NOT NULL,
  ADD COLUMN provenance_method VARCHAR  NOT NULL,   -- indexed; filter ungrounded
  ADD COLUMN model_version     VARCHAR  NULL;        -- indexed; flywheel/repro
```

## Where provenance comes from

Provenance is **emitted by the producing tool**, not assembled later by the
agent or a post-processor (see the `ToolResult.provenance` envelope in
`agent-and-tools.md`). This is why "the value can only enter through a tool
call" matters: the same call site that computes the value is the only place
that knows its true origin. Assembling provenance after the fact reintroduces
guesswork — the exact thing provenance exists to eliminate.

## How provenance flows to UI and exports

Provenance is not just for audits — it powers the product:

- **Verification UI**: each value links back to its `source_ref` (highlight the
  region on the page, jump to the schedule row). Confidence + method are shown
  so reviewers triage low-confidence / `llm_estimate` values first.
- **Exports**: annotated outputs (e.g. a PDF with numbered boxes over the
  source regions, a spreadsheet with a "source" column) are generated *from*
  `source_ref`. The export is only as auditable as the provenance behind it.
- **Filtering**: "show only values whose method is `llm_estimate` or whose
  confidence < 0.7" is the reviewer's triage query.

## Replay: the test that provenance is real

Provenance is only meaningful if it is **sufficient to reproduce the value**.
Write a replay test: given a stored record's provenance, re-run the producing
method against the source and assert you get the same value.

```python
def test_provenance_replays(record, source):
    p = record.provenance
    if p.method.startswith("calc:"):
        op = p.method.split(":", 1)[1]
        assert calculator(op, p.inputs).value == Decimal(record.value)
    elif p.method.startswith("parse:"):
        token = read_region(source, p.source_ref.locator)   # crop/OCR the cited region
        assert parse(token) == record.value
    # llm_estimate: cannot replay deterministically → that's the point.
    #   These are exactly the values that need human verification.
```

If a value's provenance does not let you replay it (and it isn't an explicit
`llm_estimate`), the provenance is incomplete.

## Review checklist

- [ ] Does **every** derived value carry a provenance object (never null)?
- [ ] Is `source_ref` specific enough for a UI to navigate to it?
- [ ] Is provenance emitted by the producing tool, not assembled afterward?
- [ ] Can deterministic values be replayed from their provenance?
- [ ] Is `method` (or equivalent) queryable, so you can filter ungrounded values?
- [ ] Do calculated values' `inputs` reference their operands' records (a chain)?
