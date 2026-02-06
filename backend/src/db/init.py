"""Database initialization module.

This module handles SQLite database connection setup, WAL mode configuration,
and schema initialization from schema.sql file.
"""

import sqlite3
from pathlib import Path
from typing import Optional

from backend.src.utils.config import get_database_path


def _resolve_db_path(db_path: Optional[str] = None) -> Path:
    """Resolve database path from optional override or settings.
    
    Args:
        db_path: Optional database path override
    
    Returns:
        Path: Resolved database path
    """
    if db_path:
        return Path(db_path).resolve()
    return get_database_path()


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create and configure a SQLite database connection.
    
    Returns:
        sqlite3.Connection: Configured database connection with WAL mode and foreign keys enabled
    """
    db_file = _resolve_db_path(db_path)

    # Ensure data directory exists
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.Connection(str(db_file))
    
    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL;")
    
    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys=ON;")
    
    # Set row factory for dict-like row access
    conn.row_factory = sqlite3.Row
    
    return conn


def init_database(db_path: Optional[str] = None) -> None:
    """Initialize database with schema from schema.sql.
    
    Args:
        db_path: Optional custom database path (defaults to data/sonarq.db)
    
    Raises:
        FileNotFoundError: If schema.sql file is not found
        sqlite3.Error: If database initialization fails
    """
    db_file = _resolve_db_path(db_path)
    
    # Read schema from file
    schema_path = Path(__file__).parent / "schema.sql"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    schema_sql = schema_path.read_text()
    
    # Create connection and execute schema
    conn = get_db_connection(str(db_file))
    try:
        conn.executescript(schema_sql)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(connections)")
        columns = [row[1] for row in cursor.fetchall()]
        if "organization" not in columns:
            cursor.execute("ALTER TABLE connections ADD COLUMN organization TEXT")
        conn.commit()
        print(f"✓ Database initialized at {db_file}")
    except sqlite3.Error as e:
        conn.rollback()
        raise sqlite3.Error(f"Failed to initialize database: {e}") from e
    finally:
        conn.close()


def check_database_exists() -> bool:
    """Check if database file exists and is initialized.
    
    Returns:
        bool: True if database exists, False otherwise
    """
    db_file = get_database_path()
    if not db_file.exists():
        return False
    
    try:
        conn = get_db_connection(str(db_file))
        cursor = conn.cursor()
        # Check if connections table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='connections'"
        )
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except sqlite3.Error:
        return False
