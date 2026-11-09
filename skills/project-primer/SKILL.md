---
name: project-primer
description: >
  Writes the pre-kickoff project primer for a Benmore client engagement: a client-facing
  PRIMER.md and a screen-share PRIMER_PRESENTATION.html in the project's Discovery folder.
  Use before the first kickoff call with a new client. Triggered by "create a primer",
  "write a primer for BEN-XXX", "pre-kickoff primer", "client primer", "prep the kickoff",
  or "prepare a primer for [client/project]". Reads the sales handoff, the client's own
  documents, signed agreements and email history, restates what has already been agreed,
  shows what changed in the client's latest documents, adds cited market and regulatory
  context that builds on the client's own research, and turns the open scope decisions into
  numbered kickoff questions with options.
context: fork
---

# Project Primer

The primer is what the client reads before kickoff, and what we screen-share during it. Its
job is to make the client think "they understood us, they did the reading, and they know
what has to be decided." It is not a sales document and not a scope agreement.

The reference example is the BEN-228 primer (`~/Benmore/dev/228/Discovery/`, if you have it locally). When in
doubt about tone, depth or structure, read it. Do not copy any of its content: it is
confidential client material.

Two outputs, both in `<project dir>/Discovery/`:

1. `PRIMER.md`: the full written primer.
2. `PRIMER_PRESENTATION.html`: the screen-share version, built from
   `assets/primer-presentation-template.html`.

---

## Step 1: Find the project and gather everything that exists

Locate the project directory. Projects live in `~/Benmore/dev/<BEN number>/` or
`~/Benmore/dev/<BEN number>-<Name>/`. If none exists, create `~/Benmore/dev/<BEN number>/`
and a `Discovery/` folder inside it. If there is no `.benmore-project` file in the project
root, write the project's portal UUID into one (look it up with
`bm benmore lookup <BEN number>`) so token usage is attributed.

Collect every source before writing anything. Read the latest version of each document in
full, not a summary.

| Source                           | Where to find it                                                                            | What it gives the primer                                                       |
| -------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Sales handoff notes              | Pasted by the user, or `Discovery/sales_notes.md`                                           | Client background, priorities, expectations already set                        |
| Client materials folder          | `client-materials/`, often with a `00 Agent-Readable Text/` subfolder and a README          | The client's own plans, protocols, business plan, patent drafts, feature lists |
| Signed agreements                | `client-materials/.../01 Signed Agreements/`                                                | What the SOW actually covers, fees, credits, what does not apply               |
| Email correspondence             | `client-materials/.../04 Email Correspondence/`                                             | Commitments and corrections made in writing, with dates                        |
| Sales call notes and transcripts | `client-materials/.../05 Call Notes and Transcripts/`, or the portal                        | The client's own words, quotes, priorities                                     |
| Portal project context           | `bm benmore context <BEN number>`                                                           | Team, earlier deliverables and recommendations, meetings                       |
| Client Slack channel             | Slack MCP (`slack_read_channel`) with the channel ID from the portal. Never the Benmore API | Anything said after the handoff                                                |

If the sales notes are pasted in chat, save them verbatim to `Discovery/sales_notes.md`
first, with a one-line header saying where they came from and when.

Ask the user, in one message, only for what you cannot find: usually the sales notes, the
kickoff date and time, or their own complexity hypotheses. Do not ask for anything already
on disk or in the conversation.

---

## Step 2: Work out the facts before writing

Build these lists in your head (or a scratch file) first. The primer is only as good as
these.

1. **Agreed ground rules.** Every commercial or process point already communicated to the
   client: what the SOW covers, how the build is priced, credits, what happens to early
   price figures, compliance phasing, Discovery length and cadence, support terms, dates.
   Record who said it, in what channel, on what date, and whether the client accepted it.
   Only points the client has already seen belong in the primer. Internal notes, margins,
   staffing and anything said only inside Benmore stay out.
2. **Document versions.** If the client has sent several versions of a document, list what
   each new version added and how it affects Phase 1 (High / Medium / Low, with a reason).
   Note which files are the current source of truth.
3. **The client's own research.** If they already did market, competitor or patent research,
   that is the starting point. Build on it; do not redo it.
