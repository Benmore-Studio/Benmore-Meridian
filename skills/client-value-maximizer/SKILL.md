---
name: client-value-maximizer
description: >
  Use when the user says "maximize value", "quick wins", "audit the codebase",
  "client value pass", "find improvements", "low-hanging fruit", "value maximizer",
  "what can we improve", or wants to systematically find and implement high-impact
  improvements across a codebase — especially for UI design, payments, accessibility,
  performance, and code quality. Also triggers pre-PR validation, SOLID/OOP review,
  and full test + documentation pipeline.
---

# Client Value Maximizer

Systematic pipeline: audit across 10 dimensions in parallel → prioritize by impact/effort → brainstorm additions → implement in parallel groups by file ownership → verify with LSP + Playwright → document fully → deliver.

---

## Step 0: Brainstorm + Codebase Study (REQUIRED — before any code)

### 0A. Invoke Skills
1. Invoke `using-superpowers` — loads all applicable skills for the session.
2. Invoke `superpowers:brainstorming` with this prompt:

> "Find simple additions that would add a ton of value for the client. Look for:
> - Code reusability — where is logic duplicated? What shared utilities are missing?
> - SOLID and OOP violations — what has too many responsibilities? What is tightly coupled?
> - Similar tests to prevent similar errors — what classes of bug keep recurring? Write regression anchors.
> - Features built without hallucination — only suggest features that have clear evidence in the codebase or explicit user request. Never invent requirements.
> - UI, design, payments improvements the client will feel immediately."

### 0B. Study the Entire Codebase
Before writing a single line, read and understand:
- Directory structure and module boundaries
- Existing abstractions, base classes, shared utilities — reuse them, don't duplicate
- Naming conventions, file organisation patterns, coding style
- How the changed area fits into the overall data flow (draw or describe it)
- What tests already exist — understand what's already covered before adding more

**No implementation until you can answer:** "Where does this feature fit in the existing architecture, and what existing code does it touch or reuse?"

---

## Step 1: Discover (Parallel Audit — 10 Dimensions)

Deploy one subagent per dimension. All run in parallel. Each reports findings only — no implementation.

### Dimensions

| # | Dimension | Focus |
|---|-----------|-------|
| 1 | **Frontend UX** | Navigation clarity, empty states, loading skeletons, error boundaries, form UX |
| 2 | **UI Design & Visual Quality** | Design system consistency, spacing, typography, color contrast, dark mode, animations, micro-interactions, component hierarchy, visual polish |
| 3 | **Payments & Checkout** | Payment flow UX, trust signals, error recovery, retry logic, pricing clarity, PCI surface, webhook handling, failed-charge UX |
| 4 | **Backend API** | N+1 queries, missing pagination, error shapes, auth gaps, rate limiting, input validation |
| 5 | **SEO & Metadata** | Title/description, OG tags, structured data, canonical URLs, sitemap, robots.txt |
| 6 | **Accessibility (a11y)** | WCAG 2.1 AA, keyboard nav, ARIA labels, focus management, color contrast, screen reader support |
| 7 | **Conversion & Growth** | CTA clarity, onboarding friction, upsell opportunities, pricing page, social proof, abandonment recovery |
| 8 | **Performance** | Bundle size, LCP/CLS/FID, image optimization, lazy loading, caching headers, DB query cost |
| 9 | **Code Quality — SOLID/OOP** | SRP violations, tight coupling, missing abstractions, duplicated logic, missing interfaces, fragile inheritance, poor encapsulation |
| 10 | **Emails & Notifications** | Transactional email copy, delivery reliability, unsubscribe flow, notification preferences |

### Agent Dispatch Prompt Template

