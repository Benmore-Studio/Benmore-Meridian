---
name: django-production
description: Use when auditing Django codebases for production readiness or implementing production best practices with modern tooling (uv, ruff, pytest, Docker, drf-spectacular). Provides automated detection, gap analysis, and step-by-step implementation with ready-to-use configuration templates.
---

# Django Production Readiness Skill

## Overview

This skill transforms Django projects into production-ready applications with automated quality gates, security scanning, and fast developer feedback loops. It enables "vibe coding" with AI assistants while maintaining production quality through automation.

**Core Principles:**
1. **Fast feedback** - All checks run locally in <30 seconds
2. **Automated gates** - Catch issues before code review/CI
3. **Zero manual quality checks** - Everything is automated
4. **Modern tooling** - uv, ruff, pytest, Docker, drf-spectacular
5. **Production confidence** - Ship fast without breaking things

## When to Use This Skill

Invoke this skill when you encounter these situations:

**Symptoms of needing production readiness:**
- No pre-commit hooks or linting configured
- Using outdated tools (pip+requirements.txt, flake8, black separately)
- No automated testing or coverage tracking
- Secrets/credentials potentially in version control
- No Docker configuration or inconsistent local dev environments
- API documentation missing or outdated
- No CI/CD pipeline or manual deployment process
- Unclear how to validate changes locally before pushing

**Proactive use cases:**
- Starting a new Django project (set up correctly from day 1)
- Inheriting an existing Django codebase (audit current state)
- Preparing for production deployment (ensure all gates in place)
- Migrating from Django REST Framework to modern API practices
- Onboarding new developers (standardize local setup)

## Pre-Flight Check

Before implementing changes, run these detection commands to audit the current state:

```bash
# Check Python package management
ls pyproject.toml 2>/dev/null && echo "✓ pyproject.toml exists" || echo "✗ No pyproject.toml"
command -v uv >/dev/null && echo "✓ uv installed" || echo "✗ uv not installed"

# Check code quality tools
grep -q "ruff" pyproject.toml 2>/dev/null && echo "✓ ruff configured" || echo "✗ ruff not configured"
grep -q "mypy" pyproject.toml 2>/dev/null && echo "✓ mypy configured" || echo "✗ mypy not configured"
ls .pre-commit-config.yaml 2>/dev/null && echo "✓ pre-commit configured" || echo "✗ pre-commit not configured"

# Check testing
grep -q "pytest" pyproject.toml 2>/dev/null && echo "✓ pytest configured" || echo "✗ pytest not configured"
grep -q "pytest-django" pyproject.toml 2>/dev/null && echo "✓ pytest-django configured" || echo "✗ pytest-django not configured"
grep -q "pytest-cov" pyproject.toml 2>/dev/null && echo "✓ coverage configured" || echo "✗ coverage not configured"

# Check security
command -v gitleaks >/dev/null && echo "✓ gitleaks installed" || echo "✗ gitleaks not installed"
ls gitleaks.toml 2>/dev/null && echo "✓ gitleaks configured" || echo "✗ gitleaks not configured"
grep -q "django-environ\|python-decouple" requirements.txt pyproject.toml 2>/dev/null && echo "✓ env vars tool configured" || echo "✗ env vars tool not configured"

# Check Docker
ls Dockerfile 2>/dev/null && echo "✓ Dockerfile exists" || echo "✗ No Dockerfile"
ls docker-compose.yml 2>/dev/null && echo "✓ docker-compose exists" || echo "✗ No docker-compose.yml"

# Check API documentation (if DRF)
python -c "import rest_framework" 2>/dev/null && echo "✓ DRF installed" || echo "✗ DRF not installed"
grep -q "drf-spectacular" requirements.txt pyproject.toml 2>/dev/null && echo "✓ drf-spectacular configured" || echo "✗ drf-spectacular not configured"

# Check CI/CD
ls .github/workflows/*.yml 2>/dev/null && echo "✓ GitHub Actions configured" || echo "✗ No CI configured"

# Check Makefile
ls Makefile 2>/dev/null && echo "✓ Makefile exists" || echo "✗ No Makefile"
```

