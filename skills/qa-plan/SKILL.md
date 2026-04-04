---
name: qa-plan
description: Generate a detailed QA test plan from code changes. Reads git diffs, discovers project docs, traces blast radius across modules, risk-scores each area, and outputs a comprehensive markdown test plan with prioritized test cases, smoke checklist, and exit criteria. Use when fixing bugs, shipping features, preparing releases, or anytime you need to know what to test.
context: fork
---

# QA Plan Generator

Generate comprehensive, code-traced QA test plans from code changes. Analyzes diffs, discovers project context, traces blast radius, and produces an actionable test plan.

## When to Use
- After fixing a bug — generate targeted QA for what changed
- After implementing a feature — generate tests + regression checks
- Before a release — comprehensive QA covering all changes since last release
- On-demand — "QA the health module" or "test plan for this PR"
- Anytime you're unsure what to test

## Input Modes

The skill accepts flexible input and auto-detects what you gave it:

| Input | Detection | Example |
|-------|-----------|---------|
| No args | Reads unstaged + staged git diff | `/qa-plan` |
| Branch name | Arg matches a git branch | `/qa-plan fix/custom-drugs` |
| Module/directory | Arg matches a project directory | `/qa-plan health` |
| PR number | Starts with `#` or is numeric | `/qa-plan #419` |
| Freeform | Anything else — matched against files/modules | `/qa-plan "the offline sync changes"` |

## Pipeline

Execute these 6 steps in order. Steps 2 and 3 use parallel subagents for speed.

---

### Step 1: Gather Changes

Based on the input mode, collect the raw change data.

**For git diff (default — no args):**
```bash
# Staged + unstaged changes
git diff HEAD

# If no diff, try committed changes on current branch vs main
git diff main...HEAD
```

**For branch comparison:**
```bash
git diff main...<branch-name>
```

**For PR number:**
```bash
gh pr diff <number>
```

**For module name:**
```bash
# All recent changes in that module
git log --oneline -20 --all -- '<module>/**'
git diff main...HEAD -- '<module>/**'
```

**For freeform input:**
- Search for files/directories matching the description
- Fall back to full project diff if no match

From the diff, extract and record:

```
CHANGE INVENTORY
================
Files changed:        [list of file paths]
Functions modified:   [function/method names + file locations]
Model fields changed: [new, removed, or type-changed fields]
Imports added/removed:[new cross-module coupling]
API shape changes:    [new/removed/renamed response fields]
Validation changes:   [new error codes, changed validators]
Query filter changes: [modified .filter() / .exclude() / WHERE clauses]
Signal changes:       [new/modified signal handlers]
```

Also extract the **root cause / motivation** from:
1. Commit messages in the diff
2. PR description (if PR input)
3. Ask the user if unclear

---

### Step 2: Discover Project Context

Launch **parallel Explore subagents** to discover the project landscape. This step makes the skill project-agnostic — it learns whatever codebase it's in.

**Agent A — Documentation Discovery:**
```
Find and read:
- Root CLAUDE.md (project-level docs)
- Module-level CLAUDE.md or README files for changed modules
- Any architecture docs, flow diagrams, or dependency maps
- CHANGELOG.md (recent bug history — informs risk scoring)

Extract:
- Framework identity (Django, FastAPI, Express, Rails, etc.)
- Mobile stack (React Native, Flutter, Swift, etc.)
- Database (PostgreSQL, SQLite, etc.)
- Key architectural patterns (multi-tenancy, FIFO, event sourcing, etc.)
- Known hot spots / historically buggy areas
```

**Agent B — Code Structure Discovery:**
```
Find and catalog:
- Test file locations and naming patterns
- Signal/event handler registrations for changed models
- Middleware stack (if web framework)
- URL/route configuration for changed endpoints
- Service layer files that wrap the changed models
- Cross-module import graph for changed files
```

Combine Agent A + B outputs into a **Project Context Record**:

