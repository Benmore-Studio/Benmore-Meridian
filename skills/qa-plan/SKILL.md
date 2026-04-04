---
name: qa-plan
description: Generate a QA test plan from code changes. Analyzes git diffs, traces blast radius, risk-scores each area, and outputs prioritized test cases with smoke checklist and exit criteria.
context: fork
---

# QA Plan Generator

Systematically generate QA test plans from code changes by tracing blast radius, scoring risk, and producing prioritized test cases.

## When to Use
- After fixing a bug — generate targeted QA for what changed
- After implementing a feature — generate tests + regression checks
- Before a release — comprehensive QA covering all changes since last release
- On-demand — "QA the health module" or "test plan for this PR"
- Anytime you're unsure what to test

## Input Modes

The skill accepts flexible input. Detection priority (first match wins):

1. **PR number**: starts with `#` or is purely numeric → `/qa-plan #419`
2. **Branch name**: `git rev-parse --verify <arg>` succeeds → `/qa-plan fix/custom-drugs`
3. **Module/directory**: directory exists in the project → `/qa-plan health`
4. **Freeform**: anything else — matched against files/modules → `/qa-plan "the offline sync changes"`
5. **No args** (default): reads unstaged + staged git diff → `/qa-plan`

## Workflow

Execute these 6 steps in order. Steps 2 and 3 use parallel subagents for speed.

---

### Step 1: Gather Changes

Based on the input mode, collect the raw change data.

First, detect the default branch:
```bash
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@') || DEFAULT_BRANCH="main"
```

**For git diff (default — no args):**
```bash
# Working tree changes (staged + unstaged) vs HEAD
git diff HEAD

# Also capture untracked files (new files not yet git-added)
git ls-files --others --exclude-standard

# If empty (clean tree), fall back to branch commits vs default branch
git diff ${DEFAULT_BRANCH}...HEAD
```
**Early exit**: If all diffs are empty and no untracked files exist, report "No changes detected. Specify a branch, module, or PR number." and STOP.

**For branch comparison:**
```bash
git diff ${DEFAULT_BRANCH}...<branch-name>
```

**For PR number:**
```bash
gh pr diff <number>
```
If `gh` is not installed, fall back to: `git log --oneline ${DEFAULT_BRANCH}...HEAD` and read changed files manually.

**For module name:**
```bash
git diff ${DEFAULT_BRANCH}...HEAD -- '<module>/**'
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

**Degraded mode** (no CLAUDE.md or docs found):
- Infer framework from `package.json` / `requirements.txt` / `Gemfile` / `go.mod`
- Infer architecture from directory structure
- Note "Project Context: INFERRED (no documentation found)" in the output header
- Blast radius analysis in Step 3 will have reduced confidence — flag this in caveats

---

### Step 3: Blast Radius Analysis (2-Hop)

Launch **parallel Explore subagents** to trace dependencies outward. Cap at **10 subagents max**. If >20 changed files, group by module and launch one agent per module. If subagents are unavailable, execute sequentially.

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

**Priority** (per test case, NOT per section): P0 = the fix itself or data-loss/security paths. P1 = direct integrators. P2 = adjacent, shared models. P3 = theoretical coupling only.

**Type**: `smoke` | `functional` | `regression` | `edge` | `security` | `offline`

**MANDATORY: Every test case must have a non-empty Caveats column.** Read the actual source code to populate caveats with real file references, line numbers, architecture constraints, setup requirements, or known limitations. Never leave caveats empty. Never fabricate code references — verify them by reading the file.

Generate test cases using the coverage depth from Step 4:
- Exhaustive areas (20-25): 5-8 test cases covering happy path, error paths, boundary values, permissions, offline
- Heavy areas (12-19): 3-5 test cases covering happy path, error path, one edge case
- Standard areas (6-11): 1-2 test cases covering happy path and one negative case
- Smoke areas (1-5): 0-1 test cases (covered by smoke checklist instead)

#### Section 5: Regression Test Cases

Tests for areas found via **Hop 2 only** (indirect blast radius — not directly changed, not a direct caller). Same table format, `Type = regression`. Always include regressions for historically buggy areas in the blast radius.

**Disambiguation**: Section 4 covers Hop 0 (changed code) and Hop 1 (direct callers/callees). Section 5 covers Hop 2 only. Section 6 covers cross-cutting edge cases not specific to a single feature area.

#### Section 6: Edge Cases & Negative Tests

Cross-cutting boundary conditions that span multiple feature areas: zero/null/empty, duplicate submissions, race conditions, max-length inputs, invalid FK references. Same table format, `Type = edge`.

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

A quick-pass checkbox list drawn from P0 and P1 test cases. 5-15 items (scale to change size). Format:

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

1. **Create** `docs/` directory if it doesn't exist: `mkdir -p docs/`

2. **Save** to `docs/QA-PLAN-{YYYY-MM-DD}-{slug}.md`
   - `{slug}` generation: PR input → PR title kebab-cased (max 40 chars). Branch input → branch name with `/` → `-`. Module input → module name. Default diff → most-changed module name.

3. **Print summary**: total test cases, P0/P1/P2/P3 breakdown, modules covered.

**Token budget**: If blast radius exceeds 30 areas, consolidate to the top 15 by risk score. Hard cap: 8 test cases per section even for Exhaustive areas. If total exceeds 60 test cases, drop P3 and condense P2 to smoke-only.

---

## Key Principles

1. **Caveats are mandatory** — every test case must reference real code (file:line), architecture constraints, or setup prerequisites. Read the source to populate these; never fabricate references.
2. **Risk drives depth** — exhaustive testing for score 20+, smoke-only for score 1-5. Don't waste time on low-risk areas.
3. **Blast radius over gut feel** — trace dependencies systematically (2 hops). The regressions you miss are always in the second hop.
4. **Priority per test case, not per section** — a "P1 section" may contain individual P2 or P3 tests. Assign granularly.
5. **Conditional sections** — only include security/offline sections when the blast radius warrants them. Shorter plans get read; long ones get skipped.
6. **Verify, don't assume** — if a git command fails or a doc doesn't exist, adapt. Detect the default branch; fall back gracefully on missing `gh` CLI.

## Self-Review Checklist

Before finalizing the QA plan, verify:

- [ ] Every test case has a non-empty **Caveats** column with verified code references
- [ ] Priority is assigned per test case, not per section
- [ ] P0 tests cover the specific change that triggered the plan
- [ ] Blast radius Hop 2 areas have regression test cases
- [ ] Smoke checklist has 5-15 items from P0/P1 tests
- [ ] Exit criteria are present and actionable
- [ ] Conditional sections only included when relevant
- [ ] No placeholder text ("TBD", "TODO")
- [ ] Scope section explicitly lists excluded modules
