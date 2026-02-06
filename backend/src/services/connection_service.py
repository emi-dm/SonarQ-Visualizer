"""Connection service for business logic."""

from typing import List, Optional
from sqlalchemy.orm import Session

from backend.src.db.repositories.connection_repository import ConnectionRepository
from backend.src.models.connection import Connection
from backend.src.services.sonarqube_client import SonarQubeClient
from backend.src.utils.errors import ConnectionError, AuthenticationError
from backend.src.utils.logger import get_logger

logger = get_logger(__name__)


class ConnectionService:
    """Service for connection management business logic."""
    
    def __init__(self, db: Session):
        """Initialize service with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.repository = ConnectionRepository(db)
    
    def create_connection(
        self,
        name: str,
        server_url: str,
        token: str,
        validate: bool = True
    ) -> tuple[Connection, Optional[dict]]:
        """Create a new connection with optional validation.
        
        Args:
            name: Connection name
            server_url: SonarQube server URL
            token: Authentication token
            validate: Whether to validate connection before saving
            
        Returns:
            tuple: (Created connection, Optional validation result)
            
        Raises:
            ConflictError: If connection name already exists
            ConnectionError: If validation is requested and fails
            AuthenticationError: If token is invalid
        """
        validation_result = None
        server_version = None
        
        # Validate connection if requested
        if validate:
            logger.info(f"Validating connection to {server_url}")
            client = SonarQubeClient(server_url, token)
            try:
                validation_result = client.validate_connection()
                server_version = validation_result.get('version')
                logger.info(f"Connection validated successfully. Version: {server_version}")
            finally:
                client.close()
        
        # Create connection in database
        connection = self.repository.create(
            name=name,
            server_url=server_url,
            server_version=server_version
        )
        
        # Update validation timestamp if validated
        if validate and validation_result:
            connection = self.repository.update_validation_timestamp(
                connection.id,
                server_version=server_version
            )
        
        return connection, validation_result
    
    def validate_connection(self, connection_id: int, token: str) -> dict:
        """Validate an existing connection.
        
        Args:
            connection_id: Connection ID to validate
            token: Authentication token
            
        Returns:
            dict: Validation result with status and version
            
        Raises:
            NotFoundError: If connection not found
            ConnectionError: If validation fails
            AuthenticationError: If token is invalid
        """
        connection = self.repository.get_by_id(connection_id)
        
        logger.info(f"Validating connection: {connection.name} (ID: {connection_id})")
        
        client = SonarQubeClient(connection.server_url, token)
        try:
            validation_result = client.validate_connection()
            
            # Update connection with validation info
            server_version = validation_result.get('version')
            self.repository.update_validation_timestamp(
                connection_id,
                server_version=server_version
            )
            
            logger.info(f"Connection validated: {connection.name}. Version: {server_version}")
            
            return {
                'status': 'valid',
                'server_version': server_version,
                'server_status': validation_result.get('status')
            }
        finally:
            client.close()
    
    def get_connection(self, connection_id: int) -> Connection:
        """Get connection by ID.
        
        Args:
            connection_id: Connection ID
            
        Returns:
            Connection: Found connection
            
        Raises:
            NotFoundError: If connection not found
        """
        return self.repository.get_by_id(connection_id)
    
    def list_connections(self) -> List[Connection]:
        """List all connections.
        
        Returns:
            List[Connection]: All connections ordered by creation date (newest first)
        """
        return self.repository.get_all()
    
    def update_connection(
        self,
        connection_id: int,
        name: Optional[str] = None,
        server_url: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Connection:
        """Update connection details.
        
        Args:
            connection_id: Connection ID to update
            name: Optional new name
            server_url: Optional new server URL
            is_active: Optional active status
            
        Returns:
            Connection: Updated connection
            
        Raises:
            NotFoundError: If connection not found
            ConflictError: If new name conflicts with existing connection
        """
        return self.repository.update(
            connection_id=connection_id,
            name=name,
            server_url=server_url,
            is_active=is_active
        )
    
    def delete_connection(self, connection_id: int) -> None:
        """Delete a connection.
        
        Args:
            connection_id: Connection ID to delete
            
        Raises:
            NotFoundError: If connection not found
        """
        connection = self.repository.get_by_id(connection_id)
        logger.info(f"Deleting connection: {connection.name} (ID: {connection_id})")
        self.repository.delete(connection_id)
