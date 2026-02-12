"""MetricsSnapshot SQLAlchemy model.

Represents quality metrics captured for a project branch.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Index
from sqlalchemy.orm import validates
from sqlalchemy.types import JSON

from backend.src.db.base import Base


def utc_now() -> datetime:
    """Return current UTC datetime as naive for DB compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class MetricsSnapshot(Base):
    """Metrics snapshot model for project quality metrics."""

    __tablename__ = "metrics_snapshots"
    __table_args__ = (
        Index("ix_metrics_project_branch_date", "project_id", "branch_name", "analysis_date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    branch_name = Column(String(255), nullable=False, default="main")
    analysis_date = Column(DateTime, nullable=False)
    fetch_timestamp = Column(DateTime, nullable=False, default=utc_now)

    bugs_count = Column(Integer, nullable=False, default=0)
    vulnerabilities_count = Column(Integer, nullable=False, default=0)
    code_smells_count = Column(Integer, nullable=False, default=0)
    coverage_pct = Column(Float, nullable=True)
    duplications_pct = Column(Float, nullable=True)
    quality_gate_status = Column(String(20), nullable=False)
    quality_gate_details = Column(JSON, nullable=True)
    severity_breakdown = Column(JSON, nullable=True)
    ncloc = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    def __init__(self, **kwargs):
        if "fetch_timestamp" not in kwargs or kwargs["fetch_timestamp"] is None:
            kwargs["fetch_timestamp"] = utc_now()
        super().__init__(**kwargs)

    @validates("branch_name")
    def validate_branch_name(self, key: str, branch_name: str) -> str:
        trimmed = branch_name.strip() if branch_name else ""
        if not trimmed:
            raise ValueError("Branch name cannot be empty")
        return trimmed

    @validates("bugs_count", "vulnerabilities_count", "code_smells_count")
    def validate_counts(self, key: str, value: int) -> int:
        if value is None or value < 0:
            raise ValueError(f"{key} must be >= 0")
        return value

    @validates("coverage_pct", "duplications_pct")
    def validate_percentages(self, key: str, value: Optional[float]) -> Optional[float]:
        if value is None:
            return value
        if value < 0 or value > 100:
            raise ValueError(f"{key} must be between 0 and 100")
        return value

    @validates("quality_gate_status")
    def validate_quality_gate_status(self, key: str, value: str) -> str:
        if value not in {"OK", "WARN", "ERROR"}:
            raise ValueError("quality_gate_status must be one of OK, WARN, ERROR")
        return value

    @validates("analysis_date")
    def validate_analysis_date(self, key: str, value: datetime) -> datetime:
        if self.fetch_timestamp and value > self.fetch_timestamp:
            raise ValueError("analysis_date cannot be after fetch_timestamp")
        return value

    @validates("fetch_timestamp")
    def validate_fetch_timestamp(self, key: str, value: datetime) -> datetime:
        if self.analysis_date and self.analysis_date > value:
            raise ValueError("analysis_date cannot be after fetch_timestamp")
        return value

    @validates("severity_breakdown", "quality_gate_details")
    def validate_json_fields(self, key: str, value: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if value is None:
            return value
        if not isinstance(value, dict):
            raise ValueError(f"{key} must be a JSON object")
        return value

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics snapshot to dictionary representation.
        
        Returns:
            Dictionary with all metrics fields
        """
        return {
            "id": self.id,
            "project_id": self.project_id,
            "branch_name": self.branch_name,
            "analysis_date": self.analysis_date.isoformat() if self.analysis_date else None,
            "fetch_timestamp": self.fetch_timestamp.isoformat() if self.fetch_timestamp else None,
            "bugs_count": self.bugs_count,
            "vulnerabilities_count": self.vulnerabilities_count,
            "code_smells_count": self.code_smells_count,
            "coverage_pct": self.coverage_pct,
            "duplications_pct": self.duplications_pct,
            "quality_gate_status": self.quality_gate_status,
            "quality_gate_details": self.quality_gate_details,
            "severity_breakdown": self.severity_breakdown,
            "ncloc": self.ncloc,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self) -> str:
        return f"<MetricsSnapshot(id={self.id}, project_id={self.project_id}, branch='{self.branch_name}')>"
