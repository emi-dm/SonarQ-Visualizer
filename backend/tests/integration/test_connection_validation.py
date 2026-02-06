"""Integration tests for connection validation flow with mock SonarQube API."""

import pytest
import requests_mock
from fastapi.testclient import TestClient
from backend.src.main import app
from backend.src.db.init import init_database
import tempfile
import os


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name
    
    init_database(db_path)
    yield db_path
    
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def client(test_db):
    """FastAPI test client with test database."""
    from backend.src.utils.config import settings
    original_path = settings.database_path
    settings.database_path = test_db
    
    client = TestClient(app)
    
    yield client
    
    settings.database_path = original_path


class TestConnectionValidation:
    """Integration tests for connection validation with SonarQube API mocking."""
    
    def test_validate_connection_success(self, client):
        """Test successful connection validation."""
        # Create connection first
        payload = {
            "name": "Test Connection",
            "server_url": "https://sonarqube.test.com",
            "token": "squ_validtoken123",
            "validate": False
        }
        create_response = client.post("/api/v1/connections", json=payload)
        connection_id = create_response.json()["id"]
        
        # Mock SonarQube API response
        with requests_mock.Mocker() as m:
            m.get(
                "https://sonarqube.test.com/api/system/status",
                json={
                    "id": "test-sonarqube",
                    "version": "9.9.0",
                    "status": "UP"
                },
                status_code=200
            )
            
            # Validate connection
            validate_payload = {"token": "squ_validtoken123"}
            response = client.post(
                f"/api/v1/connections/{connection_id}/validate",
                json=validate_payload
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["server_version"] == "9.9.0"
            assert data["server_status"] == "UP"
    
    def test_validate_connection_invalid_token(self, client):
        """Test connection validation with invalid token."""
        # Create connection
        payload = {
            "name": "Test Connection",
            "server_url": "https://sonarqube.test.com",
            "token": "squ_test",
            "validate": False
        }
        create_response = client.post("/api/v1/connections", json=payload)
        connection_id = create_response.json()["id"]
        
        # Mock SonarQube API with 401 Unauthorized
        with requests_mock.Mocker() as m:
            m.get(
                "https://sonarqube.test.com/api/system/status",
                json={"errors": [{"msg": "Unauthorized"}]},
                status_code=401
            )
            
            validate_payload = {"token": "squ_invalidtoken"}
            response = client.post(
                f"/api/v1/connections/{connection_id}/validate",
                json=validate_payload
            )
            
            assert response.status_code == 401
            data = response.json()
            assert "error" in data
    
    def test_validate_connection_server_unreachable(self, client):
        """Test connection validation when server is unreachable."""
        # Create connection
        payload = {
            "name": "Test Connection",
            "server_url": "https://sonarqube.test.com",
            "token": "squ_test",
            "validate": False
        }
        create_response = client.post("/api/v1/connections", json=payload)
        connection_id = create_response.json()["id"]
        
        # Mock connection timeout
        with requests_mock.Mocker() as m:
            m.get(
                "https://sonarqube.test.com/api/system/status",
                exc=requests_mock.exceptions.ConnectTimeout
            )
            
            validate_payload = {"token": "squ_test"}
            response = client.post(
                f"/api/v1/connections/{connection_id}/validate",
                json=validate_payload
            )
            
            assert response.status_code == 503
            data = response.json()
            assert "error" in data
    
    def test_validate_connection_timeout(self, client):
        """Test connection validation with 30 second timeout."""
        # Create connection
        payload = {
            "name": "Test Connection",
            "server_url": "https://sonarqube.test.com",
            "token": "squ_test",
            "validate": False
        }
        create_response = client.post("/api/v1/connections", json=payload)
        connection_id = create_response.json()["id"]
        
        # Mock read timeout
        with requests_mock.Mocker() as m:
            m.get(
                "https://sonarqube.test.com/api/system/status",
                exc=requests_mock.exceptions.ReadTimeout
            )
            
            validate_payload = {"token": "squ_test"}
            response = client.post(
                f"/api/v1/connections/{connection_id}/validate",
                json=validate_payload
            )
            
            assert response.status_code == 503
            data = response.json()
            assert "timeout" in data["error"].lower()
    
    def test_create_connection_with_validation(self, client):
        """Test creating connection with immediate validation."""
        with requests_mock.Mocker() as m:
            m.get(
                "https://sonarqube.test.com/api/system/status",
                json={
                    "id": "test-sonarqube",
                    "version": "9.9.0",
                    "status": "UP"
                },
                status_code=200
            )
            
            payload = {
                "name": "Test Connection",
                "server_url": "https://sonarqube.test.com",
                "token": "squ_validtoken",
                "validate": True  # Request validation during creation
            }
            
            response = client.post("/api/v1/connections", json=payload)
            
            assert response.status_code == 201
            data = response.json()
            assert data["server_version"] == "9.9.0"
            assert data["last_validated_at"] is not None
    
    def test_connection_validation_updates_timestamp(self, client):
        """Test that successful validation updates last_validated_at."""
        # Create connection
        payload = {
            "name": "Test Connection",
            "server_url": "https://sonarqube.test.com",
            "token": "squ_test",
            "validate": False
        }
        create_response = client.post("/api/v1/connections", json=payload)
        connection_id = create_response.json()["id"]
        
        # Initial state - not validated
        get_response = client.get(f"/api/v1/connections/{connection_id}")
        assert get_response.json()["last_validated_at"] is None
        
        # Validate connection
        with requests_mock.Mocker() as m:
            m.get(
                "https://sonarqube.test.com/api/system/status",
                json={"id": "test", "version": "9.9.0", "status": "UP"},
                status_code=200
            )
            
            validate_payload = {"token": "squ_test"}
            client.post(
                f"/api/v1/connections/{connection_id}/validate",
                json=validate_payload
            )
        
        # Check updated state
        get_response = client.get(f"/api/v1/connections/{connection_id}")
        assert get_response.json()["last_validated_at"] is not None
