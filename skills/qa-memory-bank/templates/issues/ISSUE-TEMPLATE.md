# ISSUE-NNNN: <one-line title>

- **Severity:** S0 | S1 | S2 | S3 | S4
- **Role(s) affected:** anonymous | <role-1> | <role-2> | … | all
- **Area:** auth | <feature-area> | ux-gap | security | cross-cutting | …
- **Status folder:** open  ← (matches the folder this file lives in)
- **Filed:** YYYY-MM-DD
- **Last updated:** YYYY-MM-DD
- **Filed by:** Claude session (commit/branch if relevant)

## Summary

One paragraph in plain English. What's broken, who hits it, why it matters.

## Steps to reproduce

1. Log in as `<test-account>`.
2. Navigate to <screen>.
3. …

Include any non-obvious preconditions (specific data state, role permissions, prior actions in the same session).

## Expected

What should happen.

## Actual

What actually happens. Include error text verbatim if any.

## Evidence

- Screenshot: `qa-memory-bank/screenshots/ISSUE-NNNN-<slug>.png`
- Console excerpt (only relevant lines):
  ```
  ...
  ```
- Network excerpt (only relevant requests):
  ```
  POST /api/v1/... → 500
  body: { ... }
  ```

## Environment

- URL: `<full URL>`
- Browser/viewport: <browser> <width>×<height>
- Build/commit (if known): <git sha>
- Backend health: ok | not checked

## Notes / hypothesis

- Suspected file/area: `<path/to/file>` or component name.
- Related issues: ISSUE-NNNN.
- Workaround: …

---

## Fix notes  ← (added by engineering when moving to ready-for-retest/)

- PR/commit: …
- Summary of change: …
- Anything QA should pay extra attention to during retest: …

---

## Retest YYYY-MM-DD: PASS | FAIL  ← (added by QA on retest)

- Re-ran original repro: <observation>
- Regression check around <area>: <observation>
- If FAIL: detailed new-failure description.
