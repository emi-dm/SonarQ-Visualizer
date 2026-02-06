# Research: SonarQube Report Visualizer

**Feature**: 001-sonarqube-visualizer  
**Date**: 2026-02-06  
**Purpose**: Technical research and decision rationale for implementation

## Overview

This document captures research findings and technical decisions for building a web-based SonarQube metrics visualizer with Python backend, vanilla JavaScript frontend, and SQLite storage.

## Technology Stack Research

### 1. Backend Framework Choice

**Decision**: FastAPI

**Rationale**:

- Modern async Python framework with excellent performance
- Built-in OpenAPI/Swagger documentation generation (supports constitution's documentation requirement)
- Type hints and Pydantic validation align with mypy enforcement
- Simpler setup than Flask for REST APIs with automatic request/response validation
- Good SQLAlchemy integration for database ORM

**Alternatives Considered**:

- **Flask**: More mature and well-documented, but requires additional libraries for OpenAPI docs and validation. Rejected because FastAPI provides these features out-of-box and better supports async operations.
- **Django**: Full-featured but too heavy for this use case. Includes unnecessary features (admin panel, templating) that add complexity. Violates simplicity principle.

### 2. SonarQube API Client Strategy

**Decision**: Use `requests` library with custom client class wrapping API calls

**Rationale**:

- SonarQube REST API is well-documented and straightforward
- `requests` is the de-facto standard for HTTP in Python (simple, reliable)
- Custom wrapper allows us to:
  - Centralize authentication token handling
  - Implement retry logic for transient failures
  - Add structured logging for all API calls (constitution requirement)
  - Abstract API version differences between SonarQube 8.x and 9.x

**Alternatives Considered**:

- **python-sonarqube-api**: Third-party library exists but adds unnecessary dependency and may lag behind SonarQube API updates. Custom wrapper gives us more control and aligns with simplicity principle.

### 3. Database ORM and Migrations

**Decision**: SQLAlchemy for ORM, simple schema.sql for initial schema (no Alembic initially)

**Rationale**:

- SQLAlchemy is the standard Python ORM with excellent SQLite support
- Type-safe models align with mypy type checking
- For initial release (v0.1.0), a simple schema.sql file is sufficient
- Alembic can be added later if schema migrations become complex
- KISS principle: start simple, add complexity when needed

**Alternatives Considered**:

- **Raw SQL**: More control but increases verbosity and reduces type safety. Rejected for maintainability reasons.
- **Django ORM**: Requires using Django framework. Too heavy for our needs.

### 4. Frontend Charting Library

**Decision**: Chart.js v4

**Rationale**:

- Lightweight (~60KB minified) and no dependencies
- Responsive out-of-box (matches mobile/tablet requirement)
- Supports all needed chart types: line (trends), pie (distribution), gauge (coverage)
- Excellent documentation and large community
- MIT license (permissive)

**Alternatives Considered**:

- **D3.js**: Very powerful but requires significant code to achieve basic charts. Violates simplicity requirement for this use case.
- **Plotly.js**: Feature-rich but larger bundle size (~3MB). Overkill for our needs.
- **ApexCharts**: Good alternative but Chart.js is simpler and sufficient.

### 5. Frontend State Management and Storage

**Decision**: Browser localStorage for authentication token and configuration; no framework state management

**Rationale**:

- Vanilla JS with localStorage meets requirement (per spec clarifications)
- Simple key-value storage sufficient for token and basic config
- No need for complex state management library (Redux, MobX) without reactive framework
- Data fetching handled via fetch API directly from backend

**Security Note**: localStorage accessible to JavaScript; documented in assumptions section as acceptable risk for local/trusted deployment

**Alternatives Considered**:

- **SessionStorage**: Data lost on tab close. Rejected for poor UX (user would re-enter credentials frequently).
- **Cookies**: More secure with httpOnly flag but requires backend session management. Adds unnecessary complexity for local deployment use case.

### 6. Property-Based Testing Strategy

**Decision**: Hypothesis library for Python backend PBT

**Rationale**:

- Standard PBT library for Python with pytest integration
- Strategies for:
  - API response parsing: generate various JSON structures matching SonarQube API schemas
  - Database queries: generate date ranges, project lists of varying sizes
  - Staleness calculations: generate timestamps across timezones and edge cases (far past, future)
  - Metrics aggregation: generate metric values at boundaries (0, negatives, very large numbers)

**Key Properties to Test**:

1. **API Parsing Invariant**: Any valid SonarQube JSON response parses without exception
2. **Database Round-trip**: Saved data equals retrieved data (no lossy transformations)
3. **Staleness Display**: Time differences always positive, formatted consistently
4. **Metrics Math**: Aggregations (sum, average, trend) mathematically correct for any input list

**Alternatives Considered**:

- **No PBT**: Rely solely on example-based tests. Rejected as it violates constitution Principle I (NON-NEGOTIABLE).

### 7. CI/CD and Linting Configuration

**Decision**: GitHub Actions with three-stage pipeline

**Pipeline**:

1. **Lint**: black (formatter check), flake8 (style), mypy (types), ESLint (JS) - fast feedback
2. **Unit + PBT**: pytest with Hypothesis (limited seeds for PRs: 100 examples)
3. **Integration**: Full API and DB tests

**Rationale**:

- Fail fast: linting errors catch early without running slow tests
- PBT limited on PRs for speed; full exhaustive run (1000+ examples) on main branch
- Aligns with constitution: lint gates must pass before merge

**Configuration Files**:

- `pyproject.toml`: black, mypy, pytest config
- `.eslintrc.json`: ESLint rules for vanilla JS
- `.github/workflows/ci.yml`: GitHub Actions pipeline

### 8. Frontend Responsive Design Approach

**Decision**: CSS Flexbox and Grid with mobile-first design

**Rationale**:

- Modern CSS features well-supported in target browsers (Chrome, Firefox, Safari, Edge - last 2 versions)
- No CSS framework needed (Bootstrap, Tailwind) - keeps bundle small and minimalist
- Mobile-first ensures core functionality works on smallest screens first
- CSS variables for theming (colors, spacing) - easy customization

**Breakpoints**:

- Mobile: < 640px (stacked layout)
- Tablet: 640px - 1024px (2-column for dashboard)
- Desktop: > 1024px (3-column for multi-project dashboard)

**Alternatives Considered**:

- **Bootstrap**: Adds significant bundle size and opinionated styles. Violates minimalist requirement.
- **Tailwind CSS**: Utility-first approach nice but requires build step (PostCSS). Adds complexity for vanilla JS project.

## Security Research

### Token Storage Security

**Risk Assessment**:

- **localStorage** is accessible to any JavaScript running on same origin
- XSS vulnerabilities could expose tokens
- No encryption at rest in browser

**Mitigations**:

1. Document in README: tool intended for trusted environments only
2. Implement Content Security Policy (CSP) headers from backend
3. Never log tokens (even in debug mode)
4. Recommend HTTPS for SonarQube connections to prevent MITM
5. Add token rotation reminder in UI (e.g., "Last refreshed: X days ago")

**Threat Model**: Documented in `docs/security.md` (Phase 1 output)

### HTTPS Requirement

**Decision**: Require HTTPS for SonarQube API connections

**Rationale**:

- Prevents token interception in transit
- Most SonarQube instances (especially cloud) use HTTPS by default
- Add warning in UI if user attempts HTTP connection

## Best Practices Research

### 1. SonarQube API Usage

**Key Findings**:

- Use `/api/system/status` for connection validation (lightweight)
- Use `/api/projects/search` for project listing (paginated)
- Use `/api/measures/component` for metrics (efficient single endpoint)
- Use `/api/project_branches/list` for branch information
- Rate limiting: SonarQube Cloud has limits; implement exponential backoff

**Pagination Strategy**: SonarQube APIs use `ps` (page size) and `p` (page number); fetch all pages for complete data

### 2. SQLite for Web Application

**Considerations**:

- SQLite supports one writer at a time; acceptable for single-user or small team use
- WAL (Write-Ahead Logging) mode improves concurrency
- PRAGMA settings:
  - `journal_mode=WAL` - better concurrency
  - `synchronous=NORMAL` - balance safety and performance
  - `foreign_keys=ON` - enforce referential integrity

**Database Location**: `./data/sonarq-visualizer.db` (relative to app root)

### 3. Frontend Performance

**Optimizations**:

- Lazy load Chart.js (only when user navigates to visualizations)
- Debounce search/filter inputs (300ms delay)
- Virtual scrolling for large project lists (if > 100 projects)
- Cache API responses client-side (in-memory cache for session)

## Open Questions (Resolved)

None. All technical context questions resolved through this research.

## Implementation Priority

Based on this research:

1. **Critical Path** (MVP blockers):
   - FastAPI backend scaffolding with SQLAlchemy models
   - SonarQube API client with authentication
   - SQLite schema and basic CRUD operations
   - Minimal frontend: connection form, project list, metrics display (table)

2. **High Priority** (P1-P2 features):
   - Chart.js integration for basic trend charts
   - Staleness indicators
   - Refresh functionality
   - Mobile-responsive styling

3. **Medium Priority** (P3 enhancements):
   - Multi-project dashboard with comparison
   - Advanced filtering
   - Export to CSV/JSON
   - Performance optimizations (lazy loading, debouncing)

4. **Lower Priority** (polish):
   - Dark mode
   - Custom color themes
   - Advanced PBT coverage
   - Performance benchmarking

## References

- SonarQube Web API: https://docs.sonarqube.org/latest/extend/web-api/
- FastAPI Documentation: https://fastapi.tiangolo.com/
- Chart.js Documentation: https://www.chartjs.org/docs/latest/
- Hypothesis Documentation: https://hypothesis.readthedocs.io/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
