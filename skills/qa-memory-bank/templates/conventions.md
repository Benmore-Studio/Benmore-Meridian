# Conventions

## Issue IDs

- Format: `ISSUE-NNNN` — zero-padded, monotonically increasing across all categories.
- Allocate the next ID by running `ls qa-memory-bank/issues/{open,ready-for-retest,verified-fixed,wont-fix}` and taking max + 1.
- File name: `ISSUE-NNNN-<short-kebab-slug>.md` (e.g. `ISSUE-0007-login-rejects-valid-mfa-code.md`).

## Severity

| Level    | When to use |
|----------|-------------|
| **S0 — Blocker** | App unusable for a role: cannot log in, primary navigation broken, data loss, security breach (auth bypass, sensitive-data leak). |
| **S1 — Critical** | Core feature broken: cannot create/read/update primary entity, feature throws unhandled error, broken navigation on a major flow. |
| **S2 — Major** | Significant degradation: secondary feature broken, data displayed incorrectly, validation missing on important field, slow page (>5s) on critical path. |
| **S3 — Minor** | Cosmetic, layout, copy, low-impact UX gap (e.g., missing confirmation dialog on delete, wrong icon, inconsistent spacing). |
| **S4 — Trivial** | Typo, small visual polish, suggestion for nice-to-have. |

When unsure, pick the higher severity — easier to downgrade than miss.

## Issue file structure

Use [`issues/ISSUE-TEMPLATE.md`](./issues/ISSUE-TEMPLATE.md) as a starting point. Required sections:

- Header: ID, title, severity, role, area, status, dates.
- **Summary** — one paragraph, plain English.
- **Steps to reproduce** — numbered, deterministic. Include test account used.
- **Expected vs Actual.**
- **Evidence** — screenshot path(s), console excerpt, network excerpt.
- **Environment** — URL, browser, viewport, build commit if known.
- **Notes** — hypothesis, related issues, suggested fix area (file path/line if obvious from codebase).

## Issue lifecycle

```
        ┌────── filed ──────┐
        ▼                   │
  issues/open/  ──fix──▶ issues/ready-for-retest/
                              │
                  ┌───────────┴────────────┐
                  ▼                        ▼
          retest passes              retest fails
                  │                        │
                  ▼                        ▼
       issues/verified-fixed/      back to issues/open/  (append `## Retest <date>` section)

  issues/wont-fix/   ← terminal (user/eng explicitly accepts)
```

**Moving a file = `git mv` semantics: just use `mv`.** Don't duplicate. The folder it lives in is the source of truth for status — never edit a status field in two places that can disagree.

## Tracker rows

Each tracker is a markdown table. Columns:

| Test ID | Area | Test case | Steps (short) | Expected | Status | Issue | Last run | Notes |

- **Test ID** — `<area>-NNN`, e.g. `AUTH-001`, `SMOKE-014`.
- **Status** — see legend in [`README.md`](./README.md). Update inline as you test.
- **Issue** — link to issue file if `fail` or `retest`, else blank.
- **Last run** — ISO date you last touched this row.

When you change a row's status, also update **Last run**. Don't silently pass over rows.

## Retest workflow (THE important loop)

Engineering signals "fixed" by:
1. Moving issue file to `issues/ready-for-retest/`.
2. Appending a `## Fix notes` section with PR/commit and a summary of what changed.
3. Flipping the tracker row to `retest`.

QA's first job each session is to clear `ready-for-retest/`:
- Re-run the **original repro** (not a different path).
- If pass: `mv` the file to `verified-fixed/`, append a `## Retest <YYYY-MM-DD>: PASS` block, set the tracker row to `pass`, update **Last run**.
- If fail: `mv` back to `open/`, append a `## Retest <YYYY-MM-DD>: FAIL` block describing the new failure (it may be different from the original — note that), set the tracker row back to `fail`.
- Do additional regression around the changed area (smoke the surrounding screens) — many "fixed" patches break something nearby.

## Filing UX gaps (no-bug, but worth raising)

Missing affordances (no empty state, no delete button, no validation message, no confirmation on destructive action) are real findings even though they aren't bugs in code that exists. File these as normal issues with severity S3 (or S2 if it materially blocks a workflow). Use the area tag `ux-gap` in the title prefix:

`ISSUE-0042-ux-gap-medications-list-no-empty-state.md`

These also get tracked in [`trackers/07-ux-gaps.md`](./trackers/07-ux-gaps.md).

## When to NOT file

- A test you couldn't run because of environment (server down, no seed data, account locked) — log in `session-log.md`, mark tracker row `blocked`, **do not** open an issue.
- Behavior you're unsure about — note it in the tracker row's **Notes** column with a `?`, and continue. If still unsure after the area is done, file as S4 with the question explicit.
- Duplicates — if symptom matches an existing open issue, add a `## Additional repro <date>` block to that issue instead of filing a new one.
- Findings that only repro outside the project's declared design viewport — downgrade to S4 or label with the platform (`web-only`, `desktop-only`) in the title.
