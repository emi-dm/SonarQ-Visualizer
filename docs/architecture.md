# Architecture

## Overview

SonarQube Report Visualizer is a local-first web app composed of a FastAPI backend, a vanilla JavaScript frontend, and a SQLite database. The backend provides a REST API for connections, projects, metrics, and dashboard aggregation. The frontend consumes the API and renders interactive views, while all metrics snapshots are cached locally for offline access.

## Component Diagram

Browser (HTML/CSS/JS) communicates with the FastAPI API over HTTP. The API integrates with SonarQube’s REST endpoints and persists data in SQLite. The backend also serves the static frontend assets.

## Data Flow

1. User creates or validates a connection.
2. Backend verifies credentials against SonarQube and stores connection metadata locally.
3. User syncs projects and refreshes metrics.
4. Backend fetches metrics, validates boundaries, and stores snapshots.
5. Frontend renders metrics tables and charts using the cached snapshots.

## Backend Layers

- API layer: `backend/src/api/` (HTTP routes and error mapping)
- Service layer: `backend/src/services/` (business logic and SonarQube client)
- Data layer: `backend/src/db/` and `backend/src/models/` (SQLite persistence)

## Frontend Layers

- `frontend/index.html`: layout and UI structure
- `frontend/js/app.js`: UI logic and state
- `frontend/js/api-client.js`: REST API client wrapper
- `frontend/js/charts.js`: Chart.js visualizations
- `frontend/css/styles.css`: responsive styling

## Key Design Decisions

- FastAPI for type-validated REST APIs and easy OpenAPI generation.
- SQLite for local, lightweight persistence.
- Vanilla JS for simplicity and minimal dependencies.
- Chart.js for visualizations with lazy loading.
