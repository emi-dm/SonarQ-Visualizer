"""Structured logging utility with JSON format.

This module provides a configured logger with JSON formatting for errors,
API calls, and other application events per FR-034 requirement.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string.
        
        Args:
            record: Log record to format
            
        Returns:
            str: JSON-formatted log entry
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
        }
        
        # Add context from extra fields
        if hasattr(record, "user_action"):
            log_data["context"] = {
                "user_action": record.user_action,
            }
            if hasattr(record, "endpoint"):
                log_data["context"]["endpoint"] = record.endpoint
            if hasattr(record, "duration_ms"):
                log_data["context"]["duration_ms"] = record.duration_ms
            if hasattr(record, "error_details"):
                log_data["context"]["error_details"] = record.error_details
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def get_logger(name: str) -> logging.Logger:
    """Get configured logger instance.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        
    Returns:
        logging.Logger: Configured logger with JSON formatting
    """
    logger = logging.getLogger(name)
    
    # Only add handler if not already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Console handler with JSON formatting
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        handler.setFormatter(JSONFormatter())
        
        logger.addHandler(handler)
        logger.propagate = False
    
    return logger


def log_api_call(
    logger: logging.Logger,
    endpoint: str,
    method: str,
    duration_ms: Optional[float] = None,
    status_code: Optional[int] = None,
    error: Optional[str] = None
) -> None:
    """Log API call with structured context.
    
    Args:
        logger: Logger instance
        endpoint: API endpoint path
        method: HTTP method
        duration_ms: Request duration in milliseconds
        status_code: HTTP status code
        error: Error message if request failed
    """
    extra: Dict[str, Any] = {
        "user_action": "api_call",
        "endpoint": f"{method} {endpoint}",
    }
    
    if duration_ms is not None:
        extra["duration_ms"] = duration_ms
    
    if error:
        extra["error_details"] = error
        logger.error(f"API call failed: {method} {endpoint}", extra=extra)
    else:
        logger.info(
            f"API call: {method} {endpoint} [{status_code}]",
            extra=extra
        )


def log_database_operation(
    logger: logging.Logger,
    operation: str,
    table: str,
    duration_ms: Optional[float] = None,
    error: Optional[str] = None
) -> None:
    """Log database operation with structured context.
    
    Args:
        logger: Logger instance
        operation: Database operation (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
        duration_ms: Operation duration in milliseconds
        error: Error message if operation failed
    """
    extra: Dict[str, Any] = {
        "user_action": "database_operation",
        "endpoint": f"{operation} {table}",
    }
    
    if duration_ms is not None:
        extra["duration_ms"] = duration_ms
    
    if error:
        extra["error_details"] = error
        logger.error(f"Database operation failed: {operation} {table}", extra=extra)
    else:
        logger.info(f"Database operation: {operation} {table}", extra=extra)
