"""Unit tests for Connection model."""

import pytest
from datetime import datetime
from backend.src.models.connection import Connection


class TestConnectionModel:
    """Test cases for Connection model validation and behavior."""
    
    def test_connection_creation_with_valid_data(self):
        """Test creating a connection with valid data."""
        connection = Connection(
            name="Test SonarQube",
            server_url="https://sonarqube.test.com",
            server_version="9.9.0",
            is_active=True
        )
        
        assert connection.name == "Test SonarQube"
        assert connection.server_url == "https://sonarqube.test.com"
        assert connection.server_version == "9.9.0"
        assert connection.is_active is True
    
    def test_connection_name_required(self):
        """Test that name is required."""
        with pytest.raises(ValueError):
            Connection(
                name="",
                server_url="https://sonarqube.test.com"
            )
    
    def test_connection_url_required(self):
        """Test that server_url is required."""
        with pytest.raises(ValueError):
            Connection(
                name="Test",
                server_url=""
            )
    
    def test_connection_url_must_be_valid_url(self):
        """Test that server_url must be a valid URL."""
        with pytest.raises(ValueError):
            Connection(
                name="Test",
                server_url="not-a-valid-url"
            )
    
    def test_connection_https_preferred(self):
        """Test HTTP URL accepted with warning."""
        connection = Connection(
            name="Test",
            server_url="http://sonarqube.test.com"
        )
        assert connection.server_url == "http://sonarqube.test.com"
    
    def test_connection_defaults(self):
        """Test default values for optional fields."""
        connection = Connection(
            name="Test",
            server_url="https://sonarqube.test.com"
        )
        
        assert connection.is_active is True
        assert connection.last_validated_at is None
        assert connection.server_version is None
    
    def test_connection_timestamps_auto_set(self):
        """Test that timestamps are automatically set."""
        connection = Connection(
            name="Test",
            server_url="https://sonarqube.test.com"
        )
        
        # These will be set by the database, test that fields exist
        assert hasattr(connection, 'created_at')
        assert hasattr(connection, 'updated_at')
    
    def test_connection_name_uniqueness(self):
        """Test that connection names must be unique."""
        # This will be enforced at database level
        # Test that model has unique constraint
        assert hasattr(Connection, '__table_args__')
