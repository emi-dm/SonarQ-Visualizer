"""Metrics service for fetching and storing SonarQube metrics."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from backend.src.db.repositories.connection_repository import ConnectionRepository
from backend.src.db.repositories.metrics_repository import MetricsRepository
from backend.src.db.repositories.project_repository import ProjectRepository
from backend.src.models.metrics_snapshot import MetricsSnapshot
from backend.src.services.sonarqube_client import SonarQubeClient
from backend.src.utils.errors import InvalidAPIResponseError, NotFoundError
from backend.src.utils.logger import get_logger

logger = get_logger(__name__)


def utc_now_naive() -> datetime:
    """Return UTC timestamp as naive datetime for DB compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def aggregate_metrics(snapshots: List[dict]) -> dict:
    """Aggregate metrics snapshots for totals and averages."""
    total_bugs = sum(s["bugs_count"] for s in snapshots)
    total_vulnerabilities = sum(s["vulnerabilities_count"] for s in snapshots)
    total_code_smells = sum(s["code_smells_count"] for s in snapshots)

    coverage_values = [s["coverage_pct"] for s in snapshots if s.get("coverage_pct") is not None]
    duplication_values = [s["duplications_pct"] for s in snapshots if s.get("duplications_pct") is not None]

    avg_coverage = sum(coverage_values) / len(coverage_values) if coverage_values else None
    avg_duplications = sum(duplication_values) / len(duplication_values) if duplication_values else None

    return {
        "total_bugs": total_bugs,
        "total_vulnerabilities": total_vulnerabilities,
        "total_code_smells": total_code_smells,
        "avg_coverage": avg_coverage,
        "avg_duplications": avg_duplications
    }


class MetricsService:
    """Service for metrics operations."""

    def __init__(self, db: Session):
        self.db = db
        self.connection_repo = ConnectionRepository(db)
        self.project_repo = ProjectRepository(db)
        self.metrics_repo = MetricsRepository(db)

    def refresh_metrics(self, project_id: int, token: str, branch: Optional[str] = None) -> MetricsSnapshot:
        """Refresh metrics for a project from SonarQube.
        
        Args:
            project_id: Project ID to refresh
            token: Authentication token  
            branch: Optional branch name. If None, uses SonarQube's default branch.
            
        Returns:
            MetricsSnapshot: Created metrics snapshot
        """
        project = self.project_repo.get_by_id(project_id)
        connection = self.connection_repo.get_by_id(project.connection_id)

        client = SonarQubeClient(connection.server_url, token)
        try:
            metrics_data = client.get_project_metrics(project.project_key, branch)
        finally:
            client.close()

        analysis_date = metrics_data.get("analysis_date")
        fetch_timestamp = utc_now_naive()
        if analysis_date and analysis_date > fetch_timestamp:
            raise InvalidAPIResponseError("Analysis date is in the future")

        # Use the branch name from response if available, otherwise use provided branch or "main"
        branch_name = metrics_data.get("branch_name") or branch or "main"

        snapshot = MetricsSnapshot(
            project_id=project_id,
            branch_name=branch_name,
            analysis_date=analysis_date or fetch_timestamp,
            fetch_timestamp=fetch_timestamp,
            bugs_count=metrics_data["bugs_count"],
            vulnerabilities_count=metrics_data["vulnerabilities_count"],
            code_smells_count=metrics_data["code_smells_count"],
            coverage_pct=metrics_data.get("coverage_pct"),
            duplications_pct=metrics_data.get("duplications_pct"),
            quality_gate_status=metrics_data["quality_gate_status"],
            quality_gate_details=metrics_data.get("quality_gate_details"),
            severity_breakdown=metrics_data.get("severity_breakdown"),
            ncloc=metrics_data.get("ncloc")
        )

        return self.metrics_repo.create(snapshot)

    def get_metrics(self, project_id: int, branch: Optional[str] = None, limit: int = 30) -> List[MetricsSnapshot]:
        """Get metrics for a project.
        
        Args:
            project_id: Project ID
            branch: Optional branch name filter. If None, fetches all branches.
            limit: Maximum number of snapshots to return
            
        Returns:
            List[MetricsSnapshot]: List of metrics snapshots
        """
        self.project_repo.get_by_id(project_id)
        # If branch is explicitly None, fetch for default branch "main"
        branch_filter = branch if branch is not None else "main"
        return self.metrics_repo.list_snapshots(project_id, branch_filter, limit)

    def get_latest_snapshot(self, project_id: int, branch: Optional[str] = None) -> MetricsSnapshot:
        """Get latest metrics snapshot for a project.

        Args:
            project_id: Project ID
            branch: Optional branch name filter. If None, uses default branch "main"

        Returns:
            MetricsSnapshot: Latest metrics snapshot
        """
        self.project_repo.get_by_id(project_id)
        branch_filter = branch if branch is not None else "main"
        snapshot = self.metrics_repo.get_latest_snapshot(project_id, branch_filter)
        if not snapshot:
            raise NotFoundError(
                "No metrics snapshots found for this project",
                {"project_id": project_id, "branch_name": branch_filter}
            )
        return snapshot
