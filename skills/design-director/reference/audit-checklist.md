# Design Director — Diagnostic Checklist (the volume engine)

This is the forcing function. Reading it is what makes the survey **exhaustive**
instead of a handful of taste calls. Walk it against **every surface** you
enumerated, and within each surface walk **every category below**. Do not skip a
category because the screen "looks fine" — look for the specific check, then log
what you find.

## How to walk it

For **each surface × each category**, log every instance you find as one row:

```
surface · category · vocabulary term · symptom (plain English) · severity · fix command
```

Rules that produce volume (this is the point):

- **Log every instance, including small ones.** A weak focal point, a 13px label
  that should be 14, a missing hover state, an off-token gray — each is its own
  row. Hundreds of small true findings is the goal, not a tidy top-10.
- **Do not dedupe repeated drift away.** If the same wrong gray appears on 12
  screens, log it once with `×12 across pages` in the symptom — that is a
  systemic P1, not twelve P3s, but it still gets counted.
- **Use the canonical `vocabulary` term** for the symptom (pull it from
  `vocabulary.md` — do not coin jargon). The term sharpens the diagnosis; the
  plain-English half explains it to the user.
- **Every finding maps to one `impeccable` fix command** (the right column).
  That is what makes the backlog executable in Stage 2.
- **Opportunities are findings too.** A missing modal, an absent chart, a
  card-grid that should be a data table — log these in the Opportunity Inventory,
  not the issue register. The user explicitly wants these surfaced unprompted.

### Severity (mirror impeccable's P0–P3)

- **P0 Blocking** — prevents the core task or fails WCAG A (no keyboard path,
  trap, unreadable contrast, broken responsive that hides the primary action).
- **P1 Major** — significant friction or WCAG AA violation, or systemic drift
  (off-token color across many pages). Fix before release.
- **P2 Minor** — annoyance with a workaround (weak hierarchy, loose spacing,
  missing hover). Fix in the pass.
- **P3 Polish** — no real user impact (a 1px nudge, a slightly-off radius).

---

## 1. Hierarchy & layout → `layout`

- [ ] **Focal point** — does each screen have ONE clear `hierarchy` winner, or
  does everything compete at the same weight? (no winner = P1)
- [ ] **Scan pattern** — does the eye follow a deliberate Z or F path, or bounce?
- [ ] **`negative space`** — is there breathing room, or is it crowded? Crowding
  removes clarity, it does not add information.
- [ ] **Dead whitespace** — large empty regions that read as a bug, not rhythm.
- [ ] **Spacing scale** — are gaps from a consistent scale (4/8/12/16/24/32…) or
  ad-hoc? Off-scale values are drift → also log under category 12.
- [ ] **`gap` vs margin** — trailing space after the last item, uneven gutters.
- [ ] **Alignment / `grid`** — elements off the column grid, ragged edges,
  optically misaligned icons next to text.
- [ ] **`border radius` nesting** — inner radius should be outer minus padding;
  matching both leaves a visible gap (concentric radii).
- [ ] **`layout shift`** — content jumping as images/fonts load (reserve space,
  set `aspect ratio`).
- [ ] **`overflow` / `z-index`** — clipped content, modals/tooltips behind things
  they should sit above, `overflow:hidden` silently breaking `sticky positioning`.
- [ ] **`asymmetry`** — is the layout interesting, or a safe symmetric stack of
  identical cards? (identical card grid = a richness opportunity → category 5)

## 2. Typography → `typeset`

- [ ] **`type scale`** — sizes pulled from a defined scale, or arbitrary px?
- [ ] **`leading`** — lines suffocating (too tight) or not reading as a paragraph
  (too loose)?
- [ ] **`tracking`** — uppercase labels/`eyebrows` need more; body rarely does.
- [ ] **`line length`** — body text wider than ~65ch is hard to read; cap with
  `max-width`.
- [ ] **`tabular nums`** — any prices, stats, counters, timers, or table numbers
  NOT using tabular figures = misalignment as they change. (P1 in data UIs)
- [ ] **`weight`** — is hierarchy carried by weight, or is everything one weight?
  Italic used for UI hierarchy (wrong) instead of emphasis/citation.
- [ ] **Balanced headings / `widow` / `orphan`** — single stranded words on
  multi-line headings (`text-wrap: balance`).
- [ ] **`text overflow`** — long strings with no truncation, or three periods
  instead of a real ellipsis, or cutting mid-word.
- [ ] **`font stack` / `font smoothing`** — missing fallback causing reflow;
  inconsistent smoothing across the app.

## 3. Color & consistency → `colorize` (and contract-extend)

