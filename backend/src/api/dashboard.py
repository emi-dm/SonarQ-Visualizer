"""Dashboard API router for multi-project aggregation.

Endpoints:
- GET /dashboard - Multi-project dashboard with aggregated metrics
"""

from typing import Optional, Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.src.constants import DASHBOARD_PATH
from backend.src.db.base import get_db
from backend.src.services.dashboard_service import DashboardService
from backend.src.utils.logger import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix=DASHBOARD_PATH, tags=["dashboard"])


@router.get("")
async def get_dashboard(
    db: Annotated[Session, Depends(get_db)],
    connection_id: Optional[int] = Query(None, description="Filter by connection ID"),
    project_ids: Optional[str] = Query(
        None,
        description="Comma-separated project IDs to include (optional, default: all)"
    ),
    branch: Optional[str] = Query(None, description="Branch name to compare. If not specified, uses latest from any branch")
):
    """Get multi-project dashboard data with aggregated metrics.
    
    Returns:
        Dashboard data with projects list and aggregate statistics
    """
    logger.info(
        f"GET /dashboard - connection_id={connection_id}, "
        f"project_ids={project_ids}, branch={branch}"
    )
    
    # Parse project_ids if provided
    parsed_project_ids = None
    if project_ids:
        try:
            parsed_project_ids = [int(pid.strip()) for pid in project_ids.split(",")]
        except ValueError:
            logger.error(f"Invalid project_ids format: {project_ids}")
            return {
                "error": "Invalid project_ids format. Must be comma-separated integers."
            }
    
    # Get dashboard data from service
    dashboard_service = DashboardService(db)
    
    try:
        dashboard_data = dashboard_service.get_dashboard_data(
            connection_id=connection_id,
            project_ids=parsed_project_ids,
            branch=branch
        )
        
        logger.info(
            f"Dashboard data retrieved: {len(dashboard_data['projects'])} projects"
        )
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {str(e)}", exc_info=True)
        return {
            "error": "Failed to retrieve dashboard data",
            "details": str(e)
        }


@router.get("/comparison")
async def get_project_comparison(
    db: Annotated[Session, Depends(get_db)],
    project_ids: str = Query(..., description="Comma-separated project IDs to compare"),
    branch: str = Query("main", description="Branch name to compare")
):
    """Get metrics comparison for specific projects.
    
    Returns:
        List of project metrics for side-by-side comparison
    """
    logger.info(f"GET /dashboard/comparison - project_ids={project_ids}, branch={branch}")
    
    # Parse project_ids
    try:
        parsed_project_ids = [int(pid.strip()) for pid in project_ids.split(",")]
    except ValueError:
        logger.error(f"Invalid project_ids format: {project_ids}")
        return {
            "error": "Invalid project_ids format. Must be comma-separated integers."
        }
    
    if not parsed_project_ids:
        return {
            "error": "At least one project ID must be provided"
        }
    
    # Get comparison data from service
    dashboard_service = DashboardService(db)
    
    try:
        comparison_data = dashboard_service.get_project_comparison(
            project_ids=parsed_project_ids,
            branch=branch
        )
        
        logger.info(f"Comparison data retrieved for {len(comparison_data)} projects")
        
        return {
            "projects": comparison_data,
            "count": len(comparison_data)
        }
        
    except Exception as e:
        logger.error(f"Error fetching comparison data: {str(e)}", exc_info=True)
        return {
            "error": "Failed to retrieve comparison data",
            "details": str(e)
        }


@router.get("/trends/{project_id}")
async def get_project_trends(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    branch: str = Query("main", description="Branch name"),
    limit: int = Query(30, ge=1, le=100, description="Number of historical snapshots")
):
    """Get historical metrics for trend analysis.
    
    Returns:
        List of metrics snapshots ordered by analysis date
    """
    logger.info(
        f"GET /dashboard/trends/{project_id} - branch={branch}, limit={limit}"
    )
    
    dashboard_service = DashboardService(db)
    
    try:
        trends_data = dashboard_service.get_trends_data(
            project_id=project_id,
            branch=branch,
            limit=limit
        )
        
        logger.info(f"Trends data retrieved: {len(trends_data)} snapshots")
        
        return {
            "project_id": project_id,
            "branch": branch,
            "snapshots": trends_data,
            "count": len(trends_data)
        }
        
    except Exception as e:
        logger.error(f"Error fetching trends data: {str(e)}", exc_info=True)
        return {
            "error": "Failed to retrieve trends data",
            "details": str(e)
        }
