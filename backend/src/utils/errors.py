"""Custom exception classes for error handling.

This module defines application-specific exceptions with clear error messages
per FR-009 requirement.
"""

from typing import Any, Dict, Optional


class SonarQBaseException(Exception):
    """Base exception for SonarQube Visualizer application."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize exception with message and optional details.
        
        Args:
            message: Human-readable error message
            details: Additional error context for logging/debugging
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(SonarQBaseException):
    """Database operation failed."""
    pass


class ValidationError(SonarQBaseException):
    """Input validation failed."""
    pass


class ConnectionError(SonarQBaseException):
    """SonarQube server connection failed."""
    pass


class AuthenticationError(SonarQBaseException):
    """Authentication with SonarQube server failed."""
    pass


class TokenExpiredError(AuthenticationError):
    """SonarQube authentication token has expired."""
    pass


class RateLimitError(SonarQBaseException):
    """SonarQube API rate limit exceeded."""
    
    def __init__(
        self,
        message: str,
        retry_after_seconds: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize rate limit error.
        
        Args:
            message: Human-readable error message
            retry_after_seconds: Seconds to wait before retrying
            details: Additional error context
        """
        super().__init__(message, details)
        self.retry_after_seconds = retry_after_seconds


class InvalidAPIResponseError(SonarQBaseException):
    """SonarQube API returned invalid or malformed response."""
    pass


class PartialSyncError(SonarQBaseException):
    """Partial synchronization failure for multiple projects."""
    
    def __init__(
        self,
        message: str,
        failed_projects: list[str],
        total_projects: int,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize partial sync error.
        
        Args:
            message: Human-readable error message
            failed_projects: List of project keys that failed
            total_projects: Total number of projects attempted
            details: Additional error context
        """
        super().__init__(message, details)
        self.failed_projects = failed_projects
        self.total_projects = total_projects
        self.failure_rate = len(failed_projects) / total_projects if total_projects > 0 else 0


class NotFoundError(SonarQBaseException):
    """Requested resource not found."""
    pass


class ConflictError(SonarQBaseException):
    """Resource conflict detected (e.g., duplicate connection name)."""
    pass