- [ ] **Off-token color (drift!)** — any raw hex / one-off gray not from a
  `semantic token`. Pure `#808080` looks like a placeholder; a `tinted neutral`
  feels chosen. Every off-token color is a finding → systemic ones are P1.
- [ ] **`contrast ratio`** — body text < 4.5:1, large/UI < 3:1 = P0/P1.
- [ ] **`chroma` / `saturation`** — flat, lifeless tints (reduced via opacity
  instead of chroma), or full-saturation brand colors vibrating in dark mode.
- [ ] **`color-only state`** — error shown only by a red border, status only by
  color = invisible to colorblind users. Always pair with icon or text. (P1)
- [ ] **`dark mode`** — missing dark variants, brightest surface not at top of
  the layering hierarchy, light tokens used directly in dark.
- [ ] **Easy-on-the-eyes check** — is the palette restrained and harmonious, or
  are there too many competing hues? Too-vivid backgrounds behind body text.

## 4. Information architecture → `layout` / `shape`

- [ ] **`mental model`** — does the structure match how users think, or internal
  org/DB terminology?
- [ ] **`progressive disclosure`** — everything dumped on one page vs revealed as
  the user goes deeper? Dense screens with no drill-down.
- [ ] **`navigation` / `wayfinding`** — is nav discoverable, or buried inside
  cards? Can the user tell where they are? Missing `breadcrumb` at depth.
- [ ] **Labelling** — labels match user language, `front-loaded`, scannable.
- [ ] **Depth** — too many clicks to the core action; flatten or add a
  `command menu`.

## 5. Components & richness — the "small additions" → Opportunity Inventory

For each surface, ask: **is the strongest component being used, or a lazy
default?** Every repetitive `card` grid, every wall of text, every "we'll just
list it" is an opportunity. Explicitly consider proposing each of these where it
answers a real user question:

- [ ] **`Modal / Dialog`** — needs focus trap + inert background — for focused
  tasks / confirmations.
- [ ] **`Sheet` / `Drawer`** — side/bottom panel for contextual detail without
  leaving the page.
- [ ] **`Popover`** (interactive) vs **`Tooltip`** (non-interactive) — pick the
  right one; flag tooltips holding links.
- [ ] **`Data table`** — right-aligned `tabular nums`, sortable, sticky header —
  instead of a card grid of records.
- [ ] **`Command menu`** — keyboard-driven nav/actions for power users.
- [ ] **Inspector `Drawer` / `comparison rail` / `status matrix` / `timeline` /
  `kanban` / `calendar` / `map`** — when the data has structure a card can't show.
- [ ] **`Accordion` / `Tabs` / `Stepper`** — used correctly (tabs for same-content
  filtering, accordion for secondary content, stepper to set expectations)?
- [ ] **`Badge` vs `Tag`** — attached/informational vs standalone/selectable —
  used correctly?
- [ ] **`Avatar` fallback, `Separator` overuse, `Carousel` on desktop** (often a
  sign the layout wasn't solved).

Each proposed addition must name the **user question it answers**. No decorative
components.

## 6. Data flows & visualization → Opportunity Inventory + `craft`

- [ ] **Un-visualized data** — any quantitative, relational, time-based, status,
  funnel, financial, or workload data shown as raw text/cards with NO chart is a
  finding. Propose the chart that answers the user's question (trend → line,
  distribution → bar/histogram, mix → stacked/donut, relationship → scatter,
  progress → `progress`).
- [ ] **Drill-down without context loss** — can the user inspect a detail without
  losing where they were? (→ inspector `drawer` / `modal`).
- [ ] **Sticky context** — headers/labels that stay visible while scrolling dense
  data.
- [ ] **`funnel` / `conversion` surfaces** — is drop-off visible and actionable?
- [ ] **No fake data** — visualizations use real or clearly local/demo data; do
  not invent business metrics.

## 7. States — none are optional → `harden` / `onboard`

For **every interactive surface**, each missing state is its own finding:

- [ ] **`Empty state`** — first-run view that explains why it's empty + a real
  next action. "No items found" alone = P1.
- [ ] **Loading** — `skeleton` matching final layout, not a `spinner` over blank
  space; `skeleton shimmer` respects reduced motion.
- [ ] **`Error state`** — says what failed + how to recover, not "Invalid input".
- [ ] **Populated & dense/overflow** — does it survive long text and many rows?
- [ ] **Control states** — `Button`/`Input` each need distinct default, `hover
  state`, `focus state`, `active state`, `disabled state`, and loading/selected
  where relevant. Log each missing one.
