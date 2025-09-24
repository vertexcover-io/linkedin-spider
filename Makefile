.PHONY: install
install:
	@uv sync --extra dev
	@uv run pre-commit install

.PHONY: install-prod
install-prod:
	@uv sync

.PHONY: check
check:
	@uv lock --locked
	@uv run pre-commit run -a
	@uv run mypy

.PHONY: test
test:
	@uv run python -m pytest --doctest-modules

.PHONY: build
build: clean-build
	@uvx --from build pyproject-build --installer uv

.PHONY: clean-build
clean-build:
	@uv run python -c "import shutil; import os; shutil.rmtree('dist') if os.path.exists('dist') else None"

.PHONY: run-cli
run-cli:
	@uv run linkedin-spider-cli

.PHONY: run-mcp
run-mcp:
	@uv run linkedin-spider-mcp

.PHONY: dev-install
dev-install: install

.PHONY: clean
clean: clean-build
	@uv run python -c "import shutil; import os; [shutil.rmtree(d) if os.path.exists(d) else None for d in ['__pycache__', '.pytest_cache', '.mypy_cache', '.coverage']]"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  install      - Install dev dependencies and pre-commit hooks"
	@echo "  install-prod - Install production dependencies only"
	@echo "  dev-install  - Alias for install"
	@echo "  check        - Run code quality tools"
	@echo "  test         - Run tests"
	@echo "  build        - Build wheel file"
	@echo "  clean        - Clean build artifacts and cache"
	@echo "  run-cli      - Run LinkedIn scraper CLI"
	@echo "  run-mcp      - Run LinkedIn scraper MCP server"

.DEFAULT_GOAL := help
