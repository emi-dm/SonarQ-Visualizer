"""Project repository for database CRUD operations."""

from typing import List, Optional, Tuple
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.src.models.project import Project
from backend.src.utils.errors import ConflictError, NotFoundError, DatabaseError
from backend.src.utils.logger import get_logger

logger = get_logger(__name__)


class ProjectRepository:
    """Repository for Project model operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        connection_id: int,
        project_key: str,
        name: str,
        description: Optional[str] = None,
        last_analysis_date: Optional[datetime] = None
    ) -> Project:
        try:
            project = Project(
                connection_id=connection_id,
                project_key=project_key,
                name=name,
                description=description,
                last_analysis_date=last_analysis_date
            )
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)
            logger.info(f"Created project: {project.project_key} (ID: {project.id})")
            return project
        except IntegrityError as e:
            self.db.rollback()
            if "UNIQUE constraint failed" in str(e):
                raise ConflictError(
                    f"Project with key '{project_key}' already exists",
                    {"project_key": project_key, "connection_id": connection_id}
                )
            raise DatabaseError(f"Failed to create project: {e}")
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to create project: {e}")

    def update(self, project: Project) -> Project:
        try:
            self.db.commit()
            self.db.refresh(project)
            return project
        except IntegrityError as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to update project: {e}")
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to update project: {e}")

    def get_by_id(self, project_id: int) -> Project:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise NotFoundError(
                f"Project with ID {project_id} not found",
                {"project_id": project_id}
            )
        return project

    def get_by_key(self, connection_id: int, project_key: str) -> Optional[Project]:
        return (
            self.db.query(Project)
            .filter(Project.connection_id == connection_id, Project.project_key == project_key)
            .first()
        )

    def list_by_connection(
        self,
        connection_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Project], int]:
        query = self.db.query(Project).filter(Project.connection_id == connection_id)
        total = query.count()
        projects = (
            query.order_by(Project.name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return projects, total

    def delete(self, project_id: int) -> None:
        try:
            project = self.get_by_id(project_id)
            self.db.delete(project)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to delete project: {e}")
