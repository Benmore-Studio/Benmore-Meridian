# Django Production Readiness Checklist

> **Comprehensive guide for productionizing Django applications with modern tooling, automated quality gates, and fast developer feedback loops.**

**Last Updated:** January 2026
**Django Version:** 5.0+
**Python Version:** 3.11+

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Package Management (uv)](#package-management-uv)
4. [Code Quality (ruff + mypy)](#code-quality-ruff--mypy)
5. [Testing (pytest)](#testing-pytest)
6. [Security (gitleaks + django-environ)](#security-gitleaks--django-environ)
7. [Django Settings Structure](#django-settings-structure)
8. [API Documentation (drf-spectacular)](#api-documentation-drf-spectacular)
9. [Docker Configuration](#docker-configuration)
10. [CI/CD Pipeline (GitHub Actions)](#cicd-pipeline-github-actions)
11. [Monitoring & Logging (Sentry)](#monitoring--logging-sentry)
12. [Makefile Commands](#makefile-commands)
13. [Verification Steps](#verification-steps)
14. [Troubleshooting](#troubleshooting)

---

## Overview

This checklist transforms Django projects into production-ready applications with:

**Core Principles:**
- **Fast feedback** - All checks run locally in <30 seconds
- **Automated gates** - Catch issues before code review/CI
- **Zero manual quality checks** - Everything is automated
- **Modern tooling** - uv, ruff, pytest, Docker, drf-spectacular
- **Production confidence** - Ship fast without breaking things

**Technology Stack:**
- **Package Manager:** uv (10-100x faster than pip/poetry)
- **Linting & Formatting:** ruff (replaces black, flake8, isort, pylint, pyupgrade)
- **Type Checking:** mypy with django-stubs
- **Testing:** pytest + pytest-django + pytest-cov
- **Security:** gitleaks (secret scanning) + django-environ
- **API Docs:** drf-spectacular (OpenAPI 3.0)
- **Containers:** Docker multi-stage builds
- **CI/CD:** GitHub Actions
- **Monitoring:** Sentry

---

## Quick Start

**5-Minute Production Setup:**

```bash
# 1. Install modern tooling
curl -LsSf https://astral.sh/uv/install.sh | sh
brew install gitleaks  # or download from GitHub releases

# 2. Initialize project
uv init  # Creates pyproject.toml
uv add django djangorestframework drf-spectacular django-environ gunicorn whitenoise sentry-sdk
uv add --dev pytest pytest-django pytest-cov ruff mypy django-stubs pre-commit

# 3. Set up quality gates
uv run pre-commit install

# 4. Create configuration files (see templates below)
# - pyproject.toml (dependencies + tool configs)
# - Makefile (fast commands)
# - .pre-commit-config.yaml (hooks)
# - .env.example (environment variables)
# - gitleaks.toml (secret scanning)

# 5. Run local validation
make check  # < 30 seconds

# 6. Ready to develop!
make dev
```

---

## Package Management (uv)

### Why uv?

- **10-100x faster** than pip/poetry
- **Compatible** with pip standards (pyproject.toml)
- **Automatic** virtual environment management
- **Modern** Rust-based tool with active development

### Installation

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

### Configuration (pyproject.toml)

Create a comprehensive `pyproject.toml`:

```toml
[project]
name = "myproject"
version = "0.1.0"
description = "Django project with production-ready configuration"
requires-python = ">=3.11"
dependencies = [
    "django>=5.0.0,<6.0.0",
    "django-environ>=0.11.0",
    "psycopg[binary]>=3.1.0",
    "djangorestframework>=3.14.0",
    "drf-spectacular>=0.27.0",
    "django-cors-headers>=4.3.0",
    "gunicorn>=21.0.0",
    "whitenoise>=6.6.0",
    "sentry-sdk>=1.40.0",
    "python-json-logger>=2.0.7",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.2.0",
    "mypy>=1.8.0",
    "django-stubs>=4.2.7",
    "djangorestframework-stubs>=3.14.5",
    "pre-commit>=3.6.0",
]

test = [
    "pytest>=8.0.0",
    "pytest-django>=4.7.0",
    "pytest-cov>=4.1.0",
    "pytest-xdist>=3.5.0",
    "factory-boy>=3.3.0",
    "faker>=22.0.0",
    "freezegun>=1.4.0",
    "safety>=3.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Common Commands

```bash
uv sync                    # Install dependencies
uv sync --all-groups       # Install all dependency groups
uv add django              # Add production dependency
uv add --dev pytest        # Add dev dependency
uv run python manage.py    # Run Django commands
uv run pytest              # Run tests
uv lock --upgrade          # Update dependencies
```

---

## Code Quality (ruff + mypy)

### Ruff Configuration

Ruff replaces 5+ tools: black, flake8, isort, pylint, pyupgrade.

**Add to pyproject.toml:**

```toml
[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "DJ",   # flake8-django
    "SIM",  # flake8-simplify
    "ARG",  # flake8-unused-arguments
    "S",    # bandit (security)
]

ignore = [
    "E501",   # line too long
    "B008",   # function calls in defaults
    "S101",   # use of assert
]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]
"*/migrations/*.py" = ["ALL"]
"*/tests/*.py" = ["S101", "ARG"]

[tool.ruff.lint.isort]
known-first-party = ["config", "apps"]
```

**Commands:**

```bash
uv run ruff check .         # Lint
uv run ruff check --fix .   # Lint + auto-fix
uv run ruff format .        # Format
```

### Mypy Configuration

**Add to pyproject.toml:**

```toml
[tool.mypy]
python_version = "3.11"
plugins = ["mypy_django_plugin.main", "mypy_drf_plugin.main"]
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[[tool.mypy.overrides]]
module = "*.migrations.*"
ignore_errors = true

[tool.django-stubs]
django_settings_module = "config.settings"
```

**Commands:**

```bash
uv run mypy .  # Type check all files
```

---

## Testing (pytest)

### Pytest Configuration

**Add to pyproject.toml:**

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.test"
python_files = ["test_*.py", "*_test.py", "tests.py"]
addopts = [
    "--cov",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--strict-markers",
    "--reuse-db",
    "-n", "auto",  # Parallel testing
]
testpaths = ["tests"]
markers = [
    "slow: slow tests",
    "integration: integration tests",
    "unit: unit tests",
]

[tool.coverage.run]
source = ["."]
omit = ["*/migrations/*", "*/tests/*", "*/venv/*"]
branch = true

[tool.coverage.report]
fail_under = 80
show_missing = true
```

### Test Structure

```
project/
├── tests/
│   ├── conftest.py         # Shared fixtures
│   ├── test_models.py
│   ├── test_views.py
│   └── test_api.py
```

**Example conftest.py:**

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

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()
```

**Commands:**

```bash
uv run pytest                     # Run all tests
uv run pytest --cov               # With coverage
uv run pytest -x --ff             # Fast mode (fail fast, last failed first)
uv run pytest -n auto             # Parallel
uv run pytest -m unit             # Only unit tests
uv run pytest -k "test_user"      # Filter by name
```

---

## Security (gitleaks + django-environ)

### Gitleaks (Secret Scanning)

**Installation:**

```bash
# macOS
brew install gitleaks

# Linux
wget https://github.com/gitleaks/gitleaks/releases/download/v8.18.1/gitleaks_8.18.1_linux_x64.tar.gz
tar -xzf gitleaks_8.18.1_linux_x64.tar.gz
sudo mv gitleaks /usr/local/bin/
```

**Configuration (gitleaks.toml):**

```toml
title = "Gitleaks Configuration"

[extend]
useDefault = true

[[rules]]
id = "django-secret-key"
description = "Django SECRET_KEY"
regex = '''SECRET_KEY\s*=\s*['\"]([^'\"]{20,})['\"]'''
tags = ["key", "django"]

[[rules]]
id = "aws-access-key"
description = "AWS Access Key"
regex = '''(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}'''
tags = ["key", "AWS"]

[allowlist]
paths = [
    '''\.env\.example$''',
    '''^tests/fixtures/.*''',
]

[[allowlist.regexes]]
regex = '''SECRET_KEY\s*=\s*['\"]django-insecure-.*['\"]'''
```

**Commands:**

```bash
gitleaks detect --source . --verbose  # Scan for secrets
```

### Django-Environ (Environment Variables)

**Installation:**

```bash
uv add django-environ
```

**Configuration:**

1. Create `.env.example`:

```bash
SECRET_KEY=change-me-to-a-random-50-character-string
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

2. Update `settings/base.py`:

```python
import environ

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env()

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
DATABASES = {"default": env.db("DATABASE_URL")}
```

3. Add `.env` to `.gitignore`:

```bash
echo ".env" >> .gitignore
```

---

## Django Settings Structure

### Split Settings

```
config/
└── settings/
    ├── __init__.py
    ├── base.py       # Shared settings
    ├── dev.py        # Development
    ├── prod.py       # Production
    └── test.py       # Testing
```

### base.py (Shared Settings)

**Key sections:**

```python
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# Database with connection pooling
DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["CONN_MAX_AGE"] = 60

# Static files with whitenoise
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# DRF configuration
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
}

# DRF-Spectacular
SPECTACULAR_SETTINGS = {
    "TITLE": "My API",
    "DESCRIPTION": "API documentation",
    "VERSION": "1.0.0",
}
```

### dev.py (Development)

```python
from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += [
    "django_extensions",
    "debug_toolbar",
]

MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
INTERNAL_IPS = ["127.0.0.1"]
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

### prod.py (Production)

```python
from .base import *
from .base import env
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Sentry
sentry_sdk.init(
    dsn=env("SENTRY_DSN"),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    environment="production",
)
```

### test.py (Testing)

```python
from .base import *

SECRET_KEY = "django-insecure-test-key"
DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
```

---

## API Documentation (drf-spectacular)

### Why drf-spectacular?

- **OpenAPI 3.0** (not 2.0/Swagger)
- **Official DRF recommendation**
- **Better type hints support**
- **Active maintenance**

### Installation

```bash
uv add drf-spectacular
```

### Configuration

**1. Add to INSTALLED_APPS:**

```python
INSTALLED_APPS = [
    # ...
    'drf_spectacular',
]
```

**2. Configure REST Framework:**

```python
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Your API',
    'DESCRIPTION': 'API description',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
```

**3. Add URLs:**

```python
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema')),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema')),
]
```

**4. Document endpoints:**

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

### Commands

```bash
uv run python manage.py spectacular --file schema.yml  # Generate schema
```

### Access Documentation

- **Swagger UI:** http://localhost:8000/api/schema/swagger/
- **ReDoc:** http://localhost:8000/api/schema/redoc/
- **OpenAPI Schema:** http://localhost:8000/api/schema/

---

## Docker Configuration

### Dockerfile (Multi-Stage Build)

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder

RUN apt-get update && apt-get install -y build-essential libpq-dev curl
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Stage 2: Runtime
FROM python:3.11-slim

RUN apt-get update && apt-get install -y libpq5

RUN groupadd -r django && useradd -r -g django django
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --chown=django:django . /app/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod

USER django

RUN python manage.py collectstatic --noinput

HEALTHCHECK --interval=30s --timeout=3s \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/')"

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "config.wsgi:application"]
```

### docker-compose.yml

```yaml
version: '3.9'

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    command: uv run python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/myapp
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

### Commands

```bash
docker build -t myapp:latest .          # Build image
docker-compose up -d                    # Start services
docker-compose down                     # Stop services
docker-compose logs -f                  # View logs
docker-compose exec web bash            # Shell access
```

---

## CI/CD Pipeline (GitHub Actions)

### Configuration (.github/workflows/ci.yml)

```yaml
name: CI

on: [push, pull_request]

env:
  PYTHON_VERSION: '3.11'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v2
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - run: uv sync --all-groups
      - run: uv run ruff check .
      - run: uv run ruff format --check .

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v2
      - uses: actions/setup-python@v5
      - run: uv sync --all-groups
      - run: uv run mypy .

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
    env:
      DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v2
      - uses: actions/setup-python@v5
      - run: uv sync --all-groups
      - run: uv run pytest --cov --cov-report=xml
      - uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
      - uses: astral-sh/setup-uv@v2
      - run: uv run safety check || true

  docker:
    runs-on: ubuntu-latest
    needs: [lint, typecheck, test, security]
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          tags: myapp:${{ github.sha }}
```

---

## Monitoring & Logging (Sentry)

### Installation

```bash
uv add sentry-sdk python-json-logger
```

### Configuration

**settings/prod.py:**

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=env("SENTRY_DSN"),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False,
    environment=env("SENTRY_ENVIRONMENT", default="production"),
)
```

### Structured Logging

```python
LOGGING = {
    "version": 1,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
}
```

---

## Makefile Commands

**Complete Makefile for fast local validation:**

```makefile
.DEFAULT_GOAL := help
PYTHON := uv run python
MANAGE := $(PYTHON) manage.py

##@ Development
.PHONY: install
install: ## Install dependencies
	uv sync --all-groups
	uv run pre-commit install

.PHONY: dev
dev: ## Run development server
	$(MANAGE) runserver

##@ Code Quality
.PHONY: lint
lint: ## Lint code
	uv run ruff check .

.PHONY: format
format: ## Format code
	uv run ruff check --fix .
	uv run ruff format .

.PHONY: typecheck
typecheck: ## Type check
	uv run mypy .

##@ Testing
.PHONY: test
test: ## Run tests
	$(PYTHON) -m pytest

.PHONY: test-cov
test-cov: ## Run tests with coverage
	$(PYTHON) -m pytest --cov --cov-report=html

##@ Security
.PHONY: security-scan
security-scan: ## Run security scans
	gitleaks detect --source . --verbose
	uv run safety check

##@ All Checks
.PHONY: check-all
check-all: format lint typecheck test security-scan ## Run ALL checks
	@echo "✅ All checks passed!"

.PHONY: help
help: ## Display help
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?##/ { printf "  %-20s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
```

**Usage:**

```bash
make install        # Setup project
make dev            # Start development
make check-all      # Full validation (<30s)
make test-cov       # Tests with coverage
```

---

## Verification Steps

### Local Verification Checklist

- [ ] `make install` succeeds
- [ ] `make check-all` passes (<30 seconds)
- [ ] Pre-commit hooks run on commit
- [ ] Tests pass with ≥80% coverage
- [ ] No secrets detected by gitleaks
- [ ] Docker image builds successfully
- [ ] API docs load at `/api/schema/swagger/`
- [ ] `python manage.py check --deploy` passes

### Commands

```bash
# Full local validation
make install
make check-all

# Test pre-commit hooks
git commit --allow-empty -m "test"

# Docker validation
docker build -t myapp:latest .
docker run --rm myapp:latest python manage.py check

# Production checks
DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py check --deploy
```

---

## Troubleshooting

### Issue: uv not found

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Add to PATH: export PATH="$HOME/.cargo/bin:$PATH"
```

### Issue: Pre-commit hooks not running

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

### Issue: Tests failing with "No module named 'config'"

```bash
export DJANGO_SETTINGS_MODULE=config.settings.test
# Or add to pyproject.toml [tool.pytest.ini_options]
```

### Issue: Gitleaks false positives

Add to `gitleaks.toml` allowlist:

```toml
[allowlist]
paths = ['''\.env\.example$''', '''tests/fixtures/.*''']
```

### Issue: mypy errors with Django models

```bash
uv add --dev django-stubs
# Add to pyproject.toml:
[tool.mypy]
plugins = ["mypy_django_plugin.main"]
```

---

## Next Steps

After completing this checklist:

1. **Run `make check-all`** - Ensure all validation passes
2. **Commit changes** - Pre-commit hooks validate automatically
3. **Push to GitHub** - CI/CD runs full validation
4. **Monitor Sentry** - Set up error tracking
5. **Document workflow** - Add README with setup instructions
6. **Iterate** - Adjust coverage targets, add more tests

---

## Additional Resources

- **uv:** https://github.com/astral-sh/uv
- **ruff:** https://github.com/astral-sh/ruff
- **pytest:** https://docs.pytest.org/
- **drf-spectacular:** https://drf-spectacular.readthedocs.io/
- **gitleaks:** https://github.com/gitleaks/gitleaks
- **Django deployment checklist:** https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

---

**Questions or issues?** Open an issue or reach out for support!
