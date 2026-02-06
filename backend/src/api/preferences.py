"""Preferences API router for user configuration management.

Endpoints:
- GET /preferences - Get all user preferences
- PUT /preferences - Update user preferences
- DELETE /preferences/{key} - Delete a specific preference
- POST /preferences/reset - Reset all preferences to defaults
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.src.db.base import get_db
from backend.src.services.preferences_service import PreferencesService
from backend.src.utils.logger import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/preferences", tags=["preferences"])


class PreferencesUpdate(BaseModel):
    """Request model for updating preferences."""
    pass  # Accept any JSON object (additionalProperties: true in OpenAPI)
    
    class Config:
        extra = "allow"  # Allow additional fields


@router.get("")
async def get_preferences(db: Session = Depends(get_db)):
    """Get all user preferences.
    
    Returns all user-set preferences merged with default values.
    
    Returns:
        Dictionary of all preferences (user-set + defaults)
    """
    logger.info("GET /preferences")
    
    preferences_service = PreferencesService(db)
    
    try:
        preferences = preferences_service.get_all_preferences()
        
        logger.info(f"Retrieved {len(preferences)} preferences")
        
        return preferences
        
    except Exception as e:
        logger.error(f"Error retrieving preferences: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to retrieve preferences", "details": str(e)}
        )


@router.put("")
async def update_preferences(
    preferences: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update user preferences.
    
    Updates specified preferences while preserving others.
    Validates values for predefined keys.
    
    Args:
        preferences: Dictionary of key-value pairs to update
        
    Returns:
        Updated preferences dictionary
    """
    logger.info(f"PUT /preferences - updating {len(preferences)} preferences")
    
    preferences_service = PreferencesService(db)
    
    try:
        updated_preferences = preferences_service.update_preferences(preferences)
        
        logger.info(f"Successfully updated preferences")
        
        return updated_preferences
        
    except ValueError as e:
        logger.warning(f"Validation error updating preferences: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={"error": "Invalid preference value", "details": str(e)}
        )
    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to update preferences", "details": str(e)}
        )


@router.get("/{key}")
async def get_preference(
    key: str = Path(..., description="Preference key"),
    db: Session = Depends(get_db)
):
    """Get a single preference value.
    
    Args:
        key: Preference key
        
    Returns:
        Preference value or default
    """
    logger.info(f"GET /preferences/{key}")
    
    preferences_service = PreferencesService(db)
    
    try:
        value = preferences_service.get_preference(key)
        
        if value is None:
            logger.warning(f"Preference not found: {key}")
            raise HTTPException(
                status_code=404,
                detail={"error": "Preference not found", "key": key}
            )
        
        return {"key": key, "value": value}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving preference {key}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to retrieve preference", "details": str(e)}
        )


@router.delete("/{key}")
async def delete_preference(
    key: str = Path(..., description="Preference key to delete"),
    db: Session = Depends(get_db)
):
    """Delete a specific preference.
    
    Resets the preference to its default value (if predefined).
    
    Args:
        key: Preference key to delete
        
    Returns:
        Success message with default value
    """
    logger.info(f"DELETE /preferences/{key}")
    
    preferences_service = PreferencesService(db)
    
    try:
        default_value = preferences_service.reset_preference(key)
        
        logger.info(f"Deleted preference: {key}")
        
        return {
            "message": "Preference deleted",
            "key": key,
            "default_value": default_value
        }
        
    except Exception as e:
        logger.error(f"Error deleting preference {key}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to delete preference", "details": str(e)}
        )


@router.post("/reset")
async def reset_all_preferences(db: Session = Depends(get_db)):
    """Reset all preferences to default values.
    
    Deletes all user-set preferences and returns defaults.
    
    Returns:
        Dictionary of default preferences
    """
    logger.warning("POST /preferences/reset - resetting all preferences")
    
    preferences_service = PreferencesService(db)
    
    try:
        defaults = preferences_service.reset_to_defaults()
        
        logger.info("All preferences reset to defaults")
        
        return {
            "message": "All preferences reset to defaults",
            "preferences": defaults
        }
        
    except Exception as e:
        logger.error(f"Error resetting preferences: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to reset preferences", "details": str(e)}
        )


@router.get("/keys/predefined")
async def get_predefined_keys(db: Session = Depends(get_db)):
    """Get list of predefined preference keys.
    
    Returns all recognized preference keys with their default values.
    
    Returns:
        Dictionary with predefined keys and default values
    """
    logger.info("GET /preferences/keys/predefined")
    
    preferences_service = PreferencesService(db)
    
    try:
        from backend.src.services.preferences_service import PREDEFINED_KEYS
        
        keys = preferences_service.get_predefined_keys()
        
        return {
            "predefined_keys": keys,
            "count": len(keys),
            "defaults": PREDEFINED_KEYS
        }
        
    except Exception as e:
        logger.error(f"Error retrieving predefined keys: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to retrieve predefined keys", "details": str(e)}
        )
