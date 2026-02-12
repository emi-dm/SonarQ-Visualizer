"""Health check API endpoint."""

from fastapi import APIRouter
from datetime import datetime, timezone
from backend.src.utils.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check() -> dict[str, str]:
    """Health check endpoint.
    
    Returns API health status and version information.
    
    Returns:
        dict: Health status, version, and timestamp
    """
    return {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }
