# Django Production Checklist

**Time: 45-60 minutes | Django 5.0+ | Python 3.11+**

> Tick off each box as you complete it. All items should be checked when done.

---

## Phase 1: Install Core Tools (10 min)

### Package Managers & Build Tools

- [ ] Install uv (Python package manager):
  - **macOS/Linux**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - **Windows**: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
  - **Homebrew alternative (slower)**: `brew install uv`
  - Verify: `uv --version` (should be ≥0.4.0)

- [ ] Install tree (view project structure):
  - **macOS**: `brew install tree`
  - **Linux**: `sudo apt-get install tree` (Debian/Ubuntu) or `sudo yum install tree` (CentOS)
  - **Windows**: `choco install tree` (with Chocolatey)
  - Verify: `tree --version`

- [ ] Install Make (build automation):
  - **macOS**: `xcode-select --install` (includes Make)
  - **Linux**: `sudo apt-get install build-essential` or `sudo yum install make`
  - **Windows**: Use `choco install make` or Visual Studio Build Tools
  - Verify: `make --version`

### Security & Monitoring Tools

- [ ] Install gitleaks (secret detection):
  - **macOS**: `brew install gitleaks`
  - **Linux**: Download from https://github.com/gitleaks/gitleaks/releases
  - Verify: `gitleaks version`

- [ ] Install Git (version control):
  - **macOS**: `brew install git` or `xcode-select --install`
  - **Linux**: `sudo apt-get install git`
  - **Windows**: Download from https://git-scm.com
  - Verify: `git --version` (should be ≥2.40.0)

### Docker Installation

**Choose one option:**

**Option A: Docker Desktop (Recommended - All platforms)**
- [ ] Download from https://www.docker.com/products/docker-desktop
- [ ] Install and start Docker Desktop
- [ ] Verify: `docker --version` && `docker run hello-world`

**Option B: Docker CLI only (Linux)**
- [ ] Install Docker CE: `sudo apt-get install docker-ce docker-ce-cli containerd.io`
- [ ] Add to sudo group: `sudo usermod -aG docker $USER`
- [ ] Verify: `docker --version` && `docker ps`

**Option C: Colima (macOS - Lightweight alternative)**
- [ ] Install: `brew install colima`
- [ ] Start: `colima start`
- [ ] Verify: `docker --version`

---

## Phase 2: Setup Project Structure (5 min)

- [ ] Create project directory: `mkdir my-django-project && cd my-django-project`
- [ ] View structure as you build: `tree -L 2` (after directories exist)
- [ ] Initialize git: `git init`
- [ ] Create `.gitignore` from template: (see Phase 4)

---

## Phase 3: Setup Python Environment (5 min)

- [ ] Create venv: `uv venv --python 3.12`
- [ ] Activate venv:
  - **macOS/Linux**: `source .venv/bin/activate`
  - **Windows**: `.venv\Scripts\activate`
- [ ] Verify activation: `which python` (shows .venv path)
- [ ] Install dependencies: `uv sync --all-groups`
- [ ] Add core deps: `uv add django-environ djangorestframework drf-spectacular gunicorn whitenoise sentry-sdk`
- [ ] Add dev deps: `uv add --dev pytest pytest-django pytest-cov ruff mypy django-stubs pre-commit factory-boy`

---

## Phase 4: Copy Config Files (5 min)

Copy from `~/.claude/skills/django-production/templates/`:

- [ ] Copy `pyproject.toml` - Python project metadata
- [ ] Copy `Makefile` - Build automation commands
- [ ] Copy `.pre-commit-config.yaml` - Git hooks configuration
- [ ] Copy `.env.example` - Environment variables template
- [ ] Copy `gitleaks.toml` - Secret scanning rules
- [ ] Copy `Dockerfile` - Container image definition
- [ ] Copy `docker-compose.yml` - Multi-container orchestration
- [ ] Copy `.dockerignore` - Docker build exclusions
- [ ] Copy `.github/workflows/ci.yml` - CI/CD pipeline

---

## Phase 5: Security Setup (10 min)

- [ ] Create `.env` from `.env.example`: `cp .env.example .env`
- [ ] Add `.env` to `.gitignore`: `echo ".env" >> .gitignore`
- [ ] Generate SECRET_KEY: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- [ ] Add to `.env`: `SECRET_KEY=<generated-key>`
- [ ] Set `DEBUG=False` in `.env`
- [ ] Set `ALLOWED_HOSTS=localhost,127.0.0.1` in `.env`
- [ ] Set `DATABASE_URL=sqlite:///db.sqlite3` in `.env` (for development)
- [ ] Scan for secrets: `gitleaks detect --source . --verbose`
- [ ] Verify: Gitleaks passes (no secrets found)
- [ ] Add `.gitleaks` to `.gitignore` if present