```
PROJECT CONTEXT
===============
Framework:        [e.g., Django 5.2 + DRF]
Mobile:           [e.g., React Native + Expo]
Database:         [e.g., PostgreSQL]
Key patterns:     [e.g., multi-tenant via middleware, FIFO inventory, RBAC]
Test location:    [e.g., <module>/tests/]
Signal map:       [model → signals that fire]
Middleware:       [ordered list]
Hot spots:        [areas with recent bug history]
```

---

### Step 3: Blast Radius Analysis (2-Hop)

Launch **parallel Explore subagents** — one per changed file — to trace dependencies outward.

**Hop 1 — Direct Dependencies:**

For each changed file, find:
- **Callers**: What imports or calls the changed functions? (grep for the function name across the project)
- **Callees**: What does the changed code call? (read the changed functions, note outbound calls)
- **Signal consumers**: If a model was changed, what signal handlers fire on its save/delete?
- **Serializers/Views**: Which serializers expose the changed model fields? Which views use them?
- **Mobile consumers**: Which mobile service files call the changed API endpoints?
- **Test files**: Which existing tests cover the changed code?

**Hop 2 — Indirect Dependencies:**

For each Hop 1 result, find:
- What calls the Hop 1 callers? (e.g., if a service changed, what views call that service? what tasks?)
- What downstream calculations consume the Hop 1 outputs? (e.g., reports that read from the changed model)
- What mobile screens call the Hop 1 mobile services?

**Output format:**

```
BLAST RADIUS
============
[Changed] health/serializers.py:TreatmentEventSerializer.validate()
  ├─ [Hop 1] health/views.py:TreatmentEventViewSet.bulk_create()
  │    ├─ [Hop 2] mobile/src/services/healthService.js:createBulkTreatment()
  │    └─ [Hop 2] mobile/app/(health)/add-treatment.js (UI)
  ├─ [Hop 1] health/views.py:TreatmentEventViewSet.create()
  │    └─ [Hop 2] mobile/src/services/healthService.js:createTreatmentEvent()
  ├─ [Hop 1] inventory/services.py:PharmaceuticalInventoryDeductionService (signal chain)
  │    └─ [Hop 2] reports/views.py (treatment cost in closeout)
  └─ [Hop 1] invoices/services.py:calculate_treatment_items()
       └─ [Hop 2] invoices/pdf_generator.py (invoice PDF)
```

---

### Step 4: Risk Scoring

For each area in the blast radius, compute **Risk Score = Likelihood (1-5) x Impact (1-5)**.

**Likelihood factors:**

| Factor | 1 (Low) | 3 (Medium) | 5 (High) |
|--------|---------|------------|----------|
| Lines changed | < 10 | 10-50 | 50+ |
| Complexity of change | Rename / typo fix | Logic change | New algorithm or data flow |
| Cross-module coupling | Single file | 2-3 modules | 4+ modules |
| Bug history in area | No recent bugs | 1-2 bugs in recent history | 3+ bugs (hot spot) |

**Impact factors:**

| Factor | 1 (Low) | 3 (Medium) | 5 (High) |
|--------|---------|------------|----------|
| Financial data affected | Display-only | Report calculations | Invoice / billing amounts |
| Data integrity | Read-only path | Update with validation | Write path (counts, inventory, balances) |
| User-facing severity | Cosmetic | Feature degraded | Feature broken / data loss |
| Multi-tenant exposure | Single-tenant data | Cross-tenant query | Auth / permission bypass |
| Reversibility | Easy rollback | Manual correction needed | Irreversible (inventory deducted, notifications sent) |

**Coverage depth by risk score:**

| Score | Label | Test Depth |
|-------|-------|------------|
| 20-25 | Exhaustive | Every combination, boundary values, negative tests, offline, permissions |
| 12-19 | Heavy | Happy path + error path + one edge case + permission check |
| 6-11 | Standard | Happy path + one negative test |
| 1-5 | Smoke/Skip | Smoke test only or skip entirely |

