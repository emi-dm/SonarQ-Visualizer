"""Preferences repository for database operations.

Handles CRUD operations for UserPreferences with key-value storage.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.src.models.user_preferences import UserPreferences
from backend.src.utils.logger import get_logger


logger = get_logger(__name__)


class PreferencesRepository:
    """Repository for user preferences database operations."""
    
    def __init__(self, db: Session):
        """Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get(self, key: str) -> Optional[Any]:
        """Get a preference value by key.
        
        Args:
            key: Preference key (e.g., 'theme', 'chart_type')
            
        Returns:
            Deserialized preference value, or None if not found
        """
        pref = self.db.query(UserPreferences).filter(UserPreferences.key == key).first()
        
        if pref:
            logger.debug(f"Retrieved preference: {key}")
            return pref.get_value()
        
        return None
    
    def get_all(self) -> Dict[str, Any]:
        """Get all preferences as a dictionary.
        
        Returns:
            Dictionary mapping preference keys to their values
        """
        preferences = self.db.query(UserPreferences).all()
        
        result = {}
        for pref in preferences:
            result[pref.key] = pref.get_value()
        
        logger.debug(f"Retrieved {len(result)} preferences")
        return result
    
    def set(self, key: str, value: Any) -> UserPreferences:
        """Set a preference value (create or update).
        
        Args:
            key: Preference key
            value: Preference value (any JSON-serializable type)
            
        Returns:
            The created or updated UserPreferences instance
        """
        pref = self.db.query(UserPreferences).filter(UserPreferences.key == key).first()
        
        if pref:
            # Update existing preference
            pref.set_value(value)
            logger.info(f"Updated preference: {key}")
        else:
            # Create new preference
            pref = UserPreferences.create(key, value)
            self.db.add(pref)
            logger.info(f"Created preference: {key}")
        
        self.db.commit()
        self.db.refresh(pref)
        
        return pref
    
    def set_many(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Set multiple preferences at once.
        
        Args:
            preferences: Dictionary of key-value pairs to set
            
        Returns:
            Dictionary of all preferences after update
        """
        for key, value in preferences.items():
            self.set(key, value)
        
        logger.info(f"Updated {len(preferences)} preferences")
        return self.get_all()
    
    def delete(self, key: str) -> bool:
        """Delete a preference by key.
        
        Args:
            key: Preference key to delete
            
        Returns:
            True if deleted, False if not found
        """
        pref = self.db.query(UserPreferences).filter(UserPreferences.key == key).first()
        
        if pref:
            self.db.delete(pref)
            self.db.commit()
            logger.info(f"Deleted preference: {key}")
            return True
        
        return False
    
    def exists(self, key: str) -> bool:
        """Check if a preference key exists.
        
        Args:
            key: Preference key to check
            
        Returns:
            True if key exists, False otherwise
        """
        count = self.db.query(UserPreferences).filter(UserPreferences.key == key).count()
        return count > 0
    
    def clear_all(self) -> int:
        """Delete all preferences.
        
        Returns:
            Number of preferences deleted
        """
        count = self.db.query(UserPreferences).count()
        self.db.query(UserPreferences).delete()
        self.db.commit()
        
        logger.warning(f"Cleared all preferences ({count} items)")
        return count
