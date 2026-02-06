# Tasks: SonarQube Report Visualizer

**Input**: Design documents from `/specs/001-sonarqube-visualizer/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included per constitution requirement (TDD approach with property-based testing is NON-NEGOTIABLE)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Web app structure: `backend/src/`, `backend/tests/`, `frontend/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project directory structure: backend/src/{models,services,api,db,utils}, backend/tests/{unit,integration,property}, frontend/{css,js,assets}, docs/, data/
- [x] T002 Initialize Python project with requirements.txt including: fastapi, uvicorn, sqlalchemy, requests, pytest, pytest-cov, hypothesis, black, flake8, mypy
- [x] T003 [P] Configure Python tooling in pyproject.toml: black (line-length=100), mypy (strict=true), pytest settings
- [x] T004 [P] Setup .gitignore for Python, SQLite, editor files, and `__pycache__`
- [x] T005 [P] Create README.md with project overview and quickstart (≤5 steps from quickstart.md)
- [x] T006 [P] Initialize CHANGELOG.md with version 0.1.0 entry (Keep a Changelog format)
- [x] T007 [P] Setup frontend package.json for ESLint and development tooling
- [x] T008 [P] Configure ESLint in .eslintrc.json for vanilla JavaScript (ES6+)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T009 Create database schema in backend/src/db/schema.sql with tables: connections, projects, metrics_snapshots, user_preferences (per data-model.md)
- [x] T010 Implement database initialization in backend/src/db/init.py with SQLite connection, WAL mode, foreign keys enforcement
- [x] T011 [P] Create SQLAlchemy base configuration in backend/src/db/base.py with declarative base and session factory
- [x] T012 [P] Implement structured logging utility in backend/src/utils/logger.py with JSON format for errors/API calls
- [x] T013 [P] Create configuration management in backend/src/utils/config.py for environment variables and database path
- [x] T014 [P] Implement error handling utilities in backend/src/utils/errors.py with custom exception classes
- [x] T015 Create FastAPI application in backend/src/main.py with CORS middleware, CSP headers, and router registration
- [x] T016 Implement health check endpoint in backend/src/api/health.py with GET /api/v1/health returning status and version
- [x] T017 Create application entrypoint in backend/app.py with init-db CLI command for database initialization
- [x] T018 [P] Setup frontend HTML structure in frontend/index.html with responsive meta tags and main layout sections
- [x] T019 [P] Create base CSS styles in frontend/css/styles.css with CSS variables, mobile-first responsive design, flexbox/grid layouts
- [x] T020 [P] Implement utility functions in frontend/js/utils.js for date formatting, DOM helpers, localStorage operations

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Connect to SonarQube Instance (Priority: P1) 🎯 MVP

**Goal**: Enable users to configure and authenticate against a SonarQube server, validating credentials and storing connection details

**Independent Test**: Provide valid SonarQube credentials and verify successful connection validation without fetching any report data

### Tests for User Story 1 ✅

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T021 [P] [US1] Unit test for Connection model in backend/tests/unit/models/test_connection.py with validation rules
- [x] T022 [P] [US1] Property-based test for connection validation edge cases in backend/tests/property/test_connection_validation.py using Hypothesis (URL formats, timeout scenarios)
- [x] T023 [P] [US1] Integration test for connection create endpoint in backend/tests/integration/test_connections_api.py with mock SonarQube responses
- [x] T024 [P] [US1] Integration test for connection validation flow in backend/tests/integration/test_connection_validation.py with success/failure scenarios

### Implementation for User Story 1

