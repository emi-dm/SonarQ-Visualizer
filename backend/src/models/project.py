"""Project SQLAlchemy model.

Represents a SonarQube project tracked by the visualizer.
"""

from datetime import datetime, timezone
import re

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Index
from sqlalchemy.orm import validates

from backend.src.db.base import Base


def utc_now() -> datetime:
    """Return current UTC datetime as naive for DB compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Project(Base):
    """Project model for SonarQube projects."""

    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("connection_id", "project_key", name="uq_projects_connection_key"),
        Index("ix_projects_last_analysis_date", "last_analysis_date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(Integer, ForeignKey("connections.id"), nullable=False)
    project_key = Column(String(255), nullable=False)
    name = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    last_analysis_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    @validates("name")
    def validate_name(self, key: str, name: str) -> str:
        """Validate project name."""
        trimmed = name.strip() if name else ""
        if not trimmed:
            raise ValueError("Project name cannot be empty")
        return trimmed

    @validates("project_key")
    def validate_project_key(self, key: str, project_key: str) -> str:
        """Validate project key format."""
        trimmed = project_key.strip() if project_key else ""
        if not trimmed:
            raise ValueError("Project key cannot be empty")
        if not re.match(r"^[A-Za-z0-9_.:-]+$", trimmed):
            raise ValueError("Invalid project key format")
        return trimmed

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, key='{self.project_key}', name='{self.name}')>"
