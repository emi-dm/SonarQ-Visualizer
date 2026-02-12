"""Dashboard service for multi-project statistics calculation.

Implements FR-029 dashboard aggregation formulas for metrics across multiple projects.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.src.models.project import Project
from backend.src.models.metrics_snapshot import MetricsSnapshot
from backend.src.utils.logger import get_logger


logger = get_logger(__name__)


class DashboardService:
    """Service for dashboard data aggregation and multi-project statistics."""
    
    def __init__(self, db: Session):
        """Initialize dashboard service with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_dashboard_data(
        self,
        connection_id: Optional[int] = None,
        project_ids: Optional[List[int]] = None,
        branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get multi-project dashboard data with aggregated metrics.
        
        Args:
            connection_id: Filter by connection ID (optional)
            project_ids: List of specific project IDs to include (optional)
            branch: Branch name to compare across projects. If None, uses latest snapshot from any branch.
            
        Returns:
            Dictionary with 'projects' list and 'aggregates' statistics
        """
        logger.info( 
            f"Fetching dashboard data - connection_id={connection_id}, "
            f"project_ids={project_ids}, branch={branch}"
        )
        
        # Build query for projects
        query = self.db.query(Project)
        
        if connection_id:
            query = query.filter(Project.connection_id == connection_id)
        
        if project_ids:
            query = query.filter(Project.id.in_(project_ids))
        
        projects = query.all()
        
        # Fetch latest metrics for each project
        project_data = []
        all_metrics = []
        
        for project in projects:
            # Build query for latest metrics snapshot
            snapshot_query = self.db.query(MetricsSnapshot).filter(
                MetricsSnapshot.project_id == project.id
            )
            
            # Filter by branch if specified, otherwise get latest from any branch
            if branch:
                snapshot_query = snapshot_query.filter(
                    MetricsSnapshot.branch_name == branch
                )
            
            latest_snapshot = snapshot_query.order_by(
                MetricsSnapshot.fetch_timestamp.desc()
            ).first()
            
            if latest_snapshot:
                # Calculate staleness
                staleness_hours = self._calculate_staleness_hours(
                    latest_snapshot.fetch_timestamp
                )
                
                project_data.append({
                    "project_id": project.id,
                    "project_name": project.name,
                    "project_key": project.project_key,
                    "latest_metrics": latest_snapshot.to_dict(),
                    "staleness_hours": staleness_hours
                })
                
                all_metrics.append(latest_snapshot)
        
        # Calculate aggregate statistics (FR-029)
        aggregates = self._calculate_aggregates(all_metrics)
        
        logger.info(
            f"Dashboard data retrieved: {len(project_data)} projects with metrics"
        )
        
        return {
            "projects": project_data,
            "aggregates": aggregates
        }
    
    def _calculate_staleness_hours(self, fetch_timestamp: datetime) -> float:
        """Calculate hours since metrics were last fetched.
        
        Args:
            fetch_timestamp: When metrics were fetched
            
        Returns:
            Hours since fetch (rounded to 2 decimal places)
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        delta = now - fetch_timestamp
        hours = delta.total_seconds() / 3600
        
        return round(hours, 2)
    
    def _calculate_aggregates(self, metrics: List[MetricsSnapshot]) -> Dict[str, Any]:
        """Calculate aggregate statistics across all projects (FR-029).
        
        Implements formulas:
        - total_bugs = SUM(bugs_count)
        - total_vulnerabilities = SUM(vulnerabilities_count)
        - avg_coverage = AVG(coverage_pct) excluding nulls
        - quality_gate_pass_rate = (COUNT(status='OK') / COUNT(*)) * 100
        
        Args:
            metrics: List of MetricsSnapshot objects
            
        Returns:
            Dictionary with aggregate statistics
        """
        if not metrics:
            return {
                "total_projects": 0,
                "total_bugs": 0,
                "total_vulnerabilities": 0,
                "total_code_smells": 0,
                "avg_coverage": None,
                "avg_duplications": None,
                "quality_gate_pass_rate": 0.0
            }
        
        # Calculate totals
        total_bugs = sum(m.bugs_count for m in metrics)
        total_vulnerabilities = sum(m.vulnerabilities_count for m in metrics)
        total_code_smells = sum(m.code_smells_count for m in metrics)
        
        # Calculate average coverage (excluding nulls)
        coverage_values = [m.coverage_pct for m in metrics if m.coverage_pct is not None]
        avg_coverage = None
        if coverage_values:
            avg_coverage = round(sum(coverage_values) / len(coverage_values), 2)
        
        # Calculate average duplications (excluding nulls)
        duplication_values = [m.duplications_pct for m in metrics if m.duplications_pct is not None]
        avg_duplications = None
        if duplication_values:
            avg_duplications = round(sum(duplication_values) / len(duplication_values), 2)
        
        # Calculate quality gate pass rate
        ok_count = sum(1 for m in metrics if m.quality_gate_status == 'OK')
        total_count = len(metrics)
        quality_gate_pass_rate = round((ok_count / total_count) * 100.0, 2)
        
        logger.debug(
            f"Aggregates calculated - total_bugs={total_bugs}, "
            f"total_vulnerabilities={total_vulnerabilities}, "
            f"avg_coverage={avg_coverage}, "
            f"quality_gate_pass_rate={quality_gate_pass_rate}%"
        )
        
        return {
            "total_projects": total_count,
            "total_bugs": total_bugs,
            "total_vulnerabilities": total_vulnerabilities,
            "total_code_smells": total_code_smells,
            "avg_coverage": avg_coverage,
            "avg_duplications": avg_duplications,
            "quality_gate_pass_rate": quality_gate_pass_rate
        }
    
    def get_project_comparison(
        self,
        project_ids: List[int],
        branch: str = "main"
    ) -> List[Dict[str, Any]]:
        """Get metrics comparison for specific projects.
        
        Args:
            project_ids: List of project IDs to compare
            branch: Branch name to compare (default: 'main')
            
        Returns:
            List of project metrics for comparison
        """
        logger.info(f"Fetching comparison data for {len(project_ids)} projects")
        
        dashboard_data = self.get_dashboard_data(
            project_ids=project_ids,
            branch=branch
        )
        
        return dashboard_data["projects"]
    
    def get_trends_data(
        self,
        project_id: int,
        branch: str = "main",
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Get historical metrics for trend analysis.
        
        Args:
            project_id: Project ID
            branch: Branch name
            limit: Number of historical snapshots to return (default: 30)
            
        Returns:
            List of metrics snapshots ordered by analysis date (oldest first)
        """
        logger.info(f"Fetching trend data for project {project_id}, limit={limit}")
        
        snapshots = (
            self.db.query(MetricsSnapshot)
            .filter(
                and_(
                    MetricsSnapshot.project_id == project_id,
                    MetricsSnapshot.branch_name == branch
                )
            )
            .order_by(MetricsSnapshot.analysis_date.asc())
            .limit(limit)
            .all()
        )
        
        trends = [snapshot.to_dict() for snapshot in snapshots]
        
        logger.info(f"Retrieved {len(trends)} snapshots for trends")
        return trends
