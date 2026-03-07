# Project: linkedin-spider

LinkedIn scraping library with CLI and MCP server interfaces, built on Selenium with anti-detection.

## Stack

Python 3.10+ · Selenium · FastMCP · cyclopts · uv (package manager)

## Structure

- `src/linkedin_spider/core/` — Config, auth, driver management, main `LinkedinSpider` orchestrator
- `src/linkedin_spider/scrapers/` — Specialized scrapers (profile, company, search, connections, conversations) inheriting `BaseScraper`
- `src/linkedin_spider/cli/` — CLI commands via cyclopts (optional dep)
- `src/linkedin_spider/mcp/` — MCP server via FastMCP exposing 11 tools (optional dep)
- `src/linkedin_spider/utils/` — Human behavior simulation, tracking, pattern detection
- `examples/` — Usage examples for each scraper type
- `tests/` — pytest (markers: `slow`, `integration`)

## Commands

- `make check` — Pre-commit hooks + mypy typecheck
- `make test` — Run pytest
- `make build` — Build wheel
- `make clean` — Remove dist/cache artifacts
- `uv sync` — Install all deps
- `uv run linkedin-spider-cli` — Run CLI locally
- `uv run linkedin-spider-mcp` — Run MCP server locally

## Workflow

1. Explore codebase before implementing changes
2. Run `make check` and `make test` before calling a task done
3. Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`, `perf:`, `ci:`
4. Ask before committing to git

## Key Patterns

- **Single driver instance**: `LinkedinSpider` reuses one Chrome WebDriver across all scrapers
- **Session persistence**: Chrome profile at `~/.linkedin_spider_profiles/{session_id}/` for cookie reuse
- **Auth priority**: li_at cookie → cached cookies → email/password → error
- **Optional extras**: CLI and MCP are optional deps; imports fail gracefully with helpful messages
- **Anti-detection**: 130+ lines of stealth JS injected into Chrome + human-like delays/mouse movement
- **Platform-specific**: macOS gets extra Chrome flags; user agents differ by OS

## Critical Rules

- NEVER commit `.env` files or credentials
- ALWAYS use type hints — mypy strict mode is enforced (`disallow_untyped_defs=true`)
- ALWAYS handle Chrome process cleanup — lingering processes leak resources (see `driver.py` atexit handlers)
- Do NOT add Chrome flags without testing on both macOS and Linux — the Dockerfile uses chromium from apt