---

## Phase 6: Django Settings (10 min)

- [ ] Create `config/settings/` directory
- [ ] Create `config/__init__.py` (empty init file)
- [ ] Copy `settings/base.py` template
- [ ] Copy `settings/dev.py` template
- [ ] Copy `settings/prod.py` template
- [ ] Copy `settings/test.py` template
- [ ] Create `config/settings/__init__.py` (empty init file)
- [ ] Update `base.py` INSTALLED_APPS with your apps
- [ ] Update `base.py` ROOT_URLCONF path
- [ ] Update `base.py` WSGI_APPLICATION path
- [ ] Test dev settings: `DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py check`
- [ ] Test prod settings: `DJANGO_SETTINGS_MODULE=config.settings.prod SECRET_KEY=test DATABASE_URL=sqlite:///test.db python manage.py check --deploy`

---

## Phase 7: Project Structure Verification (3 min)

- [ ] View entire project structure: `tree -I '__pycache__|*.pyc|.venv|.git|node_modules'`
- [ ] Expected structure includes:
  ```
  my-django-project/
  ├── .env                      # Secrets (NOT in git)
  ├── .env.example              # Template for .env
  ├── .gitignore                # Git exclusions
  ├── Dockerfile                # Container definition
  ├── docker-compose.yml        # Container orchestration
  ├── Makefile                  # Build commands
  ├── pyproject.toml            # Python project config
  ├── manage.py                 # Django CLI
  ├── .venv/                    # Virtual environment
  ├── config/
  │   ├── __init__.py
  │   ├── wsgi.py               # WSGI entry point
  │   ├── asgi.py               # ASGI entry point
  │   ├── urls.py               # URL routing
  │   └── settings/
  │       ├── __init__.py
  │       ├── base.py           # Shared settings
  │       ├── dev.py            # Development overrides
  │       ├── prod.py           # Production overrides
  │       └── test.py           # Testing overrides
  ├── apps/
  │   └── your_app/
  │       ├── models.py
  │       ├── views.py
  │       ├── serializers.py
  │       └── tests.py
  └── tests/
      ├── conftest.py           # Pytest fixtures
      └── test_*.py             # Test files
  ```

---

## Phase 8: Testing (10 min)

- [ ] Create `tests/` directory: `mkdir tests`
- [ ] Create `tests/conftest.py` with fixtures
- [ ] Write at least one test file: `tests/test_example.py`
- [ ] Run tests: `uv run pytest -v`
- [ ] Tests pass (all green)
- [ ] Run with coverage: `uv run pytest --cov --cov-report=term-missing`
- [ ] Coverage report generated (≥80% target)
- [ ] Add pytest config to `pyproject.toml`

---

## Phase 9: Code Quality (5 min)

- [ ] Install pre-commit hooks: `uv run pre-commit install`
- [ ] Run formatters: `uv run ruff format .`
- [ ] Run linter: `uv run ruff check .` (fix auto-fixable: `--fix`)
- [ ] Run type checker: `uv run mypy .`
- [ ] Test pre-commit: `git add . && git commit --allow-empty -m "test"`
- [ ] Pre-commit hooks run and pass

---

## Phase 10: Makefile Validation (2 min)

- [ ] Makefile in project root
- [ ] Test install: `make install` (completes without error)
- [ ] Test dev: `make dev` (server starts)
- [ ] Test testing: `make test` (tests run)
- [ ] Test check-all: `make check-all` (completes in <30s)
- [ ] All Make targets work

---

## Phase 11: API Documentation (5 min) - SKIP IF NOT USING DRF

- [ ] Add `drf_spectacular` to `INSTALLED_APPS` in `base.py`
- [ ] Set `REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS']` in `base.py`
- [ ] Configure `SPECTACULAR_SETTINGS` in `base.py`
- [ ] Add URL patterns in `config/urls.py`:
  ```python
  from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

  urlpatterns = [
      path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
      path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
  ]
  ```
- [ ] Start dev server: `make dev`
- [ ] Visit: `http://localhost:8000/api/docs/`
- [ ] Swagger UI loads and shows endpoints

---

## Phase 12: Docker Setup (10 min)

- [ ] Dockerfile in project root
- [ ] docker-compose.yml in project root
- [ ] `.dockerignore` file in project root
- [ ] Ensure Docker is running: `docker ps` (no error)
- [ ] Build image: `docker build -t myapp:latest .`
- [ ] Build succeeds (shows "Successfully built...")
- [ ] Start services: `docker-compose up -d`
- [ ] Check status: `docker-compose ps` (all services healthy)
- [ ] View logs: `docker-compose logs -f`
- [ ] Test app in container: `curl http://localhost:8000`
- [ ] Stop services: `docker-compose down`

