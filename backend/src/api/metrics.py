"""Metrics API router for project metrics endpoints."""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.src.db.base import get_db
from backend.src.services.metrics_service import MetricsService
from backend.src.utils.errors import (
    NotFoundError,
    AuthenticationError,
    TokenExpiredError,
    RateLimitError,
    InvalidAPIResponseError,
    ConnectionError
)
from backend.src.utils.logger import get_logger, log_api_call
import time

logger = get_logger(__name__)
router = APIRouter(prefix="/projects", tags=["metrics"])


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


class MetricsListResponse(BaseModel):
    project_id: int
    branch_name: str
    snapshots: List[MetricsSnapshotResponse]


class MetricsRefreshRequest(BaseModel):
    token: str = Field(..., min_length=1)
    branch: str = Field(default="main")


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None


def build_error_response(status_code: int, error: str, message: str, details: Optional[dict] = None) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": error, "message": message, "details": details})


@router.get("/{project_id}/metrics", response_model=MetricsListResponse)
async def get_metrics(
    project_id: int,
    branch: str = Query(default="main"),
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db)
):
    start_time = time.time()

    try:
        service = MetricsService(db)
        snapshots = service.get_metrics(project_id, branch, limit)

        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/projects/{project_id}/metrics", "GET", duration_ms, 200)

        return MetricsListResponse(
            project_id=project_id,
            branch_name=branch,
            snapshots=[MetricsSnapshotResponse.from_orm(s) for s in snapshots]
        )

    except NotFoundError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/projects/{project_id}/metrics", "GET", duration_ms, 404, str(e))
        return build_error_response(status.HTTP_404_NOT_FOUND, "NOT_FOUND", e.message, e.details)


@router.post("/{project_id}/metrics/refresh", response_model=MetricsSnapshotResponse, status_code=status.HTTP_201_CREATED)
async def refresh_metrics(
    project_id: int,
    payload: MetricsRefreshRequest,
    db: Session = Depends(get_db)
):
    start_time = time.time()

    try:
        service = MetricsService(db)
        snapshot = service.refresh_metrics(project_id, payload.token, payload.branch)

        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/projects/{project_id}/metrics/refresh", "POST", duration_ms, 201)
        return MetricsSnapshotResponse.from_orm(snapshot)

    except (AuthenticationError, TokenExpiredError) as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/projects/{project_id}/metrics/refresh", "POST", duration_ms, 401, str(e))
        error_code = "TOKEN_EXPIRED" if isinstance(e, TokenExpiredError) else "AUTHENTICATION_FAILED"
        return build_error_response(status.HTTP_401_UNAUTHORIZED, error_code, e.message, e.details)
    except InvalidAPIResponseError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/projects/{project_id}/metrics/refresh", "POST", duration_ms, 422, str(e))
        return build_error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, "INVALID_API_RESPONSE", e.message, e.details)
    except RateLimitError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/projects/{project_id}/metrics/refresh", "POST", duration_ms, 429, str(e))
        return build_error_response(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "RATE_LIMIT_EXCEEDED",
            e.message,
            {"retry_after_seconds": e.retry_after_seconds}
        )
    except NotFoundError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/projects/{project_id}/metrics/refresh", "POST", duration_ms, 404, str(e))
        return build_error_response(status.HTTP_404_NOT_FOUND, "NOT_FOUND", e.message, e.details)
    except ConnectionError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/projects/{project_id}/metrics/refresh", "POST", duration_ms, 503, str(e))
        return build_error_response(status.HTTP_503_SERVICE_UNAVAILABLE, "CONNECTION_FAILED", e.message, e.details)