```
You are auditing this codebase for [DIMENSION NAME] improvements.
Focus on quick wins — high-impact changes that require minimal effort.

For each finding output exactly:
FILE: <absolute path>
ISSUE: <one-line description>
SEVERITY: critical | high | medium | low
EFFORT: trivial (<30min) | small (1-2h) | medium (half day) | large (1+ day)
FIX: <concrete fix description>
SOLID_VIOLATION: (if Code Quality dimension) SRP | OCP | LSP | ISP | DIP | none
---

Report findings only. Do NOT implement anything.
```

---

## Step 2: LSP Code Intelligence Pass

Before synthesis, run an **LSP diagnostic pass** across all files flagged in Step 1.

Use the `LSP` tool on each flagged file to:

- **Diagnostics** — surface type errors, unused imports, undefined references
- **Hover** — verify types match documented intent
- **Find references** — identify dead code or over-coupled modules
- **Go to definition** — trace call chains for API and payment handlers

This grounds the audit in compiler-verified facts rather than pattern-matching guesses.

```
For each flagged file:
  LSP diagnostics → add to findings if errors found
  LSP hover on payment/auth functions → verify types
  LSP find-references on shared utilities → flag if duplicated elsewhere
```

Add new findings from LSP pass to the audit pool with `SEVERITY: high` if they are type errors or undefined references.

---

## Step 3: Synthesize

Merge all findings into a **Quick Wins Report**.

Rules:
1. **Deduplicate** — same file + issue from multiple dimensions = one entry, tag both dimensions
2. **Prioritize** — severity (critical > high > medium > low), then effort (trivial > small > medium > large)
3. **Tag dependencies** — note if item A must precede item B
4. **Count** — totals by severity and effort tier
5. **Estimate** — sum effort ranges per priority tier

Present to user. Default: implement P0 (critical) + P1 (high).

---

## Step 4: Scope (Requirements Doc)

Write a requirements document for approved items.

Group by **file ownership** — two agents must never touch the same file.

Algorithm:
1. Collect all files touched by approved items
2. Build conflict graph (shared edges = shared files)
3. Connected components = implementation groups
4. Assign one agent per group
5. If group > 10 items, split into sequential sub-batches

### For each item include:
- File path(s)
- Issue description
- Acceptance criteria (testable)
- SOLID principle to apply (if code quality)
- Reuse opportunities (flag if pattern exists elsewhere in codebase)

Present requirements doc for approval before implementing.

---

## Step 5: Implement (Parallel Batches)

### A. UI / Design Additions (prioritize these for maximum client impact)

For every UI component touched, the implementing agent MUST:

- Apply design system tokens (colors, spacing, radius) — no magic numbers
- Add hover, focus, and active states
- Add loading skeletons for async content
- Add empty states with actionable CTAs
- Ensure dark mode compatibility
- Add micro-interactions (transition durations 150–300ms)
- Use semantic HTML (`<button>`, `<nav>`, `<main>`, `<section>`)
- Ensure text contrast ratio ≥ 4.5:1 (WCAG AA)
- Make all interactive elements keyboard-accessible

### B. Payments Additions

For every payment flow touched, the implementing agent MUST:

- Show trust signals (SSL badge, card logos, "secured by" text) at checkout
- Add clear pricing breakdown before confirmation
- Handle card decline with specific, actionable error messages (not generic "payment failed")
- Implement retry UI with exponential backoff guidance
- Mask card numbers in UI and logs (PCI surface reduction)
- Add loading + success + error states to every payment action
- Test failed webhook delivery recovery path
- Verify idempotency keys on charge retries

### C. Code Quality — SOLID/OOP Additions

For every refactored module:

- **SRP**: Each class/function does one thing. Extract if it does two.
- **OCP**: Extend via composition, not modification. Add interfaces/abstractions.
- **LSP**: Subtypes must fulfill parent contracts. Remove covariant violations.
- **ISP**: Split fat interfaces. No "do nothing" implementations.
- **DIP**: Depend on abstractions. Inject dependencies, don't instantiate them.
- Extract duplicated logic into shared utilities. Document the utility's purpose.
- Add JSDoc / type annotations on all public APIs.

