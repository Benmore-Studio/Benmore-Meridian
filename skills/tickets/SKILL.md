---
name: tickets
description: Custom GitHub Issue Generator Skill
---

# Custom GitHub Issue Generator Skill

## Purpose
Generate comprehensive, enterprise-grade GitHub issues organized into Epics with full project planning: iterations, priorities, sizes, hour estimates, day scheduling, and GitHub Projects integration. This skill performs a holistic analysis of your entire project, generates all necessary documentation (README.md, CLAUDE.md, flow diagrams), and provides a 3-subagent execution pattern for implementation.

## When to Use
- Planning a new project or major feature from scratch
- Breaking down complex multi-week projects into actionable sprints
- Creating developer-ready work items with precise scheduling
- Setting up GitHub Projects with proper field mappings
- Generating issues that can be immediately executed by any developer

---

## Phase 1: Holistic Project Discovery

### MANDATORY: Full Project Scan
Before generating ANY issues, this skill will:

```
1. SCAN PROJECT ROOT
   ├── Read CLAUDE.md / README.md / PROJECT.md
   ├── Find all docs/ directories
   ├── Locate all .md files (plans, specs, guides)
   ├── Find diagram files (ASCII, Mermaid, PlantUML)
   ├── Scan for HTML mockups/wireframes
   └── Check for existing issue templates

2. ANALYZE ARCHITECTURE
   ├── Identify tech stack (Django, React, etc.)
   ├── Map existing directory structure
   ├── Find integration points (APIs, webhooks)
   ├── Identify data models
   └── Note existing patterns/conventions

3. EXTRACT REQUIREMENTS FROM:
   ├── Flow diagrams → User journeys
   ├── API specs → Endpoints needed
   ├── Data models → Database design
   ├── Integration docs → External services
   └── Business logic docs → Rules/validation
```

### Discovery Commands (Run First)
```bash
# Find all documentation
find . -name "*.md" -type f | head -50

# Find flow diagrams
find . -path "*/docs/*" -name "*.md" | head -30
find . -path "*/flows/*" -name "*.md" | head -30

# Find HTML mockups
find . -name "*.html" -type f | head -20

# Find existing structure
ls -la
ls -la docs/ 2>/dev/null || echo "No docs folder"

# Check for project config
cat CLAUDE.md 2>/dev/null || cat README.md 2>/dev/null
```

---

## Phase 2: GitHub Project Configuration

### Project Field Mappings Template
```bash
# REQUIRED: Ask user for these or discover from existing project
PROJECT_URL="https://github.com/orgs/{ORG}/projects/{NUM}"
PROJECT_ID="PVT_xxx"

# Fields (get via: gh project field-list {NUM} --owner {ORG})
STATUS_FIELD="PVTSSF_xxx"
PRIORITY_FIELD="PVTSSF_xxx"
SIZE_FIELD="PVTSSF_xxx"
ESTIMATE_FIELD="PVTF_xxx"
ITERATION_FIELD="PVTIF_xxx"

# Status Options
BACKLOG="xxx"
READY="xxx"
IN_PROGRESS="xxx"
IN_REVIEW="xxx"
DONE="xxx"

# Priority Options
P0="xxx"  # Critical - blocks other work
P1="xxx"  # High - core functionality
P2="xxx"  # Medium - important but not blocking

# Size Options (Story Points / Complexity)
SIZE_XS="xxx"  # 1h or less, trivial change
SIZE_S="xxx"   # 2h, simple task
SIZE_M="xxx"   # 3h, moderate complexity
SIZE_L="xxx"   # 4-6h, significant work
SIZE_XL="xxx"  # 8h+, major effort

# Iterations (discover or create)
ITER1="xxx"  # Week 1-2: Phase name
ITER2="xxx"  # Week 3-4: Phase name
ITER3="xxx"  # Week 5-6: Phase name
ITER4="xxx"  # Week 7: Phase name
ITER5="xxx"  # Week 8+: Buffer
```

### Discover Existing Project Fields
```bash
# List project fields
gh project field-list {PROJECT_NUM} --owner {ORG} --format json

# List iterations
gh api graphql -f query='
  query {
    organization(login: "{ORG}") {
      projectV2(number: {NUM}) {
        field(name: "Iteration") {
          ... on ProjectV2IterationField {
            configuration {
              iterations { id title startDate duration }
            }
          }
        }
      }
    }
  }
'
```

---

## Phase 3: Epic & Issue Structure

### Epic Template
```markdown
# ⭐⭐⭐ Epic {N}: {Epic Title}

## Epic Overview
{2-3 sentence description of what this epic accomplishes}

**Priority:** P0/P1/P2 ({reason})
**Estimated Hours:** {X} hours
**Iteration:** {N} (Week {X-Y}: {Phase Name})
**Spec:** See {link to flow diagram or spec doc}

## Tickets in this Epic

| # | Title | Priority | Size | Hours | Day |
|---|-------|----------|------|-------|-----|
| {epic}.1 | {Task title} | P0 | S | 2h | Day 1 |
| {epic}.2 | {Task title} | P0 | M | 3h | Day 1 |
| ... | ... | ... | ... | ... | ... |

## Detailed Ticket Breakdown

### {epic}.1 {Task title} ({hours}h)
- Bullet point requirement 1
- Bullet point requirement 2
- Reference: `path/to/file.py:line`

### {epic}.2 {Task title} ({hours}h)
- Bullet point requirement 1
- ...

## Done When
- [ ] Verification criteria 1
- [ ] Verification criteria 2
- [ ] All tests passing
```

