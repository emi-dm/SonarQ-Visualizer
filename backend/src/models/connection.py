"""Connection SQLAlchemy model.

Represents an authenticated connection to a SonarQube server.
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, UniqueConstraint, Index
from sqlalchemy.orm import validates
from datetime import datetime
from urllib.parse import urlparse

from backend.src.db.base import Base


class Connection(Base):
    """Connection model for SonarQube server connections."""
    
    __tablename__ = "connections"
    __table_args__ = (
        UniqueConstraint("name", name="uq_connections_name"),
        Index("ix_connections_server_url", "server_url"),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    server_url = Column(String(512), nullable=False)
    organization = Column(String(255), nullable=True)
    server_version = Column(String(50), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    last_validated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, **kwargs):
        """Initialize connection with sensible defaults."""
        if "is_active" not in kwargs or kwargs["is_active"] is None:
            kwargs["is_active"] = True
        super().__init__(**kwargs)
    
    @validates('name')
    def validate_name(self, key: str, name: str) -> str:
        """Validate connection name.
        
        Args:
            key: Field name
            name: Connection name to validate
            
        Returns:
            str: Validated and trimmed name
            
        Raises:
            ValueError: If name is empty after trimming
        """
        trimmed = name.strip() if name else ""
        if not trimmed:
            raise ValueError("Connection name cannot be empty")
        if len(trimmed) > 255:
            raise ValueError("Connection name cannot exceed 255 characters")
        return trimmed
    
    @validates('server_url')
    def validate_server_url(self, key: str, server_url: str) -> str:
        """Validate server URL.
        
        Args:
            key: Field name
            server_url: URL to validate
            
        Returns:
            str: Validated URL
            
        Raises:
            ValueError: If URL is invalid
        """
        if not server_url:
            raise ValueError("Server URL cannot be empty")
        
        parsed = urlparse(server_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Invalid URL format. Must be a valid HTTP or HTTPS URL")
        if any(char.isspace() for char in server_url):
            raise ValueError("Invalid URL format. URL must not contain spaces")
        
        # Remove trailing slash
        return server_url.rstrip('/')

    @validates('organization')
    def validate_organization(self, key: str, organization: str) -> str:
        if organization is None:
            return organization
        trimmed = organization.strip()
        if not trimmed:
            raise ValueError("Organization cannot be empty")
        return trimmed
    
    def __repr__(self) -> str:
        """String representation of Connection."""
        return f"<Connection(id={self.id}, name='{self.name}', server_url='{self.server_url}')>"
