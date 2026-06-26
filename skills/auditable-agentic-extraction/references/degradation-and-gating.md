# Graceful degradation & capability-based gating (patterns 5 & 6)

These two patterns govern *which tools run and what happens when one is
missing*. They share a principle: **decide based on capability, not on
crashes or empty results.**

## Contents

- Pattern 5: graceful degradation when a model/tool is missing
- Pattern 6: capability-based gating (the OCR example)
- Why result-based gating is a trap
- Combining the two
- Review checklist

## Pattern 5: graceful degradation

A missing or unconfigured model must **narrow the system's capability**, not
crash it. The pipeline should still produce values from a lower-confidence
source and *say so in provenance*.

Concretely: if the ML symbol/object detector has no weights configured, do not
abort the document. Fall back to a less-precise source (e.g. counting from a
structured table/schedule that lists the same items, or an LLM estimate), and
stamp the provenance with the weaker `method` and a lower `confidence` so the
reviewer knows to scrutinize it.

```python
def get_detector():
    """Return a detector or None — never raise on a missing model."""
    key = config.get("DETECTOR_MODEL")        # e.g. an object-storage key
    if not key:
        return None                            # detector simply off
    try:
        return load_detector(key)
    except ModelLoadError as e:
        log.warning("detector unavailable, degrading: %s", e)
        return None

def count_items(region, schedule_table) -> ToolResult:
    detector = get_detector()
    if detector is not None:
        hits = detector.detect(region)
        return ToolResult(ok=True, value=len(hits), provenance={
            "method": "detector", "confidence": detector.confidence(hits),
            "model_version": detector.version, "source_ref": region.ref,
        })
    # DEGRADED PATH — capability narrowed, not broken:
    if schedule_table is not None:
        n = schedule_table.count_rows_for(region.item_type)
        return ToolResult(ok=True, value=n, provenance={
            "method": "schedule_lookup", "confidence": 0.6,   # honestly lower
            "source_ref": schedule_table.ref,
        })
    return ToolResult(ok=False, error="no detector and no schedule to count from")
```

Principles:
- **`None` over exception** for an absent optional model. Loading is the only
  place that knows it's missing; turn that into a capability flag, not a crash.
- **The fallback is honest.** Lower `confidence`, different `method` — the
  reviewer and the flywheel both see it was a degraded path.
- **Document-level config gate.** `DETECTOR_MODEL=""` is a valid, supported
  state ("detector off"), not an error.

## Pattern 6: capability-based gating

**Gate on what the input *can* yield, not on what the primary path *did*
yield.** The canonical case is OCR:

- A **vector / born-digital** document has a real text layer — read it directly,
  cheaply, exactly. Running OCR on it adds cost and *introduces* errors.
- A **scanned** document (image-only, no text layer) needs OCR.

The correct gate is **"does this page have a usable text layer?"** — a property
of the input — *before* you try extraction:

```python
def needs_ocr(page) -> bool:
    """Capability check: gate OCR on the ABSENCE of a usable text layer,
    decided up front — NOT on whether extraction came back empty."""
    text = page.extract_text_layer()
    # a real text layer yields a meaningful amount of selectable text;
    # a scan yields nothing (or a few stray characters from artifacts).
    return len(text.strip()) < MIN_TEXT_CHARS

def read_page(page) -> ToolResult:
    if needs_ocr(page):
        return ocr_read(page)            # scanned → OCR is the right tool
    return text_layer_read(page)         # vector → exact, cheap, no OCR
```

## Why result-based gating is a trap

The tempting shortcut — "if extraction returned nothing, *then* run OCR" — fails
both directions:

- **False fire:** a vector page that legitimately has no extractable items
  (e.g. a blank or purely-graphical page) returns empty → you waste an OCR pass
  and may invent text from noise.
- **False skip:** a scanned page that returned *garbage* (a few junk chars from
  compression artifacts) looks "non-empty" → you skip OCR and trust the garbage.

Empty results conflate "the input had nothing" with "we couldn't read the
input." Capability gating separates them: it asks *can this input be read this
way?* before reading, so the decision is about the input, not about a possibly-
buggy first attempt.

The same logic generalizes beyond OCR:
- Use the detector only on pages whose type can contain detectable symbols.
- Use the schedule parser only when a schedule table is actually present.
- Use a date parser path only on fields typed as dates.

Gate each tool on a **precondition about the input**, checked up front.

## Combining the two

Degradation (5) and gating (6) compose: gating decides *which* tool the input
is eligible for; degradation decides *what to do when the eligible tool is
unavailable*. A page may be eligible for the detector (gating) but the detector
may be absent (degradation) → fall back to the schedule, with honest provenance.

```
input ──► capability gate ──► eligible tool present? ──yes──► run it
            (pattern 6)              (pattern 5)        │
                                          │no            │
                                          ▼              ▼
                                  degraded fallback   value + provenance
                                  (lower confidence,   (full confidence)
                                   honest method)
```

## Review checklist

- [ ] Is OCR (and any fallback path) gated on an input capability checked up
      front — not on an empty/failed primary result?
- [ ] Does a missing optional model return `None` and degrade, rather than raise?
- [ ] Is "model not configured" a supported, tested state?
- [ ] Does every degraded path stamp a weaker `method` + lower `confidence`?
- [ ] Are tool preconditions (page type, table presence, field type) checked
      before invoking the tool, not discovered by its failure?
