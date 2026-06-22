---
name: design-director
description: >-
  Use when frontend UI quality needs improving but the user cannot name the
  design problem, asks why output looks generic / AI-default / off, wants
  vocabulary-driven diagnosis before using impeccable, needs an agent to choose
  the right impeccable subcommands instead of running all of them, or keeps
  nitpicking ("colors look off", "font's ugly", "spacing's weird") build after
  build because the project has no written design system. Establishes and
  enforces a DESIGN.md design contract so style stops drifting between builds.
---

# Design Director

## Why this exists

If the user keeps saying "the colors look off," "the font's ugly," or "the
spacing's weird" on every build, the problem is not the agent's taste — it is
that **nothing in the project tells it what right looks like.** With no written
system, every UI build reaches for framework defaults, the style drifts, and the
user is left nitpicking each pass by hand.

The Design Director removes that loop. It does two things:

1. **Gives the project ONE design contract** (a `DESIGN.md`) so "what good looks
   like" is written down once and read before every UI build — style stops
   drifting.
2. **Diagnoses each screen in precise terms** and routes to the *smallest useful*
   `impeccable` chain, then verifies the result visually.

If you find yourself critiquing output instead of pointing at a contract the
output should have honored, you skipped Stage 0.

## Core Principle

Act as the design director and router. The user should not need design
vocabulary or know which `impeccable` command to run. Diagnose the screen in
precise terms, choose the smallest useful `impeccable` command chain, set a
concrete ambition level, implement, then verify visually.

**Do not run all `impeccable` commands.** Running everything averages
conflicting workflows into generic output.

**Default stance for vague "make it better" UI work:** aim for a visibly
stronger composition, not a safer polish pass. If the screen can still be
described as "cards with nicer spacing," the pass is not done.

## Stage 0 — The Design Contract (before any UI edit)

Before diagnosing or editing a single screen, settle where "what good looks
like" lives. This is the step that stops the nitpick loop.

1. **Look for an existing contract.** Check for `DESIGN.md`, `PRODUCT.md`,
   `BRAND.md`, a brand kit, or design tokens (`tokens.*`, `theme.*`, CSS
   variables, a Tailwind/`shadcn` theme). If one exists, **it owns direction.**
   Read it first. `impeccable` and every richness idea become *executors* of
   that contract, never deciders. New surfaces must comply with it — that is how
   drift is prevented.

2. **If no contract exists, decide whether to create one.** Establish a
   `DESIGN.md` (see template at the bottom) when ANY of these are true:
   - The user has nitpicked visual details (color/font/spacing) more than once.
   - The work spans more than one screen, or will recur.
   - The user asks for "a design system," "consistency," "stop the drift," or
     "make everything match."

   For a genuine one-screen one-off with no recurrence, you may skip the file
   and instead pin an inline mini-contract (palette, type scale, spacing,
   radius, shadow) at the top of your operating brief — but say you did so and
   offer to promote it to `DESIGN.md` if the user wants it to stick.

3. **Write the contract ONCE, then freeze it.** A `DESIGN.md` must be concrete
   and decision-complete: exact palette with semantic tokens, type scale,
   spacing scale, radius scale, elevation/shadow, border/stroke, motion
   (durations + easings + reduced-motion rule), component rules, and the
   required states every interactive surface must ship. Vague adjectives
   ("modern," "clean") are not a contract. After it is written, treat it as
   fixed for the rest of the work; change it deliberately, not per-screen.

4. **Read the contract before every build and obey it.** When you implement a
   screen, the contract's tokens are the source of truth. Do not introduce a new
   gray, a new radius, or a one-off shadow that the contract does not define —
   extend the contract instead, then use it.

Only one system may own direction at a time. Never run two direction-owning
sources (e.g. an existing brand kit *and* a fresh `design-taste` proposal)
against the same surface in one pass.

## Required Sub-Skills

- **REQUIRED SUB-SKILL:** Use `vocabulary` first for design terminology and
  diagnosis.
