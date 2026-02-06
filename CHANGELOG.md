# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial project structure with backend and frontend directories
- Database schema for connections, projects, metrics snapshots, and user preferences
- FastAPI backend framework with REST API endpoints
- Connection management (create, validate, list, update, delete)
- Project synchronization from SonarQube instances
- Metrics fetching and storage with historical tracking
- Multi-project dashboard with aggregations
- Interactive visualizations using Chart.js
- Responsive frontend design for mobile, tablet, and desktop
- Property-based testing with Hypothesis
- Structured logging with JSON format
- Comprehensive test suite (unit, integration, property-based)

### Security

- Token storage in browser localStorage (documented security consideration)
- HTTPS requirement for SonarQube connections
- Content Security Policy (CSP) headers implementation
- Input validation to prevent SQL injection and XSS

## [0.1.0] - TBD

### Summary

Initial MVP release with core functionality:

- SonarQube connection management
- Project metrics fetching and display
- Basic visualizations and dashboard
- Offline capability with SQLite storage

[Unreleased]: https://github.com/username/sonarq-visualizer/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/username/sonarq-visualizer/releases/tag/v0.1.0
