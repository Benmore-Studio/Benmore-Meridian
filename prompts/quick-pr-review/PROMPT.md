---
name: quick-pr-review
description: Fast code review focusing on bugs, security, and style
tags: [review, pr, code-quality]
scope: general
project: ""
---

Review the current PR or recent changes. Focus on:

1. **Bugs** — Logic errors, off-by-one, null handling, race conditions
2. **Security** — Injection, auth bypass, secrets in code, OWASP top 10
3. **Style** — Naming, consistency with codebase patterns, dead code
4. **Tests** — Missing coverage for new logic, edge cases

Be concise. Flag only real issues, not style nits.

$ARGUMENTS
