# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.3.0] - 2026-05-12
### :sparkles: New Features
- [`2d2389e`](https://github.com/vertexcover-io/linkedin-spider/commit/2d2389ec285667e277fa1fa5dcf53d674d214a37) - **auth**: add browser warm-up to DriverManager *(commit by [@amankumarsingh77](https://github.com/amankumarsingh77))*
- [`475ab36`](https://github.com/vertexcover-io/linkedin-spider/commit/475ab3639b37d52d135746d03cbab758e3190d3f) - **auth**: add manual browser login flow to AuthManager *(commit by [@amankumarsingh77](https://github.com/amankumarsingh77))*
- [`78d987a`](https://github.com/vertexcover-io/linkedin-spider/commit/78d987a1d061821cf92bd1488ece934512dc38cd) - **auth**: restructure auth priority — saved cookies > li_at > manual login *(commit by [@amankumarsingh77](https://github.com/amankumarsingh77))*
- [`7fd5d43`](https://github.com/vertexcover-io/linkedin-spider/commit/7fd5d4388f82d490d3cb2e572a847455247e4014) - **cli**: remove email/password, add login command for manual auth *(commit by [@amankumarsingh77](https://github.com/amankumarsingh77))*
- [`cafa3c1`](https://github.com/vertexcover-io/linkedin-spider/commit/cafa3c1168b914138c68bb69640de1a285003998) - **auth**: add session cookie validation after authentication *(commit by [@amankumarsingh77](https://github.com/amankumarsingh77))*
- [`15f5535`](https://github.com/vertexcover-io/linkedin-spider/commit/15f5535b6a753853878313b1f289f0dc9ce89d82) - **mcp**: add per-session file logging and tool-level request/error tracing *(commit by [@kgritesh](https://github.com/kgritesh))*
- [`5f6b592`](https://github.com/vertexcover-io/linkedin-spider/commit/5f6b592df665d359e6d38b6194f53553230628cd) - **scrapers**: rewrite search filters with typeahead resolver and URN cache *(commit by [@kgritesh](https://github.com/kgritesh))*
- [`ce2306e`](https://github.com/vertexcover-io/linkedin-spider/commit/ce2306eea636e5d801e13668d8275c0bfe4b41ed) - **cli**: add search filter flags and clean selenium error output *(commit by [@kgritesh](https://github.com/kgritesh))*
- [`2772815`](https://github.com/vertexcover-io/linkedin-spider/commit/27728151c9314c6f58c5402ecb119d23be182eb2) - **scrapers**: cache profile→compose-URL to skip profile visit on repeat sends *(commit by [@kgritesh](https://github.com/kgritesh))*
- [`58acc17`](https://github.com/vertexcover-io/linkedin-spider/commit/58acc17e64195ff20d97f02e3500abf9d33d9a33) - **cli**: add send-message command *(commit by [@kgritesh](https://github.com/kgritesh))*

### :bug: Bug Fixes
- [`d517ddd`](https://github.com/vertexcover-io/linkedin-spider/commit/d517ddde1977a205d6d155326a82a9da479b6027) - **cli**: add logging configuration so auth flow logs are visible *(commit by [@amankumarsingh77](https://github.com/amankumarsingh77))*
- [`f92ac92`](https://github.com/vertexcover-io/linkedin-spider/commit/f92ac920068f21b9ce19827734b59d705a836b71) - **scrapers**: update selectors for LinkedIn's new DOM layout *(commit by [@amankumarsingh77](https://github.com/amankumarsingh77))*
- [`5ee6b36`](https://github.com/vertexcover-io/linkedin-spider/commit/5ee6b36b872eb612ffb96649ceef6c7e3945ae30) - **scrapers**: improve connection request reliability with direct invite URL navigation *(commit by [@amankumarsingh77](https://github.com/amankumarsingh77))*
- [`84bb078`](https://github.com/vertexcover-io/linkedin-spider/commit/84bb078ebc4f6a620abb60419c2465cfba1de67a) - **driver**: support Apple Silicon and drop unstable Chrome flags *(commit by [@kgritesh](https://github.com/kgritesh))*
- [`79672c2`](https://github.com/vertexcover-io/linkedin-spider/commit/79672c2a955837359ab9f9cd5fbcaf186a442c38) - **scrapers**: repair send-button selector for current LinkedIn UI *(commit by [@kgritesh](https://github.com/kgritesh))*

### :zap: Performance Improvements
- [`e989d4a`](https://github.com/vertexcover-io/linkedin-spider/commit/e989d4adb941aa7987eaf74ae9af048bc88662ce) - **driver**: use eager page-load strategy to avoid waiting on analytics *(commit by [@kgritesh](https://github.com/kgritesh))*

### :recycle: Refactors
- [`ae82f76`](https://github.com/vertexcover-io/linkedin-spider/commit/ae82f767442628286972aac4a55016c39fde8e1b) - **auth**: remove email/password from LinkedinSpider constructor *(commit by [@amankumarsingh77](https://github.com/amankumarsingh77))*
- [`54d47af`](https://github.com/vertexcover-io/linkedin-spider/commit/54d47afc77bd9e62fb74d93c49d608b7d981d046) - **mcp**: remove email/password from MCP server auth *(commit by [@amankumarsingh77](https://github.com/amankumarsingh77))*

### :construction_worker: Build System
- [`334b370`](https://github.com/vertexcover-io/linkedin-spider/commit/334b37064899b6f405410414721888e3c5f03fde) - **release**: switch changelog generation from PR-based to conventional commits *(commit by [@kgritesh](https://github.com/kgritesh))*

### :memo: Documentation Changes
- [`b70a9b7`](https://github.com/vertexcover-io/linkedin-spider/commit/b70a9b707c7c6956dcdda57dcdaf6632013087b7) - **examples**: update auth examples for manual-login-first flow *(commit by [@amankumarsingh77](https://github.com/amankumarsingh77))*

### :wrench: Chores
- [`6a8f1a7`](https://github.com/vertexcover-io/linkedin-spider/commit/6a8f1a7e6bf344d7af3da2ba878da38ea38e2266) - update CHANGELOG.md for v0.2.7 *(commit by [@actions-user](https://github.com/actions-user))*

### :flying_saucer: Other Changes
- [`cca1c66`](https://github.com/vertexcover-io/linkedin-spider/commit/cca1c6671cd46284724f4bf0d7126ac390b78263) - Merge pull request [#15](https://github.com/vertexcover-io/linkedin-spider/pull/15) from vertexcover-io/feat/manual-login-auth

feat(auth): replace email/password with manual-login-first auth flow *(commit by [@amankumarsingh77](https://github.com/amankumarsingh77))*
- [`8e6e4f2`](https://github.com/vertexcover-io/linkedin-spider/commit/8e6e4f26658b0344f5041d56f9d6dafd25897b6a) - Merge pull request [#16](https://github.com/vertexcover-io/linkedin-spider/pull/16) from vertexcover-io/fix/scraper-selectors

fix(scrapers): update selectors for LinkedIn's new DOM layout *(commit by [@amankumarsingh77](https://github.com/amankumarsingh77))*
- [`c0276dc`](https://github.com/vertexcover-io/linkedin-spider/commit/c0276dc6cc37588cb47244f292099f397e090a7f) - Merge pull request [#17](https://github.com/vertexcover-io/linkedin-spider/pull/17) from vertexcover-io/fix/connection-request-reliability

fix(scrapers): improve connection request reliability *(commit by [@amankumarsingh77](https://github.com/amankumarsingh77))*


## [v0.2.7] - 2026-03-19

- No changes

## [v0.2.6] - 2026-03-19

- No changes

## [Unreleased]

### Added

- `send_message` tool — send messages in existing or new LinkedIn conversations with dry-run support

## [v0.2.5] - 2026-03-19

- No changes

## [v0.2.4] - 2026-03-07

- No changes

## [v0.2.3] - 2026-03-07

- No changes

## [v0.2.2] - 2026-03-07

- No changes

## [v0.2.1] - 2026-03-07

- No changes

## [v0.1.0] - 2025-09-24

## [v0.2.0] - 2025-12-01

- No changes

## [v0.1.9] - 2025-11-27

## 🔄 Other Changes

- fix cookie auth (#8) @amankumarsingh77

## [v0.1.8] - 2025-11-24

- No changes

## [v0.1.7] - 2025-11-24

- No changes

## [v0.1.6] - 2025-11-24

- No changes

## [v0.1.5] - 2025-11-22

- No changes

## [v0.1.4] - 2025-11-22

- No changes

## [v0.1.3] - 2025-11-22

## 🔄 Other Changes

- :wip: feature to search posts based on a topic (#6) @kgritesh
- Feat/open link (#7) @Hungerarray

## [v0.1.2] - 2025-09-24

- No changes

## [v0.1.1] - 2025-09-24

- No changes

## 🔄 Other Changes

- Refactor/remove relative imports (#3) @amankumarsingh77
- Refact: Rename project and minor changes (#4) @amankumarsingh77
[v0.3.0]: https://github.com/vertexcover-io/linkedin-spider/compare/v0.2.7...v0.3.0
