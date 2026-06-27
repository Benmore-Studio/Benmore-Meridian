# Agent-brain / deterministic-hands (patterns 1 & 3)

The agent is an LLM that **orchestrates**: it classifies the input, decides
where to look, picks which tool to call with which arguments, and decides when
it is done. It never writes a final value into the output. Every value that
reaches the structured record is produced by a **tool** that also returns
where/how it got it — deterministic where possible, but always *attributable*
(see the methods ladder below).

Code below is **language-neutral with Go as the lead example**; a brief
secondary-language note follows each concept where it helps. The concepts —
"a tool", "the result envelope", "the agent loop" — are not tied to any
framework.

## Contents

- The division of labor
- Methods of providing a value (the ladder)
- The perception/computation split (pattern 3)
- The tool-result contract (typed, never a blob)
- A language-neutral agent loop (Go)
- A deterministic calculator tool (kill free-form LLM arithmetic)
- Self-consistency for the agent's *decisions*
- Review checklist

## The division of labor

| Concern | Owner | Why |
|---|---|---|
| What kind of document/region is this? | LLM | Judgment, fuzzy, contextual |
| Where is the relevant content? | LLM (vision) | Spatial/semantic perception |
| Which tool to call, with what args? | LLM | Planning |
| The actual value (count, measure, sum, parse) | **a tool, never the LLM** | Must be attributable — exact and replayable where the rung allows |
| Is the result good enough / am I done? | LLM | Judgment over tool outputs |

Rule of thumb: **if a number in the final output cannot be traced to a specific
tool call, the design is wrong.**

## Methods of providing a value (the ladder)

"A tool produces the value" raises the obvious question: *which* tool, and how
much do you trust it? There is more than one legitimate way a value enters the
output. Rank them — prefer the highest rung the input supports, and always stamp
which rung you used in `origin.method` so reviewers can triage by it.

| Rung | `method` (convention) | Produces the value by | Replayable? | Where `confidence` comes from |
|---|---|---|---|---|
| 1. Exact computation | `calc:<op>` | exact decimal math over operands | **yes** (same op+operands → same answer) | inherited: `min` of operand confidences (the math adds no error) |
| 2. Exact parse | `parse:<kind>` | deterministic parse of a read token (`"12'-6\""` → `12.5`) | **yes** (re-parse the cited region) | high, fixed (e.g. `0.99`); parse is exact, the *read* is the risk |
| 3. Reference lookup | `lookup:<table>` | reading a structured table/standard the source points at | yes (re-read the row) | measured accuracy of that lookup path, not a guess (see degradation-and-gating.md) |
| 4. Model inference | `detector:<name>` | an ML detector/classifier over a region | *reproducible*, not deterministic (stochastic; pin seeds/temp to approximate) | the detector's own score, mapped into `[0,1]` |
| 5. OCR / transcription | `ocr:<engine>` | reading characters off a pixel region | weakly reproducible (engines vary run-to-run) | engine score; **re-read to verify high-stakes values** |
| 6. LLM estimate | `llm_estimate` | the model's best guess when nothing above applies | **no** — and that is the point | low by construction; always routed to human review |

Reading the ladder:
- **Higher is more trustworthy and more auditable.** Reach for the lowest rung
  only when the input genuinely cannot support a higher one (no text layer, no
  detector, no schedule). A field that *could* be parsed but is `llm_estimate`d
  is a design smell, not a fallback.
- **Rungs 4–6 are not "deterministic" — they are still attributable.** The
  invariant is that the value entered through a tool call carrying `method` +
  `source_ref` + `confidence`, never that the same input always yields the same
  bits. Use the word *attributable*, not *deterministic*, when a rung is
  probabilistic.
- **Transcription (rung 5) needs a verify step for high-stakes values.** An LLM
  or OCR reading `12,408.55` off a crop *is* the model authoring a value unless
  something checks it — re-read the cited `source_ref` region with a second
  method (or a human) and compare before trusting it.
- `method` is the single most useful triage field: "show every value at rung ≥4"
  is exactly the set a reviewer should look at first.

### Structural claims use the same ladder

The output is not always a scalar. A clause boundary, a cross-reference link, and
a redline between two versions are **claims** too, and they obey the same rule:
a tool produces them and stamps `method` + `source_ref` + `confidence`; the LLM
never just asserts them. Three more `method` rungs cover structural work:

| `method` | Produces | Replayable? | `confidence` from |
|---|---|---|---|
| `segment:<unit>` | splits a document into comparable units (clauses, sentences, rows) using the canonical model + structure | yes (deterministic over a fixed canonical model) | high if rule-based; detector score if learned |
| `align:<unit>` | matches a unit in version A to its counterpart in version B (across renumbering/moves) | reproducible | similarity/match score; low matches → human review |
| `diff:<granularity>` | computes the change between two aligned units (text or semantic) | yes for textual; reproducible for semantic | textual = high; semantic/materiality often `llm_estimate`-grade → review-first |