- **REQUIRED SUB-SKILL:** Use `impeccable` second for frontend design execution.
- **REQUIRED SUB-SKILL WHEN AVAILABLE:** Use `playwright` or `playwright-cli`
  for browser verification after UI changes.
- **OPTIONAL DETAIL-POLISH REFERENCE:** If `make-interfaces-feel-better` is
  installed, use it for micro-interaction and surface-detail checks after the
  main design direction is chosen.
- When the task touches live UI quality, use browser verification if available:
  desktop screenshot, mobile screenshot, critique, one revision.

If any sub-skill is unavailable, continue with the same workflow and say which
dependency was missing.

## Workflow

1. **Settle the contract (Stage 0)**
   - Find the existing design contract, or establish/pin one. Do not start
     editing pixels before "what good looks like" is written down somewhere.

2. **Collect the evidence**
   - Inspect the current screen, screenshot, route, or relevant component.
   - Run the `impeccable` setup/context steps before design output.
   - Read the relevant `impeccable` register reference: `brand` for
     marketing/landing/portfolio surfaces, `product` for app/dashboard/tool
     surfaces.

3. **Translate weakness into vocabulary**
   - Use `vocabulary` to name the top 5 design failures with its **canonical
     terms** — pull the definition from the skill's `vocabulary.md`, do not coin
     jargon. Reach for the precise word: `tracking` (uniform letter-spacing) vs
     `kerning` (between two specific glyphs); `leading` (line spacing) vs `gap`;
     `type scale`, `line length`, `tabular nums`; `chroma`/`contrast ratio`/
     `tinted neutral`/`semantic token`; `negative space`, `hierarchy`,
     `layout shift`; `affordance`, `focus state`, `touch target`; `easing`,
     `stagger`, `choreography`, `motion as feedback`, `reduced motion`;
     `progressive disclosure`, `wayfinding`, `empty state`, `error state`;
     `microcopy`, `CTA`, `inline error`, `front-loading`.
   - For each term, write: `term -> actual screen symptom -> desired change`.
   - Use plain English after the term. The user is not expected to know the
     jargon — the term sharpens *your* diagnosis, the plain English explains it.
   - When you name a component or interaction, use the right half of the
     confusable pair so the fix is unambiguous: badge (attached, informational)
     vs tag (standalone, selectable); tooltip (non-interactive) vs popover
     (interactive); modal vs sheet (side panel) vs drawer (bottom panel);
     ease-out (entering) vs ease-in (leaving); opacity (still occupies space and
     takes pointer events) vs visibility.
   - Where a failure is really "this violates the contract" (off-token color,
     ad-hoc radius), say so — that is a drift bug, not a taste call.

4. **Set the ambition level**
   - Choose one: `surgical` (fix a narrow flaw), `strong` (material redesign),
     or `showpiece` (memorable visual system).
   - Default to `strong` for vague improvement requests.
   - Default to `showpiece` when the user asks for fancy, cool, rich, charts,
     motion, impressive, or non-generic output.
   - If choosing `surgical`, state why a richer pass would be wrong for the
     product or request.

5. **Run the rich surface inventory**
   - Look for opportunities to add memorable, useful surface area before
     choosing commands.
   - Consider these by default: data visualizations/charts, dense detail modals,
     drawers/sheets, command menus, navigational sidebars, comparison tables,
     timelines, maps, calendars, status matrices, keyboard shortcuts,
     empty/error states, and purposeful animation.
   - For `strong`, select at least two rich surface candidates unless the
     product context makes them inappropriate.
   - For `showpiece`, select at least three rich surface candidates, including
     one motion idea and one data/structure idea.
   - If the product has any quantitative, relational, time-based, status,
     funnel, financial, legal, operational, or workflow data, propose at least
     one chart or structured visualization.
   - Do not add decorative charts. Every chart must answer a real user question
     and use real or clearly local/demo data consistent with the product.