**Action:** Run this pre-flight check and create TodoWrite items for each ✗ (missing) item.

## Audit Checklist

Use TodoWrite to create tasks for each category below. Mark as `in_progress` when auditing, `completed` when verified.

### 1. Package Management
- [ ] Using `uv` (not pip/poetry/pipenv)
- [ ] `pyproject.toml` exists with proper dependencies
- [ ] `uv.lock` file present and up-to-date
- [ ] Dev dependencies separated from production

### 2. Code Quality Tools
- [ ] `ruff` configured (replaces black, flake8, pylint, isort)
- [ ] `mypy` or `pyright` for type checking
- [ ] Pre-commit hooks installed and running
- [ ] `.ruff.toml` or `[tool.ruff]` in pyproject.toml

### 3. Testing Infrastructure
- [ ] `pytest` + `pytest-django` configured
- [ ] `pytest-cov` for coverage tracking
- [ ] Coverage target ≥80% defined
- [ ] `factory_boy` or `model_bakery` for test fixtures
- [ ] Fixtures in `conftest.py`

### 4. Security
- [ ] `gitleaks` configured and running in pre-commit
- [ ] `django-environ` or `python-decouple` for env vars
- [ ] `.env.example` file exists
- [ ] No secrets in version control
- [ ] `DEBUG=False` in production settings
- [ ] `SECRET_KEY` from environment variable
- [ ] `ALLOWED_HOSTS` properly configured
- [ ] Security middleware enabled (HSTS, CSP, etc.)

### 5. Django Configuration
- [ ] Settings split (base.py, dev.py, prod.py)
- [ ] Database connection from env vars
- [ ] Static files configured (`STATIC_ROOT`, `MEDIA_ROOT`)
- [ ] CORS configured if needed (`django-cors-headers`)
- [ ] Session/cache backends configured

### 6. API Documentation (if DRF)
- [ ] `drf-spectacular` installed (not drf-yasg)
- [ ] Spectacular settings configured
- [ ] OpenAPI schema endpoint configured
- [ ] Swagger UI accessible at `/api/schema/swagger/`
- [ ] ReDoc accessible at `/api/schema/redoc/`

### 7. Docker Configuration
- [ ] `Dockerfile` exists with multi-stage build
- [ ] `docker-compose.yml` for local development
- [ ] `.dockerignore` file present
- [ ] Non-root user configured in container
- [ ] Health check endpoint configured

### 8. CI/CD
- [ ] GitHub Actions workflow exists
- [ ] Runs linting (ruff)
- [ ] Runs tests with coverage reporting
- [ ] Runs security scans (gitleaks, safety)
- [ ] Builds Docker image on main branch

### 9. Monitoring & Logging
- [ ] Sentry SDK installed and configured
- [ ] Structured logging (JSON format)
- [ ] Health check endpoint exists
- [ ] Performance monitoring configured

### 10. Makefile
- [ ] `Makefile` exists with common commands
- [ ] Fast validation loop (`make check`)
- [ ] Easy setup (`make install`, `make dev`)

## Implementation Phases (Priority Order)

Implement in this order for maximum impact with minimal effort.

### Phase 1: Package Management & Dev Environment (CRITICAL)

**Why first:** Everything else depends on proper dependency management.

**Steps:**
1. Install uv (if not present):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Create `pyproject.toml` (or migrate from requirements.txt):
   - See template at `~/.claude/skills/django-production/templates/pyproject.toml`
   - Copy template and adjust project name, Python version, dependencies

3. Initialize project:
   ```bash
   uv sync
   source .venv/bin/activate  # or: . .venv/bin/activate
   ```

**Validation:**
```bash
uv sync  # Should complete without errors
uv run python --version  # Should show Python 3.11+
```

