# Django Production Checklist ✅

**Total Time:** 45-60 minutes | **Django 5.0+ | Python 3.11+**

> **Print this and check off boxes as you complete them.** All checks run in <30 seconds when done.

---

## 📦 Phase 1: Modern Tooling Setup (10 min) - CRITICAL

### Install Core Tools

```bash
# Install uv (10-100x faster than pip)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install gitleaks (secret scanner)
brew install gitleaks  # macOS
# Linux: https://github.com/gitleaks/gitleaks/releases

# Verify installations
uv --version
gitleaks version
```

- [ ] uv installed and working
- [ ] gitleaks installed and working

### Initialize Project

```bash
# Option A: Using uv (recommended)
uv sync --all-groups

# Option B: Fallback to pip
uv venv --python 3.12
source .venv/bin/activate
pip install -r requirements.txt
```

- [ ] Virtual environment created
- [ ] Virtual environment activated (`source .venv/bin/activate`)

### Install Dependencies

```bash
# Core dependencies
uv add django-environ djangorestframework drf-spectacular gunicorn whitenoise sentry-sdk

# Development dependencies
uv add --dev pytest pytest-django pytest-cov ruff mypy django-stubs pre-commit factory-boy
```

- [ ] Core dependencies installed
- [ ] Dev dependencies installed
- [ ] Can run `python -c "import django; print(django.VERSION)"`

---

## 📝 Phase 2: Configuration Files (10 min) - CRITICAL

### Create Essential Files

Copy these templates from `~/.claude/skills/django-production/templates/`:

**Core configs:**
- [ ] `pyproject.toml` - Dependencies, ruff, pytest, mypy, coverage
- [ ] `Makefile` - Fast commands (`make check-all`)
- [ ] `.pre-commit-config.yaml` - Pre-commit hooks
- [ ] `.env.example` - Environment variable template
- [ ] `gitleaks.toml` - Secret scanning config

**Verify pyproject.toml includes:**
- [ ] Ruff configuration (`[tool.ruff]`)
- [ ] Pytest configuration (`[tool.pytest.ini_options]`)
- [ ] Mypy configuration (`[tool.mypy]`)
- [ ] Coverage configuration (`[tool.coverage.run]`, `[tool.coverage.report]`)

---

## 🔐 Phase 3: Security Setup (10 min) - CRITICAL

### Environment Variables

```bash
# Create .env from example
cp .env.example .env

# Add to .gitignore
echo ".env" >> .gitignore
```

- [ ] `.env.example` exists (template for team)
- [ ] `.env` exists (your actual secrets)
- [ ] `.env` in `.gitignore`
- [ ] `gitleaks.toml` configured

### Update Django Settings

In your `settings/base.py`:

```python
import environ

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env()

SECRET_KEY = env("SECRET_KEY")  # From environment
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
DATABASES = {"default": env.db("DATABASE_URL")}
```

**Security checklist:**
- [ ] `SECRET_KEY` from environment (not hardcoded)
- [ ] `DEBUG=False` in production settings
- [ ] `ALLOWED_HOSTS` properly configured
- [ ] Database connection uses `DATABASE_URL`

### Run Security Checks

```bash
# Scan for secrets
gitleaks detect --source . --verbose

# Django security check
python manage.py check --deploy
```

- [ ] Gitleaks passes (no secrets found)
- [ ] Django deployment check passes

---

## 🏗️ Phase 4: Django Settings Split (10 min) - HIGH PRIORITY

### Create Settings Structure

```bash
mkdir -p config/settings
```

Copy from templates:
- [ ] `config/settings/__init__.py`
- [ ] `config/settings/base.py` - Shared configuration
- [ ] `config/settings/dev.py` - Development (DEBUG=True)
- [ ] `config/settings/prod.py` - Production (security hardened)
- [ ] `config/settings/test.py` - Testing (fast, in-memory)

### Update Settings Files

**In `base.py`, replace with your app:**
- [ ] Update `INSTALLED_APPS` with your apps
- [ ] Update `ROOT_URLCONF` (e.g., `config.urls`)
- [ ] Update `WSGI_APPLICATION` (e.g., `config.wsgi.application`)
- [ ] Configure `DATABASES` with django-environ

**In `prod.py`, configure:**
- [ ] Security headers (HSTS, CSP, secure cookies)
- [ ] Sentry integration
- [ ] Static file storage
- [ ] Cache backend (Redis)

### Test Settings

```bash
# Test development settings
DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py check

# Test production settings (with fake env vars)
DJANGO_SETTINGS_MODULE=config.settings.prod \
SECRET_KEY=test-key \
DATABASE_URL=postgresql://user:pass@localhost/db \
ALLOWED_HOSTS=example.com \
python manage.py check --deploy
```

- [ ] Dev settings work
- [ ] Prod settings pass deployment checks

---

