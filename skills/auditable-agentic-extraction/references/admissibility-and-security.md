# Admissibility, tamper-evidence, determinism, and sensitive content

Provenance ([provenance.md](provenance.md)) makes a value traceable *inside* your
system: you can point at a `SourceRef` and an `Origin` and say where the number came
from. Admissibility is the rung above. It makes that trail trustworthy to an *outside*
party — an auditor, opposing counsel, a regulator, a customer disputing a charge — who
starts from the assumption that you might be wrong, sloppy, or adversarial. When an
extracted value bills someone, settles a dispute, or enters a regulated record, the trail
has to survive a hostile reader.

A defensible system answers three questions for that reader:

1. **Is this the original source, unaltered?** (integrity)
2. **Exactly how was each value or change produced, and can you reproduce it?** (determinism)
3. **Who saw or changed what, and when?** (chain of custody)

This file is about turning *auditable* into *defensible*. It does not replace the
provenance, document-model, or comparison machinery — it hardens them. Match the
mechanism to the threat; do not bolt cryptography onto a low-stakes summary.

## Contents

- [From auditable to defensible](#from-auditable-to-defensible)
- [Tamper-evident source integrity](#tamper-evident-source-integrity)
- [The audit log: tamper-evident chain of custody](#the-audit-log-tamper-evident-chain-of-custody)
- [Determinism and reproducibility](#determinism-and-reproducibility)
- [Signed exports](#signed-exports)
- [Privilege and sensitive content](#privilege-and-sensitive-content)
- [Access control and view auditing](#access-control-and-view-auditing)
- [Keeping secrets out of logs and provenance](#keeping-secrets-out-of-logs-and-provenance)
- [Threat-model framing](#threat-model-framing)
- [Anti-patterns](#anti-patterns)
- [Review checklist](#review-checklist)

## From auditable to defensible

Provenance is a system of record for *you*. Admissibility is a system of record for
*everyone else*. The difference is the trust assumption: internal provenance assumes the
log is honest; admissibility assumes the reader doubts it. Every mechanism here exists to
close one of those doubts — that the source was swapped, that a value was hand-tuned after
the fact, that the log was quietly edited, or that someone saw content they should not
have.

You do not need all of it for every document. A throwaway summary needs none of it. A
value that bills a client, or a redline that decides a contract dispute, needs the full
stack. The skill's honesty rule applies: do not over-apply.

## Tamper-evident source integrity

The foundation is proving the source is the original, unaltered. Two distinct hashes do
two distinct jobs — keep **both**.

**1. The raw-upload digest.** Hash the exact bytes the user uploaded, on ingest, before
any processing. This proves the *file* is unaltered — that the PDF on disk today is
byte-for-byte the one received.

```go
sum := sha256.Sum256(raw)        // raw = original uploaded bytes
digest := hex.EncodeToString(sum[:])
// store digest immutably alongside the object; re-verify on every read
```

Store the raw bytes in **write-once storage** (WORM / S3 Object Lock / append-only) and
never re-save over them. On any later read, re-hash and compare; a mismatch means the
object was tampered with or corrupted, and the value derived from it is no longer
defensible.

**2. The canonical `doc_id`.** The canonical-model `doc_id` (see
[comparison-and-versioning.md](comparison-and-versioning.md)) is a content hash of the
*canonical document model* ([document-model.md](document-model.md)), not the raw bytes.
This is content addressing: two byte-different uploads that canonicalize to the same
document (re-encoded PDF, re-exported with the same text and layout) get the same
`doc_id`, so comparison and dedup are stable across cosmetic re-encodes.

The two hashes answer different questions. The raw digest proves *this file* was not
touched. The `doc_id` gives a *stable identity* for the content regardless of encoding.
You need the raw digest for chain-of-custody ("the exhibit is the file we received") and
the `doc_id` for comparison and versioning ("this is the same contract"). Record both; in
the envelope, `SourceRef.doc_id` carries the canonical id and the raw digest lives with
the stored object.

> Secondary-language note (Python): `hashlib.sha256(raw).hexdigest()`.
> Secondary-language note (TS): `crypto.createHash("sha256").update(raw).digest("hex")`.

## The audit log: tamper-evident chain of custody

Every state transition gets one append-only entry: ingested, canonicalized, value
produced, verified, corrected, exported, **viewed**. Each entry records the actor, the
timestamp, the action, and references to what it touched.

Append-only is not enough on its own — an append-only table can still be edited by anyone
with database access. Make it **tamper-evident** with a hash chain: each entry includes
the hash of the previous entry, so deleting or reordering any entry breaks the chain and
becomes detectable.

```go
type Entry struct {
    Seq      uint64    // strictly increasing
    PrevHash string    // hash of the prior entry; "" for genesis
    Actor    string    // user/service identity
    Action   string    // "value_produced", "verified", "exported", "viewed"...
    RefIDs   []string  // doc_id / field id / export id this concerns
    Time     time.Time // server time, monotonic source preferred
    Hash     string    // = H(Seq‖PrevHash‖Actor‖Action‖RefIDs‖Time)
}
```

`Hash` is computed over a canonical serialization of all the other fields. A verifier
walks the chain from genesis: recompute each `Hash`, check it matches, and check each
`PrevHash` equals the prior entry's `Hash`.

**Be precise about what this buys you.** A hash chain detects tampering *only if the head
(the most recent `Hash`) is protected against rewrite.* An attacker with full write access
can recompute the entire chain from the edited point forward and produce a valid-looking
chain. The chain raises the bar from "edit one row" to "rewrite every subsequent row," but
it is not magic. To close that gap, **anchor** the head periodically: sign it with a key
the writer does not hold, push it to append-only/WORM storage, write it to a separate
system, or submit it to an external trusted timestamp authority (RFC 3161) or transparency
log. Anchoring is what lets you prove the log existed in a given state at a given time,
even against an insider.

## Determinism and reproducibility

A defensible value is one a third party can *reproduce* from stored inputs. The replay
test in [provenance.md](provenance.md) is the proof: re-run the recorded inputs through
the recorded code and get the recorded output. For that to hold, pin and record
**everything that affects the output**:

- `Origin.model_version` — already in the envelope.
- The **prompt / template version** used (a prompt change is a logic change).
- Detector / classifier **weights version** for any ML scoring.
- The **canonical-model builder version** ([document-model.md](document-model.md)) — a
  change in how the model is built changes anchors and offsets.
- **Library versions** of deterministic parsers, calculators, and date/number coercers.

For the deterministic rungs of the ladder (`parsed`, `computed`,
`deterministic_tool`-backed values), this is enough: same inputs + same pinned versions =
identical output, byte for byte. That is the gold standard and the reason the ladder
pushes values toward deterministic tools wherever possible.

For the LLM rung (`llm_estimate`), be honest: **exact reproducibility is not guaranteed.**
Providers update hosted models silently, and sampling is non-deterministic. You cannot
promise an outside party that re-running the prompt next year yields the same tokens. So:

- Record the **exact request** — model id, full prompt text (or its version), parameters,
  `temperature=0`, and a fixed `seed` where the provider supports one — so you can re-run
  and *show* the same output today, and explain the request precisely later.
- Treat these values as the **review-first tier**: they are not defensible on the model's
  say-so. Either back them with a deterministic tool that the model only *orchestrates*,
  or have a human verify them. The lack of guaranteed LLM reproducibility is exactly *why*
  high-stakes values must be deterministic-tool-backed or human-verified — not why you
  give up.

## Signed exports

The deliverable that leaves your system — the annotated PDF, the extracted dataset, the
redline report ([comparison-and-versioning.md](comparison-and-versioning.md)) — should be
self-describing and verifiable. Embed (or attach as a manifest):

- The **source digest(s)** and `doc_id`(s) the export was derived from.
- The **`model_version`s** and prompt/builder versions used.
- The **verification status** of each value.
- A **digital signature** over the export (and its manifest), so a recipient can verify it
  came from you and was not altered in transit.

A signature proves *origin and integrity of the export*; it says nothing about whether the
underlying value is correct. Keep the verification status distinct from automation
confidence. As in [verification-flywheel.md](verification-flywheel.md), **human
verification is its own status, not `confidence = 1`.** "A reviewer checked this against
the source" and "the detector scored this 0.99" are different claims to a third party;
collapsing them into one number destroys the distinction precisely when it matters most.

## Privilege and sensitive content

High-stakes documents carry privileged (attorney-client, work-product), regulated (PHI
under HIPAA), or personal (PII) content. Handle it deliberately.

- **Classification.** Tag sensitive spans in the canonical model
  ([document-model.md](document-model.md)) — privileged, PHI, PII — so downstream stages
  can gate behavior on the tag rather than guessing.
- **Redaction-aware processing.** A redaction in the source is a *fact to preserve, never
  to see through.* Represent "this region was redacted" as a first-class element of the
  document model. Critically, **never leak text hidden under a redaction rectangle that is
  still present in the PDF text layer** — a black box drawn over still-extractable text is
  the classic redaction failure. Detect text under redaction annotations and refuse to
  extract it; surface it as redacted, not as content.
- **Data minimization.** Do not send privileged or regulated content to a third-party LLM
  without authorization. Gate which **rungs and tools** are permitted on a sensitive
  document: an on-prem or fully deterministic path may be *required*, with the
  `llm_estimate` rung disabled. The classification tags drive that gate.
- **Retention and right-to-deletion.** Content addressing interacts cleanly with deletion:
  you can **delete the raw bytes and any sensitive content while keeping the hash, the
  `doc_id`, and the audit metadata.** The chain of custody and integrity proofs survive a
  lawful deletion request because they reference content by digest, not by storing it.

## Access control and view auditing

Least privilege governs who may view, annotate, or export each document, scoped by
classification. And — this is the part that is easy to forget — **every view of sensitive
content is itself an audit-log `viewed` event.** Reading is a state transition for
chain-of-custody purposes: an auditor asking "who has seen this privileged document" needs
an answer, and that answer is the access log. View auditing is not a separate system from
the hash-chained log above; it is the same log.

## Keeping secrets out of logs and provenance

The audit and provenance machinery must not become the leak. Progress logs, `Origin`
records, and processing traces should store **references and anchors, not raw sensitive
values.** Do not dump full SSNs, card numbers, or privileged passages into a
`processing_log` or a provenance record "for debugging." Store the anchor (page, span,
`doc_id`) that *locates* the value in the protected source, not the value itself. The log
should be safe to show an auditor without re-disclosing the very content it is protecting.

## Threat-model framing

Pick mechanisms by who you are defending against:

- **The internal mistake** (most common). A wrong value, a transposed digit, a stale
  document. Provenance + the replay test catch it. No cryptography needed.
- **The honest outside auditor.** Assumes you are competent but wants to *check*. Needs
  reproducibility (pinned versions, replay) and integrity (source digests, signed
  exports). Tamper-evidence is reassuring but not the point.
- **The adversary who wants to alter the record** — an insider hiding a change, a
  counterparty disputing what was delivered. Needs tamper-evidence (hash-chained,
  anchored log), access control, and signed exports.

Do not over-engineer. A low-stakes internal summary does not need an anchored hash chain
or signed exports; provenance is enough. Spend the cryptography where a hostile reader is
plausible.

## Anti-patterns

**Re-saving over the original upload.** Overwriting the ingested file destroys the only
proof it is unaltered → store raw bytes once in WORM/object-lock storage; never rewrite,
only append new versions with new digests.

**An editable audit log.** A log anyone with DB access can edit or delete without trace
proves nothing → hash-chain the entries and anchor the head externally; a plain
append-only table is not tamper-evident.

**Un-pinned model/prompt/builder versions.** If you cannot say which prompt, model, or
canonical-builder produced a value, you cannot reproduce it → record `model_version`,
prompt version, builder version, and library versions alongside every value.

**Privileged content to a third-party model with no gate.** Sending PHI/privileged text to
a hosted LLM "to extract a field" without authorization → classify sensitive spans and
gate the LLM rung; require a deterministic or on-prem path on sensitive docs.

**"Redaction" that only draws a black box.** A rectangle over text that is still in the
PDF text layer leaks the very thing it hides → remove the underlying text and represent
the region as a redaction fact in the model.

**Raw PII in logs/provenance.** Dumping full sensitive values into processing logs or
provenance records turns your audit trail into a breach → store anchors and references,
not raw sensitive content.

**Treating human-verified and machine-confident as one field.** Collapsing "a reviewer
checked this" into `confidence = 1` erases the distinction a third party most needs → keep
verification status separate from automation confidence (see
[verification-flywheel.md](verification-flywheel.md)).

## Review checklist

- [ ] Raw uploaded bytes are hashed (SHA-256) on ingest and stored in write-once storage; the digest is re-verified on read.
- [ ] Both hashes are kept: the raw-upload digest (file unaltered) and the canonical `doc_id` (stable content identity).
- [ ] Original uploads are never overwritten; new versions get new digests.
- [ ] Every state transition (including `viewed`) writes an append-only audit entry with actor, timestamp, action, and ref ids.
- [ ] The audit log is hash-chained (`PrevHash`) and its head is anchored externally (signed / WORM / trusted timestamp).
- [ ] The chain's limits are understood: it detects tampering only if the head is protected.
- [ ] Every output-affecting version is pinned and recorded: `model_version`, prompt/template, detector weights, canonical builder, parser/calculator libraries.
- [ ] Deterministic rungs pass the replay test (identical output from stored inputs).
- [ ] `llm_estimate` values record the exact request (model, prompt, params, `temperature=0`, seed) and are flagged review-first, backed by a deterministic tool or human verification.
- [ ] Exports carry source digest(s), versions, and verification status, and are digitally signed.
- [ ] Human-verified status is distinct from automation confidence — not `confidence = 1`.
- [ ] Sensitive spans are classified; the LLM rung is gated on sensitive documents (on-prem/deterministic path available).
- [ ] Redactions are first-class facts; no text under a redaction rectangle is extractable or extracted.
- [ ] Retention/deletion can remove raw bytes while preserving hash + audit metadata (right-to-deletion compatible).
- [ ] Logs and provenance store anchors/references, never raw PII or privileged text.
- [ ] Access is least-privilege and scoped by classification; views of sensitive content are audited.
- [ ] Mechanisms match the threat; no heavy cryptography on low-stakes outputs.
