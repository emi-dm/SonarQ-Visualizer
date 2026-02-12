"""Connection repository for database CRUD operations."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone

from backend.src.models.connection import Connection
from backend.src.utils.errors import ConflictError, NotFoundError, DatabaseError
from backend.src.utils.logger import get_logger

logger = get_logger(__name__)


class ConnectionRepository:
    """Repository for Connection model database operations."""
    
    def __init__(self, db: Session):
        """Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create(
        self,
        name: str,
        server_url: str,
        server_version: Optional[str] = None,
        organization: Optional[str] = None
    ) -> Connection:
        """Create a new connection.
        
        Args:
            name: Connection name
            server_url: SonarQube server URL
            server_version: Optional server version
            
        Returns:
            Connection: Created connection
            
        Raises:
            ConflictError: If connection name already exists
            DatabaseError: If database operation fails
        """
        try:
            connection = Connection(
                name=name,
                server_url=server_url,
                server_version=server_version,
                organization=organization
            )
            
            self.db.add(connection)
            self.db.commit()
            self.db.refresh(connection)
            
            logger.info(f"Created connection: {connection.name} (ID: {connection.id})")
            return connection
            
        except IntegrityError as e:
            self.db.rollback()
            if "UNIQUE constraint failed" in str(e):
                raise ConflictError(
                    f"Connection with name '{name}' already exists",
                    {"name": name}
                )
            raise DatabaseError(f"Failed to create connection: {e}")
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to create connection: {e}")
    
    def get_by_id(self, connection_id: int) -> Connection:
        """Get connection by ID.
        
        Args:
            connection_id: Connection ID
            
        Returns:
            Connection: Found connection
            
        Raises:
            NotFoundError: If connection not found
        """
        connection = self.db.query(Connection).filter(Connection.id == connection_id).first()
        if not connection:
            raise NotFoundError(
                f"Connection with ID {connection_id} not found",
                {"connection_id": connection_id}
            )
        return connection
    
    def get_all(self) -> List[Connection]:
        """Get all connections.
        
        Returns:
            List[Connection]: List of all connections
        """
        return self.db.query(Connection).order_by(Connection.created_at.desc()).all()
    
    def get_by_name(self, name: str) -> Optional[Connection]:
        """Get connection by name.
        
        Args:
            name: Connection name
            
        Returns:
            Optional[Connection]: Connection if found, None otherwise
        """
        return self.db.query(Connection).filter(Connection.name == name).first()
    
    def update(
        self,
        connection_id: int,
        name: Optional[str] = None,
        server_url: Optional[str] = None,
        server_version: Optional[str] = None,
        organization: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Connection:
        """Update connection fields.
        
        Args:
            connection_id: Connection ID to update
            name: Optional new name
            server_url: Optional new server URL
            server_version: Optional new server version
            is_active: Optional active status
            
        Returns:
            Connection: Updated connection
            
        Raises:
            NotFoundError: If connection not found
            ConflictError: If new name conflicts with existing connection
            DatabaseError: If update fails
        """
        try:
            connection = self.get_by_id(connection_id)
            
            if name is not None:
                connection.name = name
            if server_url is not None:
                connection.server_url = server_url
            if server_version is not None:
                connection.server_version = server_version
            if organization is not None:
                connection.organization = organization
            if is_active is not None:
                connection.is_active = is_active
            
            self.db.commit()
            self.db.refresh(connection)
            
            logger.info(f"Updated connection: {connection.name} (ID: {connection.id})")
            return connection
            
        except IntegrityError as e:
            self.db.rollback()
            if "UNIQUE constraint failed" in str(e):
                raise ConflictError(
                    f"Connection with name '{name}' already exists",
                    {"name": name}
                )
            raise DatabaseError(f"Failed to update connection: {e}")
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to update connection: {e}")
    
    def update_validation_timestamp(
        self,
        connection_id: int,
        server_version: Optional[str] = None
    ) -> Connection:
        """Update connection's last validation timestamp.
        
        Args:
            connection_id: Connection ID
            server_version: Optional detected server version
            
        Returns:
            Connection: Updated connection
        """
        connection = self.get_by_id(connection_id)
        connection.last_validated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        if server_version:
            connection.server_version = server_version
        
        self.db.commit()
        self.db.refresh(connection)
        
        return connection
    
    def delete(self, connection_id: int) -> None:
        """Delete connection.
        
        Args:
            connection_id: Connection ID to delete
            
        Raises:
            NotFoundError: If connection not found
            DatabaseError: If deletion fails
        """
        try:
            connection = self.get_by_id(connection_id)
            
            self.db.delete(connection)
            self.db.commit()
            
            logger.info(f"Deleted connection: {connection.name} (ID: {connection.id})")
            
        except Exception as e:
            self.db.rollback()
            raise DatabaseError(f"Failed to delete connection: {e}")
