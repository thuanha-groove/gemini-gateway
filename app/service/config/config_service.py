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
    async def _prepare_config_data(
        config_data: Dict[str, Any],
        existing_settings_map: Dict[str, Dict[str, Any]],
    ) -> (List[Dict[str, Any]], List[Dict[str, Any]]):
        settings_to_update: List[Dict[str, Any]] = []
        settings_to_insert: List[Dict[str, Any]] = []
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
        existing_keys = set(existing_settings_map.keys())

        for key, value in config_data.items():
            if isinstance(value, list) or isinstance(value, dict):
                db_value = json.dumps(value)
            elif isinstance(value, bool):
                db_value = str(value).lower()
            else:
                db_value = str(value)

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

        return settings_to_insert, settings_to_update

    @staticmethod
    async def _execute_db_operations(
        settings_to_insert: List[Dict[str, Any]],
        settings_to_update: List[Dict[str, Any]],
    ):
        if not settings_to_insert and not settings_to_update:
            return

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
            raise HTTPException(
                status_code=500, detail=f"Failed to update settings in database: {e}"
            )

    @staticmethod
    async def update_config(config_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            for key, value in config_data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
                    logger.debug(f"Updated setting in memory: {key}")

            existing_settings_raw: List[Dict[str, Any]] = await get_all_settings()
            existing_settings_map: Dict[str, Dict[str, Any]] = {
                s["key"]: s for s in existing_settings_raw
            }

            settings_to_insert, settings_to_update = await ConfigService._prepare_config_data(
                config_data, existing_settings_map
            )

            await ConfigService._execute_db_operations(
                settings_to_insert, settings_to_update
            )

            await reset_key_manager_instance()
            key_manager = await get_key_manager_instance(settings.API_KEYS, settings.VERTEX_API_KEYS)
            logger.info("KeyManager instance re-initialized with updated settings.")

            return await ConfigService.get_config()
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred while updating config: {e}")
            raise HTTPException(
                status_code=500, detail=f"An unexpected error occurred: {e}"
            )

    @staticmethod
    async def delete_key(key_to_delete: str) -> Dict[str, Any]:
        """Delete a single API key"""
        key_manager = await get_key_manager_instance()
        await key_manager.delete_api_key(key_to_delete)
        settings.API_KEYS = key_manager.api_keys
        await ConfigService.update_config({"API_KEYS": settings.API_KEYS})
        logger.info(f"Key '{key_to_delete}' has been successfully deleted.")
        return {"success": True, "message": f"Key '{key_to_delete}' has been successfully deleted."}

    @staticmethod
    async def delete_selected_keys(keys_to_delete: List[str]) -> Dict[str, Any]:
        """Bulk delete selected API keys"""
        key_manager = await get_key_manager_instance()
        for key in keys_to_delete:
            await key_manager.delete_api_key(key)
        settings.API_KEYS = key_manager.api_keys
        await ConfigService.update_config({"API_KEYS": settings.API_KEYS})
        logger.info(f"Successfully deleted {len(keys_to_delete)} keys.")
        return {"success": True, "message": f"Successfully deleted {len(keys_to_delete)} keys."}

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
