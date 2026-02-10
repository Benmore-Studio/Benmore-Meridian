# Django Production-Ready Makefile
# Fast local validation and development commands
# Run 'make help' to see all available commands

.DEFAULT_GOAL := help
SHELL := /bin/bash
PYTHON := uv run python
MANAGE := $(PYTHON) manage.py

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

##@ Development

.PHONY: install
install: ## Install all dependencies with uv
	@echo "$(BLUE)Installing dependencies...$(NC)"
	uv sync --all-groups
	@echo "$(GREEN)✓ Dependencies installed$(NC)"
	@$(MAKE) pre-commit-install

.PHONY: dev
dev: ## Run development server
	@echo "$(BLUE)Starting development server...$(NC)"
	$(MANAGE) runserver

.PHONY: shell
shell: ## Open Django shell with shell_plus
	$(MANAGE) shell_plus --ipython

.PHONY: dbshell
dbshell: ## Open database shell
	$(MANAGE) dbshell

.PHONY: createsuperuser
createsuperuser: ## Create Django superuser
	$(MANAGE) createsuperuser

##@ Code Quality

.PHONY: lint
lint: ## Run ruff linter
	@echo "$(BLUE)Running ruff linter...$(NC)"
	uv run ruff check .

.PHONY: format
format: ## Format code with ruff
	@echo "$(BLUE)Formatting code...$(NC)"
	uv run ruff check --fix .
	uv run ruff format .
	@echo "$(GREEN)✓ Code formatted$(NC)"

.PHONY: format-check
format-check: ## Check code formatting without making changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	uv run ruff format --check .

.PHONY: typecheck
typecheck: ## Run mypy type checker
	@echo "$(BLUE)Running type checker...$(NC)"
	uv run mypy .

##@ Testing

.PHONY: test
test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	$(PYTHON) -m pytest

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(PYTHON) -m pytest --cov --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ Coverage report generated at htmlcov/index.html$(NC)"

.PHONY: test-fast
test-fast: ## Run tests in fast mode (fail fast, last failed first)
	@echo "$(BLUE)Running tests in fast mode...$(NC)"
	$(PYTHON) -m pytest -x --ff

.PHONY: test-watch
test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	$(PYTHON) -m pytest-watch

.PHONY: test-parallel
test-parallel: ## Run tests in parallel
	@echo "$(BLUE)Running tests in parallel...$(NC)"
	$(PYTHON) -m pytest -n auto

.PHONY: test-unit
test-unit: ## Run only unit tests
	$(PYTHON) -m pytest -m unit

.PHONY: test-integration
test-integration: ## Run only integration tests
	$(PYTHON) -m pytest -m integration

##@ Security

.PHONY: security-scan
security-scan: ## Run all security scans (gitleaks + safety)
	@echo "$(YELLOW)Running security scans...$(NC)"
	@$(MAKE) gitleaks
	@$(MAKE) safety-check
	@echo "$(GREEN)✓ Security scans complete$(NC)"

.PHONY: gitleaks
gitleaks: ## Run gitleaks secret scanner
	@echo "$(YELLOW)Running gitleaks...$(NC)"
	@if command -v gitleaks >/dev/null 2>&1; then \
		gitleaks detect --source . --verbose; \
	else \
		echo "$(RED)✗ gitleaks not installed. Install: brew install gitleaks$(NC)"; \
		exit 1; \
	fi

.PHONY: safety-check
safety-check: ## Check for known security vulnerabilities in dependencies
	@echo "$(YELLOW)Running safety check...$(NC)"
	uv run safety check --json

##@ Database

.PHONY: migrate
migrate: ## Run database migrations
	@echo "$(BLUE)Running migrations...$(NC)"
	$(MANAGE) migrate

.PHONY: makemigrations
makemigrations: ## Create new migrations
	@echo "$(BLUE)Creating migrations...$(NC)"
	$(MANAGE) makemigrations

.PHONY: showmigrations
showmigrations: ## Show all migrations
	$(MANAGE) showmigrations

.PHONY: migrate-check
migrate-check: ## Check if migrations are up to date
	@echo "$(BLUE)Checking migrations...$(NC)"
	$(MANAGE) makemigrations --check --dry-run

