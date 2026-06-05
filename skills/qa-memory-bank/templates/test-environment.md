# Test Environment

> **Fill this in at bootstrap.** Anything left as `TODO` will block QA sessions until the user provides it. Don't guess URLs, credentials, or compliance posture.

## App under test

- **What it is:** TODO — e.g. "Django + DRF backend with React Native (Expo) frontend tested via web build"
- **URL (frontend):** `http://localhost:TODO/`
- **URL (backend, if separate):** `http://localhost:TODO/` — health check at `TODO`
- **Stack notes:** TODO

If the frontend URL is unreachable, set the relevant tracker rows to `blocked`, file no bugs, append a session-log entry explaining the outage, and stop. **Do not** start the dev server — that's the user's responsibility.

## Platform & viewport

- **Primary platform:** TODO — web | iOS | Android | desktop | hybrid
- **Design viewport:** TODO — width × height (e.g. `390×844` for mobile, `1280×720` for desktop)
- **Spot-check viewports:** TODO (e.g. `360×800` for Android, `768×1024` for tablet)
- **Resize on every fresh browser launch** to the design viewport before any other action.

### If this is a mobile app tested via web build

> Delete this section if not applicable.

The app is mobile-first (iOS/Android via React Native / Expo / similar). Web is a QA proxy because Playwright drives a browser, not a native app. Implications:

1. **Default viewport is mobile.** Layout findings only reproducible at desktop sizes get downgraded to S4 or labeled `web-build-only`.
2. **Web-only symptoms with cross-platform causes** still get filed against the underlying cause (e.g. a misclassified API error code is real on mobile too even if the `console.error` is web-only).
3. **Genuinely web-only concerns** (don't apply to native): HTML form/password manager semantics, `document.title`, React DOM property warnings, CSS layout outside the design viewport, URL/path-based routing.
4. **Cannot test via web** (mark `n/a` with a note): camera flows, biometric auth, push notifications, native share/photo picker, OS permission prompts, background tasks, native splash, app icon.

## Test accounts

> Fill in seeded accounts the project provides. If a seeder command exists, document it.

All seeded users share password: `TODO`

| Role | Email | Notes |
|---|---|---|
| TODO | `TODO` | TODO |

If login fails for these accounts, the seeder probably hasn't run on the current DB. Mark the row `blocked`, log it, and stop — do not file a bug for missing seed data.

To (re-)seed:
```
TODO — e.g. uv run python manage.py seed_data
```

## Tooling

- **Browser driver:** TODO — e.g. `playwright-cli` skill, Playwright direct, Cypress
- **Screenshots:** save into `qa-memory-bank/screenshots/` named `<ISSUE-ID>-<short-slug>.png`. For ambient evidence not tied to a bug, prefix with `evidence-` and date.
- **Console & network logs:** capture via the driver when filing a bug; paste relevant excerpt into the issue file (do **not** dump full logs — keep to the offending lines plus a few of context).

## Scope

**In scope:**
- TODO — list roles and the surfaces under test
- Functional, UX/UI, error handling, basic security (authz, session, input validation), accessibility smoke checks, performance smell tests
- Looking for **missing** UX affordances (e.g., a list with no delete, no empty state, no loading skeleton, no validation message)

**Out of scope (note in session log if encountered, do not deep-dive):**
- TODO — e.g. native-only behaviors, penetration testing, backend unit tests, load testing
