"""Metrics API router for project metrics endpoints."""

from datetime import datetime
from typing import Optional, List, Annotated
import csv
import io
import json

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.src.constants import PROJECTS_PATH
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
router = APIRouter(prefix=PROJECTS_PATH, tags=["metrics"])


class MetricsSnapshotResponse(BaseModel):
    id: int
    project_id: int
    branch_name: str
    analysis_date: datetime
    fetch_timestamp: datetime
    bugs_count: int
    vulnerabilities_count: int
    code_smells_count: int
    coverage_pct: Optional[float] = None
    duplications_pct: Optional[float] = None
    quality_gate_status: str
    quality_gate_details: Optional[dict] = None
    severity_breakdown: Optional[dict] = None
    ncloc: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MetricsListResponse(BaseModel):
    project_id: int
    branch_name: str
    snapshots: List[MetricsSnapshotResponse]


class MetricsRefreshRequest(BaseModel):
    token: str = Field(..., min_length=1)
    branch: Optional[str] = Field(default=None, description="Branch name. If not provided, uses the default branch.")


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None


def build_error_response(status_code: int, error: str, message: str, details: Optional[dict] = None) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": error, "message": message, "details": details})


@router.get("/{project_id}/metrics", response_model=MetricsListResponse)
async def get_metrics(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    branch: Optional[str] = Query(default=None, description="Branch name filter. If not provided, fetches main branch."),
    limit: int = Query(default=30, ge=1, le=100)
):
    start_time = time.time()

    try:
        service = MetricsService(db)
        snapshots = service.get_metrics(project_id, branch, limit)

        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/projects/{project_id}/metrics", "GET", duration_ms, 200)

        return MetricsListResponse(
            project_id=project_id,
            branch_name=branch or "main",
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
    db: Annotated[Session, Depends(get_db)]
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


@router.get("/{project_id}/metrics/export")
async def export_latest_metrics(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    format: str = Query(default="json", description="Export format: json or csv"),
    branch: Optional[str] = Query(default=None, description="Branch name filter. Defaults to main.")
):
    start_time = time.time()

    if format not in {"json", "csv"}:
        return build_error_response(
            status.HTTP_400_BAD_REQUEST,
            "VALIDATION_ERROR",
            "Invalid export format. Use 'json' or 'csv'.",
            {"format": format}
        )

    try:
        service = MetricsService(db)
        snapshot = service.get_latest_snapshot(project_id, branch)
        branch_name = snapshot.branch_name or branch or "main"

        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/projects/{project_id}/metrics/export", "GET", duration_ms, 200)

        if format == "json":
            response_payload = MetricsSnapshotResponse.from_orm(snapshot).dict()
            return JSONResponse(status_code=status.HTTP_200_OK, content=response_payload)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "project_id",
            "branch_name",
            "analysis_date",
            "fetch_timestamp",
            "bugs_count",
            "vulnerabilities_count",
            "code_smells_count",
            "coverage_pct",
            "duplications_pct",
            "quality_gate_status",
            "quality_gate_details",
            "severity_breakdown",
            "ncloc"
        ])
        writer.writerow([
            snapshot.project_id,
            branch_name,
            snapshot.analysis_date.isoformat() if snapshot.analysis_date else "",
            snapshot.fetch_timestamp.isoformat() if snapshot.fetch_timestamp else "",
            snapshot.bugs_count,
            snapshot.vulnerabilities_count,
            snapshot.code_smells_count,
            snapshot.coverage_pct if snapshot.coverage_pct is not None else "",
            snapshot.duplications_pct if snapshot.duplications_pct is not None else "",
            snapshot.quality_gate_status,
            json.dumps(snapshot.quality_gate_details) if snapshot.quality_gate_details else "",
            json.dumps(snapshot.severity_breakdown) if snapshot.severity_breakdown else "",
            snapshot.ncloc if snapshot.ncloc is not None else ""
        ])

        filename = f"project_{project_id}_{branch_name}_latest_metrics.csv"
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )

    except NotFoundError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/projects/{project_id}/metrics/export", "GET", duration_ms, 404, str(e))
        return build_error_response(status.HTTP_404_NOT_FOUND, "NOT_FOUND", e.message, e.details)
