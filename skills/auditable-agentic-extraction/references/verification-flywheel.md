# Human verification + correction flywheel (pattern 4)

Two jobs, one loop:
1. **Verification** — a human confirms or corrects each value before it is
   trusted. This is the safety net for everything the automation got wrong.
2. **Flywheel** — every correction is captured as a *labeled example* that
   improves the detectors/models, so the same mistake gets rarer over time.

The insight: a correction is not just a patch to one record — it is a free,
high-quality, in-distribution training label that you already paid a human to
produce. Throwing it away is the most expensive mistake in the whole design.

## Contents

- The verification surface
- The verify/correct loop (code)
- Turning a correction into a label
- Closing the loop: retrain → measure → deploy
- Accuracy metrics that matter
- Review checklist

## The verification surface

Provenance (pattern 2) is what makes verification fast. The UI should let a
reviewer, per value:
- see the value, its `confidence`, and its `method`;
- jump to the `source_ref` (highlight the region / scroll to the row);
- **confirm** (value is right), **correct** (supply the right value), or
  **flag** (can't tell — needs escalation, must leave a note).

Triage by sorting on confidence ascending and surfacing `llm_estimate` /
fallback-method values first — those are the least grounded.

## The verify/correct loop

```python
from enum import Enum

class Verdict(str, Enum):
    CONFIRM = "confirm"     # automation was right
    CORRECT = "correct"     # human supplied a different value
    FLAG    = "flag"        # cannot determine; needs escalation + note

def apply_verification(record, verdict: Verdict, corrected_value=None, note=None):
    if verdict is Verdict.CONFIRM:
        record.status = "verified"
        emit_label(record, label_value=record.value, kind="confirmation")
    elif verdict is Verdict.CORRECT:
        if corrected_value is None:
            raise ValueError("correction requires a value")
        record.original_value = record.value      # keep what the model said
        record.value = corrected_value             # human value wins
        record.status = "verified"
        # the disagreement is the most valuable training signal:
        emit_label(record, label_value=corrected_value, kind="correction")
    elif verdict is Verdict.FLAG:
        if not note:
            raise ValueError("flag requires a note")  # no silent flags
        record.status = "flagged"
        record.review_note = note
    record.verified_by = current_user()
    record.verified_at = now()
    record.save()

def project_is_verified(records) -> bool:
    """Completeness gate: a document is 'verified' only when every value is
    either confirmed/corrected or flagged-with-a-note. No silent gaps."""
    return all(r.status in ("verified", "flagged") and
               (r.status != "flagged" or r.review_note) for r in records)
```

Key rules:
- **Keep `original_value`** alongside the corrected value. You need the
  (wrong → right) pair both for the training label and for measuring accuracy.
- **No silent flags.** A flag without a note is a black hole; require the note.
- **Completeness gate.** "Document verified" must mean *every* value was looked
  at — confirmed, corrected, or explicitly flagged.

## Turning a correction into a label

`emit_label` is where the flywheel turns. The label couples the *source region*
(from provenance) with the *human-confirmed value*. That is exactly a training
example for the detector/model that originally produced (or should have
produced) the value.

```python
def emit_label(record, label_value, kind: str):
    """Persist a training label from a human verdict.

    The label = (source region) + (correct value) + (which model to teach).
    Provenance.source_ref is what makes this a usable, localized label.
    """
    p = record.provenance
    TrainingLabel.create(
        source_ref   = p.source_ref,            # WHERE in the source (the crop/region)
        label_value  = label_value,             # the human-confirmed correct value
        label_kind   = kind,                    # "confirmation" | "correction"
        target_model = p.model_version,          # which model this teaches
        prior_value  = record.original_value,    # what the model had said (None if confirmed)
        prior_conf   = p.confidence,
    )
```

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
- [ ] Does the label carry the `source_ref` so it's a localized example?
- [ ] Is `original_value` preserved on correction?
- [ ] Are flags required to carry a note (no silent flags)?
- [ ] Is "document verified" gated on full coverage (every value handled)?
- [ ] Is accuracy measured on *reviewed* values and broken down per model version?
