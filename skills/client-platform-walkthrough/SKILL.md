---
name: client-platform-walkthrough
description: Use when the user asks for a client-facing platform guide, product walkthrough, onboarding documentation, demo doc, sales handoff, customer-facing tour, or any "thorough docs for clients" of a web application. Trigger whenever the user mentions making a guide for clients, walkthrough docs, screenshot-driven documentation, customer onboarding tour, or wants to document a platform for non-engineers. Also trigger on phrases like "make a guide", "client doc", "user manual for X", "walk through the platform", "screenshots for clients", or when the user gestures at an existing engineer-facing guide and asks for a customer version. Generates a comprehensive screenshot-driven walkthrough that combines parallel codebase research (via subagents), systematic page-capture via the playwright-cli skill, and a structured business-language markdown deliverable.
---

# Client Platform Walkthrough Generator

This skill produces a **complete, screenshot-driven, client-facing tour of a web application**: every persona's entry point, every important page, every feature, with images saved alongside the markdown so the doc renders offline. It's the deliverable a sales engineer or solutions architect would hand a new customer.

The skill chains three things you already have:
1. **Parallel research subagents** to map the codebase fast (so you understand the surface before opening the browser).
2. **The playwright-cli skill** to actually walk the live app and capture screenshots.
3. **A consistent client-doc structure** so every guide you produce reads the same way.

Without this skill, a model usually either (a) writes a generic outline with no screenshots, or (b) screenshots one or two pages and stops. The structure below forces full coverage and a consistent business-language voice.

---

## When this skill applies

Trigger this when:

- The user wants documentation **for end users, not engineers** — phrases like "for clients," "for customers," "user guide," "platform tour," "onboarding doc," "demo handoff."
- The deliverable is a **walkthrough of a real running web app**, not API reference or architecture diagrams.
- Screenshots are part of what's being asked for (or strongly implied — "thorough docs," "show them what to expect").
- An **engineer-facing version of the same doc may already exist** (e.g., `*_PLAYWRIGHT_GUIDE.md`, `ONBOARDING_GUIDE.md`) — the user wants the client analog.

Do **not** trigger this skill for:

- API reference docs (use OpenAPI / Swagger generation).
- Architecture or runbook docs (those are engineer-facing).
- Marketing copy (this is operational, not promotional — though tone-wise it's friendlier than a runbook).

---

## High-level workflow

The whole job is four phases. Don't skip phases — each one feeds the next.

```
Phase 1: Orient        → understand what's being built and what already exists
Phase 2: Research      → dispatch parallel subagents to map every surface
Phase 3: Capture       → playwright-cli walk through pages, save screenshots
Phase 4: Write         → produce the markdown using the template in references/doc-template.md
```

### Phase 1 — Orient (5 minutes)

Before any tool call:

1. **Find the existing doc, if any.** Look for files like `ONBOARDING*.md`, `WALKTHROUGH*.md`, `DEMO*.md`, `PLAYWRIGHT*.md` in `docs/`. Read the table of contents and the first few hundred lines. This shows you the established voice, screenshot naming convention, and which routes the team considers important.
2. **Check what's running.** Probe the dev server with `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000` (and the typical alternates: 3001, 8000, 8001). If nothing is running, ask the user to start it before continuing — you cannot capture screenshots without a live app.
3. **Read CLAUDE.md (or equivalent).** It usually lists routes, personas, and live-vs-stubbed feature status. The "live vs. coming soon" section of the eventual deliverable depends on knowing which integrations are stubs.

### Phase 2 — Research (parallel, ~3 minutes wall-clock)

Dispatch **three subagents in parallel in a single message**. They explore the codebase while you start screenshotting in Phase 3 — don't wait for them sequentially.

Suggested split:

| Agent | Focus | Output |
|---|---|---|
| Agent A | All persona-1 pages (e.g., athlete, customer, end-user) — every route + UI labels + preconditions | A markdown file: routes mapped, ~150 words each |
| Agent B | All persona-2/persona-3 pages (e.g., admin, organization, advisor) — same shape | Same |
| Agent C | Backend feature inventory — what's live vs. stubbed, per app/module | A markdown file flagging stubs explicitly |

Use `model: haiku` for these — speed matters more than depth here, and you'll verify everything via the actual screenshots.

Prompts should ask the agent to use **business-friendly language** (no Django ORM jargon, no test-count-as-smoke-check), give **concrete UI labels** (button text, headings) over abstract descriptions, and **flag missing routes** instead of hallucinating them.

### Phase 3 — Capture (do not skip the playwright-cli skill)

**Invoke the `playwright-cli` skill before opening a browser.** It tells you the right command shapes, ref-based interaction, and screenshot syntax. Do not freelance browser automation — the skill exists for a reason.

Then follow this capture protocol:

1. **Set up a stable workspace.**
   - Pick a screenshot directory: `docs/screenshots/client-guide/` (or whatever fits the repo's existing convention).
   - Create it before starting: `mkdir -p docs/screenshots/client-guide/`.
   - Use **absolute paths** in `--filename` arguments. Relative paths break the moment your shell `cd`s, and `cd` will silently invalidate the playwright-cli session because session state lives in `.playwright-cli/` of the cwd.

2. **Set a consistent viewport.** `playwright-cli resize 1440 900` once, at the start. This is desktop-standard and renders well in markdown.

3. **Use a numbered prefix on every screenshot.** Format: `NN-area-detail.png` where `NN` zero-pads to 2 digits and increments in document order. Examples:
   ```
   01-welcome-modal.png
   02-landing-hero.png
   11-institution-step1-empty.png
   11b-institution-step1-filled.png   ← suffix when capturing two states of the same screen
   ```
   Document order is more important than feature order — the reader scrolls top-to-bottom and the screenshots should match.

4. **Capture every persona's first-touch UI.** Welcome modals, role pickers, and onboarding gates are often the *most* important screenshots because they shape first impressions. Don't dismiss them as noise.

5. **Walk wizards end-to-end with realistic synthetic data.** When a step has form fields, fill them with plausible values (e.g., "Demo State University," not "asdf"), then capture both the empty and the filled state. The filled state shows the user what their version will look like.

6. **For auth-gated pages, mint a real JWT.** Don't bypass guards by stubbing localStorage with a fake token — that hides real bugs and produces inauthentic screenshots. Instead:
   - POST to the actual register endpoint to create a demo user.
   - POST to the login endpoint to get an access + refresh JWT pair.
   - Inject **both** into `localStorage` (`access_token`, `refresh_token`) and into a cookie if the app uses cookie-based auth.
   - Now navigate; everything you screenshot is a real authenticated session.

7. **Capture meaningful states, not just happy paths.** Verification gates, empty states, error banners, and "coming soon" placeholders are part of what a client will encounter. Screenshot them and document them honestly — they reduce sales surprise.

8. **If the playwright-cli session breaks, just reopen.** A `cd` in the same shell, a tab close, or a long idle can lose the session. Reopen with `playwright-cli open <url>`, re-resize, re-inject auth, and continue. Don't waste cycles debugging the broken session.

### Phase 4 — Write the deliverable

Read `references/doc-template.md`. It has the canonical 17-section structure. Follow it.

The template is a **starting point**, not a constraint. Drop sections that don't apply. Add sections the user explicitly asks for. But preserve the spine:

```
1. What is X?                    ← business-language overview (no jargon)
2. Persona-to-page map           ← 60-second orientation table
3. First impressions             ← public site, before auth
4. For [primary persona type 1]  ← typically the buyer (institution, org, B2B customer)
5. The invitation / signup flow  ← magic-link, onboarding, account setup
6. Auth + 2FA                    ← if the platform has it
7. The main dashboard / home     ← after-auth landing
8-N. Feature deep-dives          ← one section per high-value surface
N+1. Pricing & plans             ← always include this if relevant
N+2. Security & privacy          ← masking matrix, data-rights summary
N+3. Live vs. coming soon        ← the most important honesty section
N+4. Support / FAQs              ← getting unstuck
N+5. Page reference              ← URL lookup table at the end
```

The **"live vs. coming soon"** section is non-negotiable. Customers and sales engineers both depend on it. Get this from the backend feature inventory subagent's output.

Write in **action-oriented, business-language voice**:
- "Click **Continue as Athlete**" beats "the modal has a CTA element with role=button."
- "Setup takes 10–14 days end-to-end" beats "the average pipeline duration is bounded by state filing latency."
- Quote UI labels in **bold** verbatim — that's how the reader maps your prose to what they see.

Reference every screenshot inline: `![Caption describing what's in the image](path/to/01-welcome-modal.png)`. Captions should describe the screenshot for accessibility and so the doc reads even with images broken.

### Phase 5 — End-of-job sanity check

Before declaring done:

```bash
ls docs/screenshots/client-guide/ | wc -l        # how many images
wc -l docs/CLIENT_PLATFORM_GUIDE.md              # how long is the doc
grep -c '!\[' docs/CLIENT_PLATFORM_GUIDE.md      # how many image refs
```

If the third number is much smaller than the first, you have orphan screenshots. If the third is larger than the first, you have broken image refs. Fix before handing off.

---

## Key principles

### Honesty over completeness

Every platform has stubbed integrations and pending UI. Document them. The "coming soon" section prevents the customer from being surprised in week 3 when their SMS notifications never arrive. Sales teams will tell you customers respect a guide that admits the gaps far more than one that pretends everything is shipped.

### Business voice, technical accuracy

The voice is for non-engineers. The accuracy is for engineers. These don't conflict — write "your data is encrypted at rest" and *also* note (in a smaller-typeface aside or footnote) that the encryption is Fernet AES-128. The non-engineer reads past the technical detail; the compliance officer reads it carefully. Both are served.

### Screenshots are the spine

The doc is structured around the screenshots, not the other way around. After Phase 3, lay out the screenshots in document order on disk. The markdown reads top-to-bottom, image-by-image. If a section has no screenshot, ask whether the section actually belongs in the doc — sections without visual anchors tend to be the ones the reader skips.

### One persona per section, no head-jumping

If §5 is "for athletes," every paragraph in §5 talks to the athlete. Don't break the fourth wall to address admins mid-section. Persona-mixing is the most common failure mode in walkthrough docs and the most disorienting to read.

### Reproducibility, not regeneration

End the doc with an "Appendix — How this guide was built" section that includes:
- The date the screenshots were captured
- The dev environment / branch
- A pointer to the engineer-facing companion doc (e.g., `docs/ONBOARDING_PLAYWRIGHT_GUIDE.md`)
- One-line instructions for replacing a stale screenshot (which playwright-cli command, what filename to overwrite)

This lets the next person who touches the doc edit it cleanly instead of regenerating from scratch.

---

## What success looks like

A finished walkthrough has, roughly:

- **30–60 screenshots** in a single numbered directory
- **600–900 lines of markdown** (longer is fine for complex platforms; shorter usually means under-coverage)
- **15–18 sections** following the spine above
- **At least one screenshot per major persona's first-touch UI**
- **A "live vs. coming soon" section that honestly flags every stub**
- **A page reference table at the end** that a customer can use as a sitemap

If after Phase 3 you have only 8 screenshots, you missed something. Go back to the persona-to-page map from Phase 2 and check coverage.

---

## Reference files

- `references/doc-template.md` — the canonical 17-section markdown skeleton with prose patterns to copy.
- `references/screenshot-checklist.md` — a per-page coverage checklist organized by typical SaaS personas (B2B buyer, end-user, advisor, admin). Use this to verify you didn't miss surfaces.
- `references/playwright-recipes.md` — common playwright-cli sequences for auth injection, modal dismissal, and form-fill iteration. Read this if you find yourself fighting the browser instead of capturing pages.

Read these only when you reach the relevant phase — keep SKILL.md as the index.
