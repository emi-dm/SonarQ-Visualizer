"""Integration tests for preferences API endpoint.

Tests GET /preferences and PUT /preferences with key-value storage.
"""

import pytest
from fastapi.testclient import TestClient
from backend.src.main import app
from backend.src.db.base import get_db
from backend.src.models.user_preferences import UserPreferences


client = TestClient(app)


@pytest.fixture
def test_db(tmp_path):
    """Create test database for preferences testing."""
    from backend.src.db.init import init_db
    
    db_path = tmp_path / "test_preferences.db"
    init_db(str(db_path))
    
    yield db_path


class TestPreferencesAPI:
    """Integration tests for preferences API endpoint."""

    def test_get_preferences_empty(self, test_db):
        """Test GET /preferences returns empty object when no preferences set."""
        response = client.get("/api/v1/preferences")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return empty dict or default preferences
        assert isinstance(data, dict)

    def test_put_preferences_new_keys(self, test_db):
        """Test PUT /preferences creates new preference keys."""
        preferences = {
            "theme": "dark",
            "chart_type": "line",
            "time_range": "30d"
        }
        
        response = client.put(
            "/api/v1/preferences",
            json=preferences
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["theme"] == "dark"
        assert data["chart_type"] == "line"
        assert data["time_range"] == "30d"

    def test_get_preferences_after_put(self, test_db):
        """Test GET /preferences returns previously set values."""
        # Set preferences
        preferences = {
            "default_branch": "main",
            "page_size": 20
        }
        
        client.put("/api/v1/preferences", json=preferences)
        
        # Get preferences
        response = client.get("/api/v1/preferences")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["default_branch"] == "main"
        assert data["page_size"] == 20

    def test_put_preferences_update_existing(self, test_db):
        """Test PUT /preferences updates existing preference values."""
        # Set initial preferences
        client.put("/api/v1/preferences", json={"theme": "light"})
        
        # Update preferences
        response = client.put("/api/v1/preferences", json={"theme": "dark"})
        
        assert response.status_code == 200
        
        # Verify updated value
        get_response = client.get("/api/v1/preferences")
        assert get_response.json()["theme"] == "dark"

    def test_put_preferences_partial_update(self, test_db):
        """Test PUT /preferences updates only specified keys."""
        # Set multiple preferences
        client.put("/api/v1/preferences", json={
            "theme": "light",
            "chart_type": "bar",
            "time_range": "7d"
        })
        
        # Update only one preference
        response = client.put("/api/v1/preferences", json={"theme": "dark"})
        
        assert response.status_code == 200
        
        # Verify all preferences
        get_response = client.get("/api/v1/preferences")
        data = get_response.json()
        
        assert data["theme"] == "dark"  # Updated
        assert data["chart_type"] == "bar"  # Unchanged
        assert data["time_range"] == "7d"  # Unchanged

    def test_put_preferences_complex_values(self, test_db):
        """Test PUT /preferences handles complex JSON values."""
        preferences = {
            "dashboard_layout": {
                "columns": 3,
                "widgets": ["metrics", "charts", "trends"]
            },
            "filters": {
                "selected_projects": [1, 2, 3],
                "date_range": {"start": "2026-01-01", "end": "2026-02-06"}
            }
        }
        
        response = client.put("/api/v1/preferences", json=preferences)
        
        assert response.status_code == 200
        
        # Verify complex values are preserved
        get_response = client.get("/api/v1/preferences")
        data = get_response.json()
        
        assert data["dashboard_layout"]["columns"] == 3
        assert len(data["dashboard_layout"]["widgets"]) == 3
        assert data["filters"]["selected_projects"] == [1, 2, 3]

    def test_put_preferences_empty_object(self, test_db):
        """Test PUT /preferences with empty object doesn't clear existing preferences."""
        # Set initial preferences
        client.put("/api/v1/preferences", json={"theme": "dark"})
        
        # Send empty update
        response = client.put("/api/v1/preferences", json={})
        
        assert response.status_code == 200
        
        # Existing preferences should remain
        get_response = client.get("/api/v1/preferences")
        data = get_response.json()
        
        assert "theme" in data
        assert data["theme"] == "dark"

    def test_put_preferences_invalid_json(self, test_db):
        """Test PUT /preferences validates request body."""
        response = client.put(
            "/api/v1/preferences",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        # Should return 422 for invalid JSON
        assert response.status_code == 422

    def test_preferences_persistence(self, test_db):
        """Test preferences persist across multiple requests."""
        # Set preferences in multiple calls
        client.put("/api/v1/preferences", json={"key1": "value1"})
        client.put("/api/v1/preferences", json={"key2": "value2"})
        client.put("/api/v1/preferences", json={"key3": "value3"})
        
        # All preferences should be available
        response = client.get("/api/v1/preferences")
        data = response.json()
        
        assert data["key1"] == "value1"
        assert data["key2"] == "value2"
        assert data["key3"] == "value3"

    def test_preferences_type_handling(self, test_db):
        """Test preferences correctly handles different value types."""
        preferences = {
            "string_pref": "text",
            "number_pref": 42,
            "float_pref": 3.14,
            "boolean_pref": True,
            "null_pref": None,
            "array_pref": [1, 2, 3],
            "object_pref": {"nested": "value"}
        }
        
        response = client.put("/api/v1/preferences", json=preferences)
        assert response.status_code == 200
        
        get_response = client.get("/api/v1/preferences")
        data = get_response.json()
        
        assert data["string_pref"] == "text"
        assert data["number_pref"] == 42
        assert abs(data["float_pref"] - 3.14) < 0.01
        assert data["boolean_pref"] is True
        assert data["null_pref"] is None
        assert data["array_pref"] == [1, 2, 3]
        assert data["object_pref"]["nested"] == "value"

    def test_preferences_predefined_keys(self, test_db):
        """Test that predefined preference keys work correctly."""
        # Common predefined keys from spec
        predefined_preferences = {
            "theme": "dark",
            "default_branch": "main",
            "chart_type": "line",
            "time_range": "30d",
            "page_size": 20,
            "show_trends": True
        }
        
        response = client.put("/api/v1/preferences", json=predefined_preferences)
        assert response.status_code == 200
        
        get_response = client.get("/api/v1/preferences")
        data = get_response.json()
        
        for key, value in predefined_preferences.items():
            assert data[key] == value

    def test_get_preference_existing_key(self, test_db):
        """Test GET /preferences/{key} returns a saved preference value."""
        client.put("/api/v1/preferences", json={"theme": "dark"})

        response = client.get("/api/v1/preferences/theme")

        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "theme"
        assert data["value"] == "dark"

    def test_get_preference_not_found(self, test_db):
        """Test GET /preferences/{key} returns 404 for unknown non-predefined key."""
        response = client.get("/api/v1/preferences/nonexistent_custom_key")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "Preference not found"
        assert data["detail"]["key"] == "nonexistent_custom_key"

    def test_delete_preference_resets_to_default(self, test_db):
        """Test DELETE /preferences/{key} deletes stored value and returns default."""
        client.put("/api/v1/preferences", json={"theme": "dark"})

        response = client.delete("/api/v1/preferences/theme")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Preference deleted"
        assert data["key"] == "theme"
        assert data["default_value"] == "light"

        get_response = client.get("/api/v1/preferences/theme")
        assert get_response.status_code == 200
        assert get_response.json()["value"] == "light"

    def test_reset_all_preferences(self, test_db):
        """Test POST /preferences/reset clears custom values and restores defaults."""
        client.put("/api/v1/preferences", json={"theme": "dark", "custom_key": "custom"})

        response = client.post("/api/v1/preferences/reset")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "All preferences reset to defaults"
        assert "preferences" in data
        assert data["preferences"]["theme"] == "light"

        get_response = client.get("/api/v1/preferences")
        get_data = get_response.json()
        assert get_data["theme"] == "light"
        assert "custom_key" not in get_data

    def test_get_predefined_keys_endpoint(self, test_db):
        """Test GET /preferences/keys/predefined returns key metadata."""
        response = client.get("/api/v1/preferences/keys/predefined")

        assert response.status_code == 200
        data = response.json()
        assert "predefined_keys" in data
        assert "count" in data
        assert "defaults" in data
        assert data["count"] == len(data["predefined_keys"])
        assert "theme" in data["predefined_keys"]

    def test_put_preferences_validation_error(self, test_db):
        """Test PUT /preferences returns 400 on invalid predefined value."""
        response = client.put("/api/v1/preferences", json={"theme": "neon"})

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "Invalid preference value"

    def test_get_preferences_handles_service_exception(self, test_db, monkeypatch):
        """Test GET /preferences returns 500 when service raises unexpected error."""
        from backend.src.services.preferences_service import PreferencesService

        def mock_get_all_preferences(self):
            raise RuntimeError("simulated preferences failure")

        monkeypatch.setattr(PreferencesService, "get_all_preferences", mock_get_all_preferences)

        response = client.get("/api/v1/preferences")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["error"] == "Failed to retrieve preferences"
        assert "simulated preferences failure" in data["detail"]["details"]

    def test_delete_preference_handles_service_exception(self, test_db, monkeypatch):
        """Test DELETE /preferences/{key} returns 500 when service fails."""
        from backend.src.services.preferences_service import PreferencesService

        def mock_reset_preference(self, key):
            raise RuntimeError("simulated delete failure")

        monkeypatch.setattr(PreferencesService, "reset_preference", mock_reset_preference)

        response = client.delete("/api/v1/preferences/theme")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["error"] == "Failed to delete preference"
        assert "simulated delete failure" in data["detail"]["details"]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
