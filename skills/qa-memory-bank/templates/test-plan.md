# Master Test Plan

## Goal

End-to-end QA of the app at the URL declared in `test-environment.md` with the goal that every screen for every role has been exercised against:

- **Functional** — feature works per its apparent intent and per any spec docs in the repo.
- **Negative paths** — invalid input, missing data, unauthenticated, wrong-role, network failure, expired tokens.
- **UX/UI** — empty states, loading states, error states, validation messages, confirmation dialogs, keyboard nav, focus management, copy clarity, icon/label consistency.
- **UX gaps** — affordances that *should* exist (delete, edit, undo, sort, filter, search, pagination, bulk action, detail view, empty-state CTA) but don't.
- **Security / sensitive-data** — auth bypass, IDOR (one user reading another's data), session/cookie behavior, MFA bypass, audit logging side-effects, consent gating, encrypted-field display. (Adapt to project's compliance posture — HIPAA, PCI, SOC 2, GDPR, etc., or none.)
- **Cross-cutting** — console errors, network errors (4xx/5xx leaking through UI), page load smell test, accessibility smoke (alt text, focus order, contrast obvious failures), responsive layout sanity at the spot-check viewports.

## Strategy: layered passes

We do **not** test exhaustively in one pass. Multiple cheap passes catch more in less time.

### Pass 1 — Smoke (`trackers/00-smoke.md`)
For every role: log in, hit the dashboard, navigate to each top-level screen, observe. Goal: find blockers fast and confirm the app is testable end-to-end.

### Pass 2 — Auth & onboarding (`trackers/01-auth.md`)
Register, email verify, login, MFA setup/verify, forgot password, reset password, profile completion. Both happy and negative paths. Session/token behavior.

### Pass 3 — Per-role functional sweep
Walk every screen, every CRUD path, every form, every list. One tracker per role:
- `02-<role>.md`
- `03-<role>.md`
- ...

For each screen include: render, empty state, loading state, error state, primary action(s), secondary actions, navigation back, deep-link/refresh, validation.

### Pass 4 — Security (`trackers/06-security.md`)
- Cross-user IDOR: log in as user A, try to fetch user B's resources via URL/ID swap.
- Cross-role: lower-privilege user hitting higher-privilege endpoints.
- Session: refresh after logout, token expiry, multiple tabs.
- Auth bypass on critical endpoints (UI-driven; we observe what the UI sends, we don't run raw curl).
- Consent / acknowledgment gates.
- Single-use token enforcement (if applicable).
- Sensitive-data display: anything that looks unencrypted in DOM/console where it shouldn't be.

### Pass 5 — UX gaps (`trackers/07-ux-gaps.md`)
A focused walkthrough whose only goal is to ask "what's *missing* here?" — empty states, confirmations, undo, sort/filter/search/pagination on lists, edit/delete affordances, keyboard shortcuts, breadcrumbs.

### Pass 6 — Cross-cutting (`trackers/08-cross-cutting.md`)
- Console errors/warnings on every screen (silent JS errors).
- Network 4xx/5xx that the UI swallows.
- Performance smell: page TTI, list rendering with many items, repeated calls, missing pagination.
- Accessibility smoke: tab order, focus rings, alt text on images, label/for on inputs, color-contrast obvious fails.
- Responsive: spot-check viewports.
- Copy/i18n: typos, inconsistent terminology, date/number formatting.

## Exit criteria

QA pass is "complete" when:
1. Every row in every tracker is one of `pass`, `fail` (with linked issue), `n/a`, or `blocked` (with reason logged).
2. `issues/ready-for-retest/` is empty.
3. The session log has a final entry summarizing totals (issues opened by severity, top risks, recommended priorities).

We will almost certainly not reach this in one session — that's why the trackers + retest loop exist.

## Coverage matrix (roles × areas)

> Fill in at bootstrap based on the project's actual roles and surfaces.

| Area / Role | TODO | TODO | TODO |
|---|---|---|---|
| Auth (login/register) | | | |
| Profile / settings | | | |
| Dashboard | | | |
| ... | | | |

## Inventory (from codebase scan)

> Fill in at bootstrap by scanning the project's screens/routes. Treat as authoritative for screen names but verify against actual nav.

- **Auth (N):** TODO
- **Role 1 (N):** TODO
- **Role 2 (N):** TODO
- **Shared (N):** TODO