- [x] T025 [P] [US1] Create Connection SQLAlchemy model in backend/src/models/connection.py with fields: id, name, server_url, server_version, is_active, last_validated_at, timestamps
- [x] T026 [P] [US1] Create connection repository in backend/src/db/repositories/connection_repository.py with CRUD operations
- [x] T027 [US1] Implement SonarQube API client in backend/src/services/sonarqube_client.py with token authentication, /api/system/status endpoint, 30s timeout, retry logic with exponential backoff
- [x] T028 [US1] Implement connection service in backend/src/services/connection_service.py with create, validate, list, update, delete operations
- [x] T029 [US1] Create connections API router in backend/src/api/connections.py with POST /connections, GET /connections, GET /connections/{id}, PUT /connections/{id}, DELETE /connections/{id}
- [x] T030 [US1] Implement connection validation endpoint in backend/src/api/connections.py POST /connections/{id}/validate with token validation and server info retrieval
- [x] T031 [US1] Add input validation and error handling for connections API with clear error messages per FR-009
- [x] T032 [US1] Implement structured logging for connection operations in backend/src/services/connection_service.py
- [x] T033 [US1] Create frontend connection form in frontend/index.html with fields: name, server_url, token inputs and Test/Save buttons
- [x] T034 [US1] Implement frontend API client in frontend/js/api-client.js with fetch wrapper, authorization header injection, error handling
- [x] T035 [US1] Implement connection management UI logic in frontend/js/app.js with form submission, validation feedback, localStorage token storage
- [x] T036 [US1] Add connection list display in frontend with status indicators and edit/delete actions
- [x] T037 [US1] Style connection UI components in frontend/css/styles.css with responsive layout and visual feedback

**Checkpoint**: At this point, User Story 1 should be fully functional - users can create, validate, list, and delete SonarQube connections

---

## Phase 4: User Story 2 - Fetch and Display Project Metrics (Priority: P2)

**Goal**: Enable users to retrieve quality metrics for specific SonarQube projects and view them in structured format with historical trends

**Independent Test**: Select a project from authenticated SonarQube instance and verify metrics are correctly fetched and displayed in tabular format

### Tests for User Story 2 ✅

- [ ] T038 [P] [US2] Unit test for Project model in backend/tests/unit/models/test_project.py with validation rules
- [ ] T039 [P] [US2] Unit test for MetricsSnapshot model in backend/tests/unit/models/test_metrics_snapshot.py with boundary validation (FR-032)
- [ ] T040 [P] [US2] Property-based test for metrics aggregation in backend/tests/property/test_metrics_aggregation.py using Hypothesis (various metric ranges per research.md)
- [ ] T041 [P] [US2] Property-based test for SonarQube API response parsing in backend/tests/property/test_sonarqube_parsing.py with varied JSON structures
- [ ] T042 [P] [US2] Integration test for project sync endpoint in backend/tests/integration/test_projects_sync.py with mock SonarQube API
- [ ] T043 [P] [US2] Integration test for metrics refresh flow in backend/tests/integration/test_metrics_refresh.py with partial failure scenarios (FR-024)
- [ ] T043b [P] [US2] Integration test for SonarQube edition compatibility in backend/tests/integration/test_sonarqube_editions.py with mock Community (8.x+) and Enterprise (9.x+) API responses per FR-012

### Implementation for User Story 2

