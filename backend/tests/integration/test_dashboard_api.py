"""Integration tests for dashboard API endpoint.

Tests GET /dashboard with multiple projects and aggregation verification.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from backend.src.main import app
from backend.src.db.base import get_db
from backend.src.models.connection import Connection
from backend.src.models.project import Project
from backend.src.models.metrics_snapshot import MetricsSnapshot


client = TestClient(app)


@pytest.fixture
def test_db(tmp_path):
    """Create test database with sample data."""
    from backend.src.db.init import init_db
    
    db_path = tmp_path / "test_dashboard.db"
    init_db(str(db_path))
    
    # Get database session
    db = next(get_db())
    
    # Create test connection
    connection = Connection(
        name="Test SonarQube",
        server_url="https://sonarqube.test.com",
        server_version="9.9.0",
        is_active=True,
        last_validated_at=datetime.utcnow()
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)
    
    # Create test projects
    projects_data = [
        {"project_key": "project1", "name": "Project Alpha", "description": "First project"},
        {"project_key": "project2", "name": "Project Beta", "description": "Second project"},
        {"project_key": "project3", "name": "Project Gamma", "description": "Third project"},
    ]
    
    projects = []
    for proj_data in projects_data:
        project = Project(
            connection_id=connection.id,
            project_key=proj_data["project_key"],
            name=proj_data["name"],
            description=proj_data["description"],
            last_analysis_date=datetime.utcnow() - timedelta(hours=2)
        )
        db.add(project)
        projects.append(project)
    
    db.commit()
    for proj in projects:
        db.refresh(proj)
    
    # Create metrics snapshots for each project
    metrics_data = [
        # Project Alpha - healthy project
        {
            "project_id": projects[0].id,
            "bugs_count": 5,
            "vulnerabilities_count": 2,
            "coverage_pct": 85.50,
            "quality_gate_status": "OK"
        },
        # Project Beta - needs attention
        {
            "project_id": projects[1].id,
            "bugs_count": 15,
            "vulnerabilities_count": 8,
            "coverage_pct": 62.00,
            "quality_gate_status": "WARN"
        },
        # Project Gamma - critical issues
        {
            "project_id": projects[2].id,
            "bugs_count": 30,
            "vulnerabilities_count": 12,
            "coverage_pct": 45.25,
            "quality_gate_status": "ERROR"
        },
    ]
    
    for metric_data in metrics_data:
        snapshot = MetricsSnapshot(
            project_id=metric_data["project_id"],
            branch_name="main",
            analysis_date=datetime.utcnow() - timedelta(hours=2),
            fetch_timestamp=datetime.utcnow() - timedelta(hours=1),
            bugs_count=metric_data["bugs_count"],
            vulnerabilities_count=metric_data["vulnerabilities_count"],
            code_smells_count=20,
            coverage_pct=metric_data["coverage_pct"],
            duplications_pct=3.5,
            quality_gate_status=metric_data["quality_gate_status"],
            quality_gate_details={"conditions": []},
            severity_breakdown={"CRITICAL": 2, "MAJOR": 5, "MINOR": 10},
            ncloc=10000
        )
        db.add(snapshot)
    
    db.commit()
    db.close()
    
    yield db_path


class TestDashboardAPI:
    """Integration tests for dashboard API endpoint."""

    def test_get_dashboard_all_projects(self, test_db):
        """Test GET /dashboard returns aggregated data for all projects."""
        response = client.get("/api/v1/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "projects" in data
        assert "aggregates" in data
        
        # Verify project count
        assert len(data["projects"]) == 3
        
        # Verify aggregates (FR-029 formulas)
        aggregates = data["aggregates"]
        assert aggregates["total_projects"] == 3
        assert aggregates["total_bugs"] == 50  # 5 + 15 + 30
        assert aggregates["total_vulnerabilities"] == 22  # 2 + 8 + 12
        assert abs(aggregates["avg_coverage"] - 64.25) < 0.01  # (85.50 + 62.00 + 45.25) / 3
        assert abs(aggregates["quality_gate_pass_rate"] - 33.33) < 0.01  # 1/3 * 100

    def test_get_dashboard_filtered_by_connection(self, test_db):
        """Test GET /dashboard with connection_id filter."""
        # Get connection_id from test_db
        db = next(get_db())
        connection = db.query(Connection).first()
        db.close()
        
        response = client.get(f"/api/v1/dashboard?connection_id={connection.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["projects"]) == 3
        assert data["aggregates"]["total_projects"] == 3

    def test_get_dashboard_filtered_by_project_ids(self, test_db):
        """Test GET /dashboard with project_ids filter."""
        # Get project IDs
        db = next(get_db())
        projects = db.query(Project).all()
        project_ids = f"{projects[0].id},{projects[1].id}"
        db.close()
        
        response = client.get(f"/api/v1/dashboard?project_ids={project_ids}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should only include 2 projects
        assert len(data["projects"]) == 2
        assert data["aggregates"]["total_projects"] == 2
        assert data["aggregates"]["total_bugs"] == 20  # 5 + 15 (excluding project 3)

    def test_get_dashboard_with_branch_filter(self, test_db):
        """Test GET /dashboard with branch filter."""
        response = client.get("/api/v1/dashboard?branch=main")
        
        assert response.status_code == 200
        data = response.json()
        
        # All snapshots are for 'main' branch
        assert len(data["projects"]) == 3

    def test_get_dashboard_staleness_calculation(self, test_db):
        """Test dashboard includes staleness hours for each project."""
        response = client.get("/api/v1/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        
        # Each project should have staleness_hours
        for project in data["projects"]:
            assert "staleness_hours" in project
            assert isinstance(project["staleness_hours"], (int, float))
            assert project["staleness_hours"] >= 0

    def test_get_dashboard_empty_projects(self, test_db):
        """Test GET /dashboard with no matching projects."""
        response = client.get("/api/v1/dashboard?connection_id=9999")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["projects"]) == 0
        assert data["aggregates"]["total_projects"] == 0
        assert data["aggregates"]["total_bugs"] == 0
        assert data["aggregates"]["total_vulnerabilities"] == 0
        assert data["aggregates"]["avg_coverage"] is None  # No coverage data
        assert data["aggregates"]["quality_gate_pass_rate"] == 0.0

    def test_get_dashboard_projects_without_metrics(self, test_db):
        """Test dashboard handles projects with no metrics snapshots."""
        # Add a project without metrics
        db = next(get_db())
        connection = db.query(Connection).first()
        
        new_project = Project(
            connection_id=connection.id,
            project_key="project_no_metrics",
            name="Project Without Metrics",
            description="No metrics yet",
            last_analysis_date=None
        )
        db.add(new_project)
        db.commit()
        db.close()
        
        response = client.get("/api/v1/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still work, projects without metrics are excluded from aggregates
        assert len(data["projects"]) >= 3

    def test_get_dashboard_null_coverage_handling(self, test_db):
        """Test dashboard correctly handles null coverage values in aggregation."""
        # Add project with null coverage
        db = next(get_db())
        connection = db.query(Connection).first()
        project = Project(
            connection_id=connection.id,
            project_key="project_null_cov",
            name="Project Null Coverage",
            last_analysis_date=datetime.utcnow()
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        
        snapshot = MetricsSnapshot(
            project_id=project.id,
            branch_name="main",
            analysis_date=datetime.utcnow(),
            fetch_timestamp=datetime.utcnow(),
            bugs_count=10,
            vulnerabilities_count=5,
            code_smells_count=15,
            coverage_pct=None,  # Null coverage
            duplications_pct=2.0,
            quality_gate_status="OK",
            quality_gate_details={},
            severity_breakdown={},
            ncloc=5000
        )
        db.add(snapshot)
        db.commit()
        db.close()
        
        response = client.get("/api/v1/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        
        # Average coverage should exclude null values
        # Original 3 projects: (85.50 + 62.00 + 45.25) / 3 = 64.25
        # Should remain the same, null excluded
        assert abs(data["aggregates"]["avg_coverage"] - 64.25) < 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