6. **Pick one art direction (from the contract)**
   - State a concrete visual direction in one or two sentences, drawn from the
     contract's tokens — not invented fresh per screen.
   - Do not offer generic options unless the brief is genuinely ambiguous.
   - The direction must include physical/visual language, not just adjectives
     like premium, modern, clean, or polished.
   - Include one interaction/motion idea and one information-density idea.
   - If the user names a reference bar ("feel like Linear / Stripe / Vercel"),
     translate it into the contract's terms — restrained palette, disciplined
     type scale, generous whitespace, consistent radius and shadow — rather than
     copying a look.

7. **Run the micro-polish gate**
   - After the composition/richness direction is chosen, inspect details that
     make the UI feel built by hand: concentric border radius, optical icon
     alignment, layered shadows versus hard borders, subtle image outlines,
     tabular numbers, balanced headings, pretty body wrapping, touch targets,
     tactile press states, interruptible transitions, and precise animation
     properties.
   - Prefer CSS transitions for interactive state changes; reserve keyframes for
     one-shot staged sequences.
   - For icon swaps, animate `opacity`, `scale`, and `blur`; use Motion only if
     the project already has `motion` or `framer-motion`, otherwise use CSS
     cross-fades rather than adding a dependency.
   - Avoid `transition: all`, `will-change: all`, exaggerated press scaling,
     overlapping hit areas, and entrance animations that hide content or replay
     on initial page load.
   - When reviewing or reporting these detail changes, use a compact
     `Before | After` table grouped by principle.

8. **Run the state + accessibility gate** (see the two gates below)
   - Confirm every interactive surface ships all of its states.
   - Confirm keyboard, low-vision, and multi-device users can complete the core
     action.

9. **Route to a small impeccable chain**
   - Choose 3-5 `impeccable` commands max.
   - Treat comma/slash lists in examples as alternatives; pick concrete commands
     before acting.
   - Explain why each command applies.
   - Name tempting commands intentionally skipped.
   - Turn the selected chain into a short operating prompt that includes the
     vocabulary failures, the contract tokens, art direction, rich-surface
     inventory, required states, and verification plan.
   - Read each selected command reference before using it.

10. **Execute and verify**
    - Implement the design change against the contract tokens.
    - Start or use the local dev server when the app requires one.
    - Use Playwright/Playwright CLI when available to capture desktop and mobile
      screenshots.
    - Check for visual overlap, dead whitespace, unreadable contrast, broken
      responsive behavior, blank animation states, and any off-contract value.
    - Check the ambition level honestly: `strong` must look materially different
      from the starting point; `showpiece` must contain a memorable composition
      or interaction.
    - Critique the result using the same vocabulary terms.
    - Revise once before finalizing. If the screenshot still reads as generic
      cards/text, revise the composition, not just spacing.

11. **Report the outcome**
    - State which contract was used or created (`DESIGN.md` / brand kit / inline
      mini-contract), and any tokens added to it.
    - List the vocabulary terms used.
    - List the `impeccable` command chain used.
    - Note screenshots/viewports checked.
    - Call out remaining weak spots or verification gaps.

## States Are Not Optional

A surface is not done when the happy path renders. Most "it feels unfinished"
complaints are unbuilt states. Before finalizing any interactive surface,
confirm it ships every state that applies to it:

- **Display surfaces:** empty (first-run, with a real next action), loading
  (skeletons that match final layout, not a spinner over blank space), error
  (what failed + how to recover), populated, and dense/overflow.
- **Controls:** default, hover, focus-visible, active/pressed, disabled (with a
  reason), and selected where relevant.
- **Async actions:** in-flight (button busy + disabled to prevent double
  submit), success feedback, and failure with a retry path.
- **Forms:** real-time and on-blur validation, clear inline errors next to the
  field, sensible defaults and input types, keyboard + autofill friendliness,
  a submitting state, and explicit success / failure outcomes. Split long forms
  into steps with progress and back navigation; never lose entered data on
  error.

Build these as reusable components, not per-page one-offs — that is what keeps
the next screen consistent. Treat a missing empty/error/loading state as a
defect to fix, not a nice-to-have.

