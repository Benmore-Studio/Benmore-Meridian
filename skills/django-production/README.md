# Django Production Readiness Skill

**Version:** 1.0.0
**Created:** January 2026
**Django Version:** 5.0+
**Python Version:** 3.11+

## Overview

A comprehensive Claude Code skill for auditing and productionizing Django applications with automated quality gates, security scanning, and fast developer feedback loops.

## Files Included

### Main Skill File
- **SKILL.md** - The main invocable skill file with audit logic, implementation phases, and verification steps

### Configuration Templates

#### Package Management
- **pyproject.toml** - Complete uv + ruff + pytest + mypy configuration

#### Development Tools
- **Makefile** - Fast local validation commands (<30s full check)
- **.pre-commit-config.yaml** - Pre-commit hooks (ruff, mypy, gitleaks)

#### Docker & Deployment
- **Dockerfile** - Multi-stage production build with uv
- **docker-compose.yml** - Local development environment (Django, PostgreSQL, Redis)

#### CI/CD
- **github-actions-ci.yml** - GitHub Actions workflow (lint, test, security, build)

#### Security
- **.env.example** - Environment variable template
- **gitleaks.toml** - Secret scanning configuration

#### Django Settings
- **settings/__init__.py** - Settings package initializer
- **settings/base.py** - Shared Django settings
- **settings/dev.py** - Development environment overrides
- **settings/prod.py** - Production environment with security hardening
- **settings/test.py** - Test environment (fast, isolated)

## How to Use

### For AI Assistants (Claude Code)

Invoke the skill programmatically:

```python
# In Claude Code
invoke_skill("django-production")
```

Or reference the skill by name when working on Django projects.

### For Humans

1. **Read the skill file:** `~/.claude/skills/django-production/SKILL.md`
2. **Copy templates:** Copy relevant templates to your Django project
3. **Follow implementation phases:** Complete in priority order (1-9)
4. **Verify setup:** Run `make check-all` to validate

## Standalone Guide

A comprehensive standalone guide is also available at:
- **Location:** `/Users/arkashjain/Desktop/guides/django-production-checklist.md`
- **Size:** 22KB
- **Format:** Markdown with inline examples

This guide can be used independently of the skill and includes:
- Complete configuration examples
- Step-by-step instructions
- Troubleshooting section
- All templates inline

## Key Features

### Fast Feedback Loop
- All checks run in <30 seconds locally
- Pre-commit hooks catch issues before commit
- CI/CD provides fast feedback (<5 minutes)

### Modern Tooling
- **uv:** 10-100x faster than pip/poetry
- **ruff:** Replaces black, flake8, isort, pylint, pyupgrade
- **mypy:** Strict type checking with django-stubs
- **pytest:** Fast parallel testing with coverage
- **gitleaks:** Secret detection in pre-commit and CI
- **drf-spectacular:** OpenAPI 3.0 API documentation

### Automated Quality Gates
- Formatting (ruff)
- Linting (ruff)
- Type checking (mypy)
- Testing (pytest with 80%+ coverage)
- Security scanning (gitleaks, safety)
- Django checks (migrations, deployment)

### Production Readiness
- Docker multi-stage builds
- Security-hardened settings (HSTS, CSP, etc.)
- Structured JSON logging
- Sentry error tracking
- Database connection pooling
- Static file serving (whitenoise)

## Success Criteria

The skill has succeeded if:

1. ✅ All local checks run in <30 seconds (`make check-all`)
2. ✅ Pre-commit hooks catch issues before commit
3. ✅ Tests pass with ≥80% coverage
4. ✅ No secrets in version control
5. ✅ CI/CD provides fast feedback (<5 minutes)
6. ✅ Docker containers build and run successfully
7. ✅ API documentation is auto-generated and accessible
8. ✅ Production deployment is confident and safe
9. ✅ New developers can set up in <5 minutes
10. ✅ AI coding assistants can iterate quickly with automated safety

## Template Usage

All templates can be copied directly to your project:

```bash
# Example: Copy pyproject.toml
cp ~/.claude/skills/django-production/templates/pyproject.toml ./

# Example: Copy all Django settings
cp -r ~/.claude/skills/django-production/templates/settings ./config/

# Example: Copy Makefile
cp ~/.claude/skills/django-production/templates/Makefile ./
```

## Verification Commands

After implementation, verify the setup:

```bash
# Install and setup
make install

# Run all checks
make check-all

# Test pre-commit hooks
git commit --allow-empty -m "test"

# Test Docker build
docker build -t myapp:latest .

# Check Django deployment settings
DJANGO_SETTINGS_MODULE=config.settings.prod make check

# Verify API docs (if DRF)
make dev  # Visit http://localhost:8000/api/schema/swagger/
```

## Integration with Claude Code

This skill is designed to work seamlessly with Claude Code:

1. **Automatic Detection:** The skill detects Django projects and offers to audit/productionize
2. **TodoWrite Integration:** Creates tasks for each audit category and implementation phase
3. **Template Injection:** Provides ready-to-use configuration templates
4. **Validation Guidance:** Guides through verification steps to ensure setup works

## Additional Resources

- **Django Deployment Checklist:** https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/
- **uv Documentation:** https://github.com/astral-sh/uv
- **ruff Documentation:** https://github.com/astral-sh/ruff
- **pytest Documentation:** https://docs.pytest.org/
- **drf-spectacular Documentation:** https://drf-spectacular.readthedocs.io/
- **gitleaks Documentation:** https://github.com/gitleaks/gitleaks

## License

This skill and all templates are provided as-is for use in Django projects.

## Contributing

To improve this skill:

1. Test on real Django projects
2. Identify gaps or issues
3. Update templates with best practices
4. Add new phases as Django/tooling evolves

## Changelog

### Version 1.0.0 (January 2026)
- Initial release
- 14 configuration templates
- 9 implementation phases
- Comprehensive standalone guide
- Full CI/CD pipeline
- Docker multi-stage builds
- DRF-Spectacular integration
- Sentry monitoring setup