## 🧪 Phase 5: Testing Infrastructure (10 min) - HIGH PRIORITY

### Configure Pytest

In `pyproject.toml`, add:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.test"
python_files = ["test_*.py", "*_test.py", "tests.py"]
addopts = [
    "--cov",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--reuse-db",
    "-n", "auto",  # Parallel testing
]
testpaths = ["tests"]

[tool.coverage.run]
source = ["."]
omit = ["*/migrations/*", "*/tests/*", "*/venv/*", "*/.venv/*"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

- [ ] Pytest configured in `pyproject.toml`
- [ ] Coverage target set (≥80%)

### Create Test Files

```bash
mkdir -p tests
```

Create `tests/conftest.py`:

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

- [ ] `tests/` directory exists
- [ ] `tests/conftest.py` created with fixtures
- [ ] At least one test file exists

### Run Tests

```bash
uv run pytest
uv run pytest --cov  # With coverage
```

- [ ] Tests run successfully
- [ ] Coverage report generated

---

## 🎨 Phase 6: Code Quality (5 min) - HIGH PRIORITY

### Install Pre-commit Hooks

```bash
uv run pre-commit install
```

- [ ] Pre-commit installed

### Test Tools

```bash
# Lint code
uv run ruff check .

# Format code
uv run ruff format .

# Type check
uv run mypy .
```

- [ ] Ruff linting passes (or shows fixable issues)
- [ ] Ruff formatting works
- [ ] Mypy type checking runs

### Test Pre-commit

```bash
git commit --allow-empty -m "test pre-commit hooks"
```

- [ ] Pre-commit hooks run automatically
- [ ] All hooks pass (ruff, mypy, gitleaks)

---

## 🚀 Phase 7: Makefile Commands (2 min) - RECOMMENDED

### Copy Makefile

```bash
cp templates/Makefile ./
```

- [ ] `Makefile` exists in project root

### Test Essential Commands

```bash
make install       # Setup dependencies
make dev           # Start development server
make test          # Run tests
make check-all     # Run ALL checks
```

- [ ] `make install` works
- [ ] `make test` runs tests
- [ ] `make check-all` passes in <30 seconds

---

## 📚 Phase 8: API Documentation (5 min) - IF USING DRF

### Install drf-spectacular

```bash
uv add drf-spectacular
```

- [ ] drf-spectacular installed

### Configure Django

In `settings/base.py`:

```python
INSTALLED_APPS = [
    # ...
    'drf_spectacular',
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Your API',
    'DESCRIPTION': 'API description',
    'VERSION': '1.0.0',
}
```

- [ ] Added to `INSTALLED_APPS`
- [ ] `REST_FRAMEWORK` configured
- [ ] `SPECTACULAR_SETTINGS` configured

### Add URLs

In your `urls.py`:

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
    # ...
]
```

- [ ] URL patterns added
- [ ] Can visit `/api/schema/swagger/` (after starting server)

---

## 🐳 Phase 9: Docker (10 min) - RECOMMENDED

### Create Docker Files

Copy from templates:
- [ ] `Dockerfile` - Multi-stage build with uv
- [ ] `docker-compose.yml` - Django + PostgreSQL + Redis
- [ ] `.dockerignore`

### Build and Test

```bash
# Build image
docker build -t myapp:latest .

# Start services
docker-compose up -d

# Check health
docker-compose ps

# View logs
docker-compose logs -f web
```

- [ ] Docker image builds successfully
- [ ] Docker compose starts all services
- [ ] All services are healthy
- [ ] Django accessible at http://localhost:8000

### Clean Up

```bash
docker-compose down
```

- [ ] Can stop services cleanly

---

## 🤖 Phase 10: CI/CD (5 min) - RECOMMENDED

### Create GitHub Actions

```bash
mkdir -p .github/workflows
cp templates/github-actions-ci.yml .github/workflows/ci.yml
```

- [ ] `.github/workflows/ci.yml` exists

### Update Workflow

In `ci.yml`, update:
- [ ] Project name
- [ ] Python version (if different from 3.11)
- [ ] Django settings module path
- [ ] Any project-specific configurations

### Push and Verify

```bash
git add .
git commit -m "Add production infrastructure"
git push
```

- [ ] Code pushed to GitHub
- [ ] CI workflow runs automatically
- [ ] All CI jobs pass (lint, typecheck, test, security, docker)

---

## 📊 Phase 11: Monitoring (5 min) - POST-DEPLOYMENT

### Install Sentry

```bash
uv add sentry-sdk python-json-logger
```

- [ ] Sentry SDK installed

### Configure Sentry

1. Create project at https://sentry.io
2. Add `SENTRY_DSN` to `.env`
3. Configure in `settings/prod.py`:

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=env("SENTRY_DSN"),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    environment="production",
)
```

