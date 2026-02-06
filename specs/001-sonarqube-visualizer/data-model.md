# Data Model: SonarQube Report Visualizer

**Feature**: 001-sonarqube-visualizer  
**Date**: 2026-02-06  
**Purpose**: Database schema and entity relationships

## Overview

This document defines the data model for storing SonarQube connections, projects, metrics snapshots, and user preferences. The schema is designed for SQLite with SQLAlchemy ORM.

## Database Schema

### Entity Relationship Diagram

```text
┌─────────────────────┐
│    Connection       │
│─────────────────────│
│ id (PK)             │
│ name                │
│ server_url          │
│ server_version      │
│ is_active           │
│ last_validated_at   │
│ created_at          │
│ updated_at          │
└──────────┬──────────┘
           │
           │ 1:N
           │
┌──────────▼──────────┐
│      Project        │
│─────────────────────│
│ id (PK)             │
│ connection_id (FK)  │
│ project_key         │
│ name                │
│ description         │
│ last_analysis_date  │
│ created_at          │
│ updated_at          │
└──────────┬──────────┘
           │
           │ 1:N
           │
┌──────────▼──────────┐
│   MetricsSnapshot   │
│─────────────────────│
│ id (PK)             │
│ project_id (FK)     │
│ branch_name         │
│ analysis_date       │
│ fetch_timestamp     │
│ bugs_count          │
│ vulnerabilities_cnt │
│ code_smells_count   │
│ coverage_pct        │
│ duplications_pct    │
│ quality_gate_status │
│ quality_gate_detail │
│ severity_breakdown  │ (JSON)
│ ncloc               │
│ created_at          │
└─────────────────────┘

┌─────────────────────┐
│   UserPreferences   │
│─────────────────────│
│ id (PK)             │
│ key                 │
│ value               │ (JSON)
│ updated_at          │
└─────────────────────┘
```

## Entity Definitions

### 1. Connection

Represents an authenticated connection to a SonarQube server.

**Table Name**: `connections`

**Fields**:

| Field             | Type        | Constraints                         | Description                                                     |
| ----------------- | ----------- | ----------------------------------- | --------------------------------------------------------------- |
| id                | Integer     | PK, Auto-increment                  | Unique connection identifier                                    |
| name              | String(255) | NOT NULL, UNIQUE                    | User-friendly connection name (e.g., "Production SonarQube")    |
| server_url        | String(512) | NOT NULL                            | SonarQube server URL (e.g., "https://sonarqube.company.com")    |
| server_version    | String(50)  | NULL                                | SonarQube server version (e.g., "9.9.0") detected on connection |
| is_active         | Boolean     | NOT NULL, DEFAULT TRUE              | Whether this connection is currently active                     |
| last_validated_at | DateTime    | NULL                                | Timestamp of last successful connection validation              |
| created_at        | DateTime    | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation timestamp                                       |
| updated_at        | DateTime    | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record last update timestamp                                    |

**Note**: Authentication token is NOT stored in database. It's stored in browser localStorage and passed with each API request.

**Indexes**:

- Primary key on `id`
- Unique index on `name`
- Index on `server_url` for faster lookups

**Validation Rules**:

- `server_url` must be valid HTTPS URL (HTTP allowed with warning)
- `name` must be non-empty after trim
- `server_version` follows semantic versioning pattern (optional)

### 2. Project

Represents a SonarQube project tracked by the visualizer.

**Table Name**: `projects`

**Fields**:

| Field              | Type        | Constraints                         | Description                                        |
| ------------------ | ----------- | ----------------------------------- | -------------------------------------------------- |
| id                 | Integer     | PK, Auto-increment                  | Unique project identifier                          |
| connection_id      | Integer     | FK → connections.id, NOT NULL       | Parent connection                                  |
| project_key        | String(255) | NOT NULL                            | SonarQube project key (e.g., "com.company:my-app") |
| name               | String(512) | NOT NULL                            | Project display name                               |
| description        | Text        | NULL                                | Project description from SonarQube                 |
| last_analysis_date | DateTime    | NULL                                | Timestamp of most recent analysis in SonarQube     |
| created_at         | DateTime    | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation timestamp                          |
| updated_at         | DateTime    | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record last update timestamp                       |

**Indexes**:

- Primary key on `id`
- Foreign key on `connection_id`
- Unique composite index on `(connection_id, project_key)` - prevents duplicate projects per connection
- Index on `last_analysis_date` for sorting

**Validation Rules**:

- `project_key` must match SonarQube key format (alphanumeric, dots, colons, hyphens)
- `name` must be non-empty after trim
- Cannot delete project if metrics snapshots exist (CASCADE or prevent based on preference)

**Relationships**:

- **belongs to** Connection (N:1)
- **has many** MetricsSnapshots (1:N)

### 3. MetricsSnapshot

Represents quality metrics captured at a specific point in time for a project branch.

**Table Name**: `metrics_snapshots`

**Fields**:

