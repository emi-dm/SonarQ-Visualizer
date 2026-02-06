"""Application entrypoint with CLI commands.

This module provides CLI commands for database initialization and other
administrative tasks.
"""

import sys
import argparse
from pathlib import Path

# Add backend and backend/src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from backend.src.db.init import init_database, check_database_exists
from backend.src.utils.config import settings
from backend.src.utils.logger import get_logger

logger = get_logger(__name__)


def init_db_command():
    """Initialize database with schema."""
    try:
        if check_database_exists():
            response = input("Database already exists. Reinitialize? (y/N): ")
            if response.lower() != 'y':
                print("Cancelled.")
                return
        
        init_database(settings.database_path)
        print(f"✓ Database initialized at {settings.database_path}")
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="SonarQube Report Visualizer CLI"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # init-db command
    subparsers.add_parser(
        "init-db",
        help="Initialize database with schema"
    )
    
    args = parser.parse_args()
    
    if args.command == "init-db":
        init_db_command()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
