# QA Memory Bank

> **Purpose:** Persistent QA workspace for this project. Lives across Claude sessions so any session can pick up where the last one left off without losing context.

## ⚠️ READ THIS FIRST (every session)

If you are a Claude session opening this folder for QA work, do these steps **in order** before doing anything else:

1. Read [`test-environment.md`](./test-environment.md) — URL, login creds, tooling, viewport, what cannot be tested via the available driver.
2. Read [`conventions.md`](./conventions.md) — issue IDs, severities, retest workflow, when NOT to file.
3. Read the last 1–2 entries (top of file) of [`session-log.md`](./session-log.md) — what was just done, what's next.
4. Skim [`issues/ready-for-retest/`](./issues/ready-for-retest/) — anything claimed fixed needs verification before continuing forward progress.
5. Open the relevant tracker in [`trackers/`](./trackers/) and continue from the first row whose **Status** column is `pending` or `blocked`.

When you finish your session (or hit the context budget), append a short entry to `session-log.md` describing what you tested, what you filed, and the next concrete step. **Future-you depends on this.**

## Folder layout

```
qa-memory-bank/
├── README.md                 ← you are here
├── test-plan.md              ← master test plan: scope, strategy, exit criteria
├── test-environment.md       ← URL, accounts, browser, tools (PROJECT-SPECIFIC)
├── conventions.md            ← issue lifecycle, severity, file naming, retest rules
├── session-log.md            ← append-only log; one entry per QA session
├── trackers/                 ← per-area test trackers (the running checklist)
│   ├── 00-smoke.md
│   ├── 01-auth.md
│   └── ...                   ← per-role / domain trackers, then 06-security, 07-ux-gaps, 08-cross-cutting
├── issues/
│   ├── README.md             ← issue index + workflow
│   ├── ISSUE-TEMPLATE.md     ← copy this when filing
│   ├── open/                 ← active bugs, awaiting fix
│   ├── ready-for-retest/     ← engineering says fixed; QA must verify
│   ├── verified-fixed/       ← retested and confirmed
│   └── wont-fix/             ← acknowledged but out of scope / by design
└── screenshots/              ← evidence; named after issue ID, e.g. ISSUE-0007-login-error.png
```

## Tracker status legend

Used in every tracker row:

- `pending` — not yet attempted
- `in-progress` — currently being tested (rare; only set during an active session)
- `pass` — works as expected
- `fail` — bug found; an issue file exists in `issues/open/` (link the ID)
- `blocked` — cannot test (precondition missing, server down, role unavailable); note why
- `retest` — was failed, dev claims fixed, needs re-verification (issue is in `issues/ready-for-retest/`)
- `n/a` — not applicable in current build (note why)

## How to mark a fixed item for retest (cross-session signal)

When an engineer (or another Claude session) fixes a bug:

1. They move the issue file from `issues/open/<id>.md` → `issues/ready-for-retest/<id>.md` and append a `## Fix notes` section (commit/PR + summary).
2. They flip the corresponding tracker row's **Status** from `fail` to `retest` and update the **Issue** column to point at the new path.
3. The next QA session, on startup (step 4 above), picks these up first and re-runs the original repro.
   - If the fix holds: move issue file to `issues/verified-fixed/<id>.md`, set tracker row to `pass`.
   - If it still fails: move issue file back to `issues/open/<id>.md`, append a `## Retest <date>` section explaining how it still fails, set row back to `fail`.

This loop is the single source of truth for retest cycles — **do not** rely on memory or chat history.
