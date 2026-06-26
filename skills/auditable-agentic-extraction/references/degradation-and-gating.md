# Graceful degradation & capability-based gating (patterns 5 & 6)

These two patterns govern *which tools run and what happens when one is
missing*. They share a principle: **decide based on capability, not on
crashes or empty results.**

Code below is **language-neutral with Go as the lead example**. See
[`agent-and-tools.md`](agent-and-tools.md) for the `ToolResult` envelope these
return and [`provenance.md`](provenance.md) for the `Origin`/`SourceRef` shapes.

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

Concretely (illustrative construction-takeoff aside): if an ML symbol/object
detector has no weights configured, do not abort the document. Fall back to a
less-precise source (e.g. counting from a structured table/schedule that lists
the same items, or an LLM estimate), and stamp the provenance with the weaker
`method` and a lower `confidence` so the reviewer knows to scrutinize it.

Go (lead example) — a *nil detector* is a valid, supported state, not a crash:

```go
// getDetector returns a detector or nil — it never errors on a missing model.
func getDetector(cfg Config) Detector {
    key := cfg.Get("DETECTOR_MODEL") // e.g. an object-storage key
    if key == "" {
        return nil // detector simply off — a supported state
    }
    d, err := loadDetector(key)
    if err != nil {
        log.Warn("detector unavailable, degrading", "err", err)
        return nil
    }
    return d
}

func countItems(cfg Config, region Region, schedule *ScheduleTable) ToolResult {
    if d := getDetector(cfg); d != nil {
        hits := d.Detect(region)
        return ToolResult{
            OK: true, Value: strconv.Itoa(len(hits)), Confidence: d.Confidence(hits),
            Origin:    Origin{Method: "detector:items", ModelVersion: ptr(d.Version())},
            SourceRef: region.Ref,
        }
    }
    // DEGRADED PATH — capability narrowed, not broken:
    if schedule != nil {
        n := schedule.CountRowsFor(region.ItemType)
        return ToolResult{
            OK: true, Value: strconv.Itoa(n),
            // Not a guessed constant: use the MEASURED accuracy of this lookup
            // path (how often it matched the verified value, from the flywheel),
            // so triage-by-confidence is meaningful. See provenance.md.
            Confidence: lookupPathAccuracy(),
            Origin:     Origin{Method: "lookup:schedule"},
            SourceRef:  schedule.Ref,
            Kind:       KindFallback,
        }
    }
    return ToolResult{OK: false, Err: "no detector and no schedule to count from"}
}
```

Principles:
- **A nil/None capability over a crash** for an absent optional model. Loading is
  the only place that knows it's missing; turn that into a capability flag, not an
  error that aborts the document.
- **The fallback is honest.** Lower `confidence`, different `method`, `Kind =
  fallback` — the reviewer and the flywheel both see it was a degraded path.
- **Config-level gate.** `DETECTOR_MODEL=""` is a valid, supported, *tested* state
  ("detector off"), not an error.

> Secondary-language note: Python returns `None` and checks `is not None`;
> TypeScript returns `null`. Same principle — absence is a value, not an exception.

## Pattern 6: capability-based gating

**Gate on what the input *can* yield, not on what the primary path *did*
yield.** The canonical case is OCR:

- A **vector / born-digital** document has a real text layer — read it directly,
  cheaply, exactly. Running OCR on it adds cost and *introduces* errors.
- A **scanned** document (image-only, no text layer) needs OCR.

The correct gate is **"does this page have a usable text layer?"** — a property
of the input — *before* you try extraction. Go (lead example):

```go
const minTextChars = 16

// needsOCR is a CAPABILITY check: gate OCR on the ABSENCE of a usable text
// layer, decided up front — NOT on whether extraction came back empty.
func needsOCR(page Page) bool {
    text := strings.TrimSpace(page.ExtractTextLayer())
    // a real text layer yields a meaningful amount of selectable text;
    // a scan yields nothing (or a few stray chars from compression artifacts).
    return len(text) < minTextChars
}

func readPage(page Page) ToolResult {
    if needsOCR(page) {
        return ocrRead(page)       // scanned → OCR is the right tool
    }
    return textLayerRead(page)     // vector / born-digital → exact, cheap, no OCR
}
```

> Secondary-language note: identical logic in Python (`needs_ocr(page) -> bool`)
> or TypeScript — the point is the *order*: check the capability, then choose the
> tool. (This mirrors a hard-won rule from a takeoff pipeline: gate OCR on
> scanned-vs-vector detection, never on an empty extraction result.)

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

### A second worked gate: structured vs. free-text fields

The OCR case generalizes. Suppose a form yields some fields as structured
key/value pairs (from a digital form layer) and others only as free text:

```
field ──► has structured layer? ──yes──► read_kv(field)      (method "parse:kv",   conf high)
            (capability gate)      │
                                   │no
                                   ▼
                          free_text_extract(field)            (method "llm_estimate", conf lower)
```

The gate is the *presence of the structured layer for that field*, checked up
front — not "did the structured read return empty". A genuinely-empty structured
field (the user left it blank) must NOT silently fall through to an LLM that then
invents a plausible value.

## Review checklist

- [ ] Is OCR (and any fallback path) gated on an input capability checked up
      front — not on an empty/failed primary result?
- [ ] Does a missing optional model return nil/None and degrade, rather than
      crash/raise/abort the document?
- [ ] Is "model not configured" a supported, **tested** state (a test that runs
      the pipeline with the model off and asserts the honest fallback)?
- [ ] Does every degraded path stamp a weaker `method` + lower `confidence`
      (and, where you have it, `Kind = fallback`) so the reviewer sees it?
- [ ] Are tool preconditions (page type, table presence, field type, text layer)
      checked **before** invoking the tool, not discovered by its failure?
- [ ] Does an empty primary result get distinguished from an unreadable input —
      i.e. you never treat "the input had nothing" the same as "we couldn't read it"?
- [ ] When the eligible tool is absent, does the fallback still attach a real
      `source_ref` (so the degraded value is still auditable)?
