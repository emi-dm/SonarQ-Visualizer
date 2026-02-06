"""UserPreferences model for storing user configuration.

Implements key-value JSON storage for visualization preferences, themes, and settings.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from backend.src.db.base import Base
import json
from typing import Any


class UserPreferences(Base):
    """User preferences model for key-value configuration storage.
    
    Stores user preferences like theme, chart types, time ranges, and
    dashboard layout configuration. Values are stored as JSON for flexibility.
    """
    
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(255), nullable=False, unique=True, index=True)
    value = Column(Text, nullable=False)  # JSON-encoded value
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    def __repr__(self) -> str:
        """String representation of UserPreferences."""
        return f"<UserPreferences(key='{self.key}', updated_at='{self.updated_at}')>"
    
    def get_value(self) -> Any:
        """Deserialize and return the preference value.
        
        Returns:
            The deserialized JSON value (can be str, int, float, bool, list, dict, or None)
        """
        try:
            return json.loads(self.value)
        except json.JSONDecodeError:
            # Fallback: return as string if not valid JSON
            return self.value
    
    def set_value(self, value: Any) -> None:
        """Serialize and store the preference value.
        
        Args:
            value: Any JSON-serializable value (str, int, float, bool, list, dict, None)
        """
        self.value = json.dumps(value, ensure_ascii=False)
    
    @classmethod
    def create(cls, key: str, value: Any) -> "UserPreferences":
        """Factory method to create a new preference.
        
        Args:
            key: Preference key (e.g., 'theme', 'chart_type')
            value: Preference value (will be JSON-serialized)
            
        Returns:
            New UserPreferences instance with serialized value
        """
        pref = cls(key=key)
        pref.set_value(value)
        return pref
    
    def to_dict(self) -> dict:
        """Convert preference to dictionary representation.
        
        Returns:
            Dictionary with key, value, and updated_at
        """
        return {
            "id": self.id,
            "key": self.key,
            "value": self.get_value(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
