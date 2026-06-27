# The canonical document model & robust ingestion (the anchor substrate)

Every `source_ref` in this methodology points *somewhere*. This file defines
**where**: a single normalized representation of the document that every tool,
anchor, bbox, highlight, and diff resolves against. Build it **once** per
`(document, version)` in an early stage, cache it, and make it deterministic.
Without it each tool invents its own coordinates and anchors drift the moment
the document is re-OCR'd or re-paginated. The `anchor`, `page`+`bbox`, and
`span` locators in `SourceRef` (defined in
[`envelope.openapi.yaml`](envelope.openapi.yaml)) are *only* as stable as the
substrate described here.

Code below is **language-neutral with Go as the lead example**. See
[`provenance.md`](provenance.md) for the `Origin`/`SourceRef` shapes these
anchors fill, and [`degradation-and-gating.md`](degradation-and-gating.md) for
the capability gating this file extends.

## Contents

- Why a canonical model
- The model's layers (and canonical coordinate space)
- Reading order is computed, not the content-stream order
- Text normalization (do it once, record it)
- Capability detection: the input matrix (extends gating)
- The adversarial / messy-input edge-case catalogue
- A `buildCanonicalModel` sketch
- Determinism & versioning
- Review checklist

## Why a canonical model

An `anchor` is a stable id into this model — a normalized token id — **not** a
raw character offset and **not** a render-pixel coordinate. Both of those move
when anything upstream changes. The canonical model is the fixed frame that
keeps a clause span, a table cell, and a highlight pointing at the same content
across re-renders, re-OCR, and re-pagination.

Build it in one early stage, key the cache by `(doc_id, version)`, and never let
a downstream tool re-derive its own coordinates. Every locator in `SourceRef`
(`page`+`bbox`, `anchor`, `table`+`row`, `span`) is interpreted against *this*
model and nothing else.

## The model's layers

The model is a tree: **document → pages → blocks → lines → tokens**. Each node
carries a stable `id`, a `bbox` in the **canonical page coordinate space**, and
a position in the **normalized text stream** (byte offsets into the normalized
text). Anchors are token ids.

**Canonical page coordinate space.** Pick one and convert *everything* into it.
This methodology uses **PDF points (72/inch), origin top-left, rotation
normalized out**. Alternatively use normalized `0..1` per page. The rule is
absolute:

> **Render-pixel coords are a bug.** A bbox in pixels at an arbitrary render DPI
> breaks every anchor the instant something re-renders at a different DPI. →
> Convert OCR pixel boxes (at their known DPI) into canonical points at ingest,
> store only canonical coords, and keep the DPI only as provenance metadata.

```go
// Canonical coords: PDF points, top-left origin, rotation already applied.
type Box struct{ X0, Y0, X1, Y1 float64 } // points, not pixels

type Token struct {
    ID        string // stable anchor, e.g. "p3.b2.l5.t8" or a content hash
    Page      int
    Bbox      Box      // canonical points
    Text      string   // normalized glyph text
    ByteStart int      // offset into Doc.NormText
    ByteEnd   int
    Glyphs    []Box    // source glyph rects (pre-normalization) for highlighting
}

type Line struct{ ID string; Page int; Bbox Box; Tokens []Token }
type Block struct {
    ID    string
    Page  int
    Bbox  Box
    Role  string // "body" | "footnote" | "header" | "footer" | "table" | "watermark" | "redaction"
    Lines []Line
}
type Doc struct {
    ID           string // doc_id
    Version      string
    NormText     string // the normalized text stream; anchors index into this
    Pages        []Page
    Blocks       []Block
    BuilderVer   string // model_builder_version
}
```

> Secondary-language note (Python): a `@dataclass(frozen=True)` `Token` with the
> same fields; store `bbox` as a `tuple[float, float, float, float]`.
> Secondary-language note (TypeScript): an `interface Token` with `readonly`
> fields; prefer a `Box` tuple type to avoid pixel/point confusion at call sites.