## Accessibility & Multi-Device Gate

Regular, low-vision, keyboard-only, and different-device users must all be able
to complete the **core action**. Before finalizing:

- **Walk the core path at three widths** — desktop, tablet, phone — and confirm
  no overflow, no layout shift that hides the primary action, and touch targets
  ≥ 40-44px on phone.
- **Keyboard-only:** every interactive element is reachable and operable by tab
  order, focus is always visible, focus is trapped correctly in modals, and
  `Esc`/back escapes overlays.
- **Low-vision:** text and essential UI meet contrast minimums (4.5:1 body,
  3:1 large/UI), nothing relies on color alone to convey state, and the layout
  survives a 200% zoom.
- **Motion:** honor `prefers-reduced-motion`; never gate content behind an
  animation or replay entrance animations on every load.

When tools allow, actually start the app and walk the path — do not assert
accessibility from reading code. Rate any issue found by severity and give a
concrete fix, the way a senior UX auditor would.

## Richness Defaults

When the user asks for stronger visual output but gives no design terms, bias
toward useful richness:

- **Charts and visualizations:** Prefer charts for trends, distributions,
  comparisons, status mixes, timelines, workloads, money, risk, citations, case
  outcomes, funnels, or activity. Use an existing charting library if present;
  otherwise use lightweight SVG/CSS before adding dependencies. If the user says
  they love charts, treat charts as a preference signal, but still require every
  chart to answer a user question.
- **Dense detail surfaces:** Use modals, drawers, sheets, popovers, and tables
  when the user needs drill-down without losing context. Dense does not mean
  cramped: preserve hierarchy, sticky headers, scannable labels, clear
  close/back affordances, and a reason to open the surface.
- **Navigation:** Add command menus, sidebars, breadcrumbs, tabs, segmented
  controls, and wayfinding when the surface has more than one workflow. Do not
  bury navigation inside cards.
- **Motion:** Prefer purposeful choreography over generic fade-ins. Check the
  repo for anime.js, Motion, GSAP, or existing animation helpers. If anime.js is
  available, consider timeline-driven reveals, count-ups, path motion, staggered
  evidence rows, chart draws, modal transitions, or panel transitions. Always
  support reduced motion and never hide content before animation runs.
- **Micro-interactions:** Make controls feel responsive without becoming
  theatrical: 40-44px hit areas, visible focus, `active:scale-[0.96]` where
  appropriate, interruptible hover/toggle transitions, no overlapping click
  targets, and reduced-motion fallbacks.
- **Typography details:** Use balanced headings, pretty short copy wrapping,
  tabular numbers for counters/tables/timers/prices, and root font smoothing
  when the stack supports it.
- **Surface details:** Check nested radii mathematically, use optical alignment
  for icon/text buttons, prefer layered shadow rings for elevated
  cards/buttons/dropdowns, and add neutral image outlines when images need
  separation from their background.
- **Components:** Replace repetitive cards with stronger components when
  possible: data table, timeline, status matrix, chart panel, comparison rail,
  inspector drawer, activity feed, calendar, kanban, map, command palette, or
  evidence graph.
- **Assets and data:** Use real product data, local fixtures, screenshots,
  generated images, icons, and existing components where available. Do not
  invent business facts or fake production metrics.

## Visual Proof Gate

Before finalizing frontend work, require visual evidence when tools allow it:

1. Capture at least one desktop and one mobile screenshot.
2. Compare the screenshot to the starting point or stated failure.
3. Name the remaining weakest vocabulary term.
4. Revise once against that weakness.
5. Do not claim the design is strong if no screenshot was inspected; say
   verification was unavailable. A capture that lands on a login/blank page is a
   failure, not proof — say the session expired, never present it as the result.

Playwright/Playwright CLI is useful here because design quality is visual and
stateful. Static code review cannot catch cramped composition, weak hierarchy,
broken animation states, mobile overlap, or components that technically render
but feel dead.

