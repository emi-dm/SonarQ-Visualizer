"""Connections API router with CRUD endpoints."""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from backend.src.db.base import get_db
from backend.src.services.connection_service import ConnectionService
from backend.src.utils.errors import (
    NotFoundError,
    ConflictError,
    ConnectionError as ConnError,
    AuthenticationError,
    TokenExpiredError
)
from backend.src.utils.logger import get_logger, log_api_call
import time

logger = get_logger(__name__)
router = APIRouter(prefix="/connections", tags=["connections"])


# Pydantic models for request/response
class ConnectionCreate(BaseModel):
    """Request model for creating a connection."""
    name: str = Field(..., min_length=1, max_length=255)
    server_url: str = Field(..., min_length=1)
    token: str = Field(..., min_length=1)
    validate: bool = Field(default=True)
    
    @validator('server_url')
    def validate_url(cls, v):
        """Validate server URL format."""
        from urllib.parse import urlparse

        parsed = urlparse(v)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError('Invalid URL format')
        if any(char.isspace() for char in v):
            raise ValueError('Invalid URL format')
        return v.rstrip('/')


class ConnectionUpdate(BaseModel):
    """Request model for updating a connection."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    server_url: Optional[str] = Field(None, min_length=1)
    is_active: Optional[bool] = None


class ConnectionValidate(BaseModel):
    """Request model for validating a connection."""
    token: str = Field(..., min_length=1)


class ConnectionResponse(BaseModel):
    """Response model for connection."""
    id: int
    name: str
    server_url: str
    server_version: Optional[str]
    is_active: bool
    last_validated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ValidationResponse(BaseModel):
    """Response model for validation result."""
    status: str
    server_version: Optional[str]
    server_status: Optional[str]


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str
    message: str
    details: Optional[dict] = None


def build_error_response(
    status_code: int,
    error: str,
    message: str,
    details: Optional[dict] = None
) -> JSONResponse:
    """Build a consistent error response payload."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error,
            "message": message,
            "details": details
        }
    )


@router.post("", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    connection: ConnectionCreate,
    db: Session = Depends(get_db)
):
    """Create a new SonarQube connection.
    
    Args:
        connection: Connection details
        db: Database session
        
    Returns:
        ConnectionResponse: Created connection
        
    Raises:
        HTTPException: If creation fails
    """
    start_time = time.time()
    
    try:
        service = ConnectionService(db)
        created_connection, validation_result = service.create_connection(
            name=connection.name,
            server_url=connection.server_url,
            token=connection.token,
            validate=connection.validate
        )
        
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, "/connections", "POST", duration_ms, 201)
        
        return created_connection
        
    except ConflictError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, "/connections", "POST", duration_ms, 409, str(e))
        return build_error_response(
            status.HTTP_409_CONFLICT,
            "CONFLICT",
            e.message,
            e.details
        )
    except (ConnError, AuthenticationError, TokenExpiredError) as e:
        duration_ms = (time.time() - start_time) * 1000
        status_code = 401 if isinstance(e, (AuthenticationError, TokenExpiredError)) else 422
        error_code = "AUTHENTICATION_FAILED"
        if isinstance(e, TokenExpiredError):
            error_code = "TOKEN_EXPIRED"
        if isinstance(e, ConnError):
            error_code = "VALIDATION_ERROR"
        log_api_call(logger, "/connections", "POST", duration_ms, status_code, str(e))
        return build_error_response(
            status_code,
            error_code,
            e.message,
            e.details
        )
    except ValueError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, "/connections", "POST", duration_ms, 422, str(e))
        return build_error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "VALIDATION_ERROR",
            str(e)
        )


@router.get("", response_model=List[ConnectionResponse])
async def list_connections(db: Session = Depends(get_db)):
    """List all connections.
    
    Args:
        db: Database session
        
    Returns:
        List[ConnectionResponse]: List of connections
    """
    start_time = time.time()
    
    service = ConnectionService(db)
    connections = service.list_connections()
    
    duration_ms = (time.time() - start_time) * 1000
    log_api_call(logger, "/connections", "GET", duration_ms, 200)
    
    return connections