4. **Phase 1 boundary.** What Benmore has recommended as the first build, and what is
   explicitly later.
5. **The client's own feature list,** in their words, if they sent one, with the current
   read on each item.
6. **Open decisions.** Every place where the scope could reasonably go two or three ways and
   the answer changes cost or timeline.
7. **Outstanding homework.** Access, documents or decisions the client still owes, and since
   when.

---

## Step 3: Research, with citations

Run web searches for current, citable data. Focus on what the client's own materials do
not already cover:

- Size of the problem: government or regulator statistics first (BLS, Census, the relevant
  agency), then credible industry reports and trade publications.
- **Regulatory drivers,** when the product touches a regulated area: the rule, its citation,
  its status (proposed or in effect, with dates), and what the product has to encode
  because of it. Never present a proposed rule as law.
- Evidence about the people the product serves.
- Competitors and analogous platforms: name, founded, focus, published pricing.

Rules:

- Cite every number inline as `([Source Name](url))`. If you cannot find a source, leave the
  number out.
- Say how old a figure is when it is more than two years old, and why it is still relevant.
- When sources disagree widely (market-size estimates often do), say so and give one.
- Flag anything you could not verify, e.g. "Founding years are approximate. Verify them
  before any external use."

---

## Step 4: Write PRIMER.md

Save to `<project dir>/Discovery/PRIMER.md`. Use the structure below. Sections marked
_optional_ are included only when there is real material for them; never pad one.

```markdown
# [Product Name] — Pre-Kickoff Project Primer

**Prepared by:** Benmore Technologies
**Date:** [Month D, YYYY] ([kickoff today / kickoff on ...], [time in each attendee time zone])
**Client:** [Full names, with credentials if they use them] ([Entity, if any])
**Project Code:** BEN-[XXX]

---

## What We Understand You're Building

[2-4 paragraphs of prose. Who it is for, what goes wrong for them today, what the product
changes. Use the client's own vocabulary and frameworks, and quote them where a phrase
captures it. Name what Phase 1 is and why it comes first.]

From [our calls / the materials you shared], we can see the core loop clearly:

1. **[Actor]** [does what, gets what]
2. ...

---

## Where We Stand Going Into Kickoff (optional: when terms were already discussed)

[One sentence: these were agreed in writing (who, when), restated so everyone starts from
the same place.]

- **[Point].** [What was agreed, with the figure and the source.]

---

## What Changed in Your Latest Documents (optional: when versioned documents exist)

[Which files are now the source of truth.]

| Version | What was added | Phase 1 relevance |
| ------- | -------------- | ----------------- |

[What is unchanged and still the Phase 1 core.]

---

## Industry & Market Context

### [The market or category]

[Build on the client's research; add outside data. Every number cited.]

### [Regulatory Drivers Phase 1 Has to Encode] (optional: regulated domains)

[One bold-led paragraph per rule: what it says, status, what the product must do.]

### [The People You Are Protecting / Serving]

[Evidence about the users, cited, tied back to what the client told us.]

### Existing Alternatives

| Platform | Founded | Focus | Pricing |
| -------- | ------- | ----- | ------- |

**The key gap these platforms leave:** [what none of them do]. This is [Product]'s
opportunity.

---

## What We Think the Core Value Propositions Are

### For [User type, e.g. the people using it day to day]

- **[Benefit].** [One sentence.]

### For [The buyer]

### For [Any third group the product touches]

---

## Your [Feature List / N Features], Mapped to Phases (optional: when the client sent one)

| #   | Feature (your [date] list) | Current read |
| --- | -------------------------- | ------------ |

---

## Open Questions We Want to Discuss With You

We'd like to use the kickoff call to align on these before we size anything. Each answer
moves Phase 1 timeline and cost in a predictable direction.

### Tier 1 — Core Functionality Decisions

**1. [Question as the client would ask it]**
[Why it matters, what each answer costs.]

- [Option, smallest first]
- [Option]
- [Option, largest]

[4-6 Tier 1 questions.]

### Tier 2 — Complexity & Scope Decisions

**[N]. [Question]**
[2-4 Tier 2 questions, same pattern.]

---

## Our Initial Read on Complexity

[2-3 sentences: what kind of system this is and where the work and risk sit. Say roughly how
the effort splits (e.g. back end vs interface) if you can defend it.]

- **[Dimension].** [Why it is hard and what it touches.]

None of these are blockers. They're design decisions, and each one will significantly shape
timeline and cost.

---

## What We'd Like to Accomplish in Our Kickoff Call

1. [Confirm ground rules and set a meeting cadence]
2. [Agree on Phase 1 and work through the top Tier 1 questions, named]
3. [Confirm which documents are the source of truth]
4. **Access and homework:** [each outstanding item, and since when]
5. [Next meeting or working session, and the first deliverable we'll bring back]

---

## Next Steps from Benmore's Side

After our kickoff call, we'll produce:

- [ ] Technical Requirements Document ([what it will cover for this project])
- [ ] Market Analysis ([built on their research, if they have some])
- [ ] MVP Features List ([starting from what], with a clear in/out of scope line)
- [ ] User Flow Diagrams ([the specific journeys])
- [ ] Quote, Associated Fees & Timeline for Phase 1

[If SOW template items do not apply (e.g. no existing codebase to assess), say so in one
sentence and why.]

[Closing paragraph, 2-3 sentences: why the opportunity is compelling, tied to the evidence
above, and what Discovery is for.]

---

_Prepared by Benmore Technologies — [benmoretechnologies.com](https://benmoretechnologies.com)_
```

