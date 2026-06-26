# Document-wide staged processing with progress events (pattern 7)

Process the **whole document** through a sequence of named stages rather than
looping page-by-page in one opaque step. Each stage:
- has a name the UI can show,
- emits a **progress event** when it starts/finishes,
- is **idempotent** (safe to re-run after a retry),
- can be **resumed** from the last completed stage.

This is the spine that runs the agent loop (patterns 1/3) over the document and
applies gating/degradation (5/6) at each step.

## Contents

- Why document-wide, staged
- The stage spine (code)
- Progress events
- Idempotency & resumability
- Activity-based reaping (no wall-clock timeouts)
- Review checklist

## Why document-wide, staged

A per-page loop that does "see → measure → output" in one shot can't:
- reconcile information that spans pages (a total on page 1 that depends on a
  schedule on page 9);
- show meaningful progress ("measuring", "reconciling") versus a single spinner;
- resume after a crash without redoing everything.

A document-wide staged spine does each phase across the whole document, so later
stages can use the consolidated output of earlier ones, and the UI can show a
stepper.

A representative spine (names are illustrative — adapt to the domain):

```
classify ─► detect ─► measure ─► understand ─► reconcile ─► finalize
   │           │         │            │             │           │
 page types  locate    compute     cross-ref     resolve     emit
            regions    values      context       conflicts   records
```

## The stage spine

Framework-light orchestrator. Each stage is a function
`(doc_state) -> doc_state` that reads the accumulated state and writes its
output back. The orchestrator persists state and emits events between stages.

```python
from dataclasses import dataclass, field
from typing import Callable, Any

@dataclass
class DocState:
    doc_id: str
    completed_stages: list[str] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)   # per-stage output

Stage = tuple[str, Callable[[DocState], DocState]]

def run_pipeline(state: DocState, stages: list[Stage], emit, save):
    """Run stages in order, resuming after the last completed one.
    `emit(doc_id, event)` publishes progress (WebSocket/queue/etc.).
    `save(state)` persists state so a retry can resume."""
    total = len(stages)
    for i, (name, fn) in enumerate(stages):
        if name in state.completed_stages:
            continue                           # resume: skip already-done work
        emit(state.doc_id, {"stage": name, "status": "started",
                            "index": i, "total": total})
        try:
            state = fn(state)                  # stage does its work, writes artifacts
        except Exception as e:
            emit(state.doc_id, {"stage": name, "status": "failed", "error": str(e)})
            raise                              # let the queue retry; resume picks up here
        state.completed_stages.append(name)
        save(state)                            # checkpoint AFTER the stage succeeds
        emit(state.doc_id, {"stage": name, "status": "finished",
                            "index": i, "total": total})
    emit(state.doc_id, {"stage": "done", "status": "finished",
                        "index": total, "total": total})
    return state
```

## Progress events

Emit a structured event at each stage boundary so the UI can render a stepper
and so an external watchdog can tell the job is alive (see reaping below).
Carry `index`/`total` so the UI can show "stage 4 of 6", and include the doc id
so multiple concurrent documents don't cross wires.

For real-time delivery (WebSocket etc.): **accept the connection first, then
authenticate** (e.g. a token in the first message), rather than authenticating
in the connection URL — query-string credentials leak into logs and proxies.

## Idempotency & resumability

Stages run on an at-least-once queue (Celery and friends redeliver on retry), so
every stage must be safe to run twice:

- **Checkpoint after success.** Append to `completed_stages` and `save` only
  once the stage finished; on resume, completed stages are skipped.
- **Make writes upsert, not append.** A re-run of `detect` should replace its
  prior output for the document, not add a second copy. Key artifacts by
  `(doc_id, stage)` (and region id where relevant).
- **Guard external side effects** (charges, emails, notifications) with an
  idempotency key so a redelivered task doesn't double-fire.

```python
def detect_stage(state: DocState) -> DocState:
    regions = locate_regions(state.artifacts["pages"])
    # upsert: overwrite this doc's detect output rather than appending
    state.artifacts["regions"] = regions          # replace, idempotent
    persist_regions(state.doc_id, regions, replace=True)
    return state
```

## Activity-based reaping (no wall-clock timeouts)

Do **not** kill a long-running document by elapsed wall-clock time — a large
document legitimately takes longer, and a fixed timeout kills good work. Instead,
reap on **lack of progress**:

- Each progress event updates a `last_activity_at` heartbeat for the document.
- A reaper marks a job stuck only when `now - last_activity_at` exceeds an
  *inactivity* threshold (no stage boundary crossed in N minutes), not when
  total runtime exceeds a cap.
- This distinguishes "still working, just big" (heartbeats advancing) from
  "genuinely hung" (heartbeats frozen).

```python
def is_stuck(doc, inactivity_limit_s) -> bool:
    return (now() - doc.last_activity_at).total_seconds() > inactivity_limit_s
    # NOTE: deliberately not (now() - doc.started_at) — runtime is not the signal.
```

Each emitted stage event should bump `last_activity_at`; long stages that do
internal work can heartbeat mid-stage too.

## Review checklist

- [ ] Is processing organized into named stages with start/finish events?
- [ ] Do events carry doc id + index/total so the UI can show a stepper?
- [ ] Is state checkpointed after each stage so retries resume, not restart?
- [ ] Are stage writes upserts (re-run replaces, doesn't duplicate)?
- [ ] Are external side effects idempotency-keyed against redelivery?
- [ ] Is the watchdog based on inactivity, not total runtime?
- [ ] (Real-time) Does the socket accept-then-authenticate, not auth-in-URL?