- [ ] T044 [P] [US2] Create Project SQLAlchemy model in backend/src/models/project.py with fields: id, connection_id (FK), project_key, name, description, last_analysis_date, timestamps
- [ ] T045 [P] [US2] Create MetricsSnapshot SQLAlchemy model in backend/src/models/metrics_snapshot.py with all metrics fields per data-model.md including JSON fields for severity_breakdown and quality_gate_details
- [ ] T046 [P] [US2] Create project repository in backend/src/db/repositories/project_repository.py with CRUD operations and pagination support
- [ ] T047 [P] [US2] Create metrics repository in backend/src/db/repositories/metrics_repository.py with snapshot storage and retrieval operations
- [ ] T048 [US2] Extend SonarQube API client in backend/src/services/sonarqube_client.py with /api/projects/search, /api/measures/component, /api/project_branches/list endpoints
- [ ] T049 [US2] Implement metrics parsing and validation in backend/src/services/sonarqube_client.py with boundary checks (FR-032) and malformed response handling (FR-028)
- [ ] T050 [US2] Implement project service in backend/src/services/project_service.py with sync_projects_from_sonarqube method handling partial failures per FR-024
- [ ] T051 [US2] Implement metrics service in backend/src/services/metrics_service.py with fetch_and_store_metrics, calculate_staleness (FR-027), get_historical_metrics operations
- [ ] T052 [US2] Create projects API router in backend/src/api/projects.py with GET /connections/{id}/projects (with pagination FR-030), POST /connections/{id}/projects/sync, GET /projects/{id}, GET /projects/{id}/branches
- [ ] T053 [US2] Create metrics API router in backend/src/api/metrics.py with GET /projects/{id}/metrics, POST /projects/{id}/metrics/refresh
- [ ] T054 [US2] Implement rate limiting error handling (FR-020) and token expiration detection (FR-031) in backend/src/services/sonarqube_client.py
- [ ] T055 [US2] Add structured logging for all metrics operations in backend/src/services/metrics_service.py per FR-034
- [ ] T056 [US2] Create project list UI in frontend/index.html with search/filter inputs and sync button
- [ ] T057 [US2] Implement project list rendering in frontend/js/app.js with pagination controls and staleness indicators (FR-019, FR-027)
- [ ] T058 [US2] Create project detail view in frontend/index.html with metrics display table and refresh button
- [ ] T059 [US2] Implement metrics display logic in frontend/js/app.js with quality gate status highlighting, severity breakdown, and historical comparison
- [ ] T060 [US2] Add branch selector UI in frontend for multi-branch project support
- [ ] T061 [US2] Style project list and metrics display in frontend/css/styles.css with responsive tables, status indicators, and mobile-friendly layout

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - users can connect to SonarQube, sync projects, and view metrics

---

## Phase 5: User Story 3 - Generate Aesthetic Visualizations (Priority: P3)

**Goal**: Enable users to view project metrics through interactive charts and multi-project dashboard with comparative visualizations

**Independent Test**: Load previously fetched metrics and generate various chart types (line charts for trends, pie charts for distribution, gauge for coverage)

### Tests for User Story 3 ✅

- [ ] T062 [P] [US3] Property-based test for dashboard aggregation calculations in backend/tests/property/test_dashboard_aggregation.py using Hypothesis (FR-029 formulas)
- [ ] T063 [P] [US3] Integration test for dashboard endpoint in backend/tests/integration/test_dashboard_api.py with multiple projects and aggregation verification
- [ ] T064 [P] [US3] Integration test for preferences management in backend/tests/integration/test_preferences_api.py

### Implementation for User Story 3

- [ ] T065 [P] [US3] Create UserPreferences SQLAlchemy model in backend/src/models/user_preferences.py with key-value JSON storage
- [ ] T066 [P] [US3] Create preferences repository in backend/src/db/repositories/preferences_repository.py with get/set operations
- [ ] T067 [US3] Implement dashboard aggregation service in backend/src/services/dashboard_service.py with multi-project statistics calculation per FR-029
- [ ] T068 [US3] Implement preferences service in backend/src/services/preferences_service.py with predefined keys validation
- [ ] T069 [US3] Create dashboard API router in backend/src/api/dashboard.py with GET /dashboard supporting connection_id and project_ids filters
- [ ] T070 [US3] Create preferences API router in backend/src/api/preferences.py with GET /preferences, PUT /preferences
- [ ] T071 [US3] Add Chart.js library to frontend/index.html with lazy loading strategy per research.md
- [ ] T072 [US3] Implement chart rendering module in frontend/js/charts.js with functions for line charts (trends), pie charts (severity distribution), gauge charts (coverage with color thresholds: red <50%, yellow 50-80%, green >80% per research.md)
- [ ] T073 [US3] Create multi-project dashboard UI in frontend/index.html with project cards, aggregate statistics section, and comparison view
- [ ] T074 [US3] Implement dashboard data fetching and rendering in frontend/js/app.js with filter controls (connection, time range, metrics selection)
- [ ] T074b [US3] Implement filtering capabilities in frontend/js/app.js for metric categories (bugs/vulnerabilities/code smells/coverage/duplications) and time range selection per FR-014
- [ ] T075 [US3] Add chart interactivity in frontend/js/charts.js with tooltips, click-to-drill-down from dashboard to project detail
- [ ] T076 [US3] Implement visualization preferences in frontend/js/app.js with localStorage persistence for chart types, themes, time ranges
- [ ] T077 [US3] Create responsive dashboard layout in frontend/css/styles.css with mobile (stacked), tablet (2-column), desktop (3-column) breakpoints per research.md
- [ ] T078 [US3] Style charts and visualizations in frontend/css/styles.css with consistent color scheme and accessibility considerations

