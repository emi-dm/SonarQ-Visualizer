# SonarQube Report Visualizer

A web-based visualizer for SonarQube quality reports. Connect to SonarQube instances, fetch project metrics (bugs, vulnerabilities, code coverage, etc.), and view them through interactive visualizations with offline capability.

## Features

- 🔗 **Connection Management**: Connect to multiple SonarQube instances with authentication
- 📊 **Metrics Dashboard**: View quality metrics across all projects with aggregations
- 📈 **Trend Analysis**: Historical metrics tracking with staleness indicators
- 🎨 **Interactive Visualizations**: Charts for trends, severity distributions, and coverage gauges
- 💾 **Offline Viewing**: SQLite-backed local storage for cached metrics
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile browsers

## Quick Start

Get up and running in 5 steps:

### 1. Clone and Navigate

```bash
git clone <repository-url> sonarq-visualizer
cd sonarq-visualizer
```

### 2. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Initialize Database

```bash
python backend/app.py init-db
```

### 4. Start Frontend Server (first)

```bash
npm run frontend
```

### 5. Start Backend Server and Open Browser

```bash
uvicorn backend.src.main:app --reload --host 0.0.0.0 --port 8000
```

Navigate to: **http://localhost:8080**

Note: The frontend is served separately from the backend. Start the frontend first on port 8080, then the API on port 8000.

## Requirements

- Python 3.11 or higher
- Modern web browser (Chrome, Firefox, Safari, Edge - last 2 versions)
- SonarQube server access with authentication token

## Technology Stack

- **Backend**: Python 3.11+ with FastAPI
- **Database**: SQLite (embedded, file-based)
- **Frontend**: Vanilla JavaScript (ES6+), Chart.js for visualizations
- **Testing**: pytest, Hypothesis (property-based testing)

## Documentation

- [Architecture](docs/architecture.md) - System design and data flow
- [API Documentation](docs/api.md) - REST API reference
- [Development Guide](docs/development.md) - Setup, testing, and contribution guidelines
- [Security](docs/security.md) - Security considerations and threat model

## Development

### Running Tests

```bash
# Unit tests
pytest -m unit

# Property-based tests
pytest -m property

# Integration tests
pytest -m integration

# All tests with coverage
pytest --cov
```

### Code Quality

```bash
# Format code
black backend/

# Lint Python
flake8 backend/
mypy backend/

# Lint JavaScript
npm run lint
```

## License

MIT

## Support

For issues, questions, or contributions, please refer to the [Development Guide](docs/development.md).
