# Agent-brain / deterministic-hands (patterns 1 & 3)

The agent is an LLM that **orchestrates**: it classifies the input, decides
where to look, picks which tool to call with which arguments, and decides when
it is done. It never writes a final value into the output. Every value that
reaches the structured record is produced by a deterministic tool that also
returns where/how it got it.

## Contents

- The division of labor
- The perception/computation split (pattern 3)
- The tool-result contract
- A framework-light agent loop
- A deterministic calculator tool (kill free-form LLM arithmetic)
- Self-consistency for the agent's *decisions*
- Review checklist

## The division of labor

| Concern | Owner | Why |
|---|---|---|
| What kind of document/region is this? | LLM | Judgment, fuzzy, contextual |
| Where is the relevant content? | LLM (vision) | Spatial/semantic perception |
| Which tool to call, with what args? | LLM | Planning |
| The actual value (count, measure, sum, parse) | **deterministic tool** | Must be exact, replayable, auditable |
| Is the result good enough / am I done? | LLM | Judgment over tool outputs |

Rule of thumb: **if a number in the final output cannot be traced to a specific
tool call, the design is wrong.**

## The perception/computation split (pattern 3)

Vision models are good at *localization* ("the dimension label is in this
box", "there are door symbols clustered here") and bad at *exact reading and
arithmetic*. So split it:

```
VLM:  "the total appears in the box at (x1,y1,x2,y2)"   ← WHERE
tool: crop that box → OCR/parse → "12,408.55"           ← WHAT (the value)
tool: parse "12,408.55" → Decimal("12408.55")           ← typed value + provenance
```

The VLM's bounding box becomes part of the provenance (the source location); the
tool's parse is the value. Neither alone is trusted to do the other's job.

## The tool-result contract

Every tool returns a uniform envelope so the agent can reason over results and
so provenance is captured at the source, not bolted on later:

```python
from dataclasses import dataclass, field
from typing import Any, Literal

@dataclass
class ToolResult:
    ok: bool
    value: Any = None                  # the typed, computed value (or None)
    provenance: dict[str, Any] = field(default_factory=dict)
    # provenance keys: method, source_ref, inputs, confidence — see provenance.md
    error: str | None = None           # human-readable, for the agent to react to
    kind: Literal["value", "noop", "fallback"] = "value"
```

Tools never raise into the agent loop for *expected* failures (region empty,
model absent) — they return `ok=False` with an `error` the agent can act on. A
raised exception means a real bug.

## A framework-light agent loop

Model-provider-agnostic. The loop hands the LLM a tool catalog, executes the
tool it picks, feeds the result back, and repeats until the LLM stops asking
for tools or a turn cap is hit. The key invariant is the assertion at the end:
**no value enters the output except through a tool call.**

```python
MAX_TURNS = 8  # bound the loop; an agent that never stops is a bug

def run_agent(llm, tools: dict[str, callable], doc_context: dict) -> list[dict]:
    """Drive the LLM to produce provenanced records for one document/region.

    `tools` maps tool-name -> callable(**args) -> ToolResult.
    `llm.step(messages, tool_specs)` returns either:
      - {"tool": name, "args": {...}}   (the model wants a tool run)
      - {"done": True, "records": [...]} (the model is finished)
    Every record the model emits MUST reference a prior tool_call_id.
    """
    messages = [system_prompt(), user_prompt(doc_context)]
    produced: dict[str, ToolResult] = {}   # tool_call_id -> result

    for _ in range(MAX_TURNS):
        decision = llm.step(messages, tool_specs(tools))

        if decision.get("done"):
            records = decision["records"]
            # INVARIANT: the model may only assemble/label values that a tool
            # produced. It cannot introduce a fresh number here.
            for r in records:
                src = produced.get(r["from_tool_call"])
                assert src and src.ok, "record cites no successful tool call"
                r["value"] = src.value            # value comes from the tool, not the LLM
                r["provenance"] = src.provenance  # carry origin forward
            return records

        name, args = decision["tool"], decision["args"]
        result = tools[name](**args) if name in tools else ToolResult(
            ok=False, error=f"unknown tool {name!r}")
        call_id = decision["tool_call_id"]
        produced[call_id] = result
        messages.append(tool_response_message(call_id, result))

    return []  # turn cap hit: caller marks region as needs-review, not "done"
```

Notes that matter in production:
- **Bound the loop** (`MAX_TURNS`). Cap-hit is a review signal, not a silent
  empty result.
- **The model proposes records; the harness fills in `value`/`provenance` from
  the tool that ran.** The model literally cannot type a number into the output.
- Multi-turn lets the model chain tools (locate → crop → parse → sum) instead of
  doing it all in one hallucination-prone shot.

## A deterministic calculator tool

Never let the model "calculate the total." Hand it a calculator tool with a
fixed set of operations over numeric operands, using exact decimal math:

```python
from decimal import Decimal, getcontext
getcontext().prec = 28

def calculator(op: str, operands: list[str], unit: str | None = None) -> ToolResult:
    """Deterministic math over decimal operands. The LLM chooses op + operands;
    it does NOT do the arithmetic itself."""
    nums = [Decimal(str(o)) for o in operands]
    try:
        if   op == "sum":     value = sum(nums, Decimal(0))
        elif op == "product": value = math_prod(nums)
        elif op == "area":    value = nums[0] * nums[1]          # w * h
        elif op == "diff":    value = nums[0] - nums[1]
        else: return ToolResult(ok=False, error=f"unsupported op {op!r}")
    except Exception as e:                    # malformed operand, etc.
        return ToolResult(ok=False, error=f"calc failed: {e}")

    return ToolResult(ok=True, value=value, provenance={
        "method": f"calc:{op}",
        "inputs": [str(n) for n in nums],     # exact operands → fully replayable
        "unit": unit,
        "confidence": 1.0,                     # math is exact; confidence is in the operands
    })

def math_prod(nums):
    out = Decimal(1)
    for n in nums: out *= n
    return out
```

The provenance records the *operation and the exact operands*, so anyone can
re-run the math and get the same answer. A wrong total is then always traceable
to a wrong operand (which itself has provenance), never to "the model was bad at
arithmetic."

## Self-consistency for the agent's *decisions*

The agent's judgments (classification, which region, which tool) can still vary
run-to-run. For high-stakes decisions, run the decision step N times and take
the majority; if the runs disagree beyond a threshold, mark the
value `needs_review` rather than picking one. This applies to the *decision*,
not the value — the value is deterministic once the decision is fixed.

## Review checklist

- [ ] Can you point at the tool call that produced every output value?
- [ ] Does any prompt ask the model to return a final number directly? (bug)
- [ ] Does any prompt ask the model to do arithmetic? → calculator tool.
- [ ] Does every tool return the uniform result envelope with provenance?
- [ ] Is the agent loop bounded, with cap-hit routed to review (not "done")?
- [ ] Does the harness — not the model — copy `value` from the tool into the record?