### D. Agent Dispatch Prompt (per group)

```
Implement the following items. Files you own (ONLY touch these):
[LIST FILES]

Rules:
- Meet all acceptance criteria
- Apply UI/design checklist if touching components
- Apply payments checklist if touching checkout/billing
- Apply SOLID principles if refactoring logic
- Run linter on each file after editing
- Report: item number, status (done/blocked), what changed
```

---

## Step 6: Test Suite (REQUIRED before any merge)

### A. Unit Tests

For every new function or class:
- Write unit tests covering happy path, edge cases, and error states
- Follow the same SOLID principles in test code (no mega-test files)
- Group tests by the concern they protect, not the file they're in

### B. Integration Tests

For every API endpoint or service boundary touched:
- Test the full request/response cycle
- Test auth failure, validation failure, and upstream error paths
- Mirror the same scenarios that caused prior bugs (regression anchors)

### C. End-to-End Tests with Playwright CLI

**REQUIRED:** Use `playwright-cli` skill for all UI and payment flows.

```bash
# Open the app
playwright-cli open http://localhost:3000

# Verify the golden path for each changed UI feature
playwright-cli snapshot          # baseline
playwright-cli click e5          # interact
playwright-cli snapshot          # verify result

# Payment flow E2E
playwright-cli goto /checkout
playwright-cli fill e8 "4242424242424242"   # test card
playwright-cli fill e9 "12/26"
playwright-cli fill e10 "123"
playwright-cli click e15         # submit
playwright-cli snapshot          # verify success state

# Error state E2E
playwright-cli goto /checkout
playwright-cli fill e8 "4000000000000002"   # decline card
playwright-cli click e15
playwright-cli snapshot          # verify error message is specific and helpful

# Accessibility snapshot
playwright-cli eval "document.querySelectorAll('[aria-label]').length"
playwright-cli screenshot --filename=a11y-check.png
```

For each feature changed, write a named Playwright test that:
- Covers the happy path
- Covers the primary failure mode
- Asserts on visible UI state (not just network responses)

---

## Step 7: Pre-PR Checklist (REQUIRED — do not skip)

Answer every question below. If any answer is "no", fix it before opening the PR.

---

### 7A. Did you use the right skills?
- [ ] Invoked `using-superpowers` at session start
- [ ] Invoked `superpowers:brainstorming` before writing code
- [ ] Studied the entire codebase and understand how this change fits in

---

### 7B. Have you made tests — unit, integration, and end-to-end?
- [ ] **Unit tests** — every new function/class has tests for happy path, edge cases, and error states
- [ ] **Integration tests** — every new API route or service boundary tested end-to-end (auth failure, validation failure, upstream errors)
- [ ] **E2E tests** — every changed UI flow covered with `playwright-cli` (happy path + primary failure mode)
- [ ] **Regression anchors** — tests written specifically for any bug class that recurred; named after what they prevent
- [ ] Full existing test suite passes — no regressions introduced

---

### 7C. Did you make the features list?

For every feature added or changed, document:

```
Feature: <name>
Files/folders: <list every file that implements this feature>
Objectives: <what problem does this solve?>
Nice-to-haves (deferred): <what was intentionally left out and why>

ASCII flow:
[Entry point]
      |
      v
[Step A] --fail--> [Error state]
      |
      v
[Step B]
      |
   success        fail
      |              |
      v              v
[Happy end]    [Recovery path]
```

---

### 7D. Did you document your changes to prevent future issues?
- [ ] Code comments added ONLY where the WHY is non-obvious (not what — the code says that)
- [ ] Any non-obvious design decision captured in `CLAUDE.md` under the relevant section
- [ ] Any tricky invariant, hidden constraint, or workaround has a comment explaining it
- [ ] No orphaned TODOs left in code — either fix it or file it

---

