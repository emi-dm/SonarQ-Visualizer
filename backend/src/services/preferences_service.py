"""Preferences service for user configuration management.

Handles user preferences with predefined keys validation and JSON value storage.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from backend.src.db.repositories.preferences_repository import PreferencesRepository
from backend.src.utils.logger import get_logger


logger = get_logger(__name__)


# Predefined preference keys with default values
PREDEFINED_KEYS = {
    # Theme and appearance
    "theme": "light",  # light, dark
    "color_scheme": "default",  # default, colorblind-friendly
    
    # Chart preferences
    "chart_type": "line",  # line, bar, area
    "show_trends": True,
    "show_severity_breakdown": True,
    
    # Time range defaults
    "time_range": "30d",  # 7d, 30d, 90d, 365d, all
    "default_branch": "main",
    
    # Dashboard layout
    "dashboard_columns": 3,  # 1, 2, 3
    "show_aggregates": True,
    "show_project_cards": True,
    
    # Project list preferences
    "page_size": 20,  # 10, 20, 50, 100
    "sort_by": "name",  # name, bugs_count, coverage_pct, last_analysis_date
    "sort_order": "asc",  # asc, desc
    
    # Filters
    "filter_quality_gate": None,  # None, OK, WARN, ERROR
    "filter_connection_id": None,
    "selected_projects": [],  # List of project IDs
    
    # Notifications and alerts
    "staleness_threshold_hours": 24,
    "show_staleness_warnings": True,
}


class PreferencesService:
    """Service for managing user preferences with validation."""
    
    def __init__(self, db: Session):
        """Initialize preferences service with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.repository = PreferencesRepository(db)
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """Get all user preferences merged with defaults.
        
        Returns:
            Dictionary with all preferences (user-set + defaults)
        """
        logger.info("Retrieving all preferences")
        
        # Get user preferences from database
        user_prefs = self.repository.get_all()
        
        # Merge with defaults (user preferences take precedence)
        all_prefs = {**PREDEFINED_KEYS, **user_prefs}
        
        logger.debug(f"Retrieved {len(user_prefs)} user preferences, "
                    f"{len(all_prefs)} total with defaults")
        
        return all_prefs
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a single preference value.
        
        Args:
            key: Preference key
            default: Default value if preference not found
            
        Returns:
            Preference value or default
        """
        value = self.repository.get(key)
        
        if value is not None:
            return value
        
        # Check predefined defaults
        if key in PREDEFINED_KEYS:
            return PREDEFINED_KEYS[key]
        
        return default
    
    def update_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update multiple preferences at once.
        
        Args:
            preferences: Dictionary of key-value pairs to update
            
        Returns:
            Dictionary of all preferences after update
        """
        logger.info(f"Updating {len(preferences)} preferences")
        
        # Validate and update each preference
        for key, value in preferences.items():
            self._validate_preference(key, value)
            self.repository.set(key, value)
        
        logger.info(f"Successfully updated {len(preferences)} preferences")
        
        return self.get_all_preferences()
    
    def set_preference(self, key: str, value: Any) -> Any:
        """Set a single preference value.
        
        Args:
            key: Preference key
            value: Preference value
            
        Returns:
            The set value
        """
        logger.info(f"Setting preference: {key}")
        
        self._validate_preference(key, value)
        self.repository.set(key, value)
        
        return value
    
    def reset_to_defaults(self) -> Dict[str, Any]:
        """Reset all preferences to default values.
        
        Returns:
            Dictionary of default preferences
        """
        logger.warning("Resetting all preferences to defaults")
        
        self.repository.clear_all()
        
        return PREDEFINED_KEYS.copy()
    
    def reset_preference(self, key: str) -> Any:
        """Reset a single preference to its default value.
        
        Args:
            key: Preference key to reset
            
        Returns:
            The default value for the key
        """
        logger.info(f"Resetting preference to default: {key}")
        
        self.repository.delete(key)
        
        if key in PREDEFINED_KEYS:
            return PREDEFINED_KEYS[key]
        
        return None
    
    def get_predefined_keys(self) -> List[str]:
        """Get list of predefined preference keys.
        
        Returns:
            List of predefined key names
        """
        return list(PREDEFINED_KEYS.keys())
    
    def is_predefined_key(self, key: str) -> bool:
        """Check if a key is predefined.
        
        Args:
            key: Preference key to check
            
        Returns:
            True if predefined, False otherwise
        """
        return key in PREDEFINED_KEYS
    
    def _validate_preference(self, key: str, value: Any) -> None:
        """Validate preference key and value.
        
        Args:
            key: Preference key
            value: Preference value
            
        Raises:
            ValueError: If validation fails
        """
        # Validate specific predefined keys
        if key == "theme" and value not in ["light", "dark"]:
            raise ValueError(f"Invalid theme value: {value}. Must be 'light' or 'dark'")
        
        if key == "chart_type" and value not in ["line", "bar", "area"]:
            raise ValueError(
                f"Invalid chart_type value: {value}. Must be 'line', 'bar', or 'area'"
            )
        
        if key == "time_range" and value not in ["7d", "30d", "90d", "365d", "all"]:
            raise ValueError(
                f"Invalid time_range value: {value}. "
                "Must be '7d', '30d', '90d', '365d', or 'all'"
            )
        
        if key == "page_size" and not isinstance(value, int):
            raise ValueError(f"page_size must be an integer, got {type(value)}")
        
        if key == "page_size" and value not in [10, 20, 50, 100]:
            raise ValueError(
                f"Invalid page_size value: {value}. Must be 10, 20, 50, or 100"
            )
        
        if key == "dashboard_columns" and value not in [1, 2, 3]:
            raise ValueError(
                f"Invalid dashboard_columns value: {value}. Must be 1, 2, or 3"
            )
        
        if key == "sort_order" and value not in ["asc", "desc"]:
            raise ValueError(
                f"Invalid sort_order value: {value}. Must be 'asc' or 'desc'"
            )
        
        if key == "filter_quality_gate" and value not in [None, "OK", "WARN", "ERROR"]:
            raise ValueError(
                f"Invalid filter_quality_gate value: {value}. "
                "Must be None, 'OK', 'WARN', or 'ERROR'"
            )
        
        # Custom keys are allowed (no validation) for flexibility
        if not self.is_predefined_key(key):
            logger.debug(f"Custom preference key: {key}")