**Checkpoint**: All user stories should now be independently functional - users can connect, fetch metrics, and visualize data with interactive charts

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and ensure production readiness

- [ ] T079 [P] Create architecture documentation in docs/architecture.md with system design, component diagram, data flow per plan.md
- [ ] T080 [P] Create API documentation in docs/api.md referencing contracts/api.yaml with usage examples
- [ ] T081 [P] Create development guide in docs/development.md with setup instructions, testing guidelines, contribution workflow
- [ ] T082 [P] Create security documentation in docs/security.md with threat model, token storage security, CSP implementation details per research.md
- [ ] T083 [P] Implement export functionality in backend/src/api/metrics.py for CSV/JSON export per FR-013
- [ ] T084 [P] Add export UI buttons in frontend with download handlers in frontend/js/app.js
- [ ] T085 [P] Optimize frontend performance: implement debouncing (300ms) for search inputs, virtual scrolling for large project lists (>100 projects) per FR-033
- [ ] T086 [P] Add comprehensive error messages for all user-facing errors following FR-009 clarity requirements
- [ ] T087 Configure GitHub Actions CI pipeline in .github/workflows/ci.yml with three stages: lint (black, flake8, mypy, ESLint), unit+PBT tests (100 examples), integration tests
- [ ] T088 Add pre-commit hooks configuration for local linting enforcement
- [ ] T089 Run full test suite and verify all tests pass: unit tests, property-based tests (500 examples), integration tests
- [ ] T090 Validate quickstart.md by following all 5 steps on fresh environment and documenting any improvements
- [ ] T091 Final code review and refactoring for consistency, removing TODOs and debug code
- [ ] T092 Update CHANGELOG.md with all implemented features for v0.1.0 release
- [ ] T093 Create v0.1.0 git tag and prepare release notes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User Story 1 (US1) can start after Foundational
  - User Story 2 (US2) can start after Foundational (integrates with US1 but independently testable)
  - User Story 3 (US3) can start after Foundational (reads from US2 data but independently testable with existing data)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 connection data but is independently testable with an existing connection
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US2 metrics data but is independently testable with existing metrics snapshots

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD approach)
- Models before services (repositories and business logic depend on models)
- Services before API endpoints (endpoints orchestrate services)
- API endpoints before frontend implementation (frontend consumes API)
- Core implementation before UI styling

### Parallel Opportunities

**Within Setup (Phase 1)**:

- T003, T004, T005, T006, T007, T008 can all run in parallel

**Within Foundational (Phase 2)**:

- T011, T012, T013, T014 can run in parallel
- T018, T019, T020 can run in parallel (frontend foundational work)

**Within User Story 1 (Phase 3)**:

- Tests T021, T022, T023, T024 can run in parallel
- Models T025, T026 can run in parallel

**Within User Story 2 (Phase 4)**:

- Tests T038, T039, T040, T041, T042, T043, T043b can run in parallel
- Models T044, T045, T046, T047 can run in parallel

**Within User Story 3 (Phase 5)**:

- Tests T062, T063, T064 can run in parallel
- Models T065, T066 can run in parallel

**Within Polish (Phase 6)**:

- Documentation tasks T079, T080, T081, T082 can run in parallel
- Export tasks T083, T084 can run in parallel
- Performance tasks T085, T086 can run in parallel

**Cross-Story Parallel Work** (if multiple developers):

- Once Foundational is complete, User Story 1, 2, and 3 can be worked on in parallel by different team members
- Each story's tests can be written in parallel by a QA/test engineer while implementation proceeds

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (write all tests first):
Task T021: "Unit test for Connection model in backend/tests/unit/models/test_connection.py"
Task T022: "Property-based test for connection validation in backend/tests/property/test_connection_validation.py"
Task T023: "Integration test for connection create endpoint in backend/tests/integration/test_connections_api.py"
Task T024: "Integration test for connection validation flow in backend/tests/integration/test_connection_validation.py"

