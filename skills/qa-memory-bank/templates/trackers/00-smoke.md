# 00 — Smoke

Goal of this pass: log in as every role, hit each top-level screen, look for blockers (S0/S1) and confirm the app is testable end-to-end. Do not deep-test here — that's later passes.

For each row: render the screen, observe, mark `pass` / `fail` / `blocked` / `n/a`. Fill **Last run** with today's ISO date when you touch the row.

| Test ID  | Area | Test case | Steps (short) | Expected | Status | Issue | Last run | Notes |
|----------|------|-----------|---------------|----------|--------|-------|----------|-------|
| SMOKE-001 | auth | Login page loads | navigate to URL | login form renders, no console errors | pending | | | |
| SMOKE-002 | auth | <role> login | submit creds | dashboard loads | pending | | | |
| <add rows per role × top-level screen> | | | | | | | | |