### Phase 2: Code Quality Tools (HIGH PRIORITY)

**Why early:** Enables fast feedback loop for AI-first development.

**Steps:**
1. Configure ruff in `pyproject.toml`:
   - See template at `~/.claude/skills/django-production/templates/pyproject.toml`
   - Ruff replaces: black, flake8, pylint, isort, pyupgrade

2. Set up mypy for type checking:
   - Add `[tool.mypy]` section to pyproject.toml
   - Install django-stubs: `uv add --dev django-stubs mypy`

3. Create `.pre-commit-config.yaml`:
   - See template at `~/.claude/skills/django-production/templates/.pre-commit-config.yaml`
   - Install hooks: `uv run pre-commit install`

**Validation:**
```bash
uv run ruff check .  # Should run linting
uv run ruff format .  # Should format code
uv run mypy .  # Should run type checking
git commit --allow-empty -m "test"  # Pre-commit hooks should run
```

### Phase 3: Testing Infrastructure (HIGH PRIORITY)

**Why critical:** Core TDD workflow for quality assurance.

**Steps:**
1. Install pytest ecosystem:
   ```bash
   uv add --dev pytest pytest-django pytest-cov factory-boy
   ```

2. Configure pytest in `pyproject.toml`:
   ```toml
   [tool.pytest.ini_options]
   DJANGO_SETTINGS_MODULE = "config.settings.test"
   python_files = ["test_*.py", "*_test.py"]
   addopts = "--cov --cov-report=html --cov-report=term-missing"
   ```

3. Create `conftest.py` with common fixtures:
   ```python
   import pytest
   from django.contrib.auth import get_user_model

   User = get_user_model()

   @pytest.fixture
   def user(db):
       return User.objects.create_user(
           email="test@example.com",
           password="testpass123"
       )
   ```

4. Set up coverage configuration:
   ```toml
   [tool.coverage.run]
   source = ["."]
   omit = ["*/migrations/*", "*/tests/*", "*/venv/*", "*/.venv/*"]

   [tool.coverage.report]
   fail_under = 80
   show_missing = true
   ```

**Validation:**
```bash
uv run pytest  # Should run tests
uv run pytest --cov  # Should show coverage report
```

### Phase 4: Security Foundations (HIGH PRIORITY)

**Why critical:** Prevent credential leaks and security vulnerabilities.

**Steps:**
1. Install gitleaks:
   ```bash
   brew install gitleaks  # macOS
   # or download from: https://github.com/gitleaks/gitleaks/releases
   ```

2. Create `gitleaks.toml`:
   - See template at `~/.claude/skills/django-production/templates/gitleaks.toml`

3. Add gitleaks to pre-commit hooks:
   - Already included in `.pre-commit-config.yaml` template

4. Set up environment variable management:
   ```bash
   uv add django-environ
   ```

5. Create `.env.example`:
   - See template at `~/.claude/skills/django-production/templates/.env.example`
   - Copy to `.env` and fill in actual values
   - Add `.env` to `.gitignore`

6. Update Django settings to use env vars:
   ```python
   import environ

   env = environ.Env()
   environ.Env.read_env()  # Read .env file

   SECRET_KEY = env("SECRET_KEY")
   DEBUG = env.bool("DEBUG", default=False)
   ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
   ```

**Validation:**
```bash
gitleaks detect --source . --verbose  # Should find no secrets
uv run python manage.py check --deploy  # Should pass security checks
```

### Phase 5: Django Production Settings (HIGH PRIORITY)

**Why required:** Production deployment depends on proper settings structure.

**Steps:**
1. Split settings into modules:
   ```
   config/
   └── settings/
       ├── __init__.py
       ├── base.py       # Shared settings
       ├── dev.py        # Development overrides
       └── prod.py       # Production overrides
   ```

2. Copy templates:
   - `~/.claude/skills/django-production/templates/settings/base.py`
   - `~/.claude/skills/django-production/templates/settings/dev.py`
   - `~/.claude/skills/django-production/templates/settings/prod.py`

