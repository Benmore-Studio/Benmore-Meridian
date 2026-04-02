---
name: full-pr-review-audit
description: Full PR review + code audit pipeline with parallel agents — review, simplify, document, and audit
tags: [review, audit, pr, security, code-quality, agents]
scope: general
project: ""
---

Start an agent team after first exploring the codebase — CLAUDE.md, patterns, ASCII flows, changelog of the last 8 days, and tree for the codebase.

Then run these in parallel:

1. **/pr-review-toolkit:review-pr** — One agent does full PR review
2. **/ce:review** or **/code-review:code-review** — Claude code review for style, bugs, patterns
3. **/simplify** — Fix issues found by reviewers, clean up code
4. **/productionize-app** — Document everything using redoc, swagger, CLAUDE.md, changelog, and inline docs
5. **Critical audit** — Highly critical full-codebase audit. Find any loopholes or things missed. Be highly critical and run as many sub-agents as you can. Use /find-skills to find and run as many relevant skills as possible. The code needs to be clean, no security issues, all edge cases taken into consideration, all integrations working, code getting ready for smoke testing. Do NOT commit or push anything. None of the existing functionality should break.

$ARGUMENTS
