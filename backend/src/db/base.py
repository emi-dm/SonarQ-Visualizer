"""SQLAlchemy base configuration and session management.

This module provides SQLAlchemy ORM configuration for the SonarQube Visualizer,
including declarative base and async session factory.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from pathlib import Path

# Database URL
DB_PATH = Path("data/sonarq.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create async engine with SQLite-specific settings
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False  # Allow multi-threaded access
    },
    poolclass=StaticPool,  # Use static pool for SQLite
    echo=False  # Set to True for SQL query logging during development
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Declarative base for models
Base = declarative_base()


def get_db():
    """Dependency for FastAPI to get database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
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
    Base.metadata.create_all(bind=engine)