3. Update environment-specific settings:
   - Database connection pooling
   - Static files (whitenoise or cloud storage)
   - Security headers (HSTS, CSP, X-Frame-Options)
   - Session/cache backends

**Validation:**
```bash
DJANGO_SETTINGS_MODULE=config.settings.prod uv run python manage.py check --deploy
# Should pass all deployment checks
```

### Phase 6: API Documentation (MEDIUM PRIORITY - if DRF)

**Why valuable:** Improves developer experience and API discoverability.

**Steps:**
1. Install drf-spectacular:
   ```bash
   uv add drf-spectacular
   ```

2. Add to `INSTALLED_APPS` in settings:
   ```python
   INSTALLED_APPS = [
       # ...
       'drf_spectacular',
   ]
   ```

3. Configure REST framework to use spectacular:
   ```python
   REST_FRAMEWORK = {
       'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
   }
   ```

4. Add spectacular settings:
   ```python
   SPECTACULAR_SETTINGS = {
       'TITLE': 'Your API',
       'DESCRIPTION': 'API description',
       'VERSION': '1.0.0',
       'SERVE_INCLUDE_SCHEMA': False,
   }
   ```

5. Add URL patterns:
   ```python
   from drf_spectacular.views import (
       SpectacularAPIView,
       SpectacularSwaggerView,
       SpectacularRedocView,
   )

   urlpatterns = [
       path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
       path('api/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
       path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
   ]
   ```

6. Document API endpoints with decorators:
   ```python
   from drf_spectacular.utils import extend_schema

   @extend_schema(
       summary="List all users",
       description="Returns a paginated list of all users",
       responses={200: UserSerializer(many=True)}
   )
   def list(self, request):
       # ...
   ```

**Validation:**
```bash
uv run python manage.py spectacular --file schema.yml  # Generate schema
# Visit: http://localhost:8000/api/schema/swagger/
# Visit: http://localhost:8000/api/schema/redoc/
```

**DRF-Spectacular Flow Diagram:**
```
User Request
    ↓
Django URL Router
    ↓
DRF View/ViewSet ← drf-spectacular auto-inspects
    ↓                - Serializers
    ↓                - Docstrings
    ↓                - Type hints
    ↓                - @extend_schema decorators
    ↓
OpenAPI Schema Generation
    ↓
    ├─→ Swagger UI (/api/schema/swagger/)
    ├─→ ReDoc (/api/schema/redoc/)
    └─→ OpenAPI JSON/YAML (/api/schema/)
```

### Phase 7: Docker Configuration (MEDIUM PRIORITY)

**Why important:** Ensures consistent environments and production readiness.

**Steps:**
1. Create multi-stage `Dockerfile`:
   - See template at `~/.claude/skills/django-production/templates/Dockerfile`
   - Uses uv for fast dependency installation
   - Non-root user for security
   - Multi-stage build for smaller images

2. Create `docker-compose.yml` for local dev:
   - See template at `~/.claude/skills/django-production/templates/docker-compose.yml`
   - Includes Django app, PostgreSQL, Redis

3. Create `.dockerignore`:
   ```
   .git
   .venv
   __pycache__
   *.pyc
   *.pyo
   *.pyd
   .Python
   env
   .env
   .coverage
   htmlcov
   ```

4. Add health check endpoint to Django:
   ```python
   # urls.py
   from django.http import JsonResponse

   def health_check(request):
       return JsonResponse({"status": "healthy"})

   urlpatterns = [
       path('health/', health_check),
       # ...
   ]
   ```

**Validation:**
```bash
docker build -t myapp:latest .  # Should build successfully
docker run --rm myapp:latest python manage.py check  # Should pass
docker-compose up -d  # Should start all services
docker-compose ps  # All services should be healthy
```

### Phase 8: CI/CD Pipeline (MEDIUM PRIORITY)