### 7E. Update docs — changelog, CLAUDE.md, README, tags + versions
- [ ] `CHANGELOG.md` — new entry with version, date, and bullet list of changes
- [ ] `CLAUDE.md` — updated if architecture, decisions, or data shapes changed
- [ ] `README.md` — updated if public API, setup steps, or env vars changed
- [ ] Version tag bumped: `vMAJOR.MINOR.PATCH`
  - patch → bug fix
  - minor → new feature, backwards-compatible
  - major → breaking change

---

### 7F. API docs
- [ ] Every new or changed endpoint documented: method, path, request shape, response shape, error codes
- [ ] Auth requirements stated
- [ ] Rate limits / caching behaviour noted if relevant
- [ ] Deprecations flagged with migration path

---

### 7G. Code quality — SOLID, OOP, reusability
- [ ] All LSP diagnostics clear — no type errors, no undefined references
- [ ] Linter passes with zero warnings
- [ ] **SRP** — each class/function has one reason to change
- [ ] **OCP** — extended via composition, not modification
- [ ] **LSP** — subtypes honour parent contracts
- [ ] **ISP** — no fat interfaces with "do nothing" methods
- [ ] **DIP** — dependencies injected, not instantiated inside classes
- [ ] Duplicated logic extracted into shared utilities — no copy-paste
- [ ] No magic numbers — named constants or design tokens used throughout
- [ ] New code matches existing naming conventions, file structure, abstraction level
- [ ] No new dependencies without justification

---

## Step 8: Verify Build

Run in sequence:
1. **Type check** — `tsc --noEmit` / `mypy` / equivalent
2. **Lint** — `eslint` / `ruff` / equivalent
3. **Unit + integration tests** — full suite
4. **E2E** — `playwright-cli` flows from Step 6
5. **Build** — `npm run build` / equivalent

If any step fails: identify the owning group, fix, re-run from the failing step.

---

## Step 9: Document

For each implemented item, add to the project's QA doc:
- New test cases (what to test, expected result)
- Regression checks (what broke before, how to verify it doesn't again)

Add a `## [YYYY-MM-DD] Value Maximizer Updates` section.

---

## Step 10: Deliver

Generate a delivery checklist:

```
## Delivery Summary

### Changes
- [ ] <file path> — <1-line description>
...

### Verification
- [ ] LSP diagnostics: clean
- [ ] Lint: pass
- [ ] Tests: all pass (N unit, N integration, N E2E)
- [ ] Build: success

### Documentation
- [ ] CHANGELOG updated
- [ ] README updated
- [ ] CLAUDE.md updated
- [ ] API docs updated
- [ ] Version bumped to vX.Y.Z

### Deferred Items
- <item> — <reason for deferral>

### Notes for Client
- <any caveats, known limitations, or follow-up recommendations>
```

---

## Quick Reference — Audit Dimension Checklist

| Dimension | Top 3 Quick Wins |
|-----------|-----------------|
| UI Design | Design token consistency · Loading skeletons · Empty states with CTAs |
| Payments | Specific decline messages · Trust signals at checkout · Retry UX |
| a11y | ARIA labels on icons · Focus rings · Keyboard nav for modals |
| Performance | Image lazy-load · Bundle split · Cache headers |
| Code Quality | Extract duplicated logic · Add interfaces · Inject dependencies |
| SEO | OG tags · Canonical URLs · Page title uniqueness |
| Backend API | Input validation · Consistent error shapes · Auth on all routes |
| Conversion | CTA above fold · Social proof near pricing · Reduce form fields |

---

## Stack Adaptation

| Element | Detect from | Fallback |
|---------|-------------|----------|
| Build command | `package.json` scripts, `Makefile` | Ask user |
| Lint command | `.eslintrc`, `ruff.toml` | Ask user |
| Test command | `package.json` test script, `pytest.ini` | Ask user |
| E2E | `playwright.config.*`, `tests/` | Use `playwright-cli` directly |
| QA doc | Search for `qa`, `test-plan`, `test-cases` | Ask user |