### Sub-Issue Structure (Parent → Child)
GitHub supports sub-issues to link child tickets to parent epics.

```
Epic (Parent Issue)
├── Sub-Issue 1.1
├── Sub-Issue 1.2
├── Sub-Issue 1.3
└── Sub-Issue 1.4
```

### Install gh-sub-issue Extension
Use the `gh-sub-issue` CLI extension for easy sub-issue management:

```bash
# Install the extension (one-time)
gh extension install yahsan2/gh-sub-issue

# Update when needed
gh extension upgrade sub-issue
```

### Creating Sub-Issues

**Method 1: Create & Link in One Command**
```bash
# Create a new sub-issue directly linked to parent epic
gh sub-issue create \
  --parent 2 \
  --title "[Setup] 1.1 Initialize Django project" \
  --body "$(cat docs/github-issues/001-1-init.md)" \
  --label "enhancement,backend" \
  --assignee "kashali26" \
  -R owner/repo
```

**Method 2: Link Existing Issue to Parent**
```bash
# Link existing issue #15 as sub-issue of epic #2
gh sub-issue add 2 15 -R owner/repo

# Can also use URLs
gh sub-issue add https://github.com/owner/repo/issues/2 15
```

**Method 3: Batch Create All Sub-Issues**
```bash
#!/bin/bash
# create-sub-issues.sh

REPO="owner/repo"
EPIC_NUM=$1  # Pass epic number as argument

# Create sub-issues and link to parent
gh sub-issue create -p $EPIC_NUM -t "[Setup] 1.1 Initialize Django project" \
  -b "$(cat docs/github-issues/001-1-init.md)" -l "enhancement,backend" -R $REPO

gh sub-issue create -p $EPIC_NUM -t "[Setup] 1.2 Configure settings" \
  -b "$(cat docs/github-issues/001-2-settings.md)" -l "enhancement,backend" -R $REPO

gh sub-issue create -p $EPIC_NUM -t "[Setup] 1.3 Set up Docker" \
  -b "$(cat docs/github-issues/001-3-docker.md)" -l "enhancement,backend" -R $REPO

echo "Created all sub-issues for Epic #$EPIC_NUM"
```

### Managing Sub-Issues

**List sub-issues of a parent:**
```bash
# List all open sub-issues
gh sub-issue list 2 -R owner/repo

# List all (including closed)
gh sub-issue list 2 --state all -R owner/repo

# Output as JSON
gh sub-issue list 2 --json number,title,state -R owner/repo
```