- [ ] **Async** — in-flight (busy + disabled to prevent double-submit), success
  feedback, failure with retry.
- [ ] **Forms** — label above (not just `placeholder`), `inline error` next to the
  field, sensible input types/defaults, submitting state, explicit success/
  failure, never lose entered data on error; long forms split into a `stepper`.

## 8. Interaction & affordance → `craft` / `polish`

- [ ] **`Affordance`** — does it look pressable/clickable, or must users guess?
- [ ] **`Touch target`** — interactive area ≥ 44×44px (visual can be smaller).
- [ ] **`Cursor`** — pointer on clickable, not default; text on selectable.
- [ ] **Press feedback** — `active:scale-[0.96]`-style tactile response; no
  overlapping/colliding hit areas.
- [ ] **`Copy to clipboard`** and similar need visible confirmation.
- [ ] **`Debounce`** on search/typeahead inputs.
- [ ] **`Optimistic update`** opportunities with rollback on failure.

## 9. Motion → `animate`

- [ ] **Purpose** — does motion explain state/sequence/hierarchy, or is it
  decoration? Generic fade-ins everywhere = a tell.
- [ ] **`Easing`** — `ease-out` for entering, `ease-in` for leaving; not the
  reverse; no bounce on UI.
- [ ] **`Duration`** — ~150ms for hovers, ≤ ~400ms for transitions; longer with
  no feedback reads as broken.
- [ ] **`Transition property`** — animate `opacity`/`transform`, never
  `transition: all` (catches layout props → jank).
- [ ] **`Stagger`** — list reveals ~40ms apart, not all-at-once flash.
- [ ] **`Reduced motion`** — honored; significant movement gated behind the query.
- [ ] **No content hidden behind animation**, no entrance animation replaying on
  every load.

## 10. Accessibility → `audit` / `adapt` / `harden`

- [ ] **`Contrast ratio`** — 4.5:1 body / 3:1 large/UI (`WCAG`/`APCA`).
- [ ] **Keyboard path** — every interactive element reachable and operable by
  `tab order`; logical order matching `DOM order`; `Esc`/back escapes overlays.
- [ ] **`Focus state`** — always visible; never just removed.
- [ ] **`Focus trap`** — correct inside modals; background inert to `screen
  reader`.
- [ ] **`Semantic HTML`** — real `button`/`nav`/headings, not styled `div`s;
  proper heading hierarchy.
- [ ] **`aria-label`** on icon-only controls (describe the action, not the icon).
- [ ] **`Label association`** — `for`/`id` so clicking the label focuses the field.
- [ ] **`Skip link`** before long navigation.
- [ ] **Three widths** — walk desktop / tablet / phone: no overflow, no
  `layout shift` hiding the primary action, survives 200% zoom.

## 11. Copy → `clarify`

- [ ] **`Microcopy`** — labels, empties, errors read as trustworthy and human.
- [ ] **`CTA`** — owns the action ("Save changes" > "Submit"), one primary action
  per view.
- [ ] **`Error message`** — names what went wrong AND how to fix it.
- [ ] **`Front-loading`** — most important word first; users scan.
- [ ] **`Placeholder`** not used as a label; **`sentence case`** for UI labels;
  destructive language paired with safe defaults in `confirmation dialog`s.

## 12. Consistency / drift (cross-surface) → contract-extend + `distill` / `extract`

This category is walked **across surfaces**, comparing them:

- [ ] **One concept, N renderings** — the same thing (a status pill, a card, a
  button) drawn differently on different screens. Log each divergence.
- [ ] **Off-contract values** — radii, shadows, spacing, colors not in the
  `DESIGN.md`/token set. These are drift bugs, not taste calls → extend the
  contract, then reuse the token.
- [ ] **Button hierarchy** — more than one primary `button` competing in a view;
  inconsistent primary/secondary treatment across pages.
- [ ] **`Icon library`** mixing — two icon sets with mismatched weight/size/radius.
- [ ] **Component reuse** — repeated one-off implementations that should be a
  single shared component (`distill` / `extract`).

---

## Coverage self-check (before writing the backlog)

You are not done surveying until you can answer YES to all:

- Did I walk **all 12 categories** on **every** enumerated surface?
- Did I log **state gaps per surface** (empty/loading/error + control states)?
- Did I produce at least a handful of **addition opportunities** (modals,
  charts, richer components) the user did NOT ask for?
- Did I capture **cross-surface drift** by comparing screens, not just judging
  each alone?
- Is the issue count plausibly in the **dozens-to-hundreds** for a real
  multi-screen app? A short list means I judged by taste instead of walking the
  checklist — go back.
