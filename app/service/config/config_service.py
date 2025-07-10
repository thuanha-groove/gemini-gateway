"""
Configuration service module
"""

import datetime
import json
from typing import Any, Dict, List

from dotenv import find_dotenv, load_dotenv
from fastapi import HTTPException
from sqlalchemy import insert, update

from app.config.config import Settings as ConfigSettings
from app.config.config import settings
from app.database.connection import database
from app.database.models import Settings
from app.database.services import get_all_settings
from app.log.logger import get_config_routes_logger
from app.service.key.key_manager import (
    get_key_manager_instance,
    reset_key_manager_instance,
)
from app.service.model.model_service import ModelService

logger = get_config_routes_logger()


class ConfigService:
    """Configuration service class for managing application settings"""

    @staticmethod
    async def get_config() -> Dict[str, Any]:
        return settings.model_dump()

    @staticmethod
    async def update_config(config_data: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in config_data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
                logger.debug(f"Updated setting in memory: {key}")

        # Get existing settings
        existing_settings_raw: List[Dict[str, Any]] = await get_all_settings()
        existing_settings_map: Dict[str, Dict[str, Any]] = {
            s["key"]: s for s in existing_settings_raw
        }
        existing_keys = set(existing_settings_map.keys())

        settings_to_update: List[Dict[str, Any]] = []
        settings_to_insert: List[Dict[str, Any]] = []
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

        # Prepare data for update or insertion
        for key, value in config_data.items():
            # Handle different value types
            if isinstance(value, list):
                db_value = json.dumps(value)
            elif isinstance(value, dict):
                db_value = json.dumps(value)
            elif isinstance(value, bool):
                db_value = str(value).lower()
            else:
                db_value = str(value)

            # Only update if the value has changed
            if key in existing_keys and existing_settings_map[key]["value"] == db_value:
                continue

            description = f"{key} configuration item"

            data = {
                "key": key,
                "value": db_value,
                "description": description,
                "updated_at": now,
            }

            if key in existing_keys:
                data["description"] = existing_settings_map[key].get(
                    "description", description
                )
                settings_to_update.append(data)
            else:
                data["created_at"] = now
                settings_to_insert.append(data)

        # Execute bulk insert and update in a transaction
        if settings_to_insert or settings_to_update:
            try:
                async with database.transaction():
                    if settings_to_insert:
                        query_insert = insert(Settings).values(settings_to_insert)
                        await database.execute(query=query_insert)
                        logger.info(
                            f"Bulk inserted {len(settings_to_insert)} settings."
                        )

                    if settings_to_update:
                        for setting_data in settings_to_update:
                            query_update = (
                                update(Settings)
                                .where(Settings.key == setting_data["key"])
                                .values(
                                    value=setting_data["value"],
                                    description=setting_data["description"],
                                    updated_at=setting_data["updated_at"],
                                )
                            )
                            await database.execute(query=query_update)
                        logger.info(f"Updated {len(settings_to_update)} settings.")
            except Exception as e:
                logger.error(f"Failed to bulk update/insert settings: {str(e)}")
                raise

        # Reset and re-initialize KeyManager
        try:
            await reset_key_manager_instance()
            await get_key_manager_instance(settings.API_KEYS, settings.VERTEX_API_KEYS)
            logger.info("KeyManager instance re-initialized with updated settings.")
        except Exception as e:
            logger.error(f"Failed to re-initialize KeyManager: {str(e)}")

        return await ConfigService.get_config()

    @staticmethod
    async def delete_key(key_to_delete: str) -> Dict[str, Any]:
        """Delete a single API key"""
        # Ensure settings.API_KEYS is a list
        if not isinstance(settings.API_KEYS, list):
            settings.API_KEYS = []

        original_keys_count = len(settings.API_KEYS)
        # Create a new list that does not contain the key to be deleted
        updated_api_keys = [k for k in settings.API_KEYS if k != key_to_delete]

        if len(updated_api_keys) < original_keys_count:
            # Key found and removed from the list
            settings.API_KEYS = updated_api_keys  # First, update the settings in memory
            # Use update_config to persist the changes, which handles both the database and KeyManager
            await ConfigService.update_config({"API_KEYS": settings.API_KEYS})
            logger.info(f"Key '{key_to_delete}' has been successfully deleted.")
            return {"success": True, "message": f"Key '{key_to_delete}' has been successfully deleted."}
        else:
            # Key not found
            logger.warning(f"Attempted to delete key '{key_to_delete}', but it was not found.")
            return {"success": False, "message": f"Key '{key_to_delete}' not found."}

    @staticmethod
    async def delete_selected_keys(keys_to_delete: List[str]) -> Dict[str, Any]:
        """Bulk delete selected API keys"""
        if not isinstance(settings.API_KEYS, list):
            settings.API_KEYS = []

        deleted_count = 0
        not_found_keys: List[str] = []

        current_api_keys = list(settings.API_KEYS)
        keys_actually_removed: List[str] = []

        for key_to_del in keys_to_delete:
            if key_to_del in current_api_keys:
                current_api_keys.remove(key_to_del)
                keys_actually_removed.append(key_to_del)
                deleted_count += 1
            else:
                not_found_keys.append(key_to_del)

        if deleted_count > 0:
            settings.API_KEYS = current_api_keys
            await ConfigService.update_config({"API_KEYS": settings.API_KEYS})
            logger.info(
                f"Successfully deleted {deleted_count} keys. Keys: {keys_actually_removed}"
            )
            message = f"Successfully deleted {deleted_count} keys."
            if not_found_keys:
                message += f" {len(not_found_keys)} keys not found: {not_found_keys}."
            return {
                "success": True,
                "message": message,
                "deleted_count": deleted_count,
                "not_found_keys": not_found_keys,
            }
        else:
            message = "No keys were deleted."
            if not_found_keys:
                message = f"All {len(not_found_keys)} specified keys were not found: {not_found_keys}."
            elif not keys_to_delete:
                message = "No keys specified for deletion."
            logger.warning(message)
            return {
                "success": False,
                "message": message,
                "deleted_count": 0,
                "not_found_keys": not_found_keys,
            }

    @staticmethod
    async def reset_config() -> Dict[str, Any]:
        """
        Reset configuration: prioritize loading from system environment variables, then from .env file,
        update the in-memory settings object, and refresh the KeyManager.

        Returns:
            Dict[str, Any]: The reset configuration dictionary
        """
        # 1. Reload the configuration object, which should handle the priority of environment variables and .env
        _reload_settings()
        logger.info(
            "Settings object reloaded, prioritizing system environment variables then .env file."
        )

        # 2. Reset and re-initialize KeyManager
        try:
            await reset_key_manager_instance()
            # Ensure to use the updated API_KEYS from settings
            await get_key_manager_instance(settings.API_KEYS)
            logger.info("KeyManager instance re-initialized with reloaded settings.")
        except Exception as e:
            logger.error(f"Failed to re-initialize KeyManager during reset: {str(e)}")
            # Decide whether to raise an exception or continue as needed
            # Here, we choose to log the error and continue

        # 3. Return the updated configuration
        return await ConfigService.get_config()

    @staticmethod
    async def fetch_ui_models() -> List[Dict[str, Any]]:
        """Get the list of models for UI display"""
        try:
            key_manager = await get_key_manager_instance()
            model_service = ModelService()

            api_key = await key_manager.get_first_valid_key()
            if not api_key:
                logger.error("No valid API keys available to fetch model list for UI.")
                raise HTTPException(
                    status_code=500,
                    detail="No valid API keys available to fetch model list.",
                )

            models = await model_service.get_gemini_openai_models(api_key)
            return models
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(
                f"Failed to fetch models for UI in ConfigService: {e}", exc_info=True
            )
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch models for UI: {str(e)}"
            )


# Function to reload configuration
def _reload_settings():
    """Reload environment variables and update configuration"""
    # Explicitly load .env file, overriding existing environment variables
    load_dotenv(find_dotenv(), override=True)
    # Update attributes of the existing settings object instead of creating a new instance
    for key, value in ConfigSettings().model_dump().items():
        setattr(settings, key, value)