Token ids must be **stable under re-runs** (see Determinism below): derive them
from structural position plus a short content hash, never from a global counter
that shifts when an unrelated page changes.

## Reading order is computed, not the content-stream order

A PDF's content stream emits glyphs in *draw* order, which is frequently
scrambled — right column before left, footnote glyphs mid-paragraph, a header
drawn last. **Reading order is a computed artifact.** A clause `span` must be
contiguous in reading order, so getting this wrong silently corrupts every
multi-line span.

- **Detect columns first** (gap analysis on x-projections), then order
  top-to-bottom within each column, then columns left-to-right (or RTL).
- **Segregate, do not interleave.** Headers, footers, page numbers, and
  footnotes/endnotes get their own `Block.Role` and are pulled *out* of body
  reading order — tagged, never woven into the body stream. A footnote spliced
  into a sentence makes the surrounding span non-contiguous and unquotable.
- Tables are segregated too: a table is a `Block` with role `table`, addressed
  by the `table`+`row` locator, not by body byte offsets.

**Trust-the-content-stream trap.** Reading tokens in stream order and assuming
that is reading order. → Always compute reading order; treat stream order as raw
input only.

## Text normalization (do it once, record it)

Normalize **once, deterministically**, and record exactly what was done so byte
offsets are reproducible. Normalization includes:

- de-hyphenation at line breaks (`inter-\nnational` → `international`)
- ligature expansion (`ﬁ` → `fi`, `ﬂ` → `fl`)
- smart-quote / dash normalization (curly → straight, en/em dashes)
- whitespace collapse and trailing-space trimming
- Unicode **NFC**
- stripping soft hyphens (U+00AD), zero-width chars (U+200B–200D, U+FEFF)

> **Normalization changes offsets.** Assign anchors and byte offsets **after**
> normalization, never before — otherwise an anchor points into text that no
> longer exists. → And preserve the reverse map: each `Token` keeps its source
> glyph rectangles (`Glyphs`) so a highlight computed from normalized text still
> lands on the right pixels on the page. The normalized stream is for matching;
> the glyph rects are for rendering.

These normalizers stamp `origin.method` with the `parse:` rung (e.g.
`parse:dehyphenate`) where they materially change a value; see
[`provenance.md`](provenance.md).

## Capability detection: the input matrix

This **extends** the capability gating in
[`degradation-and-gating.md`](degradation-and-gating.md). Detect up front,
**per page**, which input class you have:

- **born-digital** — a real, sane text layer
- **scanned image** — no text layer; route to OCR (the existing OCR gate)
- **hybrid** — some pages digital, some scanned (common in bundles)

Gate OCR on this per-page classification, not on the whole document.

> **Critical nuance — a text layer can be PRESENT but GARBAGE.** A PDF with a
> broken or missing `ToUnicode` CMap yields *selectable* text that decodes to
> junk glyphs (mojibake, PUA codepoints). Length checks pass; the content is
> unusable. → The capability check must test text **quality**, not text
> **length**: e.g. dictionary-word ratio, share of codepoints that decode to
> sane Unicode, absence of PUA runs. If quality is low **despite** a text layer,
> treat the page as scanned, OCR it, and stamp the degradation in provenance
> (`origin.method = "ocr:fallback_bad_textlayer"`).

```go
func classifyPage(p RawPage) string { // "digital" | "scanned" | "ocr-fallback"
    if !p.HasTextLayer() {
        return "scanned"
    }
    if textQuality(p.ExtractText()) < 0.6 { // dict-word ratio etc.
        return "ocr-fallback" // text present but junk → OCR it anyway
    }
    return "digital"
}
```

> Secondary-language note (Python): `textQuality` via a wordlist hit-rate over
> tokens plus a `str.isprintable()` / NFC round-trip check.

## The adversarial / messy-input edge-case catalogue