**Why important:** Automates validation and catches issues before deployment.

**Steps:**
1. Create `.github/workflows/ci.yml`:
   - See template at `~/.claude/skills/django-production/templates/github-actions-ci.yml`
   - Runs linting, type checking, tests, security scans
   - Builds Docker image
   - Reports coverage

2. Configure secrets in GitHub:
   - `DOCKER_USERNAME` and `DOCKER_PASSWORD` (if pushing images)
   - Any other deployment credentials

**Validation:**
```bash
# Push to GitHub and verify:
# 1. CI workflow runs automatically
# 2. All jobs pass (lint, test, security, build)
# 3. Coverage report uploaded
# 4. Docker image builds successfully
```

### Phase 9: Monitoring & Observability (LOW PRIORITY - post-deployment)

**Why later:** Important for production operations, but not blocking initial deployment.

**Steps:**
1. Install Sentry SDK:
   ```bash
   uv add sentry-sdk
   ```

2. Configure Sentry in settings:
   ```python
   import sentry_sdk
   from sentry_sdk.integrations.django import DjangoIntegration

   sentry_sdk.init(
       dsn=env("SENTRY_DSN"),
       integrations=[DjangoIntegration()],
       traces_sample_rate=1.0,
       send_default_pii=True,
   )
   ```

3. Set up structured logging:
   ```python
   LOGGING = {
       'version': 1,
       'disable_existing_loggers': False,
       'formatters': {
           'json': {
               'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
               'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
           },
       },
       'handlers': {
           'console': {
               'class': 'logging.StreamHandler',
               'formatter': 'json',
           },
       },
       'root': {
           'level': 'INFO',
           'handlers': ['console'],
       },
   }
   ```

4. Create monitoring endpoints:
   - Health check: `/health/`
   - Readiness check: `/ready/`
   - Metrics: `/metrics/` (if using Prometheus)

**Validation:**
```bash
# Trigger test Sentry error
uv run python -c "import sentry_sdk; sentry_sdk.init(); 1/0"
# Check Sentry dashboard for event
```

## Makefile - Fast Local Validation

Create a `Makefile` with these commands for instant feedback:

See full template at: `~/.claude/skills/django-production/templates/Makefile`

**Essential commands:**
```makefile
.PHONY: install dev test lint format typecheck security-scan check

install:  ## Install all dependencies
	uv sync

dev:  ## Run development server
	uv run python manage.py runserver

test:  ## Run tests
	uv run pytest

lint:  ## Lint code
	uv run ruff check .

format:  ## Format code
	uv run ruff format .

typecheck:  ## Type check
	uv run mypy .

security-scan:  ## Run security scans
	gitleaks detect --source . --verbose
	uv run safety check

check: format lint typecheck test security-scan  ## Run all checks
	@echo "✅ All checks passed!"
```

**Usage:**
```bash
make install  # Setup project
make dev      # Start development
make check    # Validate before commit (< 30 seconds)
```

## Verification & Validation

After implementing all phases, verify the setup:

### Local Verification
```bash
# 1. Install and setup
make install

# 2. Run all checks
make check
# Should pass: formatting, linting, type checking, tests, security

# 3. Test pre-commit hooks
git commit --allow-empty -m "test"
# Should run: ruff, mypy, gitleaks, pytest

# 4. Test Docker build
docker build -t myapp:latest .
# Should build successfully

# 5. Check Django deployment settings
DJANGO_SETTINGS_MODULE=config.settings.prod make check
# Should pass all deployment checks

# 6. Verify API docs (if DRF)
make dev
# Visit: http://localhost:8000/api/schema/swagger/
# Should load Swagger UI with all endpoints
```

### CI/CD Verification
```bash
# Push to GitHub
git push

# Verify in GitHub Actions:
# ✓ Lint job passes
# ✓ Test job passes (with coverage report)
# ✓ Security job passes
# ✓ Build job passes (Docker image)
```

