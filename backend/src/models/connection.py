"""Connection SQLAlchemy model.

Represents an authenticated connection to a SonarQube server.
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import validates
from datetime import datetime
from backend.src.db.base import Base
import re


class Connection(Base):
    """Connection model for SonarQube server connections."""
    
    __tablename__ = "connections"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    server_url = Column(String(512), nullable=False)
    server_version = Column(String(50), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    last_validated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
        
        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        
        if not url_pattern.match(server_url):
            raise ValueError("Invalid URL format. Must be a valid HTTP or HTTPS URL")
        
        # Remove trailing slash
        return server_url.rstrip('/')
    
    def __repr__(self) -> str:
        """String representation of Connection."""
        return f"<Connection(id={self.id}, name='{self.name}', server_url='{self.server_url}')>"