.PHONY: reset-db
reset-db: ## Reset database (WARNING: deletes all data)
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(MANAGE) flush --noinput; \
		echo "$(GREEN)✓ Database reset$(NC)"; \
	else \
		echo "$(YELLOW)Database reset cancelled$(NC)"; \
	fi

##@ Pre-commit

.PHONY: pre-commit-install
pre-commit-install: ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	uv run pre-commit install
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"

.PHONY: pre-commit-run
pre-commit-run: ## Run pre-commit on all files
	@echo "$(BLUE)Running pre-commit on all files...$(NC)"
	uv run pre-commit run --all-files

.PHONY: pre-commit-update
pre-commit-update: ## Update pre-commit hooks to latest versions
	@echo "$(BLUE)Updating pre-commit hooks...$(NC)"
	uv run pre-commit autoupdate

##@ Docker

.PHONY: docker-build
docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t myapp:latest .
	@echo "$(GREEN)✓ Docker image built: myapp:latest$(NC)"

.PHONY: docker-up
docker-up: ## Start Docker containers
	@echo "$(BLUE)Starting Docker containers...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Docker containers started$(NC)"

.PHONY: docker-down
docker-down: ## Stop Docker containers
	@echo "$(BLUE)Stopping Docker containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Docker containers stopped$(NC)"

.PHONY: docker-logs
docker-logs: ## View Docker logs
	docker-compose logs -f

.PHONY: docker-shell
docker-shell: ## Open shell in Docker container
	docker-compose exec web bash

.PHONY: docker-rebuild
docker-rebuild: ## Rebuild and restart Docker containers
	@echo "$(BLUE)Rebuilding Docker containers...$(NC)"
	docker-compose down
	docker-compose build
	docker-compose up -d
	@echo "$(GREEN)✓ Docker containers rebuilt$(NC)"

##@ Production Checks

.PHONY: production-check
production-check: ## Run Django production deployment checks
	@echo "$(YELLOW)Running production deployment checks...$(NC)"
	DJANGO_SETTINGS_MODULE=config.settings.prod $(MANAGE) check --deploy
	@echo "$(YELLOW)Testing static file collection...$(NC)"
	DJANGO_SETTINGS_MODULE=config.settings.prod $(MANAGE) collectstatic --noinput --dry-run
	@echo "$(GREEN)✓ Production checks passed$(NC)"

.PHONY: check-all
check-all: format-check lint typecheck test security-scan migrate-check production-check ## Run ALL checks (use before commit)
	@echo ""
	@echo "$(GREEN)================================================$(NC)"
	@echo "$(GREEN)✓ All checks passed! Ready to commit and push.$(NC)"
	@echo "$(GREEN)================================================$(NC)"

.PHONY: ci
ci: check-all ## Alias for check-all (CI simulation)

##@ API Documentation

.PHONY: schema
schema: ## Generate OpenAPI schema
	@echo "$(BLUE)Generating OpenAPI schema...$(NC)"
	$(MANAGE) spectacular --file schema.yml
	@echo "$(GREEN)✓ Schema generated: schema.yml$(NC)"

.PHONY: schema-validate
schema-validate: ## Validate OpenAPI schema
	@echo "$(BLUE)Validating OpenAPI schema...$(NC)"
	$(MANAGE) spectacular --validate

##@ Utilities

.PHONY: clean
clean: ## Clean temporary files and caches
	@echo "$(BLUE)Cleaning temporary files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml
	@echo "$(GREEN)✓ Cleaned temporary files$(NC)"

.PHONY: requirements
requirements: ## Export requirements.txt from pyproject.toml
	@echo "$(BLUE)Exporting requirements.txt...$(NC)"
	uv export --format requirements-txt --output-file requirements.txt
	@echo "$(GREEN)✓ requirements.txt exported$(NC)"

.PHONY: update-deps
update-deps: ## Update all dependencies to latest versions
	@echo "$(BLUE)Updating dependencies...$(NC)"
	uv lock --upgrade
	@echo "$(GREEN)✓ Dependencies updated$(NC)"

.PHONY: outdated
outdated: ## Show outdated dependencies
	@echo "$(BLUE)Checking for outdated dependencies...$(NC)"
	uv pip list --outdated

##@ Help

.PHONY: help
help: ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(BLUE)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""