Record the risk table:

```
RISK ASSESSMENT
===============
| Area                           | Likelihood | Impact | Score | Coverage   |
|--------------------------------|-----------|--------|-------|------------|
| Custom drug selection (changed)| 5         | 5      | 25    | Exhaustive |
| Bulk treatment API (Hop 1)     | 4         | 5      | 20    | Exhaustive |
| Treatment cost in closeout     | 3         | 4      | 12    | Heavy      |
| Scheduled treatments           | 2         | 3      | 6     | Standard   |
```

---

### Step 5: Generate QA Plan

Produce a markdown document with ALL of these sections. Every section is mandatory unless marked (conditional).

#### Section 1: Header / Metadata

```markdown
# QA Test Plan — {YYYY-MM-DD}

> {One-line description of what triggered this QA plan}

| Field | Value |
|-------|-------|
| **Plan ID** | QA-{YYYY-MM-DD}-{seq} |
| **Date** | {date} |
| **Trigger** | {Bug fix / Feature / Refactor / Release} |
| **Branch/PR** | {branch name or PR #} |
| **Risk Level** | {LOW / MEDIUM / HIGH / CRITICAL} |
| **Platform** | {backend-only / mobile-only / full-stack} |
| **Changed Files** | {N} files across {M} modules |
| **Modules Affected** | {list} |
```

Overall risk level = highest individual risk score:
- Any score 20+ → CRITICAL
- Any score 12-19 → HIGH
- All scores 6-11 → MEDIUM
- All scores 1-5 → LOW

#### Section 2: Root Cause / Change Summary

What changed, why, and which files were modified. For bug fixes: describe the root cause and the fix. For features: describe the user-facing behavior.

Include the change inventory from Step 1.

#### Section 3: Scope & Out-of-Scope

Explicit boundaries:
- **In scope**: List all areas from the blast radius that will be tested
- **Out of scope**: List major modules NOT affected (so the reader knows they were considered and excluded, not forgotten)

#### Section 4: Test Cases by Feature Area

This is the core output. Group by feature area. Each group gets its own markdown section with a table.

**Table format (mandatory columns):**

| # | Test Case | Priority | Type | Steps | Expected | Caveats |
|---|-----------|----------|------|-------|----------|---------|
| {section}.{seq} | **Bold descriptive name** | P0/P1/P2/P3 | smoke/functional/regression/edge/security/offline | Numbered action steps | Specific assertions (HTTP codes, field values, state changes) | Code file:line refs, architecture constraints, setup prerequisites, known limitations |

**Priority definitions (per test case, NOT per section):**

| Priority | Definition | When to assign |
|----------|------------|----------------|
| **P0** | Critical | The specific fix/feature being tested. Failure = data loss, security breach, or crash |
| **P1** | High | Features directly integrating with changed code. Revenue-affecting flows |
| **P2** | Medium | Adjacent features sharing data models but not directly modified |
| **P3** | Low | Distant features with only theoretical coupling |

**Type taxonomy:**

| Type | When used |
|------|-----------|
| `smoke` | Quick sanity check — also included in the smoke checklist |
| `functional` | Core feature behavior being tested |
| `regression` | Not directly changed, but in the blast radius |
| `edge` | Boundary values, zero/null/negative, race conditions, concurrent access |
| `security` | Multi-tenant isolation, permission enforcement, auth bypass, timing oracles |
| `offline` | Offline queue, sync ordering, conflict resolution, temp ID mapping |

**MANDATORY: Every test case must have a non-empty Caveats column.** Read the actual source code to populate caveats with real file references, line numbers, architecture constraints, setup requirements, or known limitations. Never leave caveats empty. Never fabricate code references — verify them by reading the file.