@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(
    connection_id: int,
    db: Session = Depends(get_db)
):
    """Get connection by ID.
    
    Args:
        connection_id: Connection ID
        db: Database session
        
    Returns:
        ConnectionResponse: Connection details
        
    Raises:
        HTTPException: If connection not found
    """
    start_time = time.time()
    
    try:
        service = ConnectionService(db)
        connection = service.get_connection(connection_id)
        
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/connections/{connection_id}", "GET", duration_ms, 200)
        
        return connection
        
    except NotFoundError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/connections/{connection_id}", "GET", duration_ms, 404, str(e))
        return build_error_response(
            status.HTTP_404_NOT_FOUND,
            "NOT_FOUND",
            e.message,
            e.details
        )


@router.put("/{connection_id}", response_model=ConnectionResponse)
async def update_connection(
    connection_id: int,
    connection: ConnectionUpdate,
    db: Session = Depends(get_db)
):
    """Update connection details.
    
    Args:
        connection_id: Connection ID
        connection: Fields to update
        db: Database session
        
    Returns:
        ConnectionResponse: Updated connection
        
    Raises:
        HTTPException: If update fails
    """
    start_time = time.time()
    
    try:
        service = ConnectionService(db)
        updated_connection = service.update_connection(
            connection_id=connection_id,
            name=connection.name,
            server_url=connection.server_url,
            is_active=connection.is_active
        )
        
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/connections/{connection_id}", "PUT", duration_ms, 200)
        
        return updated_connection
        
    except NotFoundError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/connections/{connection_id}", "PUT", duration_ms, 404, str(e))
        return build_error_response(
            status.HTTP_404_NOT_FOUND,
            "NOT_FOUND",
            e.message,
            e.details
        )
    except ConflictError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/connections/{connection_id}", "PUT", duration_ms, 409, str(e))
        return build_error_response(
            status.HTTP_409_CONFLICT,
            "CONFLICT",
            e.message,
            e.details
        )


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: int,
    db: Session = Depends(get_db)
):
    """Delete a connection.
    
    Args:
        connection_id: Connection ID
        db: Database session
        
    Raises:
        HTTPException: If deletion fails
    """
    start_time = time.time()
    
    try:
        service = ConnectionService(db)
        service.delete_connection(connection_id)
        
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/connections/{connection_id}", "DELETE", duration_ms, 204)
        
    except NotFoundError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/connections/{connection_id}", "DELETE", duration_ms, 404, str(e))
        return build_error_response(
            status.HTTP_404_NOT_FOUND,
            "NOT_FOUND",
            e.message,
            e.details
        )


@router.post("/{connection_id}/validate", response_model=ValidationResponse)
async def validate_connection(
    connection_id: int,
    payload: ConnectionValidate,
    db: Session = Depends(get_db)
):
    """Validate a connection with SonarQube server.
    
    Args:
        connection_id: Connection ID
        payload: Validation payload with token
        db: Database session
        
    Returns:
        ValidationResponse: Validation result
        
    Raises:
        HTTPException: If validation fails
    """
    start_time = time.time()
    
    try:
        service = ConnectionService(db)
        result = service.validate_connection(connection_id, payload.token)
        
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/connections/{connection_id}/validate", "POST", duration_ms, 200)
        
        return result
        
    except NotFoundError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/connections/{connection_id}/validate", "POST", duration_ms, 404, str(e))
        return build_error_response(
            status.HTTP_404_NOT_FOUND,
            "NOT_FOUND",
            e.message,
            e.details
        )
    except (AuthenticationError, TokenExpiredError) as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/connections/{connection_id}/validate", "POST", duration_ms, 401, str(e))
        error_code = "AUTHENTICATION_FAILED"
        if isinstance(e, TokenExpiredError):
            error_code = "TOKEN_EXPIRED"
        return build_error_response(
            status.HTTP_401_UNAUTHORIZED,
            error_code,
            e.message,
            e.details
        )
    except ConnError as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(logger, f"/connections/{connection_id}/validate", "POST", duration_ms, 503, str(e))
        error_code = "CONNECTION_FAILED"
        if "timeout" in str(e.message).lower():
            error_code = "CONNECTION_TIMEOUT"
        return build_error_response(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code,
            e.message,
            e.details
        )
