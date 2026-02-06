"""FastAPI application with CORS middleware, CSP headers, and router registration.

This is the main application module that configures FastAPI with security headers,
CORS support, and registers all API routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from pathlib import Path

from backend.src.utils.config import settings, get_cors_origins, get_csp_header
from backend.src.utils.logger import get_logger
from backend.src.api.health import router as health_router
from backend.src.api.connections import router as connections_router
from backend.src.api.projects import router as projects_router, projects_router as direct_projects_router
from backend.src.api.metrics import router as metrics_router
from backend.src.api.dashboard import router as dashboard_router
from backend.src.api.preferences import router as preferences_router

logger = get_logger(__name__)


class CSPMiddleware(BaseHTTPMiddleware):
    """Middleware to add Content Security Policy headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        """Add CSP header to response.
        
        Args:
            request: Incoming request
            call_next: Next middleware or route handler
            
        Returns:
            Response: Response with CSP header
        """
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = get_csp_header()
        return response


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="REST API for SonarQube quality metrics visualization",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add CSP middleware
app.add_middleware(CSPMiddleware)

# Register API routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(connections_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")  # /connections/{id}/projects
app.include_router(direct_projects_router, prefix="/api/v1")  # /projects/{id}
app.include_router(metrics_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(preferences_router, prefix="/api/v1")

# Mount static files for frontend
frontend_path = Path(__file__).parent.parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


@app.get("/")
async def root():
    """Serve frontend index.html at root path.
    
    Returns:
        FileResponse: Frontend HTML file
    """
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "SonarQube Report Visualizer API", "version": settings.app_version}


@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"CORS origins: {get_cors_origins()}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info(f"Shutting down {settings.app_name}")
