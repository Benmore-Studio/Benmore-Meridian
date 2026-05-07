---
name: full-app-test
description: Run a thorough end-to-end test of the entire app using the Playwright CLI against the deployed environment, with a draft PR, TEST_PLAN.md, scenario specs, fix-as-you-go iteration, and a final coverage report.
tags: [qa, testing, playwright, e2e, deployment, pr]
scope: general
project: ""
---

Run a thorough end-to-end test of the entire app using the Playwright CLI (`playwright` is installed globally).

**Where to test:** Run against the **deployed environment**, not localhost. This means:
- **Frontend** → the live Vercel URL (production deployment if it exists, otherwise the latest preview / staging deploy).
- **Backend** → the live Heroku or DigitalOcean URL the frontend points at.
- Even though these URLs may be labeled "production," the app is **still in pre-launch test mode with no real users**. Treat the deployed environment as a QA/staging environment: you have full latitude to create, modify, or delete data and to spin up as many user accounts as needed to cover every flow.
- **Hard stops:** do not touch any environment that is genuinely live with real customer data, do not call third-party APIs in live mode (Stripe live keys, real email/SMS to non-test addresses, real webhooks to external partners), and do not modify shared infrastructure (DNS, prod DB schema outside migrations, secrets).
- If you can't tell whether an environment is safe to write to, **stop and ask** before proceeding.

Determine the URLs before writing any specs:
- Check `vercel.json`, `.vercel/project.json`, or run `vercel ls` / `vercel inspect` for the frontend URL.
- Check `app.json`/`heroku.yml`, `Procfile`, or run `heroku apps:info -a <app>` for Heroku; check `.do/app.yaml` or `doctl apps list` for DigitalOcean.
- Confirm the frontend's `NEXT_PUBLIC_API_URL` (or equivalent) actually resolves to the backend you intend to test, so frontend specs hit the matching backend.
- Record both URLs in the `TEST_PLAN.md` under an "Environment" section.

## Workflow

1. **Branch & PR setup (do this first, before any testing).**
   - Create a fresh branch off the current default branch named `qa/full-app-test-<YYYY-MM-DD>`.
   - Open a draft PR titled `QA: Full app test pass (<YYYY-MM-DD>)` with an initial body that lists the planned test scopes and notes that the PR will be updated continuously as bugs are found and fixed.
   - Keep the PR in draft until the entire run is finished. Do **not** merge.

2. **Build the test plan.** Before writing any specs, write a `TEST_PLAN.md` in the repo root (or `docs/qa/` if it exists) covering:
   - Every user role and the entry points each one has.
   - Auth flows: signup, login, logout, password reset, MFA/2FA if present, session expiry, role switching.
   - Core CRUD for each primary resource — happy path and at least two failure cases per resource (validation errors, permission errors, race conditions).
   - Cross-role interactions (e.g., admin sees what a regular user just submitted).
   - Permissions and tenant isolation: prove user A cannot see, edit, or act on user B's data.
   - Payment, billing, or webhook flows if applicable — use test mode only.
   - File uploads, exports, emails/notifications — verify content and delivery side effects.
   - Empty states, loading states, error states, and offline / network-failure behavior.
   - Mobile viewport and at least one accessibility smoke pass (keyboard nav, focus order, alt text on key screens).
   - Performance smell tests on the heaviest pages (note slow loads, layout shifts, console errors).

3. **Set up the Playwright test project.**
   - If the repo already has a `playwright.config.*` and a tests directory, use it.
   - Otherwise, scaffold one in `tests/e2e/` with a `playwright.config.ts` that:
     - sets `use.trace: 'on-first-retry'`, `use.screenshot: 'only-on-failure'`, `use.video: 'retain-on-failure'`
     - configures `baseURL` from `process.env.BASE_URL` (default to the **deployed Vercel URL** identified above — never localhost; fail loudly if `BASE_URL` is unset)
     - if specs hit the API directly, expose `process.env.API_URL` the same way (default to the deployed Heroku/DO URL)
     - **does not** start a `webServer` — we are testing a deployed environment, not booting a local one
     - registers projects for `chromium`, `firefox`, `webkit`, and a `Mobile Safari` device for the mobile pass
     - sets `reporter: [['list'], ['html', { open: 'never' }]]`
   - Add `@playwright/test` as a dev dep if it's missing (`npm i -D @playwright/test`). The global `playwright` CLI works against the local install once it exists.
   - Centralize logins with `storageState` fixtures — auth once per role, reuse across specs.

4. **Author specs scenario-by-scenario.** Group by area (`auth.spec.ts`, `crud-<resource>.spec.ts`, `permissions.spec.ts`, `payments.spec.ts`, etc.). For each scenario, encode: the steps, the expected result via `expect(...)` assertions, and any console/network listeners (`page.on('console', ...)`, `page.on('pageerror', ...)`) that fail the test on unexpected errors.
   - Use `playwright codegen <url>` when you need to capture a selector or flow quickly, then clean up the output before committing.
   - Prefer role/text locators (`getByRole`, `getByLabel`, `getByText`) over CSS selectors.

5. **Run the suite and iterate.**
   - Headless run for the full pass: `playwright test --reporter=list`.
   - Single-spec debugging: `playwright test path/to.spec.ts --headed --trace=on`.
   - Inspect failures: `playwright show-report` and `playwright show-trace test-results/.../trace.zip`.
   - For each failing scenario, capture in the PR: steps, expected, actual, trace path or screenshot, and any console/network errors.

6. **Fix bugs as you go and push to the same PR.**
   - When a spec catches a bug, fix it on this QA branch, commit with a clear message referencing the failing scenario, and push.
   - Re-run the failing spec (`playwright test -g "<scenario name>"`) to confirm the fix before moving on.
   - Update the PR description with a running checklist of bugs found and resolved.
   - If a bug is out of scope or risky to fix in this pass (e.g., needs a schema migration, design decision, or third-party change), document it in the PR body under "Deferred" with reasoning instead of attempting a fix.

7. **Stop conditions.**
   - Do not merge the PR.
   - Do not mark the PR ready for review until every planned scenario has either passed or been explicitly deferred with justification.
   - Commit the spec files — they're the durable artifact of this pass and the seed of an ongoing E2E suite.

## Final summary (post in chat when done)

Produce a concise report containing:

- **Coverage** — scopes tested, scopes skipped (and why), spec files added.
- **Bugs found & fixed** — one line each: scenario → root cause → fix (commit SHA).
- **Bugs deferred** — one line each: scenario → why deferred → suggested next step.
- **Regressions or risks** — anything that worked but felt fragile, slow, or inconsistent.
- **Suggested follow-ups** — specs worth promoting to CI, refactors worth doing, monitoring worth adding.
- **PR link** — the draft PR URL so I can review before merge.
- **How to re-run** — the exact `playwright test ...` command(s) needed to reproduce the pass locally.

Keep the summary tight — bullets over prose. The PR description is where the long form lives.
