# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `backend/src/constants.py` with shared API/path constants to reduce duplicated literals
- Backward-compatible `init_db()` alias in `backend/src/db/init.py` for integration test compatibility

### Changed

- Frontend served from port 8080 and launched before backend
- FastAPI dependency injection signatures migrated to `Annotated[..., Depends(...)]` across API routers
- UTC datetime creation migrated away from `utcnow()` usage to timezone-aware sourcing with DB-safe normalization
- Route prefix and endpoint path usage centralized via constants in `backend/src/main.py` and API modules
- `CORSMiddleware` registration moved to the end of middleware setup in `backend/src/main.py`
- Optional Pydantic response/request fields now define explicit defaults where required
- Frontend lint-quality cleanup in `frontend/js/app.js` and `frontend/js/utils.js` (optional chaining, parseInt, nested ternary simplification)
- Duplicate CSS selector definitions consolidated in `frontend/css/styles.css`

### Fixed

- Syntax issues introduced by dependency signature refactors (`non-default argument follows default argument`)
- Naive/aware datetime comparison errors in metrics refresh/model validation flows
- Test database isolation issues by syncing runtime database path during test DB initialization
- Full test suite stability after Sonar-focused remediation (`74 passed`)

## [0.1.0] - 2026-02-06

### Summary

Initial MVP release with core functionality:

- SonarQube connection management
- Project metrics fetching and display
- Basic visualizations and dashboard
- Offline capability with SQLite storage

### Added

- Export latest metrics snapshot as JSON or CSV
- Project list debounced search and virtualized rendering for large lists
- Documentation set (architecture, API, development, security)
- CI pipeline for linting and tests
- Pre-commit hooks for local linting

### Fixed

- Quickstart commands updated to use correct backend module path

[Unreleased]: https://github.com/username/sonarq-visualizer/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/username/sonarq-visualizer/releases/tag/v0.1.0
