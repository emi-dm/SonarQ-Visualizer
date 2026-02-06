# API Documentation

This document provides a practical overview of the REST API. For the full contract, see `specs/001-sonarqube-visualizer/contracts/api.yaml`.

## Base URL

- Local development: `http://localhost:8000/api/v1`

## Authentication

Most endpoints do not require backend auth. SonarQube tokens are passed in request bodies for operations that call SonarQube directly.

## Key Endpoints

### Health

- `GET /health` — API status and version

### Connections

- `GET /connections` — list all connections
- `POST /connections` — create a connection
- `GET /connections/{connectionId}` — get connection details
- `PUT /connections/{connectionId}` — update connection
- `DELETE /connections/{connectionId}` — delete connection
- `POST /connections/{connectionId}/validate` — validate connection

### Projects

- `GET /connections/{connectionId}/projects` — list projects with pagination
- `POST /connections/{connectionId}/projects/sync` — sync projects from SonarQube
- `GET /projects/{projectId}` — project details
- `GET /projects/{projectId}/branches` — list branches with stored metrics

### Metrics

- `GET /projects/{projectId}/metrics` — list historical snapshots
- `POST /projects/{projectId}/metrics/refresh` — fetch and store latest metrics
- `GET /projects/{projectId}/metrics/export` — export latest snapshot as JSON or CSV

#### Export Example

- JSON export: `GET /projects/{id}/metrics/export?format=json&branch=main`
- CSV export: `GET /projects/{id}/metrics/export?format=csv&branch=main`

## Error Format

Errors follow a consistent schema:

- `error`: error code
- `message`: human-readable description
- `details`: optional structured metadata

Example:

- `{"error":"NOT_FOUND","message":"No metrics snapshots found for this project","details":{"project_id":123,"branch_name":"main"}}`