**Remove sub-issue link (doesn't delete issue):**
```bash
gh sub-issue remove 2 15 -R owner/repo

# Force without confirmation
gh sub-issue remove 2 15 --force -R owner/repo
```

### Full Epic Creation Script
```bash
#!/bin/bash
# create-epic-with-subs.sh

REPO="owner/repo"
EPIC_TITLE="⭐⭐⭐ Epic 1: Project Setup"
EPIC_BODY="docs/github-issues/001-epic-1.md"

# 1. Create the Epic (parent issue)
gh issue create \
  --repo $REPO \
  --title "$EPIC_TITLE" \
  --body-file "$EPIC_BODY" \
  --label "epic"

EPIC_NUM=$(gh issue list --repo $REPO --limit 1 --json number -q '.[0].number')
echo "Created Epic #$EPIC_NUM"

# 2. Create all sub-issues linked to epic
gh sub-issue create -p $EPIC_NUM -R $REPO \
  -t "[Setup] 1.1 Initialize Django 5.0 project" \
  -b "$(cat docs/github-issues/001-1-init.md)" \
  -l "enhancement,backend,epic-1"

gh sub-issue create -p $EPIC_NUM -R $REPO \
  -t "[Setup] 1.2 Configure Django settings" \
  -b "$(cat docs/github-issues/001-2-settings.md)" \
  -l "enhancement,backend,epic-1"

gh sub-issue create -p $EPIC_NUM -R $REPO \
  -t "[Setup] 1.3 Set up PostgreSQL + Redis Docker" \
  -b "$(cat docs/github-issues/001-3-docker.md)" \
  -l "enhancement,backend,epic-1"

# 3. List all created sub-issues
echo "Sub-issues for Epic #$EPIC_NUM:"
gh sub-issue list $EPIC_NUM -R $REPO
```

### Individual Issue Template
```markdown
## Overview
{2-3 sentences: What this accomplishes and why it's needed}

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3

## Key Files/Locations
- `path/to/modify.py` - {what to change}
- `path/to/reference.py` - {pattern to follow}

## Implementation Notes
- {Critical hint 1 - keep brief}
- {Critical hint 2 - reference existing patterns}

## Acceptance Criteria
- [ ] {Testable outcome 1}
- [ ] {Testable outcome 2}
- [ ] Tests pass: `make test`

## Metadata
- **Priority:** P{0/1/2}
- **Size:** {XS/S/M/L/XL}
- **Estimate:** {N}h
- **Iteration:** {N}
- **Day:** Day {N}
- **Depends on:** #{issue_number} (if any)
- **Blocks:** #{issue_number} (if any)
```

---

## Phase 4: Sizing & Estimation Guidelines

### Size Definitions
| Size | Hours | Complexity | Example |
|------|-------|------------|---------|
| **XS** | 1h | Trivial, single file, config change | Create Makefile, add label |
| **S** | 2h | Simple, 1-2 files, clear pattern | Create model, add endpoint |
| **M** | 3h | Moderate, 3-5 files, some logic | Implement feature with validation |
| **L** | 4-6h | Significant, multiple components | Integration with external API |
| **XL** | 8h+ | Major, architecture decisions | New app setup, complex flow |

### Priority Definitions
| Priority | Meaning | Criteria |
|----------|---------|----------|
| **P0** | Critical | Blocks other work, core functionality |
| **P1** | High | Important feature, needed soon |
| **P2** | Medium | Nice to have, can be deferred |

### Day Scheduling Logic
```
Day 1-2:   Project setup, scaffolding (8h/day)
Day 3-5:   Core models, data layer
Day 6-8:   API endpoints, business logic
Day 9-10:  Admin/dashboard features
Day 11-15: External integrations
Day 16-17: Secondary integrations
Day 18-19: Notifications, background tasks
Day 20-21: Testing, documentation
```

---

## Phase 5: Flow Diagram Generation

### ASCII Flow Diagram Template
For EVERY major flow and API endpoint, generate ASCII diagrams:

```markdown
# {FLOW NAME} FLOW
==================

OVERVIEW
{Brief description of this flow}

{ASCII DIAGRAM}
+------------------+
| Entry Point      |----+
+------------------+    |
                        |     +---------------------+
+------------------+    +---->| Step 1              |
| Alt Entry        |----+     | Description         |
+------------------+          +----------+----------+
                                         |
                                         v
                              +---------------------+
                              | Step 2              |
                              | Description         |
                              +----------+----------+
                                         |
                    +--------------------+--------------------+
                    |                                         |
                    v                                         v
         +------------------+                      +------------------+
         | Path A           |                      | Path B           |
         +--------+---------+                      +--------+---------+

API ENDPOINTS USED
+-----------------+------------------------------------------+
| Endpoint        | Purpose                                  |
+-----------------+------------------------------------------+
| POST /api/xxx   | Description                              |
| GET /api/yyy    | Description                              |
+-----------------+------------------------------------------+

EXTERNAL INTEGRATIONS
+-----------------+------------------------------------------+
| Service         | Purpose                                  |
+-----------------+------------------------------------------+
| Service Name    | What it does                             |
+-----------------+------------------------------------------+
```

---

## Phase 6: README.md Generation

### MANDATORY: Generate README.md for every project

```markdown
# {Project Name} - {Component}
{One-line description of this component}

## Prerequisites
- Python 3.11+ / Node 20+ / etc.
- Docker & Docker Compose
- Git

## Quick Start
```bash
# 1. Clone and navigate
cd {directory}

# 2. Run complete setup
make setup

# 3. Activate environment (if Python)
source .venv/bin/activate

# 4. Start development server
make dev
```

The API will be available at http://localhost:{PORT}

## Makefile Commands

### Setup & Development
| Command | Description |
|---------|-------------|
| `make setup` | Complete first-time setup |
| `make dev` | Start development server |
| `make shell` | Open interactive shell |

### Docker Services
| Command | Description |
|---------|-------------|
| `make up` | Start containers (DB, Redis, etc.) |
| `make down` | Stop containers |
| `make logs` | View container logs |

### Testing & Quality
| Command | Description |
|---------|-------------|
| `make test` | Run test suite |
| `make test-cov` | Run tests with coverage report |
| `make lint` | Run linter (ruff) |
| `make format` | Auto-format code (ruff + isort) |
| `make type-check` | Run type checking (mypy) |

## Authentication
The API uses JWT (JSON Web Tokens) for authentication.

### Get Access Token
```bash
curl -X POST http://localhost:{PORT}/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "yourpassword"}'
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Use Access Token
```bash
curl http://localhost:{PORT}/api/v1/auth/me/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Refresh Token
```bash
curl -X POST http://localhost:{PORT}/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."}'
```

## Environment Variables
Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

### Required for Development
```bash
DJANGO_SECRET_KEY=          # Auto-generated in local.py
POSTGRES_DB={db_name}
POSTGRES_USER={db_user}
POSTGRES_PASSWORD={db_pass}
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
REDIS_URL=redis://localhost:6379/0
```

### Required for Production
```bash
DJANGO_SECRET_KEY=          # Generate secure key
ALLOWED_HOSTS=api.{domain}.com
ENCRYPTION_KEY=             # Fernet key for sensitive data
SENTRY_DSN=                 # Error tracking
AWS_ACCESS_KEY_ID=          # S3 access
AWS_SECRET_ACCESS_KEY=      # S3 secret
AWS_STORAGE_BUCKET_NAME=    # S3 bucket
```

## Technology Stack
| Package | Version | Purpose |
|---------|---------|---------|
| Django | 5.0.x | Web framework |
| djangorestframework | 3.15.x | REST API |
| djangorestframework-simplejwt | 5.3.x | JWT authentication |
| drf-spectacular | 0.27.x | OpenAPI documentation |
| celery | 5.4.x | Async task queue |
| redis | 5.0.x | Cache & message broker |
| psycopg | 3.1.x | PostgreSQL driver |
| cryptography | 42.x | Encryption (Fernet) |
| httpx | 0.27.x | Async HTTP client |
| boto3 | 1.34.x | AWS S3 integration |
| ruff | 0.1.x | Linting & formatting |

## Troubleshooting

### Docker containers not starting
```bash
docker-compose down -v
docker-compose up -d
```

### Database connection refused
Wait for PostgreSQL to be ready:
```bash
docker-compose logs db
# Should see "database system is ready to accept connections"
```

### Migrations failing
Reset database:
```bash
make reset-db
```

### Import errors
Ensure virtual environment is activated:
```bash
source .venv/bin/activate
```

### Pre-commit hooks failing
Run format and lint manually:
```bash
make format
make lint
```

## API Documentation
- **Swagger UI:** http://localhost:{PORT}/api/docs/
- **ReDoc:** http://localhost:{PORT}/api/redoc/
- **OpenAPI Schema:** http://localhost:{PORT}/api/schema/

## License
Proprietary - {Organization}
```

---

## Phase 7: CLAUDE.md Generation

### MANDATORY: Generate CLAUDE.md for every project

```markdown
# CLAUDE.md - {Project Name}

This file provides context for Claude Code (AI assistant) when working on this codebase.

## Project Overview
{2-3 sentence description of what this project does and its purpose}

## Tech Stack
- **Backend:** Django 5.0 / FastAPI / Node.js
- **Database:** PostgreSQL 15+
- **Cache:** Redis
- **Task Queue:** Celery
- **API Docs:** drf-spectacular (OpenAPI 3.0)
- **Authentication:** JWT (django-simplejwt)

## Directory Structure
```
{project}/
├── {app_name}/
│   ├── settings/           # Environment-specific settings
│   │   ├── base.py         # Shared settings
│   │   ├── local.py        # Development (DEBUG=True)
│   │   └── production.py   # Production (DEBUG=False)
│   ├── apps/
│   │   ├── users/          # Custom User model, JWT auth
│   │   ├── {module1}/      # {Description}
│   │   ├── {module2}/      # {Description}
│   │   └── integrations/   # Third-party service clients
│   ├── urls.py             # Root URL routing
│   └── celery.py           # Celery configuration
├── docs/
│   └── flows/              # ASCII flow diagrams
├── requirements/
│   ├── base.txt            # Core dependencies
│   ├── local.txt           # Dev dependencies (pytest, etc.)
│   └── production.txt      # Prod dependencies (gunicorn, etc.)
└── Makefile                # Development commands
```

## Common Commands
```bash
make setup          # First-time setup (venv, deps, db, migrations)
make dev            # Start development server
make test           # Run pytest
make lint           # Run ruff linter
make format         # Auto-format with ruff + isort
make migrate        # Apply migrations
make makemigrations # Create new migrations
make shell          # Django shell
make up             # Start Docker services
make down           # Stop Docker services
```

## Code Conventions

### Python Style
- **Formatter:** ruff (replaces black, isort, flake8)
- **Line length:** 100 characters
- **Imports:** Sorted by isort (stdlib, third-party, local)
- **Docstrings:** Google style, only for complex functions
- **Type hints:** Required for function signatures

### Django Patterns
- **Models:** Inherit from `TimeStampedModel` for created_at/updated_at
- **Serializers:** Use `serializers.ModelSerializer` with explicit `fields`
- **Views:** Use `APIView` or `ViewSet`, not function-based views
- **URLs:** Nested under `/api/v1/` with versioning
- **Permissions:** Custom classes in `core/permissions.py`

### API Design
- **Auth:** JWT via `Authorization: Bearer <token>`
- **Pagination:** `PageNumberPagination` with `page_size=20`
- **Errors:** Use DRF exception handler, return structured errors
- **Versioning:** URL-based (`/api/v1/`, `/api/v2/`)

## Key Files to Know

### Settings
- `{app}/settings/base.py` - Shared config (installed apps, middleware)
- `{app}/settings/local.py` - Dev overrides (DEBUG=True, local DB)
- `{app}/settings/production.py` - Prod config (security, AWS)

### Authentication
- `apps/users/models.py` - Custom User model (AbstractUser)
- `apps/users/serializers.py` - Login, Register, User serializers
- `apps/users/views.py` - JWT endpoints

### Core Utilities
- `core/permissions.py` - RBAC permission classes
- `core/pagination.py` - Custom pagination classes
- `core/exceptions.py` - Custom exception handlers

## Database Models

### Key Models
| Model | App | Purpose |
|-------|-----|---------|
| User | users | Custom user with role field |
| {Model1} | {app} | {purpose} |
| {Model2} | {app} | {purpose} |

### Model Relationships
```
User (1) ──── (N) {Model1}
{Model1} (1) ──── (N) {Model2}
```

## External Integrations

| Service | Location | Purpose |
|---------|----------|---------|
| {Service1} | `apps/integrations/{service1}/` | {purpose} |
| {Service2} | `apps/integrations/{service2}/` | {purpose} |

### Webhook Endpoints
- `POST /webhooks/{service1}/` - Handles {events}
- `POST /webhooks/{service2}/` - Handles {events}

## Testing

### Run Tests
```bash
make test                    # Run all tests
make test-cov                # Run with coverage
pytest apps/{app}/tests/     # Run specific app tests
pytest -k "test_name"        # Run specific test
```

### Test Structure
```
apps/{app}/
└── tests/
    ├── __init__.py
    ├── conftest.py          # Fixtures
    ├── test_models.py       # Model tests
    ├── test_serializers.py  # Serializer tests
    └── test_views.py        # API tests
```

### Fixtures
- `@pytest.fixture` in `conftest.py`
- Use `baker` for model factories
- Use `APIClient` for API tests

## Environment Variables

### Required (all environments)
```
DJANGO_SECRET_KEY=
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=
POSTGRES_PORT=
```

### Required (production only)
```
ALLOWED_HOSTS=
SENTRY_DSN=
ENCRYPTION_KEY=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
```

## Security Notes

### Sensitive Data
- SSNs encrypted with Fernet (see `apps/{app}/encryption.py`)
- Bank details encrypted before storage
- Never log sensitive fields

### Authentication
- Access tokens expire in 15 minutes
- Refresh tokens expire in 7 days
- Use `IsAuthenticated` permission by default

## Common Tasks

### Add a New Model
1. Create model in `apps/{app}/models.py`
2. Create serializer in `apps/{app}/serializers.py`
3. Create views in `apps/{app}/views.py`
4. Add URLs in `apps/{app}/urls.py`
5. Run `make makemigrations && make migrate`
6. Add to admin in `apps/{app}/admin.py`

### Add a New Integration
1. Create folder `apps/integrations/{service}/`
2. Create `client.py` with API client class
3. Create `webhooks.py` if needed
4. Add URL route in `urls.py`
5. Add environment variables

### Add a New Endpoint
1. Add serializer (if new data shape)
2. Add view class/method
3. Add URL pattern
4. Add permission class if needed
5. Document in flow diagram

## Don'ts
- Don't commit `.env` files
- Don't use `print()` - use `logging`
- Don't skip migrations
- Don't hardcode secrets
- Don't disable security middleware in production
```

---

## Phase 8: Production-Ready Configuration

### MANDATORY: Include These in Every Project

### 1. pyproject.toml (Python Projects)
```toml
[project]
name = "{project_name}"
version = "0.1.0"
requires-python = ">=3.11"

[tool.ruff]
target-version = "py311"
line-length = 100
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # Pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "S",    # flake8-bandit (security)
]
ignore = [
    "E501",  # line too long (handled by formatter)
    "S101",  # use of assert (needed for tests)
]

[tool.ruff.isort]
known-first-party = ["{app_name}"]
section-order = ["future", "standard-library", "third-party", "first-party", "local-folder"]

[tool.ruff.per-file-ignores]
"**/tests/**" = ["S101"]
"**/migrations/**" = ["E501"]

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "{app_name}.settings.local"
python_files = ["test_*.py"]
addopts = "-v --tb=short"

[tool.coverage.run]
source = ["{app_name}"]
omit = ["*/migrations/*", "*/tests/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
]
```

### 2. .pre-commit-config.yaml
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [django-stubs, djangorestframework-stubs]
        args: [--ignore-missing-imports]
```

### 3. Makefile
```makefile
.PHONY: help setup dev test lint format migrate shell up down logs

# Colors
GREEN := \033[0;32m
NC := \033[0m

help:
	@echo "$(GREEN)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

# =============================================================================
# SETUP
# =============================================================================

setup: ## Complete first-time setup
	@echo "$(GREEN)Creating virtual environment...$(NC)"
	python -m venv .venv
	@echo "$(GREEN)Installing dependencies...$(NC)"
	.venv/bin/pip install -r requirements/local.txt
	@echo "$(GREEN)Installing pre-commit hooks...$(NC)"
	.venv/bin/pre-commit install
	@echo "$(GREEN)Starting Docker services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Waiting for database...$(NC)"
	sleep 3
	@echo "$(GREEN)Running migrations...$(NC)"
	.venv/bin/python manage.py migrate
	@echo "$(GREEN)Setup complete! Run 'source .venv/bin/activate' then 'make dev'$(NC)"

# =============================================================================
# DEVELOPMENT
# =============================================================================

dev: ## Start development server
	python manage.py runserver

shell: ## Open Django shell
	python manage.py shell_plus

dbshell: ## Open database shell
	python manage.py dbshell

# =============================================================================
# DOCKER
# =============================================================================

up: ## Start Docker services (PostgreSQL, Redis)
	docker-compose up -d

down: ## Stop Docker services
	docker-compose down

logs: ## View Docker logs
	docker-compose logs -f

# =============================================================================
# DATABASE
# =============================================================================

migrate: ## Apply database migrations
	python manage.py migrate

makemigrations: ## Create new migrations
	python manage.py makemigrations

superuser: ## Create superuser
	python manage.py createsuperuser

reset-db: ## Reset database (WARNING: deletes all data)
	docker-compose down -v
	docker-compose up -d
	sleep 3
	python manage.py migrate
	@echo "$(GREEN)Database reset complete$(NC)"

# =============================================================================
# TESTING & QUALITY
# =============================================================================

test: ## Run pytest
	pytest

test-cov: ## Run tests with coverage
	pytest --cov={app_name} --cov-report=html --cov-report=term-missing

lint: ## Run ruff linter
	ruff check .

format: ## Auto-format code with ruff
	ruff check --fix .
	ruff format .

type-check: ## Run mypy type checking
	mypy {app_name}

pre-commit: ## Run all pre-commit hooks
	pre-commit run --all-files

# =============================================================================
# DOCUMENTATION
# =============================================================================

docs: ## Generate OpenAPI schema
	python manage.py spectacular --file schema.yml
	@echo "$(GREEN)Schema generated at schema.yml$(NC)"
```

### 4. requirements/base.txt
```txt
# Django
Django>=5.0,<5.1
djangorestframework>=3.15,<4.0
djangorestframework-simplejwt>=5.3,<6.0
django-cors-headers>=4.3,<5.0
django-filter>=24.1,<25.0

# API Documentation
drf-spectacular>=0.27,<1.0

# Database
psycopg[binary]>=3.1,<4.0

# Task Queue
celery>=5.4,<6.0
redis>=5.0,<6.0

# Security
cryptography>=42.0,<43.0

# HTTP Client
httpx>=0.27,<1.0

# AWS
boto3>=1.34,<2.0

# Utilities
python-decouple>=3.8,<4.0
```

### 5. requirements/local.txt
```txt
-r base.txt

# Testing
pytest>=8.0,<9.0
pytest-django>=4.8,<5.0
pytest-cov>=4.1,<5.0
model-bakery>=1.17,<2.0
factory-boy>=3.3,<4.0

# Development
django-extensions>=3.2,<4.0
ipython>=8.20,<9.0

# Code Quality
ruff>=0.1,<1.0
mypy>=1.8,<2.0
django-stubs>=4.2,<5.0
djangorestframework-stubs>=3.14,<4.0
pre-commit>=3.6,<4.0

# Debugging
django-debug-toolbar>=4.2,<5.0
```

### 6. requirements/production.txt
```txt
-r base.txt

# Server
gunicorn>=21.2,<22.0

# Monitoring
sentry-sdk>=1.39,<2.0

# Static Files
whitenoise>=6.6,<7.0
```

---

## Phase 9: 3-Subagent Execution Pattern

### MANDATORY: Use This Pattern for Implementation

When executing tickets, use 3 parallel subagents:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     3-SUBAGENT EXECUTION PATTERN                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐        │
│  │   IMPLEMENTOR   │   │     CRITIC      │   │    OBSERVER     │        │
│  │   (Agent 1)     │   │   (Agent 2)     │   │   (Agent 3)     │        │
│  └────────┬────────┘   └────────┬────────┘   └────────┬────────┘        │
│           │                     │                     │                  │
│           ▼                     ▼                     ▼                  │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐        │
│  │ Writes code     │   │ Reviews code    │   │ Watches both    │        │
│  │ Creates files   │   │ Finds errors    │   │ Integrates work │        │
│  │ Implements      │   │ Security audit  │   │ Runs tests      │        │
│  │ features        │   │ Best practices  │   │ Final check     │        │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘        │
│                                                                          │
│  WORKFLOW:                                                               │
│  1. Implementor writes code for ticket                                   │
│  2. Critic reviews (hypercritical) → returns issues                      │
│  3. Implementor fixes issues                                             │
│  4. Critic approves or returns more issues                               │
│  5. Observer integrates, runs tests, commits                             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Subagent Prompts

#### Agent 1: IMPLEMENTOR
```
You are the IMPLEMENTOR agent. Your role:

1. Read the ticket requirements carefully
2. Check existing code patterns in the codebase
3. Write clean, production-ready code
4. Follow the project's conventions (see CLAUDE.md)
5. Include type hints on all function signatures
6. Add docstrings only for complex functions
7. Create unit tests for new functionality

CONSTRAINTS:
- Use ruff-compatible formatting (100 char lines)
- Follow existing patterns exactly
- No over-engineering - minimal code to solve the problem
- Use existing utilities, don't reinvent
- Encrypt sensitive data (SSN, bank details)

OUTPUT:
- List of files created/modified
- Brief explanation of approach
- Any questions for the Critic
```

#### Agent 2: CRITIC
```
You are the CRITIC agent. Your role is to be HYPERCRITICAL.

REVIEW CHECKLIST:
□ Security
  - SQL injection vulnerabilities?
  - XSS vulnerabilities?
  - Sensitive data exposed in logs?
  - Proper authentication/authorization?
  - Secrets hardcoded?

□ Code Quality
  - Type hints on all functions?
  - Following DRY principle?
  - Proper error handling?
  - Edge cases covered?
  - Consistent with existing patterns?

□ Performance
  - N+1 queries?
  - Missing database indexes?
  - Unnecessary database calls?
  - Proper caching?

□ Best Practices
  - Django best practices followed?
  - DRF conventions used correctly?
  - Proper serializer validation?
  - Permissions properly applied?

□ Testing
  - Tests cover happy path?
  - Tests cover edge cases?
  - Tests cover error cases?
  - Fixtures properly used?

□ Documentation
  - Complex logic commented?
  - API documented with drf-spectacular?
  - Flow diagrams updated?

OUTPUT:
- List of issues found (numbered)
- Severity: CRITICAL / HIGH / MEDIUM / LOW
- Specific line references
- Suggested fixes

Be harsh. Find EVERY issue. Better to catch problems now than in production.
```

#### Agent 3: OBSERVER
```
You are the OBSERVER agent. Your role:

1. Watch Implementor and Critic interact
2. Once Critic approves, integrate the work:
   - Run ruff format
   - Run ruff check --fix
   - Run pytest
   - Verify all tests pass
   - Run make migrate if needed
   - Update flow documentation if API changed

3. Final verification:
   - Start dev server (make dev)
   - Test endpoints manually (curl)
   - Check OpenAPI docs load
   - Verify no console errors

4. Commit the work:
   - git add relevant files
   - git commit with descriptive message
   - Reference ticket number in commit

OUTPUT:
- Test results summary
- Any issues found during integration
- Commit hash
- Ready for next ticket confirmation
```

### Execution Command
```
For each ticket, use the 3-subagent pattern:

ultrathink and use 3 subagents:
- Implementor: implement the ticket code
- Critic: hypercritical review (security, best practices, reusability)
- Observer: integrate work, run tests, commit

Requirements:
- Install/use: ruff, isort, drf-spectacular, pre-commit
- Generate ASCII flow diagrams for each endpoint
- Update API documentation as you go
- Ensure production-ready quality
- Reference docs/flows/ for context
```

---

## Phase 10: Output Generation

### Step 1: Generate Summary Table
```markdown
# {Project Name} - GitHub Project Plan

## Summary
| Item | Count |
|------|-------|
| GitHub Issues | {N} tickets |
| Total Hours | {N} hours (~{N} weeks @ 40h/week) |
| Epics | {N} epics |
| Iterations | {N} iterations |
| Flow Documents | {N} diagrams |
| Models | {N} models |
| API Endpoints | ~{N} endpoints |
| Integrations | {N} ({list}) |

## Epic Breakdown
| Epic | Title | Tickets | Hours | Iteration |
|------|-------|---------|-------|-----------|
| 1 | {Title} | {N} | {N}h | Iter 1 |
| 2 | {Title} | {N} | {N}h | Iter 1-2 |
| ... | ... | ... | ... | ... |

## Iteration Schedule
| Iteration | Weeks | Focus | Epics |
|-----------|-------|-------|-------|
| 1 | Week 1-2 | {Phase Name} | Epic 1, 2 |
| 2 | Week 3-4 | {Phase Name} | Epic 3, 4 |
| ... | ... | ... | ... |
```

### Step 2: Generate Directory Structure
```markdown
## Proposed Directory Structure

{project_name}/
├── backend/                          # {Tech} backend
│   ├── .docker/
│   │   └── Dockerfile
│   ├── .pre-commit-config.yaml       # Pre-commit hooks
│   ├── docker-compose.yml
│   ├── pyproject.toml                # Ruff, pytest, coverage config
│   ├── Makefile
│   ├── CLAUDE.md                     # AI assistant context
│   ├── README.md                     # Developer documentation
│   └── {app_name}/
│       ├── settings/
│       │   ├── base.py
│       │   ├── local.py
│       │   └── production.py
│       └── apps/
│           ├── {module1}/
│           │   ├── models.py
│           │   ├── serializers.py
│           │   ├── views.py
│           │   ├── urls.py
│           │   └── tests/
│           │       ├── test_models.py
│           │       └── test_views.py
│           └── integrations/
│               ├── {service1}/
│               │   ├── client.py
│               │   └── webhooks.py
│               └── {service2}/
├── docs/
│   ├── flows/                        # ASCII flow diagrams
│   │   ├── 01_{flow1}_flow.md
│   │   ├── 02_{flow2}_flow.md
│   │   └── ...
│   └── github-issues/                # Issue files for approval
│       ├── 000-project-summary.md
│       ├── 001-epic-1-{name}.md
│       └── ...
└── frontend/                         # If applicable
```

### Step 3: Generate Epic Files
Store in `docs/github-issues/`:
```
docs/github-issues/
├── 000-project-summary.md           # Full summary table
├── 001-epic-1-project-setup.md      # Epic 1 with all tickets
├── 002-epic-2-core-models.md        # Epic 2 with all tickets
├── 003-epic-3-{name}.md             # Epic 3...
├── ...
├── README.md                        # Generated README template
├── CLAUDE.md                        # Generated CLAUDE template
└── flows/
    ├── 01_{flow}_flow.md
    └── ...
```

### Step 4: Generate gh CLI Script with Sub-Issues
```bash
#!/bin/bash
# create-all-issues.sh
# Requires: gh extension install yahsan2/gh-sub-issue

REPO="owner/repo"
PROJECT_NUM=40

# =============================================================================
# EPIC 1: Project Setup
# =============================================================================

echo "Creating Epic 1..."
gh issue create \
  --repo $REPO \
  --title "⭐⭐⭐ Epic 1: {Epic Title}" \
  --body-file docs/github-issues/001-epic-1.md \
  --label "epic"

EPIC1=$(gh issue list --repo $REPO --limit 1 --json number -q '.[0].number')

# Add epic to project
gh project item-add $PROJECT_NUM --owner {ORG} --url "https://github.com/$REPO/issues/$EPIC1"

# Create sub-issues for Epic 1
gh sub-issue create -p $EPIC1 -R $REPO \
  -t "[Setup] 1.1 Initialize Django 5.0 project" \
  -b "$(cat docs/github-issues/001-1-init.md)" \
  -l "enhancement,backend,epic-1"

gh sub-issue create -p $EPIC1 -R $REPO \
  -t "[Setup] 1.2 Configure Django settings" \
  -b "$(cat docs/github-issues/001-2-settings.md)" \
  -l "enhancement,backend,epic-1"

# List sub-issues
echo "Epic 1 sub-issues:"
gh sub-issue list $EPIC1 -R $REPO

# =============================================================================
# EPIC 2: Core Models
# =============================================================================

echo "Creating Epic 2..."
# ... repeat pattern for each epic
```

---

## Phase 11: Verification Checklist Generator

### Post-Implementation Verification
```markdown
## Verification Checklist

After implementation, verify:

### Infrastructure
- [ ] Backend starts: `cd backend && make dev`
- [ ] Database runs: `docker-compose up -d`
- [ ] Migrations run: `make migrate`
- [ ] API docs load: http://localhost:{PORT}/api/docs/

### Code Quality
- [ ] Lint passes: `make lint`
- [ ] Format clean: `make format` (no changes)
- [ ] Tests pass: `make test`
- [ ] Coverage adequate: `make test-cov`
- [ ] Pre-commit passes: `make pre-commit`

### Authentication
- [ ] Login works: POST /api/v1/auth/login/
- [ ] JWT refresh works
- [ ] Permissions enforced

### Core Features
- [ ] Feature 1 works: {endpoint}
- [ ] Feature 2 works: {endpoint}
- [ ] Admin works: /admin/

### Integrations
- [ ] Webhook 1: POST /webhooks/{service}/
- [ ] Webhook 2: POST /webhooks/{service}/

### Documentation
- [ ] README.md complete and accurate
- [ ] CLAUDE.md updated with new features
- [ ] Flow diagrams match implementation
- [ ] OpenAPI schema current: `make docs`

### Production Ready
- [ ] No DEBUG=True in production settings
- [ ] SECRET_KEY from environment
- [ ] ALLOWED_HOSTS configured
- [ ] Sensitive data encrypted
- [ ] Logging configured
- [ ] Sentry configured (if applicable)
```

---

## Skill Invocation

### Required Input
```
Project: {Project name}
Repo: {owner/repo}
Assignee: {Developer name}
GitHub Username: {username}
Project Number: {GitHub Project number, if exists}
Tech Stack: {Django/FastAPI/Node/etc.}
```

### Optional Input
```
Start Day: {Day 1 date, for scheduling}
Hours Per Day: {default 8}
Existing Docs Path: {path to docs folder}
```

### Example Invocation
```
Use the custom-github-issue-generator skill to plan:

Project: Echelon NIL Platform Backend
Repo: Benmore-Studio/echelon_nil_135
Assignee: Kashan
GitHub Username: @kashali26
Project Number: 40
Tech Stack: Django 5.0, PostgreSQL, Redis, Celery
```

---

## Workflow Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    CUSTOM ISSUE GENERATOR                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. DISCOVER                                                     │
│     └─→ Scan all MDs, diagrams, HTML, specs                     │
│         └─→ Extract requirements, flows, integrations           │
│                                                                  │
│  2. CONFIGURE                                                    │
│     └─→ Set up GitHub Project field mappings                    │
│         └─→ Define iterations, priorities, sizes                │
│                                                                  │
│  3. PLAN                                                         │
│     └─→ Group into Epics by domain                              │
│         └─→ Estimate hours, assign days                         │
│             └─→ Create dependency graph                         │
│                                                                  │
│  4. GENERATE                                                     │
│     └─→ Summary table with counts                               │
│         └─→ Directory structure                                 │
│             └─→ README.md template                              │
│                 └─→ CLAUDE.md template                          │
│                     └─→ Flow diagrams (ASCII)                   │
│                         └─→ Epic files with tickets             │
│                             └─→ gh CLI script                   │
│                                                                  │
│  5. EXECUTE (3-Subagent Pattern)                                │
│     └─→ Implementor: writes code                                │
│         └─→ Critic: hypercritical review                        │
│             └─→ Observer: integrate, test, commit               │
│                                                                  │
│  6. VERIFY                                                       │
│     └─→ Generate verification checklist                         │
│         └─→ Post-implementation testing guide                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Output Artifacts

When this skill completes, you will have:

1. **`000-project-summary.md`** - Full summary table, epic breakdown, schedule
2. **`001-epic-{N}-{name}.md`** - One file per epic with all tickets
3. **`flows/0{N}_{name}_flow.md`** - ASCII flow diagrams for every flow
4. **`README.md`** - Complete developer documentation
5. **`CLAUDE.md`** - AI assistant context file
6. **`create-epic-with-subs.sh`** - Script to create epics + sub-issues via gh-sub-issue
7. **`verification-checklist.md`** - Post-implementation testing guide
8. **`project-fields.sh`** - GitHub Project field IDs for automation
9. **`pyproject.toml`** - Python project config (ruff, pytest, etc.)
10. **`.pre-commit-config.yaml`** - Pre-commit hooks config
11. **`Makefile`** - Development commands

---

## Critical Rules

### DO's ✅
- **ALWAYS scan the full project first** - read every MD, diagram, spec
- **Group into Epics** - never create orphan issues
- **Include hour estimates** - every ticket gets X hours
- **Schedule by day** - Day 1, Day 2, etc.
- **Set priorities** - P0, P1, P2 with clear reasoning
- **Use sizing** - XS, S, M, L, XL
- **Map to iterations** - Week 1-2, Week 3-4, etc.
- **Create flow diagrams** - ASCII format, no Mermaid
- **Generate README.md** - complete developer docs
- **Generate CLAUDE.md** - AI assistant context
- **Use 3-subagent pattern** - Implementor, Critic, Observer
- **Include prod-ready config** - ruff, pre-commit, pytest
- **Store locally first** - get approval before posting to GitHub

### DON'Ts ❌
- **Don't skip discovery** - you MUST read the full project first
- **Don't create flat issues** - always organize into Epics
- **Don't omit estimates** - every task needs hours
- **Don't forget dependencies** - note what blocks what
- **Don't write full implementations** - hints only
- **Don't skip directory structure** - always propose file layout
- **Don't use Mermaid** - ASCII diagrams for universal compatibility
- **Don't create issues for unknowns** - ask or add to notes instead
- **Don't skip README/CLAUDE** - mandatory for every project
- **Don't skip the Critic** - always get hypercritical review

---

## Developer Mappings

**Known Developers:**
- Funbi (Oluwafunbi Onaeko) → @ouujay
- Paul (Adeleke Paul) → @AdelekeAP
- Desmond → @LocksiDesmond
- Kashan → @kashali26
- Arkash → @ArkashJ

**To add new developer:**
1. Ask: "What is their GitHub username?"
2. Verify: "Can you confirm their GitHub profile URL?"
3. Store mapping for future use

---

## Skill Version
**Version:** 2.1.0
**Last Updated:** 2025-01-14
**Based on:** Echelon NIL Platform planning methodology + github-issue-generator skill + 3-subagent pattern + gh-sub-issue extension
