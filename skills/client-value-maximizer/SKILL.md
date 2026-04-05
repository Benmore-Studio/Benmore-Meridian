---
name: client-value-maximizer
description: >
  Maximize delivered value for any client project through a structured audit-to-implementation pipeline.
  Deploys parallel exploration agents to audit a codebase across multiple dimensions (frontend UX, backend API,
  SEO, accessibility, conversion, performance, emails/notifications), synthesizes findings into prioritized
  quick wins with effort estimates, writes a requirements doc, implements wins in parallel batches using
  file-ownership-based agent groups, verifies the build, updates QA docs, and generates a delivery checklist.
  Use when the user says "maximize value", "quick wins", "audit the codebase", "client value pass",
  "find improvements", "low-hanging fruit", "value maximizer", "what can we improve", or wants to
  systematically find and implement high-impact, low-effort improvements across an entire codebase.
  Works with any stack — not tied to a specific framework or project.
---

# Client Value Maximizer

Systematic pipeline: audit a codebase across multiple dimensions in parallel, prioritize findings by impact and effort, then implement quick wins in parallel batches with zero file conflicts.

## Pipeline Overview

1. **Discover** — Parallel agents audit the codebase across 7 dimensions
2. **Synthesize** — Merge findings into a single prioritized quick wins report
3. **Scope** — Write a requirements doc for the selected batch
4. **Implement** — Parallel agents execute grouped by file ownership
5. **Verify** — Build check, lint, test suite
6. **Document** — Update QA docs with new test cases
7. **Deliver** — Generate a delivery checklist

## Step 1: Discover (Parallel Audit)

Read [references/audit-dimensions.md](references/audit-dimensions.md) for the full audit checklist per dimension.

Deploy one subagent per dimension. Default dimensions:

1. Frontend UX
2. Backend API
3. SEO & Metadata
4. Accessibility
5. Conversion & Growth
6. Performance
7. Emails & Notifications

Add or remove dimensions based on the project. For a frontend-only project, drop Backend API. For a project with no email system, drop Emails & Notifications.

### Agent dispatch prompt template

Each agent receives:

```
You are auditing this codebase for [DIMENSION NAME] improvements.

Focus on quick wins — high-impact changes that require minimal effort.

For each finding, output exactly:
FILE: <absolute path>
ISSUE: <one-line description>
SEVERITY: critical | high | medium | low
EFFORT: trivial (<30min) | small (1-2h) | medium (half day) | large (1+ day)
FIX: <concrete fix description>
---

Read references/audit-dimensions.md section "[DIMENSION]" for the full checklist.

Search the codebase systematically. Start with the most impactful areas.
Do NOT implement anything. Report findings only.
```

### Scoping the audit

Before dispatching agents, identify what is in scope:
- Ask the user which directories/modules to audit (or default to the entire repo)
- Ask if any dimensions should be skipped or added
- Ask if there is a maximum effort threshold (e.g., "only trivial and small items")

## Step 2: Synthesize

After all agents report back, merge their findings into a single **Quick Wins Report**.

Read [references/templates.md](references/templates.md) for the report format.

Synthesis rules:
1. **Deduplicate** — Same file + same issue from different dimensions = one entry, note both dimensions
2. **Prioritize** — Sort by: severity (critical > high > medium > low), then effort (trivial > small > medium > large)
3. **Tag dependencies** — If fixing item A requires item B first, note the dependency
4. **Count** — Provide totals by severity and effort level
5. **Estimate** — Sum effort ranges for each priority tier

Present the report to the user. Ask which priority tiers to implement (default: P0 + P1).

## Step 3: Scope (Requirements Doc)

Write a requirements document for the approved items. Read [references/templates.md](references/templates.md) for the format.

Critical: group items into **implementation groups by file ownership**. Two agents must never touch the same file. If two items require the same file, they go in the same group.

Algorithm:
1. Collect all files touched by approved items
2. Build a conflict graph — items share an edge if they touch the same file
3. Connected components in the conflict graph = implementation groups
4. Assign each group to one agent

If a single group becomes too large (>10 items), split into sequential sub-batches within that group.

Present the requirements doc to the user for approval before implementing.

## Step 4: Implement (Parallel Batches)

Dispatch one subagent per implementation group. Each agent receives:

```
You are implementing the following items from the requirements doc:
[PASTE GROUP ITEMS WITH ACCEPTANCE CRITERIA]

Files you own (ONLY touch these files):
[LIST OF FILES]

Rules:
- Implement each item completely, meeting all acceptance criteria
- Do NOT touch files outside your ownership list
- Do NOT create new files unless an item explicitly requires it
- Run the linter on each file after editing
- Report back: item number, status (done/blocked), and what changed
```

After all agents complete, review their reports for any blocked items.

## Step 5: Verify

Run in sequence:
1. **Build** — Run the project's build command (`npm run build`, `python manage.py check`, etc.)
2. **Lint** — Run the project's linter (`npm run lint`, `ruff check`, etc.)
3. **Tests** — Run the existing test suite and confirm no regressions
4. **Type check** — If applicable (`npx tsc --noEmit`, `mypy`, etc.)

If any step fails:
- Identify which implementation group caused the failure
- Fix the issue (or dispatch the owning agent to fix it)
- Re-run verification from the failing step

## Step 6: Document (QA Update)

Read [references/templates.md](references/templates.md) for the QA update format.

For each implemented item, add test cases to the project's QA document:
- Find the existing QA doc (search for `qa`, `test-plan`, `test-cases` in the repo)
- If no QA doc exists, ask the user where to create one
- Add a new section with the date and "Value Maximizer Updates" heading
- Include both new test cases and regression checks

## Step 7: Deliver (Checklist)

Generate a delivery checklist using the template in [references/templates.md](references/templates.md).

The checklist must include:
- Every change with file path and description
- Build/lint/test verification results
- QA document update confirmation
- Deferred items with reasons
- Notes for the client

Present the checklist to the user as the final deliverable.

## Adapting to Any Project

This skill is stack-agnostic. Adapt these elements per project:

| Element | Detect from | Fallback |
|---------|------------|----------|
| Build command | `package.json` scripts, `Makefile`, `pyproject.toml` | Ask user |
| Lint command | `package.json`, `.eslintrc`, `ruff.toml`, `setup.cfg` | Ask user |
| Test command | `package.json` test script, `pytest.ini`, `Makefile` | Ask user |
| QA doc location | Search repo for `qa`, `test-plan`, `test-cases` | Ask user |
| Stack type | `package.json` (JS), `requirements.txt`/`pyproject.toml` (Python), `Gemfile` (Ruby) | Ask user |

## Quick Start Example

User says: "Run the value maximizer on this project, focus on quick wins only"

1. Scan repo to detect stack and tooling
2. Ask: "I see a Next.js frontend and Django backend. Should I audit both? Any dimensions to skip?"
3. Dispatch 7 parallel agents (one per dimension)
4. Merge findings into Quick Wins Report (typically 20-60 items)
5. Present report: "Found 34 items: 3 critical, 8 high, 15 medium, 8 low. The 11 critical+high items total ~6-10 hours of effort. Implement P0+P1?"
6. User approves
7. Group 11 items into 3-4 file-ownership groups
8. Present requirements doc for approval
9. Dispatch 3-4 parallel agents
10. Verify build/lint/tests
11. Update QA doc
12. Present delivery checklist