# Verify all tests FAIL (no implementation yet)

# Launch model creation in parallel:
Task T025: "Create Connection model in backend/src/models/connection.py"
Task T026: "Create connection repository in backend/src/db/repositories/connection_repository.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (8 tasks)
2. Complete Phase 2: Foundational (12 tasks) - CRITICAL blocker
3. Complete Phase 3: User Story 1 (17 tasks)
4. **STOP and VALIDATE**:
   - Run all US1 tests (should pass)
   - Manually test: create connection, validate with real SonarQube server, list connections
   - Follow quickstart.md steps 1-5
5. **MVP READY**: Users can now connect to SonarQube and validate access

**Total MVP Task Count**: 37 tasks

### Incremental Delivery

1. **Foundation** (Phases 1-2): 20 tasks → Foundation ready
2. **MVP** (+ Phase 3): 37 total tasks → User Story 1 complete → Deploy/Demo
3. **Core Value** (+ Phase 4): 62 total tasks → User Story 2 complete → Users can fetch and view metrics → Deploy/Demo
4. **Full Feature** (+ Phase 5): 80 total tasks → User Story 3 complete → Visual dashboards → Deploy/Demo
5. **Production Ready** (+ Phase 6): 95 total tasks → Polish complete → Production deployment

Each increment adds value without breaking previous stories.

### Parallel Team Strategy

With 3 developers available:

**Phase 1-2** (Week 1): All developers work together on foundational setup

- Dev A: Backend infrastructure (T009-T017)
- Dev B: Frontend infrastructure (T018-T020) + Tooling (T001-T008)
- Dev C: Documentation templates + CI setup scaffold

**Phase 3-5** (Week 2-4): Developers split by user story once foundation is ready

- Dev A: User Story 1 (T021-T037) - Connection management
- Dev B: User Story 2 (T038-T061) - Metrics fetching
- Dev C: User Story 3 (T062-T078) - Visualizations

**Phase 6** (Week 5): All developers on polish tasks

- Dev A: Documentation (T079-T082)
- Dev B: Export & optimization (T083-T086)
- Dev C: CI, testing, validation (T087-T093)

---

## Task Summary

- **Total Tasks**: 95
- **Setup Phase**: 8 tasks
- **Foundational Phase**: 12 tasks (BLOCKS all user stories)
- **User Story 1 (P1)**: 17 tasks (5 test tasks + 12 implementation tasks) 🎯 MVP
- **User Story 2 (P2)**: 25 tasks (7 test tasks + 18 implementation tasks)
- **User Story 3 (P3)**: 18 tasks (3 test tasks + 15 implementation tasks)
- **Polish Phase**: 15 tasks

**Test Coverage**: 15 test tasks (16% of total) including unit, property-based (Hypothesis), and integration tests per constitution

**Parallel Opportunities**: 32+ tasks marked [P] can run in parallel within their phases

**Independent Test Criteria**:

- **US1**: Create connection with valid credentials → Validate → Confirm success message without fetching projects
- **US2**: Select existing connection → Sync projects → Select project → View metrics in table → Verify staleness indicator
- **US3**: Load dashboard with existing metrics → Verify charts render → Compare 2+ projects → Drill down to project detail

**Suggested MVP Scope**: Complete through Phase 3 (User Story 1) = 37 tasks

---

## Notes

- [P] tasks = different files, no dependencies within same phase
- [Story] label maps task to specific user story for traceability (US1, US2, US3)
- Each user story is independently completable and testable per specification requirements
- Tests written FIRST per TDD approach (constitution Principle I - NON-NEGOTIABLE)
- Property-based tests use Hypothesis with test ranges defined in research.md
- All file paths follow project structure from plan.md
- Commit after each task or logical group of parallel tasks
- Stop at checkpoints to validate story independence
- SQLite database location: `./data/sonarq-visualizer.db`
- Frontend served by FastAPI backend, no separate static server needed
