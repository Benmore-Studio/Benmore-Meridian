---
name: cross-module-check
description: After editing code in a module, reads that module's CLAUDE.md cross-module integration section, identifies dependent modules, and dispatches parallel agents to verify each dependency still works. Use when making changes that could break cross-module contracts.
context: fork
---

# Cross-Module Dependency Check

Verify that code changes in one module don't break dependent modules by reading documented integration points and dispatching parallel verification agents.

## When to Use
- After modifying a service, model, or signal that other modules import
- Before creating a PR that touches shared interfaces (models, services, utilities)
- After changing function signatures, return types, or queryset filters
- When CLAUDE.md documents cross-module dependencies for the changed module

## Prerequisites
- Module-level CLAUDE.md files with a **Cross-Module Integration** section
- Each CLAUDE.md should document: which modules depend on this one, what they import, and how they use it

## Workflow

### Step 1: Identify Changed Modules

```
Detect changed files (git diff --name-only against base branch)
    │
    ├── Group files by module (top-level directory)
    │       e.g., lots/services.py → module = "lots"
    │            feeds/models.py  → module = "feeds"
    │
    └── Result: list of changed modules
```

### Step 2: Read Integration Maps

For each changed module:

1. Read `<module>/CLAUDE.md`
2. Find the **Cross-Module Integration** or **Cross-Module Dependencies** section
3. Extract the list of dependent modules and what they depend on

Example extraction:
```
Module: inventory
Dependents:
  - feeds (imports: FeedEventCostDetail, FIFO deduction)
  - health (imports: PharmaBatch deduction)
  - invoices (imports: FIFO costs for line items)
  - reports (imports: COG feed cost via FIFO)
  - expenses (imports: expense inventory linking)
```

### Step 3: Build Verification Matrix

```
┌─────────────────┬──────────────────────┬──────────────────────────────┐
│ Changed Module   │ Dependent Module     │ Verification Action          │
├─────────────────┼──────────────────────┼──────────────────────────────┤
│ inventory        │ feeds                │ Run feeds tests              │
│ inventory        │ health               │ Run health tests             │
│ inventory        │ invoices             │ Run invoice tests            │
│ inventory        │ reports              │ Run report tests             │
│ lots             │ sorts                │ Run sorts tests              │
│ lots             │ invoices             │ Run invoice tests            │
│ ...              │ ...                  │ ...                          │
└─────────────────┴──────────────────────┴──────────────────────────────┘
```

### Step 4: Dispatch Parallel Verification Agents

For each dependent module, dispatch an agent that:

1. Reads the dependent module's CLAUDE.md
2. Identifies the specific integration point (function, class, import)
3. Greps the dependent module for actual usage of the changed code
4. Runs that module's test suite
5. Reports: PASS (tests pass, usage matches contract) or FAIL (tests fail or contract broken)

**Agent prompt template:**
```
Module "{changed_module}" was modified. You are verifying that
"{dependent_module}" still works correctly.

Integration point: {what_the_dependent_imports}

Steps:
1. Read {dependent_module}/CLAUDE.md for context
2. Grep {dependent_module}/ for imports from {changed_module}
3. Verify the imported interfaces still match (function signatures, return types)
4. Run: python manage.py test {dependent_module} -v 2
5. Report PASS or FAIL with specific details
```

### Step 5: Aggregate Results

```
CROSS-MODULE CHECK RESULTS
===========================
Changed: inventory/services.py, inventory/models.py

  feeds     ✅ PASS  (12 tests, 0 failures)
  health    ✅ PASS  (8 tests, 0 failures)
  invoices  ⚠️ WARN  (3 tests skipped — Redis required)
  reports   ❌ FAIL  (test_closeout_report: AttributeError 'FeedCommodity' has no attribute 'average_cost')
  expenses  ✅ PASS  (6 tests, 0 failures)

ACTION REQUIRED: reports module — 'average_cost' was renamed to 'fifo_front_cost'
```

## Configuration

The skill works with any project that has module-level documentation files containing cross-module dependency information. Adapt these settings:

| Setting | Default | Description |
|---------|---------|-------------|
| Doc file name | `CLAUDE.md` | Name of module documentation file |
| Section header | `Cross-Module` | Header text to search for in docs |
| Test command | `python manage.py test {module}` | Command template for running module tests |
| Base branch | `main` | Branch to diff against |
| Max parallel agents | `6` | Limit concurrent verification agents |

## Framework Adaptations

### Django
```bash
python manage.py test {module}.tests -v 2
```

### FastAPI
```bash
pytest tests/{module}/ -v
```

### Rails
```bash
bundle exec rspec spec/{module}/
```

### Node/TypeScript
```bash
npx jest --testPathPattern={module}
```

## Key Principles

1. **Read docs first** — don't guess at dependencies, read what's documented
2. **Verify contracts** — check that function signatures, return types, and field names still match
3. **Run tests** — documentation can be stale, tests are the source of truth
4. **Report specifically** — "test X failed with error Y" not just "something broke"
5. **Skip when no docs** — if a module has no CLAUDE.md, log it as "undocumented, skipped"

## Common Pitfalls

- **Circular imports**: Module A depends on B which depends on A. Only verify the direction that was changed.
- **Transitive dependencies**: If A→B→C and you change A, verify B (direct) but not C (transitive) unless B's contract also changed.
- **Test infrastructure**: Some tests need Redis, Postgres, or external APIs. Report skipped tests as warnings, not failures.
- **Signal side effects**: Django signals cross module boundaries silently. Check `signals.py` in the changed module for cross-module signal handlers.
