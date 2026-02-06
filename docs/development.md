# Development Guide

## Prerequisites

- Python 3.11+
- Node.js 18+ (for ESLint)

## Setup

1. Create and activate a virtual environment.
2. Install backend dependencies from `backend/requirements.txt`.
3. Initialize the database using `python backend/app.py init-db`.
4. Start the frontend first with `npm run frontend` (serves on port 8080).
5. Start the backend with `uvicorn backend.src.main:app --reload --host 0.0.0.0 --port 8000`.

## Linting

- Python: `black backend/`, `flake8 backend/`, `mypy backend/`
- JavaScript: `npm run lint`

## Testing

- Unit tests: `pytest backend/tests/unit/`
- Property-based tests: `pytest backend/tests/property/ -v`
- Integration tests: `pytest backend/tests/integration/`
- Full suite: `pytest backend/tests/`

## Frontend

The frontend is served by a simple static server on port 8080. Open `http://localhost:8080` after starting the frontend.

## Pre-commit Hooks

Run `pre-commit install` to enable local hooks for formatting and linting.
