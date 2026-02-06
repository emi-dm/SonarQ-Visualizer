"""Configuration management for environment variables and application settings.

This module provides centralized configuration using environment variables
and Pydantic settings for type safety.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = "SonarQube Report Visualizer"
    app_version: str = "0.1.0"
    debug: bool = True  # Development mode by default
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_path: str = "data/sonarq.db"
    
    # CORS
    cors_origins: list[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]
    
    # Security
    csp_header: str = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
    
    # SonarQube API
    sonarqube_timeout: int = 30  # seconds
    sonarqube_retry_max_attempts: int = 4
    sonarqube_retry_delays: list[int] = [1, 2, 4, 8]  # seconds
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_database_path() -> Path:
    """Get database file path.
    
    Returns:
        Path: Absolute path to database file
    """
    return Path(settings.database_path).resolve()


def get_database_url() -> str:
    """Get database connection URL.
    
    Returns:
        str: SQLite database URL
    """
    db_path = get_database_path()
    return f"sqlite:///{db_path}"


def is_development() -> bool:
    """Check if running in development mode.
    
    Returns:
        bool: True if debug mode is enabled
    """
    return settings.debug


def get_cors_origins() -> list[str]:
    """Get allowed CORS origins.
    
    Returns:
        list[str]: List of allowed origin URLs
    """
    if is_development():
        # In development, allow all localhost variants
        return [
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "http://localhost:3000",
            "http://127.0.0.1:3000"
        ]
    return settings.cors_origins


def get_csp_header() -> str:
    """Get Content Security Policy header value.
    
    Returns:
        str: CSP header value
    """
    return settings.csp_header