### Production Readiness Checklist
- [ ] All local checks pass (`make check`)
- [ ] Pre-commit hooks run on every commit
- [ ] Tests pass with ≥80% coverage
- [ ] No secrets in version control (gitleaks passes)
- [ ] Docker image builds successfully
- [ ] CI/CD pipeline passes on main branch
- [ ] API documentation loads (if DRF)
- [ ] Django deployment check passes
- [ ] Health check endpoint responds
- [ ] Sentry captures test errors (if configured)

## Troubleshooting

### Common Issues

**Issue: uv not found**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# Add to PATH (follow installation instructions)
```

**Issue: Pre-commit hooks not running**
```bash
# Reinstall hooks
uv run pre-commit install
# Test manually
uv run pre-commit run --all-files
```

**Issue: Tests failing with "No module named 'config'"**
```bash
# Ensure DJANGO_SETTINGS_MODULE is set correctly
export DJANGO_SETTINGS_MODULE=config.settings.test
# Or add to pyproject.toml [tool.pytest.ini_options]
```

**Issue: Gitleaks finding false positives**
```bash
# Add to gitleaks.toml [allowlist] section
paths = [
  '''\.env\.example$''',  # Allow .env.example
  '''tests/fixtures/.*'''   # Allow test fixtures
]
```

**Issue: Docker build failing with permission errors**
```bash
# Ensure non-root user has correct permissions in Dockerfile
RUN chown -R django:django /app
USER django
```

**Issue: DRF-Spectacular not generating schema**
```bash
# Ensure drf-spectacular is in INSTALLED_APPS
# Ensure REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS'] is set
# Run: python manage.py spectacular --validate
```

**Issue: mypy errors with Django models**
```bash
# Install django-stubs
uv add --dev django-stubs
# Add to pyproject.toml:
[tool.mypy]
plugins = ["mypy_django_plugin.main"]

[tool.django-stubs]
django_settings_module = "config.settings"
```

## Success Criteria

This skill has succeeded if:

1. ✅ All local checks run in <30 seconds (`make check`)
2. ✅ Pre-commit hooks catch issues before commit
3. ✅ Tests pass with ≥80% coverage
4. ✅ No secrets in version control
5. ✅ CI/CD provides fast feedback (<5 minutes)
6. ✅ Docker containers build and run successfully
7. ✅ API documentation is auto-generated and accessible
8. ✅ Production deployment is confident and safe
9. ✅ New developers can set up in <5 minutes (`make install && make dev`)
10. ✅ AI coding assistants can iterate quickly with automated safety

## Template Files

All configuration templates are available at:
- `~/.claude/skills/django-production/templates/`

Key templates:
- `pyproject.toml` - Complete uv + ruff + pytest + mypy config
- `Makefile` - Fast local validation commands
- `Dockerfile` - Multi-stage production build
- `docker-compose.yml` - Local development environment
- `.pre-commit-config.yaml` - Pre-commit hooks
- `.env.example` - Environment variables template
- `gitleaks.toml` - Secret scanning configuration
- `github-actions-ci.yml` - CI/CD pipeline
- `settings/base.py`, `settings/dev.py`, `settings/prod.py` - Django settings

## Next Steps After Implementation

1. **Run `make check`** - Ensure all local validation passes
2. **Commit changes** - Pre-commit hooks will validate automatically
3. **Push to GitHub** - CI/CD will run full validation
4. **Monitor Sentry** - Set up error tracking for production
5. **Document team workflow** - Add README with development instructions
6. **Iterate and improve** - Adjust coverage targets, add more tests

## References

- **uv**: https://github.com/astral-sh/uv
- **ruff**: https://github.com/astral-sh/ruff
- **pytest**: https://docs.pytest.org/
- **drf-spectacular**: https://drf-spectacular.readthedocs.io/
- **gitleaks**: https://github.com/gitleaks/gitleaks
- **Django security checklist**: https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/