## Routing Table

| User symptom | Vocabulary focus | Impeccable chain |
|---|---|---|
| "Every build looks different / style keeps drifting" | design tokens, system, consistency, semantic color | establish/extend `DESIGN.md` first, then `critique -> distill -> choose layout or colorize -> polish` |
| "It looks bland/generic/AI" | visual language, hierarchy, contrast, rhythm, negative space | `critique -> bolder -> choose 1-2 of layout, typeset, colorize, animate -> polish`, or `critique -> overdrive -> polish` |
| "It is messy/too busy" | hierarchy, density, progressive disclosure, scannability | `critique -> quieter -> distill -> choose layout or adapt` |
| "The composition is weak" | hierarchy, focal point, grid, asymmetry, negative space | `critique -> layout -> typeset -> polish` |
| "The colors feel flat/off" | chroma, contrast ratio, tinted neutral, semantic token | `critique -> colorize -> audit -> polish` |
| "The typography feels wrong" | type scale, leading, tracking, line length, weight | `critique -> typeset -> layout -> polish` |
| "The UI works but feels lifeless" | affordance, motion as feedback, easing, choreography | `critique -> animate -> delight -> polish` or `bolder -> animate -> polish` |
| "Rebuild this page with real taste (Linear/Stripe)" | restraint, type scale, whitespace, consistent radius/shadow | pin the contract, then `critique -> layout -> typeset -> colorize -> polish` (visuals only, no new features) |
| "Mobile/responsive is bad" | breakpoint, layout shift, touch target, overflow | `audit -> adapt -> layout -> polish` |
| "Build a new UI/feature" | mental model, hierarchy, affordance, empty/error states | `shape -> craft -> adapt -> polish` |
| "Get every interaction/state right" | empty, loading, error, hover/focus/disabled, feedback | `shape -> craft -> harden -> polish` (run the States gate) |
| "Make this form usable" | validation, inline error, defaults, keyboard, multi-step | `shape -> craft -> harden -> polish` (run the States gate) |
| "Build a landing page that converts" | value prop, hierarchy, social proof, single CTA | `shape -> brand register -> craft -> typeset -> polish` |
| "The copy/labels feel unclear" | microcopy, CTA, front-loading, tone, error message | `clarify -> typeset -> polish` |
| "Make it production-ready" | accessibility, contrast, focus state, reduced motion, error state | `audit -> harden -> adapt -> polish` |
| "I want richer components/charts/modals/navigation" | information density, wayfinding, data visualization, progressive disclosure | `critique -> bolder -> choose 1-2 of layout, colorize, animate -> polish` |
| "Pull scattered UI into a design system" | tokens, component library, semantic naming, reuse | establish `DESIGN.md`, then `distill -> harden -> polish` across components |

## Command Selection Rules

- Start with the contract (Stage 0) before any `impeccable` command on recurring
  or multi-screen work.
- Start with `critique` when improving an existing surface and no recent
  critique exists.
- Start with `shape` when designing a new flow or feature before code exists.
- Use `craft` only when building a new feature end to end.
- Use `polish` only after a concrete design direction or implementation exists;
  do not use it as the first move on a weak composition.
- Use `overdrive` only when the user explicitly wants ambitious or memorable
  work and the brand can support it.
- Use `live` when a dev server is running and visual iteration is the fastest
  path.
- Use `animate` when motion can explain state, sequence, confidence, or
  hierarchy. Prefer anime.js when already in the project, when timeline
  choreography matters, or when drawing charts/paths/count-ups creates a better
  explanation than static UI.
- Use `delight` when the UI is correct but forgettable; pair it with useful
  charts, motion, or components rather than decoration.
- Use `audit` for measurable technical quality: accessibility, performance,
  responsive behavior, and contrast.
- Use `distill` / `harden` when the job is consolidating scattered UI into
  reusable, accessible, state-complete components.

## Red Flags

Stop and reroute if you catch yourself doing any of these:

