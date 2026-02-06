"""Integration tests for connections API endpoints."""

import pytest
import requests_mock
from fastapi.testclient import TestClient
from backend.src.main import app
from backend.src.db.init import init_database
from pathlib import Path
import tempfile
import os


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name
    
    # Initialize test database
    init_database(db_path)
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def client(test_db):
    """FastAPI test client with test database."""
    # Override database path in config
    from backend.src.utils.config import settings
    original_path = settings.database_path
    settings.database_path = test_db
    
    test_client = TestClient(app)
    
    yield test_client
    
    # Restore original path
    settings.database_path = original_path


class TestConnectionsAPI:
    """Integration tests for /api/v1/connections endpoints."""
    
    def test_create_connection_success(self, client):
        """Test creating a new connection successfully."""
        payload = {
            "name": "Test SonarQube",
            "server_url": "https://sonarqube.test.com",
            "token": "squ_test123",
            "validate": False  # Skip validation for this test
        }
        
        response = client.post("/api/v1/connections", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test SonarQube"
        assert data["server_url"] == "https://sonarqube.test.com"
        assert "id" in data
        assert "token" not in data  # Token should never be in response
    
    def test_create_connection_duplicate_name(self, client):
        """Test creating connection with duplicate name fails."""
        payload = {
            "name": "Duplicate",
            "server_url": "https://sonarqube.test.com",
            "token": "squ_test123",
            "validate": False
        }
        
        # Create first connection
        response1 = client.post("/api/v1/connections", json=payload)
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = client.post("/api/v1/connections", json=payload)
        assert response2.status_code == 409  # Conflict
    
    def test_create_connection_invalid_url(self, client):
        """Test creating connection with invalid URL fails."""
        payload = {
            "name": "Invalid URL",
            "server_url": "not-a-valid-url",
            "token": "squ_test123",
            "validate": False
        }
        
        response = client.post("/api/v1/connections", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_list_connections(self, client):
        """Test listing all connections."""
        # Create test connections
        for i in range(3):
            payload = {
                "name": f"Connection {i}",
                "server_url": f"https://sonarqube{i}.test.com",
                "token": "squ_test123",
                "validate": False
            }
            client.post("/api/v1/connections", json=payload)
        
        # List connections
        response = client.get("/api/v1/connections")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
    
    def test_get_connection_by_id(self, client):
        """Test retrieving a specific connection."""
        # Create connection
        payload = {
            "name": "Single Connection",
            "server_url": "https://sonarqube.test.com",
            "token": "squ_test123",
            "validate": False
        }
        create_response = client.post("/api/v1/connections", json=payload)
        connection_id = create_response.json()["id"]
        
        # Get connection
        response = client.get(f"/api/v1/connections/{connection_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == connection_id
        assert data["name"] == "Single Connection"
    
    def test_get_nonexistent_connection(self, client):
        """Test retrieving non-existent connection returns 404."""
        response = client.get("/api/v1/connections/99999")
        assert response.status_code == 404
    
    def test_update_connection(self, client):
        """Test updating an existing connection."""
        # Create connection
        payload = {
            "name": "Original Name",
            "server_url": "https://sonarqube.test.com",
            "token": "squ_test123",
            "validate": False
        }
        create_response = client.post("/api/v1/connections", json=payload)
        connection_id = create_response.json()["id"]
        
        # Update connection
        update_payload = {
            "name": "Updated Name",
            "server_url": "https://sonarqube-updated.test.com"
        }
        response = client.put(f"/api/v1/connections/{connection_id}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["server_url"] == "https://sonarqube-updated.test.com"
    
    def test_delete_connection(self, client):
        """Test deleting a connection."""
        # Create connection
        payload = {
            "name": "To Delete",
            "server_url": "https://sonarqube.test.com",
            "token": "squ_test123",
            "validate": False
        }
        create_response = client.post("/api/v1/connections", json=payload)
        connection_id = create_response.json()["id"]
        
        # Delete connection
        response = client.delete(f"/api/v1/connections/{connection_id}")
        assert response.status_code == 204
        
        # Verify deleted
        get_response = client.get(f"/api/v1/connections/{connection_id}")
        assert get_response.status_code == 404
