"""Integration tests for projects sync endpoint."""

import os
import tempfile
import requests_mock
from fastapi.testclient import TestClient
import pytest

from backend.src.main import app
from backend.src.db.init import init_database
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


class TestProjectsSync:
    """Integration tests for /connections/{id}/projects/sync."""

    def test_sync_projects_success(self, client):
        connection_id = create_connection(client)

        with requests_mock.Mocker() as m:
            m.get(
                "https://sonarqube.test.com/api/projects/search",
                json={
                    "paging": {"pageIndex": 1, "pageSize": 100, "total": 2},
                    "components": [
                        {"key": "com.example:one", "name": "Project One", "description": "A", "analysisDate": "2024-01-01T00:00:00Z"},
                        {"key": "com.example:two", "name": "Project Two", "description": "B", "analysisDate": "2024-01-02T00:00:00Z"}
                    ]
                },
                status_code=200
            )

            response = client.post(
                f"/api/v1/connections/{connection_id}/projects/sync",
                json={"token": "squ_test"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["synced_count"] == 2
            assert data["new_count"] == 2
            assert data["failed_count"] == 0

    def test_sync_projects_partial_failure(self, client):
        connection_id = create_connection(client)

        with requests_mock.Mocker() as m:
            m.get(
                "https://sonarqube.test.com/api/projects/search",
                json={
                    "paging": {"pageIndex": 1, "pageSize": 100, "total": 2},
                    "components": [
                        {"key": "com.example:one", "name": "Project One"},
                        {"name": "Missing Key"}
                    ]
                },
                status_code=200
            )

            response = client.post(
                f"/api/v1/connections/{connection_id}/projects/sync",
                json={"token": "squ_test"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["failed_count"] == 1
            assert len(data["failed_projects"]) == 1

    def test_sync_projects_partial_failure_threshold(self, client):
        connection_id = create_connection(client)

        with requests_mock.Mocker() as m:
            m.get(
                "https://sonarqube.test.com/api/projects/search",
                json={
                    "paging": {"pageIndex": 1, "pageSize": 100, "total": 3},
                    "components": [
                        {"name": "Missing Key 1"},
                        {"name": "Missing Key 2"},
                        {"key": "com.example:ok", "name": "Project OK"}
                    ]
                },
                status_code=200
            )

            response = client.post(
                f"/api/v1/connections/{connection_id}/projects/sync",
                json={"token": "squ_test"}
            )

            assert response.status_code == 409
            data = response.json()
            assert data["error"] == "PARTIAL_SYNC_FAILURE"