Each case: **what goes wrong → how to handle, and what to stamp in
provenance.** Real-world and adversarial inputs hit most of these.

- **Encrypted / password-protected PDFs.** Need a password to read. → Fail
  **loudly** with a typed error; never silently emit an empty doc that looks
  like a blank document. Stamp `origin.method = "ingest:encrypted"` on the gap.
- **Corrupt / malformed PDFs.** Broken xref, truncated streams. → Attempt
  partial recovery (rebuild xref, salvage readable pages); record which pages
  were recovered vs lost so absence is explicit, not implied.
- **Decompression / DoS limits.** PDF bombs, 50k-page docs, single 1-gigapixel
  images. → Enforce **page-count, total-pixel, and time/own-budget caps** before
  and during ingest; reject or truncate over budget. Reference activity-based
  reaping in [`staged-processing.md`](staged-processing.md) so a wedged ingest
  is reaped, not allowed to starve the pipeline.
- **Rotated / mixed-orientation pages.** Landscape scans, upside-down faxes. →
  Detect rotation per page and normalize it out; **bbox coords must account for
  rotation** so canonical boxes are upright. Store the detected angle as
  metadata.
- **Redactions.** Black-box redactions must be **detected as redactions** and
  never "seen through" or hallucinated past. A redacted region is a **first-class
  fact** — emit it as a `redaction` block, not as absence. → Conversely, text
  still present in the text layer *under* a redaction rectangle is a real
  data-leak bug: **strip it** and do not read it. Stamp `redaction` either way.
- **Strikethrough / struck text** (especially legal). Visually struck or
  deleted text often remains in the layer. → Distinguish struck from active text
  (detect strike glyphs / overlapping rules); a deleted clause that is still
  rendered must **not** be read as in-force. Tag it and exclude it from the
  active body stream.
- **Watermarks / "DRAFT" / confidentiality banners / stamps** overlapping body
  text. → Segregate into a `watermark` block so they neither corrupt OCR of the
  body nor get mistaken for content. Note their presence (a `DRAFT` stamp is
  itself a fact worth surfacing).
- **Handwriting, wet-ink signatures, initials, checkboxes / form marks.** Low
  OCR confidence by nature. → Extract at low confidence and **route to review**
  (see the verification flywheel); never auto-accept a handwritten value.
- **Word/`.docx` tracked changes + comments.** When the *source* is a
  word-processor file (not a flattened PDF), the change metadata —
  insertions/deletions, author, timestamp, comment threads — is **gold**. →
  Extract it natively from the document XML rather than diffing two renders;
  forward-reference [`comparison-and-versioning.md`](comparison-and-versioning.md).
- **Tables.** Spanning pages, nested, merged/spanned cells, borderless,
  multi-row headers. → Resolve to the `table`+`row` locator with explicit
  cell-span metadata; never flatten a merged cell into a single body offset.
- **Blank, duplicate, near-duplicate, and separator pages.** Exhibit/appendix
  dividers, scanned blanks. → Detect and tag; a bundle may be several **logical
  sub-documents** in one PDF and may need splitting into distinct `doc_id`s.
- **Mixed languages / RTL scripts.** → Detect script/direction per block; order
  RTL blocks accordingly; do not assume left-to-right column ordering globally.
- **Locale-sensitive number/date normalization** (a `parse:` concern surfaced
  here). `1.000,00` (EU) vs `1,000.00` (US); `DD/MM/YYYY` vs `MM/DD/YYYY`;
  negative-in-parens accounting `(1,200)`; and words that disagree with digits,
  e.g. *"ten thousand dollars ($1,000)"*. → **Emit BOTH interpretations with a
  conflict flag; never silently pick one.** These become `parse:` rung values;
  cross-ref [`provenance.md`](provenance.md).
