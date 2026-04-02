---
name: productionize-django
description: Audit and productionize a Django project with modern tooling
tags: [django, production, audit, uv, ruff, pytest]
scope: general
project: ""
---

Analyze the Django project at $1 and apply production best practices.

Focus on:
- Modern tooling: uv for packages, ruff for linting, pytest for tests
- Settings split (base/dev/prod) with environment variables
- Security hardening (DEBUG, ALLOWED_HOSTS, CSRF, HSTS)
- Docker + docker-compose setup
- GitHub Actions CI/CD pipeline
- Pre-commit hooks with ruff + mypy + gitleaks

$ARGUMENTS