Generate test cases using the coverage depth from Step 4:
- Exhaustive areas (20-25): 5-8 test cases covering happy path, error paths, boundary values, permissions, offline
- Heavy areas (12-19): 3-5 test cases covering happy path, error path, one edge case
- Standard areas (6-11): 1-2 test cases covering happy path and one negative case
- Smoke areas (1-5): 0-1 test cases (covered by smoke checklist instead)

#### Section 5: Regression Test Cases

Separate section for tests derived from Hop 2 blast radius. These test areas NOT directly changed but potentially affected. If the project has known historically buggy areas in the blast radius, always include regression tests for those.

Same table format as Section 4, with `Type = regression`.

#### Section 6: Edge Cases & Negative Tests

Dedicated section for boundary values, error states, and adversarial inputs:
- Zero, null, empty string, negative values
- Duplicate submissions / race conditions
- Maximum length inputs
- Invalid foreign key references
- Concurrent access to the same resource

Same table format as Section 4, with `Type = edge`.

#### Section 7: Security / Multi-Tenant Checks (CONDITIONAL)

**Only include if** the blast radius touches: authentication, authorization, permission checks, database query filters, middleware, or cross-tenant data access patterns.

Tests for:
- Data isolation between tenants/orgs/operations
- Permission enforcement (RBAC, role checks)
- Timing oracles (403 vs 404 revealing resource existence)
- CORS configuration
- Credential exposure in logs/responses
- Webhook signature verification

#### Section 8: Offline / Sync Tests (CONDITIONAL)

**Only include if** mobile service layer code is in the diff or blast radius.

Tests for:
- Offline queue behavior (enqueue, deduplication, overflow)
- Sync ordering (module priority, FIFO within priority)
- Conflict resolution (keep local, use server, decide later)
- Temp ID resolution chain across dependent entities
- Exponential backoff on failure
- Concurrent sync prevention

#### Section 9: Smoke Test Checklist

A quick-pass checkbox list drawn from P0 and P1 test cases. Maximum 15 items. Format:

```markdown
## Smoke Test Checklist

- [ ] {Action verb} — verify {specific assertion}
- [ ] {Action verb} — verify {specific assertion}
...
```

Each item should be completable in under 2 minutes. This is the "run this if you only have 15 minutes" list.

#### Section 10: Exit Criteria

What must pass before the change can ship:

```markdown
## Exit Criteria

- [ ] All P0 test cases pass
- [ ] All P1 test cases pass
- [ ] No P2 regressions introduced
- [ ] Smoke test checklist is green
- [ ] {Any project-specific criteria discovered in Step 2}
```

---

### Step 6: Save & Report

1. **Save** the QA plan to `docs/QA-PLAN-{YYYY-MM-DD}-{slug}.md`
   - `{slug}` = kebab-case summary of the change (e.g., `custom-drugs-uuid-fix`, `health-module`, `release-v1.8.0`)

2. **Print summary** to terminal:
   ```
   QA Plan saved to docs/QA-PLAN-{date}-{slug}.md

   Summary:
     Total test cases: {N}
     P0 (Critical):    {n}
     P1 (High):        {n}
     P2 (Medium):      {n}
     P3 (Low):         {n}
     Modules covered:  {list}
     Sections:         {N} (of 10)
   ```

---

## Quality Checklist (Self-Review)

Before finalizing the QA plan, verify:

- [ ] Every test case has a non-empty **Caveats** column with real code references
- [ ] All code file:line references have been verified by reading the actual file
- [ ] Priority is assigned **per test case**, not per section
- [ ] P0 tests cover the specific change that triggered the plan
- [ ] Blast radius Hop 2 areas have regression test cases
- [ ] Smoke checklist has 10-15 items drawn from P0/P1 tests
- [ ] Exit criteria are present and actionable
- [ ] Conditional sections (security, offline) are included only if relevant
- [ ] No placeholder text ("TBD", "TODO", "fill in later")
- [ ] Scope & Out-of-Scope section explicitly lists excluded modules