- [ ] Sentry project created
- [ ] `SENTRY_DSN` in `.env`
- [ ] Sentry configured in prod settings
- [ ] Test error captured in Sentry dashboard

### Add Health Check

In `urls.py`:

```python
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "healthy"})

urlpatterns = [
    path('health/', health_check),
    # ...
]
```

- [ ] Health check endpoint exists
- [ ] Returns 200 OK

---

## ✅ Final Verification (5 min)

### Run All Checks

```bash
# 1. Full validation (should pass in <30s)
make check-all

# 2. Test pre-commit hooks
git commit --allow-empty -m "test"

# 3. Run tests with coverage
make test-cov

# 4. Check production deployment
DJANGO_SETTINGS_MODULE=config.settings.prod \
SECRET_KEY=test \
DATABASE_URL=postgresql://user:pass@localhost/db \
ALLOWED_HOSTS=example.com \
python manage.py check --deploy

# 5. Build Docker image
docker build -t myapp:latest .

# 6. Start development server
make dev
```

### Production Readiness Checklist

- [ ] `make check-all` passes in <30 seconds
- [ ] Pre-commit hooks run on every commit
- [ ] All pre-commit hooks pass
- [ ] Tests pass with ≥80% coverage
- [ ] No secrets in git (gitleaks passes)
- [ ] Django deployment checks pass
- [ ] Docker image builds successfully
- [ ] Docker services start and are healthy
- [ ] CI/CD pipeline passes on GitHub
- [ ] API docs accessible at `/api/schema/swagger/` (if DRF)
- [ ] Health check responds at `/health/`
- [ ] Sentry captures errors (if configured)

---

## 🎯 Success Criteria

**You're production-ready when ALL of these are true:**

1. ✅ Local validation completes in <30 seconds
2. ✅ Pre-commit hooks catch issues automatically
3. ✅ Test coverage ≥80%
4. ✅ Zero secrets in version control
5. ✅ CI/CD pipeline green
6. ✅ Docker deployable
7. ✅ Security checks pass
8. ✅ API documentation generated

---

## 📋 Daily Commands Reference

```bash
# Development
make dev              # Start development server
make shell            # Django shell
make migrate          # Run migrations
make makemigrations   # Create migrations

# Quality Checks
make format           # Auto-format code
make lint             # Check linting
make typecheck        # Type check
make test             # Run tests
make test-cov         # Tests with coverage
make security-scan    # Gitleaks + safety

# Full Validation (< 30 seconds)
make check-all        # Run everything before commit

# Docker
make docker-build     # Build image
make docker-up        # Start all services
make docker-down      # Stop all services
make docker-logs      # View logs

# Utilities
make clean            # Clean temporary files
make requirements     # Export requirements.txt
```

---

## 🆘 Troubleshooting

### uv not found
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"
source ~/.bashrc  # or ~/.zshrc
```

### Pre-commit hooks not running
```bash
uv run pre-commit install
uv run pre-commit run --all-files  # Test manually
```

### Tests failing
```bash
export DJANGO_SETTINGS_MODULE=config.settings.test
uv run pytest -v  # Verbose output
uv run pytest -x  # Stop on first failure
```

### Gitleaks false positives
Edit `gitleaks.toml`:
```toml
[allowlist]
paths = [
    '''\.env\.example$''',
    '''^tests/fixtures/.*''',
]
```

### Docker build errors
```bash
docker build -t myapp:latest . --progress=plain  # Show all output
docker system prune -a  # Clean Docker cache
```

### CI/CD failing
```bash
# Run CI checks locally first
make check-all
docker build -t myapp:latest .
```

---

## 📚 Next Steps

After completing this checklist:

1. **Document your setup**
   - [ ] Add setup instructions to README
   - [ ] Document environment variables in .env.example
   - [ ] Add deployment instructions

2. **Train your team**
   - [ ] Share this checklist
   - [ ] Walk through Makefile commands
   - [ ] Set up team Sentry/monitoring access

3. **Deploy to production**
   - [ ] Configure production environment
   - [ ] Set up monitoring and alerts
   - [ ] Test health checks and error tracking

4. **Iterate and improve**
   - [ ] Add integration tests
   - [ ] Increase coverage targets
   - [ ] Add performance monitoring

---

## 📖 Additional Resources

**Full Documentation:**
- Comprehensive guide: [django-production-checklist.md](./django-production-checklist.md)
- Templates: `~/.claude/skills/django-production/templates/`

**Tool Documentation:**
- **uv:** https://github.com/astral-sh/uv
- **ruff:** https://github.com/astral-sh/ruff
- **pytest:** https://docs.pytest.org/
- **drf-spectacular:** https://drf-spectacular.readthedocs.io/
- **gitleaks:** https://github.com/gitleaks/gitleaks
- **Django deployment:** https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

---

**Total checked: ___ / ___ | Time spent: _____ | Ready to ship! 🚀**
