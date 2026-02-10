.PHONY: help ci install lint type-check test test-e2e build generate-api

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

ci: install lint type-check test build ## Run full CI pipeline locally

install: ## Install dependencies
	pnpm install

lint: ## Run ESLint
	pnpm run lint

type-check: ## Run TypeScript type checking
	pnpm run type-check

test: ## Run unit tests
	pnpm test

test-e2e: ## Run end-to-end tests
	pnpm run test:e2e

build: ## Build production bundle
	pnpm build

generate-api: ## Generate TypeScript types from OpenAPI schema
	pnpm run generate:api

dev: ## Start development server
	pnpm dev