- Editing pixels before a design contract exists or has been read (Stage 0
  skipped).
- Critiquing output's taste when the real fault is drift from a contract the
  output should have honored.
- Inventing a new color, radius, or shadow per screen instead of extending the
  contract and reusing its tokens.
- Asking the user to supply design vocabulary.
- Saying only "make it premium / clean / modern" without a concrete art
  direction or contract tokens.
- Running all `impeccable` commands.
- Polishing existing cards when the composition itself is the problem.
- Shipping a surface with only its happy path — no empty, loading, or error
  state.
- Claiming accessibility or responsiveness without walking the path at multiple
  widths / keyboard-only.
- Claiming visual quality without browser screenshots, or presenting a
  login/blank capture as proof.
- Producing a design that satisfies bans but has no distinctive visual language.
- Choosing `polish` when the screen needs a new composition or richer component
  model.
- Defaulting to `surgical` for a vague improvement request.
- Skipping charts or structured visualizations when the product has obvious
  data, or adding charts that do not answer a user question.
- Shipping modals/drawers with dense information but no hierarchy, sticky
  context, or escape route.
- Using animation as decoration instead of explanation or feedback.

## DESIGN.md Template

When you establish a contract, write a file like this at the repo root. Fill
every section with concrete values — a contract with adjectives instead of
tokens does not stop drift. Keep it short enough to be read before every build.

```markdown
# DESIGN.md — <project> design contract
Read this before building or editing any UI. Use these tokens; do not invent
one-off values. To change the system, edit this file, then use the new token.

## Color (semantic, not raw)
- Background: base / subtle / muted          (#…, #…, #…)
- Foreground: default / muted / subtle       (#…, #…, #…)
- Brand / primary + on-primary               (#…, #…)
- Border / ring                              (#…, #…)
- Status: success / warning / danger / info  (#…, #…, #…, #…)
- Rule: state is never conveyed by color alone.

## Typography
- Font families: display / body / mono
- Scale (px/rem + line-height): xs … 4xl
- Weights in use; tabular numbers for data; max line length ~66ch.

## Spacing & layout
- Spacing scale (e.g. 4 8 12 16 24 32 48 64); base unit = 4px.
- Container widths; grid columns; section rhythm.

## Radius & elevation
- Radius scale: sm / md / lg / full; nested radii are concentric.
- Shadows: layered ring + soft shadow per elevation level (not hard borders).

## Motion
- Durations (e.g. 120 / 200 / 320ms) and easings.
- CSS transitions for state; keyframes only for one-shot sequences.
- Always honor prefers-reduced-motion.

## Components
- Buttons, inputs, cards, modals, tables, nav: variants, sizes, default tokens.
- Source primitives from <shadcn/ui or the repo's standard>, themed by token.

## Required states (every interactive surface ships these)
- empty · loading (skeleton) · error · hover · focus-visible · active ·
  disabled · success/failure feedback.

## Accessibility baseline
- Contrast 4.5:1 body / 3:1 UI; visible focus; full keyboard operation;
  44px touch targets; survives 200% zoom.
```

## Prompt Pattern To Follow

When the user is vague, internally translate their request into this operating
brief:

```text
First settle the design contract: read the repo's DESIGN.md / brand kit / tokens
if one exists and obey it, or establish a DESIGN.md once when the work recurs.
Use vocabulary first and impeccable second; the user does not know design terms.
Diagnose the current UI in precise terms, set ambition to strong or showpiece,
choose a 3-5 command impeccable chain, inventory rich components like charts,
dense modals, navigation, and purposeful motion, pick one concrete art direction
from the contract's tokens, run a micro-polish pass for radius, alignment,
typography, hit targets, and transitions, confirm every interactive surface
ships all its states (empty/loading/error/hover/focus/disabled/success), confirm
keyboard / low-vision / desktop-tablet-phone users can complete the core action,
implement against the tokens, verify with desktop and mobile screenshots,
critique the result, and revise once. Do not run all impeccable commands, and do
not invent off-contract values.
```
