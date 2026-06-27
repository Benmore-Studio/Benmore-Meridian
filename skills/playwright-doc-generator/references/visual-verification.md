# Visual Verification — read the screenshots back before you trust them

Capturing a screenshot is not the same as verifying it. A file on disk can be a
login page, a blank skeleton, a half-loaded chart, a modal that never closed, or
text cut off at the viewport edge — and the filename will still say
`07-dashboard.png`. This reference is the gate that catches those before they
ship in a client doc.

The capture checklist (`screenshot-checklist.md`) answers **"did I get every
surface?"** (coverage). This file answers **"is each captured surface actually
good?"** (quality). Run this one *after* capture, *before* writing.

---

## How to run the gate

1. **Re-open each screenshot and actually look at it.** Read the image back with
   the Read tool — do not infer quality from the fact that a file exists. You are
   QA-ing pixels, not file counts.
2. **For every image, ask the eight failure questions below.** Most failures fall
   into one of these eight buckets. Name the failure with the vocabulary term —
   that makes the fix unambiguous and tells you *which* recapture to do.
3. **Re-capture or fix, don't caption around it.** If a screenshot is wrong, the
   answer is a new capture (re-inject auth, dismiss the modal, wait for load,
   resize), never a caption that excuses the defect ("the page was still
   loading"). A client doc with apologetic captions reads as unfinished.
4. **Do a second viewport pass.** The skill resizes to 1440×900 once. A client
   guide that never shows mobile is half a guide. Re-walk the top ~10 surfaces at
   `playwright-cli resize 390 844` (iPhone-class) and capture an `-mobile` suffix
   set. Mobile is where overflow and layout shift hide.

---

## The eight failure questions (with the vocabulary term to name each)

Ask these of every screenshot. The bold term is what you write in your notes so
the recapture is precise.

1. **Is this the real page, or an auth/empty fallback?**
   The single most common silent failure. A capture that landed on the login
   page, a 404, or a permission wall is an **expired-session** artifact, not
   proof. If you see the login form where the dashboard should be, the JWT
   expired mid-walk — re-inject `access_token` + `refresh_token` and recapture.
   Never present a login/blank capture as the result.

2. **Did a transient state get frozen?**
   A **skeleton** (placeholder holding content shape) or **spinner**
   (indeterminate loader) in the shot means you captured before load finished.
   Wait for the populated state and recapture. Exception: if you are
   *intentionally* documenting the loading state, label it as such.

3. **Is anything overlapping or clipped?**
   Look for **overflow** (content larger than its container), text cut at the
   viewport edge, a tooltip/dropdown clipped behind a sibling (**z-index**), or a
   sticky header that detached. On mobile this is where most defects live —
   **layout shift** and horizontal overflow that never appear at 1440px.

4. **Is there dead or cramped space?**
   Either extreme is a finding. Vast **negative space** with one lonely card
   reads as a broken/empty build; zero negative space (everything jammed) reads
   as cramped. Both undercut "this is a finished platform." Note which, and
   whether it's the real state or a data-loading gap.

5. **Is the hierarchy legible at thumbnail size?**
   In a doc, the reader sees the image small first. If you can't tell the primary
   action or the **focal point** when the image is scaled down, the screen has
   weak **hierarchy** — and a confused screenshot makes a confused doc. Prefer
   capturing the state where the primary **CTA** is visible and obvious.

6. **Is text readable — contrast and length?**
   Low **contrast ratio** (grey-on-grey microcopy, placeholder text mistaken for
   real content) renders even worse after markdown compression. Also watch
   **line length**: a full-width table or paragraph that runs edge to edge is
   hard to read in the shot and signals no `max-width` discipline.

7. **Are numbers and data aligned?**
   A **data table** with ragged, left-aligned numbers (no **tabular nums**,
   numbers not right-aligned) looks unfinished in a screenshot. If the platform
   has tables/stats, capture one where the alignment is correct — it's a trust
   signal for the client.

8. **Did the modal/overlay close when it should have (or open when it should)?**
   A leftover **modal**, **sheet** (edge panel), **drawer** (bottom panel), or
   cookie banner sitting over the content you meant to show is a recapture. So is
   the inverse — documenting a feature that lives behind a **popover** without
   ever opening it. Capture the state that shows the feature, with overlays
   resolved deliberately.

---

## States are part of the story, not noise

A walkthrough that only shows happy-path populated screens hides what a client
will actually hit in week one. Deliberately capture and label, where they exist:

- **Empty state** — first-run, no data yet. Show it *with* its next action
  visible. "No data" screens reassure the client the product guides them.
- **Error state** — a verification gate, a failed action, a "coming soon"
  placeholder. The skill's honesty principle depends on these.
- **Loading state** — only if you're documenting it on purpose (see #2).

These are not failures to hide — they're surfaces to document honestly. The
difference between "frozen by accident" (#2) and "documented on purpose" is
whether your caption *names it as a state*.

---

## Verification log (write this into the doc-build notes, not the deliverable)

For each screenshot, record one line:

```
07-dashboard.png        OK
08-billing.png          RECAP — expired-session (login page); re-inject JWT
11-roster-mobile.png    RECAP — overflow, table runs off right edge at 390px
14-reports.png          RECAP — skeleton frozen; wait for chart draw
```

Drive every `RECAP` to `OK` before Phase 4. A screenshot you couldn't fix gets a
caption that tells the truth ("verification gate — this is the real error banner
a new org sees"), never a caption that pretends a defect is intentional.

---

## Why this gate exists

The old end-of-job check counted files (`ls | wc -l`) and grepped image refs. That
catches orphans and broken links — but it never looks at a single pixel. A doc
can pass the file-count check with 40 screenshots that are all login pages. This
gate is the part that actually *looks*, and the vocabulary terms are what turn "it
looks off" into "it's an expired-session capture, recapture with fresh auth."
