# Quickstart Guide: SonarQube Report Visualizer

Get the SonarQube Report Visualizer running in under 5 minutes.

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.11 or higher** - Check with `python --version` or `python3 --version`
- **Modern web browser** - Chrome, Firefox, Safari, or Edge (last 2 versions)
- **SonarQube server access** - You'll need:
  - Server URL (e.g., `https://sonarqube.company.com`)
  - Authentication token with project browsing permissions

---

## Five Steps to Success

### Step 1: Clone and Navigate

```bash
git clone <repository-url> sonarq-visualizer
cd sonarq-visualizer
```

### Step 2: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

**Expected output**: Several package installations including `fastapi`, `uvicorn`, `sqlalchemy`, `requests`, `hypothesis`.

### Step 3: Initialize Database

```bash
python backend/app.py init-db
```

**Expected output**: `✓ Database initialized at data/sonarq.db`

### Step 4: Start Frontend Server (first)

```bash
npm run frontend
```

**Expected output**:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### Step 5: Start Backend Server and Open Browser

```bash
# Development mode with auto-reload
uvicorn backend.src.main:app --reload --host 0.0.0.0 --port 8000
```

Navigate to: **http://localhost:8080**

You should see the SonarQube Report Visualizer landing page.

---

## Next Steps

### Configure Your First Connection

1. Click **"Add Connection"** in the top-right
2. Enter your SonarQube details:
   - **Name**: `My SonarQube` (any descriptive name)
   - **Server URL**: `https://sonarqube.company.com`
   - **Token**: Your authentication token (paste and save)
3. Click **"Test Connection"** to validate
4. Click **"Sync Projects"** to import your project list

### Explore Your Metrics

- **Dashboard**: View all projects at a glance
- **Project Details**: Click any project to see metrics trends
- **Refresh**: Click refresh icon to fetch latest data from SonarQube

---

## Troubleshooting

### Port Already in Use

If port 8000 is occupied:

```bash
uvicorn backend.src.main:app --reload --port 8080
# Then open http://localhost:8080
```

If port 8080 is occupied (frontend):

```bash
python3 -m http.server 8081 --directory frontend
# Then open http://localhost:8081
```

### Python Version Too Old

```bash
# Check version
python3 --version

# If < 3.11, install Python 3.11+ from python.org
# Then use explicit version:
python3.11 -m venv venv
```

### ModuleNotFoundError

Ensure virtual environment is activated and dependencies are installed:

```bash
source venv/bin/activate  # Activate venv
pip install -r backend/requirements.txt  # Reinstall
```

### Database Locked

If you see "database is locked" errors:

```bash
# Stop any running backend processes
pkill -f "uvicorn backend.src.main"

# Restart server
uvicorn backend.src.main:app --reload
```

### Token Authentication Failed

- Verify your SonarQube token has **not expired**
- Check token has **Browse permission** on projects
- Ensure server URL is correct (no trailing slash)
- Try generating a new token from SonarQube: User → My Account → Security → Generate Token

### Chrome Mixed Content Warning

If using HTTPS SonarQube server with HTTP localhost:

- Run backend with HTTPS (advanced), OR
- Configure SonarQube server to allow CORS from `http://localhost:8000`

---

## Development Mode

### Backend with Auto-Reload

```bash
uvicorn backend.src.main:app --reload --log-level debug
```

### Run Tests

```bash
# All tests
pytest backend/tests/

# Unit tests only
pytest backend/tests/unit/

# Property-based tests
pytest backend/tests/property/ -v

# With coverage
pytest --cov=backend --cov-report=html
open htmlcov/index.html  # View coverage report
```

### Database Reset

To start fresh:

```bash
rm data/sonarq.db
python backend/app.py init-db
```

---

## Architecture Overview

```
┌─────────────────┐
│  Browser        │
│  (Frontend)     │ ← http://localhost:8000
│  HTML/CSS/JS    │
└────────┬────────┘
         │ REST API
         ▼
┌─────────────────┐
│  FastAPI        │
│  (Backend)      │ ← port 8000
│  Python 3.11+   │
└────────┬────────┘
         │
    ┌────┴────────────────┐
    ▼                     ▼
┌─────────┐      ┌──────────────┐
│ SQLite  │      │  SonarQube   │
│ Local   │      │  Server API  │
│ data/   │      │  (External)  │
└─────────┘      └──────────────┘
```

---

## Performance Tips

- **Refresh Strategy**: Manual refresh recommended for larger projects (reduces API load)
- **Data Retention**: Metrics snapshots stored locally for 90 days (configurable)
- **Multi-Project Dashboard**: Initial load may take 2-3s for 20+ projects

---

## Security Notes

- **Token Storage**: SonarQube tokens stored in browser localStorage (not sent to backend DB)
- **Local Network**: Backend listens on `0.0.0.0` (all interfaces) by default
- **Production Deployment**: Use HTTPS, environment variables for secrets, reverse proxy (nginx/Apache)

---

## Need Help?

- **Issues**: Check [GitHub Issues](../../issues) for known problems
- **Documentation**: See [spec.md](./spec.md) for complete requirements
- **Architecture**: See [plan.md](./plan.md) for technical details
- **Data Model**: See [data-model.md](./data-model.md) for database schema
- **API Reference**: See [contracts/api.yaml](./contracts/api.yaml) for endpoint documentation

---

**You're ready to visualize!** 🎉
