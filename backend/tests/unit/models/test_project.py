"""Unit tests for Project model."""

import pytest
from backend.src.models.project import Project


class TestProjectModel:
    """Test cases for Project model validation and behavior."""

    def test_project_creation_with_valid_data(self):
        """Test creating a project with valid data."""
        project = Project(
            connection_id=1,
            project_key="com.example:my-app",
            name="My App",
            description="Test project"
        )

        assert project.connection_id == 1
        assert project.project_key == "com.example:my-app"
        assert project.name == "My App"
        assert project.description == "Test project"

    def test_project_name_required(self):
        """Test that project name is required."""
        with pytest.raises(ValueError):
            Project(
                connection_id=1,
                project_key="com.example:my-app",
                name=""
            )

    def test_project_key_required(self):
        """Test that project key is required."""
        with pytest.raises(ValueError):
            Project(
                connection_id=1,
                project_key="",
                name="My App"
            )

    def test_project_key_format_validation(self):
        """Test that project key must match expected format."""
        with pytest.raises(ValueError):
            Project(
                connection_id=1,
                project_key="invalid key with spaces",
                name="My App"
            )

    def test_project_defaults(self):
        """Test default values for optional fields."""
        project = Project(
            connection_id=1,
            project_key="com.example:my-app",
            name="My App"
        )

        assert project.description is None
        assert project.last_analysis_date is None

    def test_project_unique_constraint(self):
        """Test that project has unique constraint on connection_id + project_key."""
        assert hasattr(Project, "__table_args__")
