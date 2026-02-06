"""Database initialization module.

This module handles SQLite database connection setup, WAL mode configuration,
and schema initialization from schema.sql file.
"""

import sqlite3
from pathlib import Path
from typing import Optional

# Database file path
DB_PATH = Path("data/sonarq.db")


def get_db_connection() -> sqlite3.Connection:
    """Create and configure a SQLite database connection.
    
    Returns:
        sqlite3.Connection: Configured database connection with WAL mode and foreign keys enabled
    """
    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.Connection(str(DB_PATH))
    
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
    if db_path:
        global DB_PATH
        DB_PATH = Path(db_path)
    
    # Read schema from file
    schema_path = Path(__file__).parent / "schema.sql"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    schema_sql = schema_path.read_text()
    
    # Create connection and execute schema
    conn = get_db_connection()
    try:
        conn.executescript(schema_sql)
        conn.commit()
        print(f"✓ Database initialized at {DB_PATH}")
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
    if not DB_PATH.exists():
        return False
    
    try:
        conn = get_db_connection()
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
