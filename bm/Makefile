.PHONY: install check test check-all fmt

install:
	uv sync --all-extras

fmt:
	uv run ruff format bm/ tests/
	uv run ruff check --fix bm/ tests/

check:
	uv run ruff check bm/ tests/
	uv run mypy bm/

test:
	uv run pytest tests/ -v

check-all: fmt check test
	@echo "✅ All checks passed"
