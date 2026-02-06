# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Frontend served from port 8080 and launched before backend

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
