-- SonarQube Report Visualizer Database Schema
-- SQLite 3.x compatible
-- Created: 2026-02-06

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Connection table: SonarQube server connections
CREATE TABLE IF NOT EXISTS connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    server_url TEXT NOT NULL,
    server_version TEXT,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    last_validated_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_connections_server_url ON connections(server_url);
CREATE INDEX IF NOT EXISTS idx_connections_is_active ON connections(is_active);

-- Project table: SonarQube projects tracked by the visualizer
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    connection_id INTEGER NOT NULL,
    project_key TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    last_analysis_date DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (connection_id) REFERENCES connections(id) ON DELETE CASCADE,
    UNIQUE(connection_id, project_key)
);

CREATE INDEX IF NOT EXISTS idx_projects_connection_id ON projects(connection_id);
CREATE INDEX IF NOT EXISTS idx_projects_last_analysis_date ON projects(last_analysis_date);

-- MetricsSnapshot table: Quality metrics captured at specific points in time
CREATE TABLE IF NOT EXISTS metrics_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    branch_name TEXT NOT NULL DEFAULT 'main',
    analysis_date DATETIME NOT NULL,
    fetch_timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    bugs_count INTEGER NOT NULL DEFAULT 0,
    vulnerabilities_count INTEGER NOT NULL DEFAULT 0,
    code_smells_count INTEGER NOT NULL DEFAULT 0,
    coverage_pct REAL,
    duplications_pct REAL,
    quality_gate_status TEXT NOT NULL,
    quality_gate_details TEXT,
    severity_breakdown TEXT,
    ncloc INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_metrics_project_branch ON metrics_snapshots(project_id, branch_name);
CREATE INDEX IF NOT EXISTS idx_metrics_fetch_timestamp ON metrics_snapshots(fetch_timestamp);
CREATE INDEX IF NOT EXISTS idx_metrics_analysis_date ON metrics_snapshots(analysis_date);

-- UserPreferences table: User configuration and preferences
CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_key ON user_preferences(key);

-- Triggers for updated_at timestamps
CREATE TRIGGER IF NOT EXISTS update_connections_timestamp 
AFTER UPDATE ON connections
BEGIN
    UPDATE connections SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_projects_timestamp 
AFTER UPDATE ON projects
BEGIN
    UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_user_preferences_timestamp 
AFTER UPDATE ON user_preferences
BEGIN
    UPDATE user_preferences SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
