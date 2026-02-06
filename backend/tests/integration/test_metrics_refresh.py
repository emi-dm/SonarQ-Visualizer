"""Integration tests for metrics refresh endpoint."""

import os
import tempfile
from datetime import datetime, timedelta

import pytest
import requests_mock
from fastapi.testclient import TestClient

from backend.src.main import app
from backend.src.db.init import init_database
from backend.src.db.base import get_sessionmaker
from backend.src.db.repositories.project_repository import ProjectRepository
from backend.src.utils.config import settings


@pytest.fixture
def test_db():
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name

    init_database(db_path)
    yield db_path

    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def client(test_db):
    original_path = settings.database_path
    settings.database_path = test_db

    test_client = TestClient(app)
    yield test_client

    settings.database_path = original_path


def create_connection(client):
    payload = {
        "name": "Test Connection",
        "server_url": "https://sonarqube.test.com",
        "token": "squ_test",
        "validate": False
    }
    response = client.post("/api/v1/connections", json=payload)
    return response.json()["id"]


def create_project(connection_id):
    session = get_sessionmaker()()
    repo = ProjectRepository(session)
    project = repo.create(
        connection_id=connection_id,
        project_key="com.example:metrics",
        name="Metrics Project",
        description=None,
        last_analysis_date=None
    )
    session.close()
    return project.id


class TestMetricsRefresh:
    """Integration tests for /projects/{id}/metrics/refresh."""

    def test_refresh_metrics_success(self, client):
        connection_id = create_connection(client)
        project_id = create_project(connection_id)

        with requests_mock.Mocker() as m:
            m.get(
                "https://sonarqube.test.com/api/measures/component",
                json={
                    "component": {
                        "key": "com.example:metrics",
                        "analysisDate": "2024-01-05T10:00:00Z",
                        "measures": [
                            {"metric": "bugs", "value": "1"},
                            {"metric": "vulnerabilities", "value": "2"},
                            {"metric": "code_smells", "value": "3"},
                            {"metric": "coverage", "value": "75.5"},
                            {"metric": "duplicated_lines_density", "value": "1.2"},
                            {"metric": "ncloc", "value": "1000"},
                            {"metric": "alert_status", "value": "OK"}
                        ]
                    }
                },
                status_code=200
            )

            response = client.post(
                f"/api/v1/projects/{project_id}/metrics/refresh",
                json={"token": "squ_test", "branch": "main"}
            )

            assert response.status_code == 201
            data = response.json()
            assert data["project_id"] == project_id
            assert data["quality_gate_status"] == "OK"

    def test_refresh_metrics_invalid_response(self, client):
        connection_id = create_connection(client)
        project_id = create_project(connection_id)

        with requests_mock.Mocker() as m:
            m.get(
                "https://sonarqube.test.com/api/measures/component",
                json={"bad": "data"},
                status_code=200
            )

            response = client.post(
                f"/api/v1/projects/{project_id}/metrics/refresh",
                json={"token": "squ_test", "branch": "main"}
            )

            assert response.status_code == 422
            data = response.json()
            assert data["error"] == "INVALID_API_RESPONSE"
