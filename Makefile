# Development and release commands for glyf. Run `make` to list them.

PYTHON_VERSION ?= 3.11
EXAMPLE_PROJECT ?= examples/simple_dbt

DOCS_DIR      := docs-site
DOCS_PROJECT  ?= glyf
DOCS_BRANCH   ?= main

.DEFAULT_GOAL := help
.PHONY: help python install test coverage build example-build example-serve \
        dashboard-ci rust python-ci ci docs-install docs-dev docs-build docs-deploy

help: ## List available targets
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "} {printf "  %-16s %s\n", $$1, $$2}'

# ---------------------------------------------------------------- python

python: ## Install the configured Python version with uv
	uv python install $(PYTHON_VERSION)

install: ## Install project and development dependencies
	uv sync --all-groups --python $(PYTHON_VERSION)

test: coverage ## Run the test suite with coverage

coverage: ## Run the test suite and write coverage reports
	uv run pytest --cov=src/glyf --cov-report=term-missing --cov-report=xml

build: ## Build package distributions for release
	uv build

example-build: ## Run dbt and glyf build for EXAMPLE_PROJECT
	cd $(EXAMPLE_PROJECT) && uv run dbt seed --profiles-dir . --full-refresh --no-partial-parse
	cd $(EXAMPLE_PROJECT) && uv run dbt build --profiles-dir .
	uv run glyf doctor --project-dir $(EXAMPLE_PROJECT)
	uv run glyf build --project-dir $(EXAMPLE_PROJECT) --zip

example-serve: ## Serve the exported site for EXAMPLE_PROJECT
	uv run glyf serve --project-dir $(EXAMPLE_PROJECT)

dashboard-ci: example-build ## The example dashboard workflow used by GitHub Actions

# ------------------------------------------------------------------ rust

rust: ## Check the formatting, lints and unit tests of the Rust core
	cargo fmt --all --check
	cargo clippy --all-targets -- -D warnings
	cargo test -p glyf-core

# -------------------------------------------------------------------- ci

python-ci: python install test build dashboard-ci ## The Python half of CI

# GitHub Actions splits this across two jobs: `python-ci` over the Python
# matrix, and `rust` once on the pinned toolchain.
ci: python-ci rust ## Run the same checks as GitHub Actions

# ------------------------------------------------------------- docs site

docs-install: ## Install the docs site dependencies
	cd $(DOCS_DIR) && npm ci

docs-dev: ## Run the docs site locally with live reload
	cd $(DOCS_DIR) && npm start

docs-build: ## Build the static docs site into docs-site/build
	cd $(DOCS_DIR) && npm run build

docs-deploy: docs-build ## Build and publish the docs site to Cloudflare Pages
	cd $(DOCS_DIR) && npx wrangler@4 pages deploy build --project-name=$(DOCS_PROJECT) --branch=$(DOCS_BRANCH)
