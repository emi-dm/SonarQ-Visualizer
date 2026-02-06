"""Metrics repository for metrics snapshot operations."""

from typing import List, Optional
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.src.models.metrics_snapshot import MetricsSnapshot
from backend.src.utils.errors import NotFoundError, DatabaseError
from backend.src.utils.logger import get_logger

logger = get_logger(__name__)


class MetricsRepository:
    """Repository for MetricsSnapshot operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, snapshot: MetricsSnapshot) -> MetricsSnapshot:
        try:
            self.db.add(snapshot)
            self.db.commit()
            self.db.refresh(snapshot)
            return snapshot
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to create metrics snapshot: {e}")

    def list_snapshots(
        self,
        project_id: int,
        branch_name: str = "main",
        limit: int = 30
    ) -> List[MetricsSnapshot]:
        return (
            self.db.query(MetricsSnapshot)
            .filter(
                MetricsSnapshot.project_id == project_id,
                MetricsSnapshot.branch_name == branch_name
            )
            .order_by(MetricsSnapshot.analysis_date.desc())
            .limit(limit)
            .all()
        )

    def get_latest_snapshot(self, project_id: int, branch_name: str = "main") -> Optional[MetricsSnapshot]:
        return (
            self.db.query(MetricsSnapshot)
            .filter(
                MetricsSnapshot.project_id == project_id,
                MetricsSnapshot.branch_name == branch_name
            )
            .order_by(MetricsSnapshot.analysis_date.desc())
            .first()
        )

    def get_branches(self, project_id: int) -> List[dict]:
        rows = (
            self.db.query(
                MetricsSnapshot.branch_name.label("branch_name"),
                func.max(MetricsSnapshot.analysis_date).label("latest_analysis_date"),
                func.count(MetricsSnapshot.id).label("snapshot_count")
            )
            .filter(MetricsSnapshot.project_id == project_id)
            .group_by(MetricsSnapshot.branch_name)
            .all()
        )

        return [
            {
                "branch_name": row.branch_name,
                "latest_analysis_date": row.latest_analysis_date,
                "snapshot_count": row.snapshot_count
            }
            for row in rows
        ]