Do not put a named individual in the footer or the header. The primer is from Benmore.

### Writing rules

- Written to the client: "you" and "we". It must read well to the client, so nothing
  internal (other clients, margins, internal disagreements, staff availability).
- Plain, specific sentences. Numbers, dates and names over adjectives. No hype words,
  no emojis.
- Attribute agreements and facts: "our Oct 27 email", "your Oct 23 list",
  "your business plan v2". This is what makes the primer trustworthy.
- Use the client's terms and frameworks exactly as they write them.
- Quote the client sparingly, where their phrase says it best.
- Open questions come from the real scope decisions found in Step 2 and the user's own
  complexity thoughts, never generic filler. Each one lists concrete options, smallest
  first.
- Separate clearly what is decided, what is proposed, and what is unknown. Never state a
  price, date or scope item as settled unless the client has already accepted it.

---

## Step 5: Build PRIMER_PRESENTATION.html

Copy `assets/primer-presentation-template.html` to
`<project dir>/Discovery/PRIMER_PRESENTATION.html` and fill it in. Keep the CSS as it is.

The presentation is the screen-share version, so it is shorter than the markdown and
focuses on the product and the decisions. Map it like this:

| PRIMER.md section                                | In the presentation                                                                                         |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| What We Understand                               | `highlight-card` + a Mermaid core-loop diagram                                                              |
| The client's framework or module map, if any     | `grid-3` of cards; the Phase 1 module as `special-card`                                                     |
| Value propositions                               | One `role-card` per user type                                                                               |
| Phase 1 contents                                 | Two `feature-card`s (one per side of the product) + a `highlight-card` for any cross-cutting guarantee      |
| Client feature list                              | Table with phase tags (`tag-high`, `tag-med`, `tag-low`, `tag-open`)                                        |
| Secondary journeys                               | "Key Flows": one card and Mermaid diagram each                                                              |
| Open questions                                   | The biggest scope question as `error-card`; the rest as `warning-card`s; keep the numbers from the markdown |
| Next steps                                       | `feature-card` for deliverables, `special-card` for later phases, closing `highlight-card`                  |
| Where We Stand, What Changed, Market, Complexity | Leave out. They stay in the written primer                                                                  |

Rules:

- No emojis. Use `→` and `•` only where a symbol is needed.
- Every placeholder replaced; delete optional sections and cards that have no content.
- Mermaid labels: keep them short, use `<br/>` for line breaks, and quote every label.
- Open the file in a browser (or render it with Playwright) and check that every Mermaid
  diagram renders and nothing overflows at phone width before calling it done.

---

## Step 6: Hand back

Tell the user both paths, list any facts you could not verify or sources you could not
reach, and list the open questions in one line each so they can check the framing before
the call.