- **OCR confusions** (`O`/`0`, `l`/`1`/`I`, `rn`/`m`, decimal/comma swap). →
  Keep **both** the raw OCR token *and* the parsed value so a reviewer can see
  the source glyphs and adjudicate. The raw token's glyph rects make the
  ambiguity visible on the page.

**Silent-empty trap.** Returning an empty document for an encrypted, corrupt, or
DoS-capped input. → Every ingest failure is a *typed, stamped* outcome, never a
blank that downstream mistakes for "the document said nothing."

## A `buildCanonicalModel` sketch

Illustrative — load, per-page quality-aware capability check, read, normalize,
assign stable ids, compute reading order, return.

```go
func buildCanonicalModel(raw RawInput) (Doc, error) {
    pdf, err := load(raw) // surfaces encrypted/corrupt as typed errors
    if err != nil {
        return Doc{}, fmt.Errorf("ingest: %w", err)
    }
    if err := enforceLimits(pdf); err != nil { // page/pixel/time caps
        return Doc{}, err
    }
    var blocks []Block
    for _, p := range pdf.Pages() {
        page := normalizeRotation(p) // bbox coords now upright
        var text PageText
        switch classifyPage(page) {   // quality-aware, per page
        case "digital":
            text = page.ReadTextLayer()              // origin: parse:textlayer
        case "scanned", "ocr-fallback":
            text = ocr(page)                          // origin: ocr:*
        }
        text = normalizeText(text)    // de-hyphenate, NFC, ligatures, strip ZW
        blocks = append(blocks, segregateAndOrder(page, text)...) // roles + reading order
    }
    doc := assemble(raw.DocID, raw.Version, blocks)
    assignStableIDs(&doc)             // anchors AFTER normalization
    doc.BuilderVer = modelBuilderVersion
    return doc, nil
}
```

> Secondary-language note (Python/TypeScript): same control flow; raise/throw a
> typed `IngestError` subclass per failure case so the caller can stamp the
> matching `origin.method` rung.

## Determinism & versioning

Building the canonical model must be **deterministic** — same bytes in, same
tree, same anchor ids out — and **versioned** via `model_builder_version`
(`Doc.BuilderVer`). Anchors are only reproducible if the builder is pinned: a
change to column detection, normalization, or id derivation is a builder version
bump, and a `SourceRef` carries the `version` it was minted against
([`envelope.openapi.yaml`](envelope.openapi.yaml)). When the builder version
changes, anchors must be re-resolved, not blindly trusted. This reproducibility
is also what makes the model admissible as evidence — forward-reference
admissibility-and-security.md.

## Review checklist

- [ ] Exactly one canonical model is built per `(doc_id, version)` and cached;
      no downstream tool invents its own coordinates.
- [ ] All bboxes are in a single canonical coordinate space (PDF points or
      `0..1`); no render-pixel coords are stored.
- [ ] Anchors are stable token ids into the normalized stream, not character
      offsets or pixel coords.
- [ ] Reading order is computed (column detection + top-to-bottom); headers,
      footers, and footnotes are segregated by `Block.Role`, not interleaved.
- [ ] Normalization (de-hyphenation, ligatures, NFC, zero-width strip) runs once
      and anchors are assigned **after** it; token→glyph-rect map is preserved.
- [ ] Capability detection is **per page** and tests text **quality**, not
      length; bad text layers fall back to OCR with a stamped degradation.
- [ ] Encrypted/corrupt/DoS inputs fail loudly with typed, stamped outcomes —
      never a silent empty document; page/pixel/time caps are enforced.
- [ ] Redactions, struck text, watermarks, and handwriting are detected and
      tagged as first-class facts; redaction-layer text is stripped, not read.
- [ ] Conflicting number/date/locale and digits-vs-words readings emit **both**
      with a conflict flag; raw OCR token is kept alongside the parsed value.
- [ ] The builder is deterministic and `model_builder_version` is recorded on
      every `Doc`; version changes trigger anchor re-resolution.