| Field                 | Type         | Constraints                         | Description                                                                   |
| --------------------- | ------------ | ----------------------------------- | ----------------------------------------------------------------------------- |
| id                    | Integer      | PK, Auto-increment                  | Unique snapshot identifier                                                    |
| project_id            | Integer      | FK → projects.id, NOT NULL          | Parent project                                                                |
| branch_name           | String(255)  | NOT NULL, DEFAULT 'main'            | Branch name (e.g., "main", "develop", "feature-x")                            |
| analysis_date         | DateTime     | NOT NULL                            | When SonarQube performed the analysis                                         |
| fetch_timestamp       | DateTime     | NOT NULL, DEFAULT CURRENT_TIMESTAMP | When we fetched this data from SonarQube                                      |
| bugs_count            | Integer      | NOT NULL, DEFAULT 0                 | Count of bug issues                                                           |
| vulnerabilities_count | Integer      | NOT NULL, DEFAULT 0                 | Count of vulnerability issues                                                 |
| code_smells_count     | Integer      | NOT NULL, DEFAULT 0                 | Count of code smell issues                                                    |
| coverage_pct          | Decimal(5,2) | NULL                                | Code coverage percentage (0.00 - 100.00)                                      |
| duplications_pct      | Decimal(5,2) | NULL                                | Duplicated lines percentage (0.00 - 100.00)                                   |
| quality_gate_status   | String(20)   | NOT NULL                            | Quality gate status: "OK", "WARN", "ERROR"                                    |
| quality_gate_details  | Text JSON    | NULL                                | JSON object with failing conditions (if any)                                  |
| severity_breakdown    | Text JSON    | NULL                                | JSON object: {"blocker": N, "critical": N, "major": N, "minor": N, "info": N} |
| ncloc                 | Integer      | NULL                                | Non-commenting lines of code                                                  |
| created_at            | DateTime     | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation timestamp                                                     |

**Indexes**:

- Primary key on `id`
- Foreign key on `project_id`
- Composite index on `(project_id, branch_name, analysis_date)` for efficient querying
- Index on `fetch_timestamp` for staleness checks

**Validation Rules**:

- `bugs_count`, `vulnerabilities_count`, `code_smells_count` must be >= 0
- `coverage_pct`, `duplications_pct` must be between 0.00 and 100.00 (or NULL)
- `quality_gate_status` must be one of: "OK", "WARN", "ERROR"
- `severity_breakdown` must be valid JSON matching expected schema
- `analysis_date` must be <= `fetch_timestamp`

**Relationships**:

- **belongs to** Project (N:1)

**Special Considerations**:

- Multiple snapshots per project/branch allowed (for historical trending)
- `fetch_timestamp` used for staleness indicators in UI
- JSON fields (`quality_gate_details`, `severity_breakdown`) allow flexible storage without schema changes

### 4. UserPreferences

Stores user-specific preferences and visualization configuration.

**Table Name**: `user_preferences`

**Fields**:

| Field      | Type        | Constraints                         | Description                                                  |
| ---------- | ----------- | ----------------------------------- | ------------------------------------------------------------ |
| id         | Integer     | PK, Auto-increment                  | Unique preference identifier                                 |
| key        | String(255) | NOT NULL, UNIQUE                    | Preference key (e.g., "dashboard.chart_types", "theme.mode") |
| value      | Text JSON   | NOT NULL                            | Preference value as JSON                                     |
| updated_at | DateTime    | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update timestamp                                        |

**Indexes**:

- Primary key on `id`
- Unique index on `key`

**Predefined Keys**:

- `dashboard.selected_projects`: Array of project IDs to show in dashboard
- `dashboard.chart_types`: Array of enabled chart types ["line", "bar", "gauge"]
- `dashboard.time_range`: Default time range for trends (e.g., "30d", "90d", "1y")
- `ui.theme`: UI theme preference ("light", "dark", "auto")
- `refresh.auto_prompt_threshold`: Hours before prompting user to refresh stale data

**Validation Rules**:

- `key` must follow dot-notation naming convention
- `value` must be valid JSON
- Specific keys have specific value schemas (validated in application layer)

## Data Types and Mappings

### SQLAlchemy → SQLite Mapping

| SQLAlchemy Type | SQLite Storage | Notes                                                |
| --------------- | -------------- | ---------------------------------------------------- |
| Integer         | INTEGER        | Auto-increment for PKs                               |
| String(N)       | TEXT           | SQLite TEXT type, N is logical limit enforced by ORM |
| Text            | TEXT           | Unlimited length                                     |
| Boolean         | INTEGER        | 0=False, 1=True                                      |
| DateTime        | TEXT           | ISO 8601 format: "YYYY-MM-DD HH:MM:SS"               |
| Decimal(M,N)    | REAL           | Floating point, precision hints for validation       |
| JSON            | TEXT           | JSON string, validated on read/write                 |

### JSON Schema Definitions

#### severity_breakdown

```json
{
  "type": "object",
  "properties": {
    "blocker": { "type": "integer", "minimum": 0 },
    "critical": { "type": "integer", "minimum": 0 },
    "major": { "type": "integer", "minimum": 0 },
    "minor": { "type": "integer", "minimum": 0 },
    "info": { "type": "integer", "minimum": 0 }
  },
  "additionalProperties": false
}
```

