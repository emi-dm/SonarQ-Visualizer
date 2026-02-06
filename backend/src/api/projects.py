"""Projects API router with list, sync, and detail endpoints."""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.src.db.base import get_db
from backend.src.services.project_service import ProjectService
from backend.src.utils.errors import (
    NotFoundError,
    PartialSyncError,
    AuthenticationError,
    TokenExpiredError,
    RateLimitError,
    ConnectionError,
    InvalidAPIResponseError,
    ValidationError
)
from backend.src.utils.logger import get_logger, log_api_call
import time

logger = get_logger(__name__)
router = APIRouter(prefix="/connections", tags=["projects"])
projects_router = APIRouter(prefix="/projects", tags=["projects"])  # Direct project endpoints


class ProjectResponse(BaseModel):
    id: int
    connection_id: int
    project_key: str
    name: str
    description: Optional[str]
    last_analysis_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MetricsSnapshotResponse(BaseModel):
    id: int
    project_id: int
    branch_name: str
    analysis_date: datetime
    fetch_timestamp: datetime
    bugs_count: int
    vulnerabilities_count: int
    code_smells_count: int
    coverage_pct: Optional[float]
    duplications_pct: Optional[float]
    quality_gate_status: str
    quality_gate_details: Optional[dict]
    severity_breakdown: Optional[dict]
    ncloc: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectDetailedResponse(ProjectResponse):
    latest_metrics: Optional[MetricsSnapshotResponse] = None
    branches: List[str] = []


class PaginationResponse(BaseModel):
    page: int
    page_size: int
    total_count: int
    total_pages: int


class ProjectListResponse(BaseModel):
    projects: List[ProjectDetailedResponse]
    pagination: PaginationResponse


class SyncRequest(BaseModel):
    token: str = Field(..., min_length=1)


class SyncResponse(BaseModel):
    synced_count: int
    new_count: int
    updated_count: int
    failed_count: int
    failed_projects: List[str]


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None


def build_error_response(status_code: int, error: str, message: str, details: Optional[dict] = None) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": error, "message": message, "details": details})


@router.get("/{connection_id}/projects", response_model=ProjectListResponse)
async def list_projects(
    connection_id: int,
    include_metrics: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    start_time = time.time()

    try:
        service = ProjectService(db)
        projects, pagination = service.list_projects(connection_id, include_metrics, page, page_size)

        response_projects = []
        for entry in projects:
            if isinstance(entry, dict):
                project = entry["project"]
                latest = entry.get("latest_metrics")
                branches = entry.get("branches") or []
                response_projects.append(ProjectDetailedResponse(
                    **ProjectResponse.from_orm(project).dict(),
                    latest_metrics=MetricsSnapshotResponse.from_orm(latest) if latest else None,
                    branches=branches
                ))
            else:
                response_projects.append(ProjectDetailedResponse(**ProjectResponse.from_orm(entry).dict()))

        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/connections/{connection_id}/projects", "GET", duration_ms, 200)

        return ProjectListResponse(
            projects=response_projects,
            pagination=PaginationResponse(**pagination)
        )

    except NotFoundError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/connections/{connection_id}/projects", "GET", duration_ms, 404, str(e))
        return build_error_response(status.HTTP_404_NOT_FOUND, "NOT_FOUND", e.message, e.details)


@router.post("/{connection_id}/projects/sync", response_model=SyncResponse)
async def sync_projects(
    connection_id: int,
    payload: SyncRequest,
    db: Session = Depends(get_db)
):
    start_time = time.time()

    try:
        service = ProjectService(db)
        result = service.sync_projects_from_sonarqube(connection_id, payload.token)

        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/connections/{connection_id}/projects/sync", "POST", duration_ms, 200)
        return result

    except PartialSyncError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/connections/{connection_id}/projects/sync", "POST", duration_ms, 409, str(e))
        return build_error_response(
            status.HTTP_409_CONFLICT,
            "PARTIAL_SYNC_FAILURE",
            e.message,
            {
                "failed_projects": e.failed_projects,
                "failed_count": len(e.failed_projects),
                "total_projects": e.total_projects,
                "threshold_exceeded": True
            }
        )
    except (AuthenticationError, TokenExpiredError) as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/connections/{connection_id}/projects/sync", "POST", duration_ms, 401, str(e))
        error_code = "TOKEN_EXPIRED" if isinstance(e, TokenExpiredError) else "AUTHENTICATION_FAILED"
        return build_error_response(status.HTTP_401_UNAUTHORIZED, error_code, e.message, e.details)
    except RateLimitError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/connections/{connection_id}/projects/sync", "POST", duration_ms, 429, str(e))
        return build_error_response(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "RATE_LIMIT_EXCEEDED",
            e.message,
            {"retry_after_seconds": e.retry_after_seconds}
        )
    except ValidationError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/connections/{connection_id}/projects/sync", "POST", duration_ms, 400, str(e))
        return build_error_response(status.HTTP_400_BAD_REQUEST, "VALIDATION_ERROR", e.message, e.details)
    except NotFoundError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/connections/{connection_id}/projects/sync", "POST", duration_ms, 404, str(e))
        return build_error_response(status.HTTP_404_NOT_FOUND, "NOT_FOUND", e.message, e.details)
    except (ConnectionError, InvalidAPIResponseError) as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/connections/{connection_id}/projects/sync", "POST", duration_ms, 503, str(e))
        return build_error_response(status.HTTP_503_SERVICE_UNAVAILABLE, "CONNECTION_FAILED", e.message, e.details)


@projects_router.get("/{project_id}", response_model=ProjectDetailedResponse)
async def get_project(
    project_id: int,
    include_metrics: bool = Query(default=False),
    db: Session = Depends(get_db)
):
    start_time = time.time()

    try:
        service = ProjectService(db)
        result = service.get_project(project_id, include_metrics)

        project = result["project"]
        latest_metrics = result.get("latest_metrics")
        branches = result.get("branches") or []

        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/projects/{project_id}", "GET", duration_ms, 200)

        return ProjectDetailedResponse(
            **ProjectResponse.from_orm(project).dict(),
            latest_metrics=MetricsSnapshotResponse.from_orm(latest_metrics) if latest_metrics else None,
            branches=branches
        )

    except NotFoundError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/projects/{project_id}", "GET", duration_ms, 404, str(e))
        return build_error_response(status.HTTP_404_NOT_FOUND, "NOT_FOUND", e.message, e.details)


@projects_router.get("/{project_id}/branches", response_model=List[dict])
async def list_branches(
    project_id: int,
    db: Session = Depends(get_db)
):
    start_time = time.time()

    try:
        service = ProjectService(db)
        branches = service.get_project_branches(project_id)

        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/projects/{project_id}/branches", "GET", duration_ms, 200)

        return branches

    except NotFoundError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/projects/{project_id}/branches", "GET", duration_ms, 404, str(e))
        return build_error_response(status.HTTP_404_NOT_FOUND, "NOT_FOUND", e.message, e.details)
