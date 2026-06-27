# Human verification + correction flywheel (pattern 4)

Two jobs, one loop:
1. **Verification** — a human confirms or corrects each value before it is
   trusted. This is the safety net for everything the automation got wrong.
2. **Flywheel** — every correction is captured as a *labeled example* that
   improves the detectors/models, so the same mistake gets rarer over time.

The insight: a correction is not just a patch to one record — it is a free,
high-quality, in-distribution training label that you already paid a human to
produce. Throwing it away is the most expensive mistake in the whole design.

Code is **language-neutral with Go as the lead example**; "a persisted record"
and "a training label" are just rows in whatever store you use. This loop is
powered by `source_ref` ([`provenance.md`](provenance.md)) — it is what makes a
correction a *localized* label.

## Contents

- The verification surface
- The verify/correct loop (code)
- Turning a correction into a label
- Closing the loop: retrain → measure → deploy
- Accuracy metrics that matter
- Review checklist

## The verification surface

Provenance (pattern 2) is what makes verification fast, and `source_ref` is the
field that makes it *possible* — without it the reviewer has no way to find the
value in the document. The UI should let a reviewer, per value:
- see the value, its `confidence`, and its `method`;
- jump to the `source_ref` — highlight the region (bbox), scroll to the row
  (table+row), or focus the token (anchor);
- **confirm** (value is right), **correct** (supply the right value), or
  **flag** (can't tell — needs escalation, must leave a note).

Triage by sorting on confidence ascending and surfacing `llm_estimate` /
fallback-method values first — those are the least grounded.

## The verify/correct loop

Go (lead example). A record is just a persisted row; `Save` writes it back.

```go
type Verdict string

const (
    Confirm Verdict = "confirm" // automation was right
    Correct Verdict = "correct" // human supplied a different value
    Flag    Verdict = "flag"    // cannot determine; needs escalation + note
)

func applyVerification(rec *Record, v Verdict, correctedValue, note string, user User) error {
    switch v {
    case Confirm:
        rec.Status = "verified"
        emitLabel(rec, rec.Value, "confirmation")

    case Correct:
        if correctedValue == "" {
            return errors.New("correction requires a value")
        }
        rec.OriginalValue = rec.Value  // keep what the model said
        rec.Value = correctedValue     // human value wins
        rec.Status = "verified"
        emitLabel(rec, correctedValue, "correction") // the disagreement is the gold

    case Flag:
        if note == "" {
            return errors.New("flag requires a note") // no silent flags
        }
        rec.Status = "flagged"
        rec.ReviewNote = note
    }
    rec.VerifiedBy = user.ID
    rec.VerifiedAt = time.Now()
    return rec.Save()
}

// documentIsVerified is the completeness gate: a document is "verified" only
// when EVERY value is confirmed/corrected, or flagged-with-a-note. No silent gaps.
func documentIsVerified(records []Record) bool {
    for _, r := range records {
        switch r.Status {
        case "verified":
            // ok
        case "flagged":
            if r.ReviewNote == "" {
                return false // a flag with no note is a black hole
            }
        default:
            return false // an un-reviewed value blocks "verified"
        }
    }
    return true
}
```

> Secondary-language note: in Python this is an `Enum` + a function that mutates a
> model and calls `.save()`; the rules (keep `original_value`, no silent flags,
> completeness gate) are language-independent.

Key rules:
- **Keep `original_value`** alongside the corrected value. You need the
  (wrong → right) pair both for the training label and for measuring accuracy.
- **No silent flags.** A flag without a note is a black hole; require the note.
- **Completeness gate.** "Document verified" must mean *every* value was looked
  at — confirmed, corrected, or explicitly flagged.

## Turning a correction into a label

`emitLabel` is where the flywheel turns. The label couples the **`source_ref`
region** (from provenance) with the *human-confirmed value*. That is exactly a
training example for the detector/model that originally produced (or should have
produced) the value — and it is `source_ref` that makes it a *localized* example
the model can learn from (a crop of the right region), not just a loose value.

```go
// emitLabel persists a training label from a human verdict.
//
// label = (source_ref region) + (correct value) + (which model to teach).
// SourceRef is what makes this a usable, LOCALIZED label — a crop of the
// exact region, not a floating value with no context.
func emitLabel(rec *Record, labelValue, kind string) error {
    p := rec.Provenance
    return TrainingLabel{
        SourceRef:   p.SourceRef,        // WHERE in the source — the crop/region/row
        LabelValue:  labelValue,         // the human-confirmed correct value
        LabelKind:   kind,               // "confirmation" | "correction"
        TargetModel: p.Origin.ModelVersion, // which model this teaches
        PriorValue:  rec.OriginalValue,  // what the model had said ("" if confirmed)
        PriorConf:   p.Confidence,
    }.Create()
}
```

If `source_ref` is vague (e.g. "page 4" with no bbox/anchor), the label is
near-useless — you cannot crop the right region to train on. This is one more
reason `source_ref` must be specific enough to navigate to (see
[`provenance.md`](provenance.md)).

Both `confirmation` and `correction` labels are useful: corrections teach the
model where it was wrong; confirmations are positive examples (and confirmations
of *low-confidence* predictions are especially valuable — they tell the model
"you were right but unsure").

## Closing the loop: retrain → measure → deploy

```
human verifies/corrects ─► TrainingLabel rows accumulate
        ▲                              │
        │                              ▼
   deploy new model  ◄── measure ◄── retrain detector on labels
   (with new model_version)    (held-out set: did accuracy go up?)
```

- New labels feed periodic retraining of the producing model.
- Always bump `model_version` on deploy so future provenance records say which
  model produced them — you can then measure accuracy *per model version* and
  prove the flywheel is working (or catch a regression).
- Hold out a labeled set the model never trains on, to measure honestly.

## Accuracy metrics that matter

- **Review coverage rate** — fraction of values a human actually verified.
  (Accuracy claims are meaningless on unreviewed values.)
- **Accuracy rate** — of reviewed values, fraction confirmed without correction.
- **Breakdown by `method` / by value type** — where is the automation weak?
  This points retraining and tool work at the right target.
- Track these **per `model_version`** to see the flywheel move.

## Review checklist

- [ ] Does every correction produce a training label (not just patch a record)?
- [ ] Does the label carry the `source_ref`, and is that `source_ref` specific
      enough to crop/localize the region (not just a page number)?
- [ ] Are *confirmations* (especially of low-confidence predictions) also captured
      as labels, not just corrections?
- [ ] Is `original_value` preserved on correction (so you have the wrong→right pair)?
- [ ] Are flags required to carry a note (no silent flags)?
- [ ] Is "document verified" gated on full coverage (every value confirmed,
      corrected, or flagged-with-note — no silent gaps)?
- [ ] Does the verification UI let the reviewer jump straight to `source_ref`
      (highlight bbox / scroll to row / focus anchor)?
- [ ] Is accuracy measured on *reviewed* values only, and broken down per
      `method` and per `model_version`?
- [ ] Does deploying a retrained model bump `model_version`, so future provenance
      records say which model produced them?