---

## Phase 13: CI/CD Pipeline (5 min)

- [ ] `.github/workflows/ci.yml` exists
- [ ] Update project name in ci.yml
- [ ] Update Python version if needed (default: 3.12)
- [ ] Update DJANGO_SETTINGS_MODULE path
- [ ] Stage all changes: `git add .`
- [ ] Create initial commit: `git commit -m "Initial Django production setup"`
- [ ] Push to GitHub: `git push -u origin main`
- [ ] Check GitHub Actions: Visit `https://github.com/your-repo/actions`
- [ ] All CI jobs pass (lint, typecheck, test, security, docker)

---

## Phase 14: Monitoring & Observability (5 min)

- [ ] Create Sentry project at https://sentry.io (free tier available)
- [ ] Copy Sentry DSN from project settings
- [ ] Add to `.env`: `SENTRY_DSN=<your-dsn>`
- [ ] Configure Sentry in `settings/prod.py`
- [ ] Create health check endpoint in `config/urls.py`:
  ```python
  def health_check(request):
      return JsonResponse({'status': 'healthy'})

  urlpatterns = [path('health/', health_check)]
  ```
- [ ] Test endpoint: `curl http://localhost:8000/health/`
- [ ] Response shows: `{"status": "healthy"}`

---

## Final Verification Checklist

Run these commands to verify everything works:

- [ ] `make install` - Succeeds
- [ ] `make check-all` - Passes in <30 seconds
- [ ] `uv run pytest --cov` - Tests pass with ≥80% coverage
- [ ] `gitleaks detect --source . --verbose` - Passes (no secrets)
- [ ] `docker build -t myapp:latest .` - Builds successfully
- [ ] `docker-compose up -d && docker-compose ps` - All healthy
- [ ] `make dev` - Server starts on `http://localhost:8000`
- [ ] `tree -I '__pycache__|*.pyc|.venv|.git|node_modules' -L 3` - Structure matches Phase 7
- [ ] Git hooks run on commit: `git commit --allow-empty -m "verify hooks"`

---

## Production Ready Criteria

All items must be checked before deploying to production:

- [ ] `make check-all` passes in <30 seconds
- [ ] Pre-commit hooks configured and passing
- [ ] Test coverage ≥80%
- [ ] No secrets in git (gitleaks clean)
- [ ] Django deployment check passes (`--deploy` flag)
- [ ] Docker image builds successfully
- [ ] Docker services start and stay healthy
- [ ] CI/CD pipeline passes on GitHub (all jobs green)
- [ ] API documentation accessible (if using DRF)
- [ ] Health check endpoint responds with 200 OK
- [ ] Sentry monitoring configured and capturing events
- [ ] Environment variables documented in `.env.example`
- [ ] Project structure matches expected layout (Phase 7)

---

## Quick Command Reference

```bash
# Environment & Tools
uv --version                    # Check uv version
python --version                # Check Python version
tree -L 2                       # View project structure (level 2)
make --version                  # Check Make version

# Development
make install                    # Install all dependencies
make dev                        # Start Django dev server
make test                       # Run all tests
make test-cov                   # Run tests with coverage

# Quality & Security
make format                     # Auto-format code (ruff)
make lint                       # Lint code (ruff check)
make typecheck                  # Type check code (mypy)
make check-all                  # Run all checks (<30s)
gitleaks detect --source .      # Scan for secrets

# Docker
docker build -t myapp:latest .  # Build Docker image
docker-compose up -d            # Start all services
docker-compose ps               # Check service status
docker-compose logs -f          # Follow service logs
docker-compose down             # Stop all services

# Git & Commits
git status                      # Check git status
git add .                       # Stage all changes
git commit -m "message"         # Create commit (runs hooks)
git push                        # Push to remote
```

---

## Key Improvements

✅ **Added**: Docker installation options (Desktop, CLI, Colima)
✅ **Added**: Tree command installation and usage
✅ **Added**: Make installation (often forgotten!)
✅ **Added**: Detailed project structure guide (Phase 7)
✅ **Added**: Complete command reference
✅ **Added**: Specific verification steps with expected outputs
✅ **Enhanced**: uv installation with fallback options
✅ **Enhanced**: Clear platform-specific instructions (macOS/Linux/Windows)
✅ **Enhanced**: Better organization and formatting

---

**Checked: __ / 120+ items | Ready to deploy! 🚀**
