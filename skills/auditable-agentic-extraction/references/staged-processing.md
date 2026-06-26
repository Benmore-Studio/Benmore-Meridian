# Document-wide staged processing with progress events (pattern 7)

Process the **whole document** through a sequence of named stages rather than
looping page-by-page in one opaque step. Each stage:
- has a name the UI can show,
- emits a **progress event** when it starts/finishes,
- is **idempotent** (safe to re-run after a retry),
- can be **resumed** from the last completed stage.

This is the spine that runs the agent loop
([`agent-and-tools.md`](agent-and-tools.md)) over the document and applies
gating/degradation ([`degradation-and-gating.md`](degradation-and-gating.md)) at
each step. Code is **language-neutral with Go as the lead example**; the spine is
just "run named functions in order, persisting between them" — no framework
required.

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

Lightweight orchestrator. Each stage is a function `(DocState) -> DocState` that
reads the accumulated state and writes its output back. The orchestrator persists
state and emits events between stages. Go (lead example):

```go
type DocState struct {
    DocID           string
    CompletedStages []string
    Artifacts       map[string]any // per-stage output, keyed by stage name
}

type Stage struct {
    Name string
    Fn   func(DocState) (DocState, error)
}

type Event struct {
    Stage  string `json:"stage"`
    Status string `json:"status"` // "started" | "finished" | "failed"
    Index  int    `json:"index"`
    Total  int    `json:"total"`
    Err    string `json:"error,omitempty"`
}

// runPipeline runs stages in order, resuming after the last completed one.
//   emit(docID, ev) publishes progress (WebSocket / event bus / etc.)
//   save(state)     persists state so a retry can resume.
func runPipeline(state DocState, stages []Stage,
    emit func(string, Event), save func(DocState) error) (DocState, error) {

    total := len(stages)
    done := map[string]bool{}
    for _, s := range state.CompletedStages {
        done[s] = true
    }

    for i, st := range stages {
        if done[st.Name] {
            continue // resume: skip already-done work
        }
        emit(state.DocID, Event{Stage: st.Name, Status: "started", Index: i, Total: total})

        next, err := st.Fn(state) // stage does its work, writes artifacts
        if err != nil {
            emit(state.DocID, Event{Stage: st.Name, Status: "failed", Index: i, Total: total, Err: err.Error()})
            return state, err // let the queue retry; resume picks up here
        }
        state = next
        state.CompletedStages = append(state.CompletedStages, st.Name)
        if err := save(state); err != nil { // checkpoint AFTER the stage succeeds
            return state, err
        }
        emit(state.DocID, Event{Stage: st.Name, Status: "finished", Index: i, Total: total})
    }
    emit(state.DocID, Event{Stage: "done", Status: "finished", Index: total, Total: total})
    return state, nil
}
```

> Secondary-language note: the same shape in Python is a list of
> `(name, fn)` tuples and a `for` loop; the orchestrator is deliberately tiny so
> it ports cleanly. What matters is the *contract* (named stages, checkpoint after
> success, emit on boundaries), not the language.

## Progress events

Emit a structured event at each stage boundary so the UI can render a stepper
and so an external watchdog can tell the job is alive (see reaping below).
Carry `index`/`total` so the UI can show "stage 4 of 6", and include the doc id
so multiple concurrent documents don't cross wires.

For real-time delivery (WebSocket etc.): **accept the connection first, then
authenticate** (e.g. a token in the first message), rather than authenticating
in the connection URL — query-string credentials leak into logs and proxies.

## Idempotency & resumability

Stages typically run on an **at-least-once background queue** — any such system
(message queue, task runner, durable-execution engine) can redeliver a job on
retry — so every stage must be safe to run twice:

- **Checkpoint after success.** Append to `completed_stages` and `save` only
  once the stage finished; on resume, completed stages are skipped.
- **Make writes upsert, not append.** A re-run of `detect` should replace its
  prior output for the document, not add a second copy. Key artifacts by
  `(doc_id, stage)` (and region id where relevant).
- **Guard external side effects** (charges, emails, notifications) with an
  idempotency key so a redelivered job doesn't double-fire.

```go
func detectStage(state DocState) (DocState, error) {
    regions := locateRegions(state.Artifacts["pages"])
    // upsert: overwrite THIS doc's detect output rather than appending a 2nd copy
    state.Artifacts["regions"] = regions
    if err := persistRegions(state.DocID, regions /* replace= */, true); err != nil {
        return state, err
    }
    return state, nil
}
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

```go
func isStuck(doc Doc, inactivityLimit time.Duration) bool {
    return time.Since(doc.LastActivityAt) > inactivityLimit
    // NOTE: deliberately NOT time.Since(doc.StartedAt) — total runtime is not the signal.
}
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
