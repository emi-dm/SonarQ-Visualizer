"""Project service for SonarQube project synchronization and retrieval."""

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from backend.src.db.repositories.connection_repository import ConnectionRepository
from backend.src.db.repositories.project_repository import ProjectRepository
from backend.src.db.repositories.metrics_repository import MetricsRepository
from backend.src.services.sonarqube_client import SonarQubeClient
from backend.src.utils.errors import PartialSyncError, InvalidAPIResponseError, ValidationError
from backend.src.utils.logger import get_logger

logger = get_logger(__name__)


class ProjectService:
    """Service for project-related operations."""

    def __init__(self, db: Session):
        self.db = db
        self.connection_repo = ConnectionRepository(db)
        self.project_repo = ProjectRepository(db)
        self.metrics_repo = MetricsRepository(db)

    def sync_projects_from_sonarqube(self, connection_id: int, token: str) -> dict:
        """Sync projects from SonarQube for a given connection."""
        connection = self.connection_repo.get_by_id(connection_id)

        if "sonarcloud.io" in connection.server_url and not connection.organization:
            raise ValidationError(
                "SonarCloud requires an organization key for project sync",
                {"organization": "required"}
            )

        client = SonarQubeClient(connection.server_url, token)
        try:
            projects = client.get_projects(organization=connection.organization)
        finally:
            client.close()

        total_projects = len(projects)
        failed_projects: List[str] = []
        created_count = 0
        updated_count = 0

        for project in projects:
            project_key = project.get("project_key")
            name = project.get("name")
            if not project_key or not name:
                failed_projects.append(project_key or "unknown")
                continue

        if total_projects > 0 and (len(failed_projects) / total_projects) > 0.5:
            raise PartialSyncError(
                "Sync rolled back: too many project failures",
                failed_projects=failed_projects,
                total_projects=total_projects,
                details={"threshold_exceeded": True}
            )

        for project in projects:
            project_key = project.get("project_key")
            name = project.get("name")
            if not project_key or not name:
                continue

            existing = self.project_repo.get_by_key(connection_id, project_key)
            if existing:
                existing.name = name
                existing.description = project.get("description")
                existing.last_analysis_date = project.get("last_analysis_date")
                self.project_repo.update(existing)
                updated_count += 1
            else:
                self.project_repo.create(
                    connection_id=connection_id,
                    project_key=project_key,
                    name=name,
                    description=project.get("description"),
                    last_analysis_date=project.get("last_analysis_date")
                )
                created_count += 1

        synced_count = created_count + updated_count
        return {
            "synced_count": synced_count,
            "new_count": created_count,
            "updated_count": updated_count,
            "failed_count": len(failed_projects),
            "failed_projects": failed_projects
        }

    def list_projects(
        self,
        connection_id: int,
        include_metrics: bool = False,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], dict]:
        """List projects for a connection with pagination."""
        self.connection_repo.get_by_id(connection_id)
        projects, total_count = self.project_repo.list_by_connection(connection_id, page, page_size)

        project_list: List[dict] = []
        for project in projects:
            project_data = project
            if include_metrics:
                latest = self.metrics_repo.get_latest_snapshot(project.id)
                project_data = {
                    "project": project,
                    "latest_metrics": latest
                }
            project_list.append(project_data)

        total_pages = (total_count + page_size - 1) // page_size
        pagination = {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages
        }

        return project_list, pagination

    def get_project(self, project_id: int, include_metrics: bool = False) -> dict:
        project = self.project_repo.get_by_id(project_id)
        latest_metrics = None
        branches: List[str] = []

        if include_metrics:
            latest_metrics = self.metrics_repo.get_latest_snapshot(project_id)
            branches = [row["branch_name"] for row in self.metrics_repo.get_branches(project_id)]

        return {
            "project": project,
            "latest_metrics": latest_metrics,
            "branches": branches
        }

    def get_project_branches(self, project_id: int) -> List[dict]:
        self.project_repo.get_by_id(project_id)
        return self.metrics_repo.get_branches(project_id)
