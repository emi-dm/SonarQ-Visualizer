"""SQLAlchemy base configuration and session management.

This module provides SQLAlchemy ORM configuration for the SonarQube Visualizer,
including declarative base and async session factory.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.src.utils.config import get_database_url

_engine = None
_engine_url = None


def get_engine():
    """Get a SQLAlchemy engine configured for the current database path."""
    global _engine, _engine_url
    database_url = get_database_url()
    if _engine is None or database_url != _engine_url:
        if _engine is not None:
            _engine.dispose()
        _engine_url = database_url
        _engine = create_engine(
            database_url,
            connect_args={
                "check_same_thread": False  # Allow multi-threaded access
            },
            poolclass=StaticPool,  # Use static pool for SQLite
            echo=False  # Set to True for SQL query logging during development
        )
    return _engine


def get_sessionmaker():
    """Create a sessionmaker bound to the current engine."""
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=get_engine()
    )

# Declarative base for models
Base = declarative_base()


def get_db():
    """Dependency for FastAPI to get database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = get_sessionmaker()()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database by creating all tables defined in models.
    
    This should be called during application startup if using SQLAlchemy models
    instead of raw SQL schema.
    """
    # Import all models here to ensure they are registered with Base
    # This will be populated as models are created
    Base.metadata.create_all(bind=get_engine())