These power [`comparison-and-versioning.md`](comparison-and-versioning.md) and
[`annotations-and-highlights.md`](annotations-and-highlights.md). The same
discipline holds: the LLM may *propose* an alignment for an ambiguous clause, but
the match is recorded as a tool result with a `source_ref` into **both** versions
— not as a free-text claim the model wrote.

## The perception/computation split (pattern 3)

Vision models are good at *localization* ("the total is in this box", "the
table of line items starts here", "these repeated symbols cluster in this
region") and bad at *exact reading and arithmetic*. So split it:

```
VLM:  "the total appears in the box at (x1,y1,x2,y2)"   ← WHERE  (becomes source_ref)
tool: crop that box → OCR/parse → "12,408.55"           ← WHAT   (the value)
tool: parse "12,408.55" → exact decimal 12408.55        ← typed value + provenance
```

The VLM's bounding box becomes the value's `source_ref` (the traceability link —
see [`typed-contract.md`](typed-contract.md) and [`provenance.md`](provenance.md));
the tool's parse is the value. Neither alone is trusted to do the other's job.

## The tool-result contract (typed, never a blob)

Every tool returns a uniform, **typed** envelope so the agent can reason over
results and so provenance is captured at the source, not bolted on later. The
envelope is part of the typed contract ([`typed-contract.md`](typed-contract.md)) —
it is never a raw map/dict.

Go (lead example):

```go
type ResultKind string

const (
    KindValue    ResultKind = "value"
    KindNoop     ResultKind = "noop"
    KindFallback ResultKind = "fallback"
)

// ToolResult is the uniform envelope every tool returns.
type ToolResult struct {
    OK         bool       `json:"ok"`
    Value      string     `json:"value,omitempty"`      // exact value as string (decimal-as-string)
    Unit       *string    `json:"unit,omitempty"`
    Origin     Origin     `json:"origin"`               // method, inputs, model_version — see provenance.md
    SourceRef  SourceRef  `json:"source_ref"`           // WHERE in the source — the traceability link
    Confidence float64    `json:"confidence"`           // 0..1
    Err        string     `json:"error,omitempty"`      // human-readable; the agent reacts to this
    Kind       ResultKind `json:"kind"`
}
```

`Origin` and `SourceRef` are the generated envelope types from
[`typed-contract.md`](typed-contract.md) — the same shapes the stored record uses,
so provenance flows through unchanged.

Tools never panic/throw into the agent loop for *expected* failures (region
empty, model absent) — they return `OK=false` with an `Err` the agent can act on.
A genuine panic/raised exception means a real bug.

> Secondary-language note: in TypeScript this is an `interface ToolResult` with
> the same fields; in Python a pydantic `BaseModel`. The invariant is identical —
> a typed envelope carrying `origin` + `source_ref`, never `map[string]any` /
> `dict` / `any`.

## A language-neutral agent loop (Go)

The loop hands the LLM a tool catalog, executes the tool it picks, feeds the
result back, and repeats until the LLM stops asking for tools or a turn cap is
hit. The key invariant is the final assembly step: **no value enters the output
except through a tool call** — the harness, not the model, copies `value` and
provenance from the tool that ran.

```go
const maxTurns = 8 // bound the loop; an agent that never stops is a bug

// Tool is a function the agent may call (deterministic or attributable; see ladder).
type Tool func(args map[string]any) ToolResult

// Decision is what one LLM step returns: either a tool call or "done".
type Decision struct {
    ToolName   string             // set when the model wants a tool run
    Args       map[string]any
    ToolCallID string
    Done       bool               // set when the model is finished
    Records    []ProposedRecord   // the model proposes records; values come from tools
}

// ProposedRecord is what the model may emit on "done": a label + which prior
// tool call produced the value. It MUST NOT carry a value itself.
type ProposedRecord struct {
    Key          string `json:"key"`
    FromToolCall string `json:"from_tool_call"` // references a prior ToolCallID
}

func runAgent(llm LLM, tools map[string]Tool, doc DocContext) ([]ExtractedValue, error) {
    msgs := initialMessages(doc)
    produced := map[string]ToolResult{} // toolCallID -> result

    for turn := 0; turn < maxTurns; turn++ {
        d := llm.Step(msgs, toolSpecs(tools))

        if d.Done {
            out := make([]ExtractedValue, 0, len(d.Records))
            for _, r := range d.Records {
                src, ok := produced[r.FromToolCall]
                if !ok || !src.OK {
                    return nil, fmt.Errorf("record %q cites no successful tool call", r.Key)
                }
                // INVARIANT: value + provenance come from the TOOL, not the model.
                out = append(out, ExtractedValue{
                    Key:        r.Key,
                    Value:      src.Value,
                    Unit:       src.Unit,
                    Origin:     src.Origin,
                    SourceRef:  src.SourceRef,
                    Confidence: src.Confidence,
                })
            }
            return out, nil
        }

        tool, known := tools[d.ToolName]
        var res ToolResult
        if known {
            res = tool(d.Args)
        } else {
            res = ToolResult{OK: false, Err: "unknown tool " + d.ToolName}
        }
        produced[d.ToolCallID] = res
        msgs = append(msgs, toolResponseMessage(d.ToolCallID, res))
    }

    // turn cap hit: caller marks the region needs-review, NOT "done".
    return nil, errCapHit
}
```

Notes that matter in production:
- **Bound the loop** (`maxTurns`). Cap-hit is a review signal, not a silent empty
  result — the caller routes it to human verification.
- **The model proposes records; the harness fills in `value`/provenance from the
  tool that ran.** The model literally cannot type a number into the output —
  `ProposedRecord` has no value field.
- **Multi-turn lets the model chain tools** (locate → crop → parse → sum) instead
  of doing it all in one hallucination-prone shot.
- Every emitted `ExtractedValue` already carries `SourceRef` (the traceability
  link) because the tool put it there.

## A deterministic calculator tool

Never let the model "calculate the total." Hand it a calculator tool with a fixed
set of operations over numeric operands, using exact decimal math (Go:
`math/big.Rat` or a decimal library; never `float64` for money/measurements).

```go
import (
    "fmt"
    "math/big"
)

// calculator does exact decimal math. The LLM chooses op + operands;
// it does NOT do the arithmetic itself.
func calculator(op string, operands []string, unit *string) ToolResult {
    nums := make([]*big.Rat, 0, len(operands))
    for _, o := range operands {
        r, ok := new(big.Rat).SetString(o)
        if !ok {
            return ToolResult{OK: false, Err: fmt.Sprintf("bad operand %q", o)}
        }
        nums = append(nums, r)
    }

    out := new(big.Rat)
    switch op {
    case "sum":
        out.SetInt64(0)
        for _, n := range nums {
            out.Add(out, n)
        }
    case "product", "area": // area = w * h
        out.SetInt64(1)
        for _, n := range nums {
            out.Mul(out, n)
        }
    case "diff":
        if len(nums) != 2 {
            return ToolResult{OK: false, Err: "diff needs exactly 2 operands"}
        }
        out.Sub(nums[0], nums[1])
    default:
        return ToolResult{OK: false, Err: "unsupported op " + op}
    }

    return ToolResult{
        OK:    true,
        Value: out.FloatString(4), // exact, fixed precision as string
        Unit:  unit,
        Origin: Origin{
            Method: "calc:" + op,
            Inputs: operands, // EXACT operands → fully replayable
        },
        // The math is exact, so it adds NO uncertainty — but the result is only
        // as confident as its least-confident operand. The harness assembling
        // the record sets Confidence = min(operand confidences); 1.0 here means
        // "the operation introduced no error", not "the answer is certain".
        Confidence: 1.0,
        Kind:       KindValue,
    }
}
```

The provenance records the *operation and the exact operands*, so anyone can
re-run the math and get the same answer. A wrong total is then always traceable
to a wrong operand (which itself has its own provenance and `source_ref`), never
to "the model was bad at arithmetic." Confidence flows the same way: a sum is no
more trustworthy than its shakiest input, so combine conservatively
(`min` of the operands' confidences) rather than asserting `1.0` on the total —
see [`provenance.md`](provenance.md).

> Secondary-language note: Python uses `decimal.Decimal` (set `getcontext().prec`),
> TypeScript a decimal library (e.g. `big.js`/`decimal.js`) — the contract is the
> same: a fixed op set, exact decimal operands, `method="calc:<op>"` + `inputs`
> as the replay receipt. Floating-point `number`/`float64` is a bug for any value
> someone is billed against.

## Self-consistency for the agent's *decisions*

The agent's judgments (classification, which region, which tool) can still vary
run-to-run. For high-stakes decisions, run the decision step N times and take the
majority; if the runs disagree beyond a threshold, mark the value `needs_review`
rather than picking one. This applies to the *decision*, not the value — the
value is deterministic once the decision is fixed and the tool runs.

## Review checklist

- [ ] Can you point at the tool call that produced **every** output value?
- [ ] Does any prompt ask the model to return a final number directly? (bug)
- [ ] Does any prompt ask the model to do arithmetic? → route to the calculator tool.
- [ ] Does every tool return the uniform **typed** result envelope (not a
      `map[string]any` / `dict` / `any`) carrying `origin` + `source_ref`?
- [ ] Is the agent loop bounded, with cap-hit routed to review (not "done")?
- [ ] Does the **harness — not the model** — copy `value`/provenance from the tool
      into the record?
- [ ] Does the proposed-record type the model emits have **no value field** (so it
      structurally cannot author a number)?
- [ ] Is exact decimal math used for every billable value (no `float64`/`number`)?