#### quality_gate_details

```json
{
  "type": "object",
  "properties": {
    "conditions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "metric": { "type": "string" },
          "status": { "type": "string", "enum": ["OK", "WARN", "ERROR"] },
          "actualValue": { "type": "string" },
          "comparator": { "type": "string" },
          "errorThreshold": { "type": "string" }
        },
        "required": ["metric", "status"]
      }
    }
  }
}
```

## Migration Strategy

### Initial Schema (v0.1.0)

Create all tables using `backend/src/db/schema.sql`:

- Simple SQL script with CREATE TABLE statements
- Run on first application startup if database doesn't exist
- Includes all indexes and foreign key constraints

### Future Migrations

When schema changes required:

1. Version database schema (add `schema_version` table)
2. Write migration scripts: `migrations/001_add_column_x.sql`
3. Consider adding Alembic if migrations become complex

## Database Concurrency & Conflict Resolution

### SQLite Concurrency Model

- **Single Writer**: SQLite allows only one write transaction at a time
- **Multiple Readers**: Multiple simultaneous read transactions allowed
- **WAL Mode**: Enabled for better concurrency (readers don't block writers during commit)

### Write Conflict Resolution Strategy

**Automatic Retry with Exponential Backoff**:

1. **First Attempt**: Execute write operation
2. **On SQLITE_BUSY or SQLITE_LOCKED**:
   - Retry 1: Wait 100ms, retry write
   - Retry 2: Wait 200ms, retry write
   - Retry 3: Wait 400ms, retry write
3. **After 3 Failed Retries**: Return error to API layer with 409 Conflict status
4. **User Action**: Frontend displays retry prompt, user can retry the operation

**SQLAlchemy Configuration**:

```python
# Connection string with timeout
engine = create_engine(
    'sqlite:///data/sonarq-visualizer.db',
    connect_args={
        'timeout': 30,  # 30 second timeout for lock acquisition
        'check_same_thread': False  # Allow multi-threaded access
    }
)

# Enable WAL mode for better concurrency
with engine.connect() as conn:
    conn.execute(text("PRAGMA journal_mode=WAL"))
    conn.execute(text("PRAGMA busy_timeout=30000"))  # 30s busy timeout
```

**Transaction Boundaries**:

- **Single Entity Operations**: Auto-commit per operation (default SQLAlchemy behavior)
- **Multi-Project Sync**: Explicit transaction with rollback on >50% failure (FR-024)
- **Batch Metrics Insert**: One transaction per project snapshot (fail independently)

## Query Patterns

### Common Queries

1. **Get all projects with latest metrics**:

```sql
SELECT p.*, ms.*
FROM projects p
LEFT JOIN metrics_snapshots ms ON ms.id = (
  SELECT id FROM metrics_snapshots
  WHERE project_id = p.id AND branch_name = 'main'
  ORDER BY analysis_date DESC
  LIMIT 1
)
WHERE p.connection_id = ?
ORDER BY p.name;
```

2. **Get metric trends for project**:

```sql
SELECT analysis_date, bugs_count, vulnerabilities_count,
       code_smells_count, coverage_pct, quality_gate_status
FROM metrics_snapshots
WHERE project_id = ? AND branch_name = ?
ORDER BY analysis_date DESC
LIMIT 30;
```

3. **Check data staleness**:

```sql
SELECT p.id, p.name,
       MAX(ms.fetch_timestamp) as last_fetch,
       (julianday('now') - julianday(MAX(ms.fetch_timestamp))) * 24 as hours_since_fetch
FROM projects p
JOIN metrics_snapshots ms ON ms.project_id = p.id
WHERE p.connection_id = ?
GROUP BY p.id
HAVING hours_since_fetch > 24;
```

## Performance Considerations

- **Indexes**: Critical for project lists and metrics queries
- **JSON queries**: SQLite 3.38+ has JSON functions; use for filtering but avoid in hot paths
- **Pagination**: Implement LIMIT/OFFSET for large project lists
- **Archival**: Consider retaining only last N snapshots per project/branch if storage grows large

## Testing Strategy

### Property-Based Tests (Hypothesis)

1. **Round-trip**: Insert random entity → retrieve → assert equality
2. **Constraints**: Generate invalid data (negative counts, out-of-range percentages) → assert validation errors
3. **Relationships**: Delete parent → assert children behavior (cascade or prevent)
4. **JSON fields** Generate random valid/invalid JSON → assert parsing/validation

### Integration Tests

1. Create connection → verify stored correctly
2. Add project to connection → verify FK relationship
3. Add metrics snapshot → query trends → verify ordering and calculations
4. Update preference → retrieve → verify JSON round-trip

## References

- SQLAlchemy Documentation: https://docs.sqlalchemy.org/en/20/
- SQLite JSON Functions: https://www.sqlite.org/json1.html
- Database Normalization: https://en.wikipedia.org/wiki/Database_normalization
