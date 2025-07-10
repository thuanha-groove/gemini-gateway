"""
Application configuration module.
"""

import datetime
import json
from typing import Any, Dict, List, Type

from pydantic import ValidationError, ValidationInfo, field_validator
from pydantic_settings import BaseSettings
from sqlalchemy import insert, select, update

from app.core.constants import (
    API_VERSION,
    DEFAULT_CREATE_IMAGE_MODEL,
    DEFAULT_FILTER_MODELS,
    DEFAULT_MODEL,
    DEFAULT_SAFETY_SETTINGS,
    DEFAULT_STREAM_CHUNK_SIZE,
    DEFAULT_STREAM_LONG_TEXT_THRESHOLD,
    DEFAULT_STREAM_MAX_DELAY,
    DEFAULT_STREAM_MIN_DELAY,
    DEFAULT_STREAM_SHORT_TEXT_THRESHOLD,
    DEFAULT_TIMEOUT,
    MAX_RETRIES,
)
from app.log.logger import Logger


class Settings(BaseSettings):
    # Database Configuration
    DATABASE_TYPE: str = "mysql"  # sqlite or mysql
    SQLITE_DATABASE: str = "default_db"
    MYSQL_HOST: str = ""
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = ""
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = ""
    MYSQL_SOCKET: str = ""

    # Validate MySQL Configuration
    @field_validator(
        "MYSQL_HOST", "MYSQL_PORT", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE"
    )
    def validate_mysql_config(cls, v: Any, info: ValidationInfo) -> Any:
        if info.data.get("DATABASE_TYPE") == "mysql":
            if v is None or v == "":
                raise ValueError(
                    "MySQL configuration is required when DATABASE_TYPE is 'mysql'"
                )
        return v

    # API Related Configuration
    API_KEYS: List[str]
    ALLOWED_TOKENS: List[str]
    BASE_URL: str = f"https://generativelanguage.googleapis.com/{API_VERSION}"
    GEMINI_GATEWAY_AUTH_TOKEN: str = ""
    MAX_FAILURES: int = 3
    TEST_MODEL: str = DEFAULT_MODEL
    TIME_OUT: int = DEFAULT_TIMEOUT
    MAX_RETRIES: int = MAX_RETRIES
    PROXIES: List[str] = []
    PROXIES_USE_CONSISTENCY_HASH_BY_API_KEY: bool = True  # Whether to use consistent hashing to select a proxy
    VERTEX_API_KEYS: List[str] = []
    VERTEX_EXPRESS_BASE_URL: str = "https://aiplatform.googleapis.com/v1beta1/publishers/google"

    # Smart Routing Configuration
    URL_NORMALIZATION_ENABLED: bool = False  # Whether to enable smart routing mapping

    # Model Related Configuration
    SEARCH_MODELS: List[str] = ["gemini-2.0-flash-exp"]
    IMAGE_MODELS: List[str] = ["gemini-2.0-flash-exp"]
    FILTERED_MODELS: List[str] = DEFAULT_FILTER_MODELS
    TOOLS_CODE_EXECUTION_ENABLED: bool = False
    SHOW_SEARCH_LINK: bool = True
    SHOW_THINKING_PROCESS: bool = True
    THINKING_MODELS: List[str] = []
    THINKING_BUDGET_MAP: Dict[str, float] = {}

    # TTS Related Configuration
    TTS_MODEL: str = "gemini-2.5-flash-preview-tts"
    TTS_VOICE_NAME: str = "Zephyr"
    TTS_SPEED: str = "normal"

    # Image Generation Related Configuration
    PAID_KEY: str = ""
    CREATE_IMAGE_MODEL: str = DEFAULT_CREATE_IMAGE_MODEL
    UPLOAD_PROVIDER: str = "smms"
    SMMS_SECRET_TOKEN: str = ""
    PICGO_API_KEY: str = ""
    CLOUDFLARE_IMGBED_URL: str = ""
    CLOUDFLARE_IMGBED_AUTH_CODE: str = ""
    CLOUDFLARE_IMGBED_UPLOAD_FOLDER: str = ""

    # Stream Optimizer Configuration
    STREAM_OPTIMIZER_ENABLED: bool = False
    STREAM_MIN_DELAY: float = DEFAULT_STREAM_MIN_DELAY
    STREAM_MAX_DELAY: float = DEFAULT_STREAM_MAX_DELAY
    STREAM_SHORT_TEXT_THRESHOLD: int = DEFAULT_STREAM_SHORT_TEXT_THRESHOLD
    STREAM_LONG_TEXT_THRESHOLD: int = DEFAULT_STREAM_LONG_TEXT_THRESHOLD
    STREAM_CHUNK_SIZE: int = DEFAULT_STREAM_CHUNK_SIZE

    # Fake Streaming Configuration
    FAKE_STREAM_ENABLED: bool = False  # Whether to enable fake streaming output
    FAKE_STREAM_EMPTY_DATA_INTERVAL_SECONDS: int = 5  # Interval for sending empty data in fake stream (seconds)

    # Scheduler Configuration
    CHECK_INTERVAL_HOURS: int = 1  # Default check interval is 1 hour
    TIMEZONE: str = "Asia/Shanghai"  # Default timezone

    # Github
    GITHUB_REPO_OWNER: str = "thuanha-groove"
    GITHUB_REPO_NAME: str = "gemini-gateway"

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    AUTO_DELETE_ERROR_LOGS_ENABLED: bool = True
    AUTO_DELETE_ERROR_LOGS_DAYS: int = 7
    AUTO_DELETE_REQUEST_LOGS_ENABLED: bool = False
    AUTO_DELETE_REQUEST_LOGS_DAYS: int = 30
    SAFETY_SETTINGS: List[Dict[str, str]] = DEFAULT_SAFETY_SETTINGS


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set default GEMINI_GATEWAY_AUTH_TOKEN (if not provided)
        if not self.GEMINI_GATEWAY_AUTH_TOKEN and self.ALLOWED_TOKENS:
            self.GEMINI_GATEWAY_AUTH_TOKEN = self.ALLOWED_TOKENS[0]


# Create a global configuration instance
settings = Settings()


def _parse_db_value(key: str, db_value: str, target_type: Type) -> Any:
    """Attempts to parse a database string value into the target Python type."""
    from app.log.logger import get_config_logger

    logger = get_config_logger()
    try:
        # Handle List[str]
        if target_type == List[str]:
            try:
                parsed = json.loads(db_value)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except json.JSONDecodeError:
                return [item.strip() for item in db_value.split(",") if item.strip()]
            logger.warning(
                f"Could not parse '{db_value}' as List[str] for key '{key}', falling back to comma split or empty list."
            )
            return [item.strip() for item in db_value.split(",") if item.strip()]
        # Handle Dict[str, float]
        elif target_type == Dict[str, float]:
            parsed_dict = {}
            try:
                parsed = json.loads(db_value)
                if isinstance(parsed, dict):
                    parsed_dict = {str(k): float(v) for k, v in parsed.items()}
                else:
                    logger.warning(
                        f"Parsed DB value for key '{key}' is not a dictionary type. Value: {db_value}"
                    )
            except (json.JSONDecodeError, ValueError, TypeError) as e1:
                if isinstance(e1, json.JSONDecodeError) and "'" in db_value:
                    logger.warning(
                        f"Failed initial JSON parse for key '{key}'. Attempting to replace single quotes. Error: {e1}"
                    )
                    try:
                        corrected_db_value = db_value.replace("'", '"')
                        parsed = json.loads(corrected_db_value)
                        if isinstance(parsed, dict):
                            parsed_dict = {str(k): float(v) for k, v in parsed.items()}
                        else:
                            logger.warning(
                                f"Parsed DB value (after quote replacement) for key '{key}' is not a dictionary type. Value: {corrected_db_value}"
                            )
                    except (json.JSONDecodeError, ValueError, TypeError) as e2:
                        logger.error(
                            f"Could not parse '{db_value}' as Dict[str, float] for key '{key}' even after replacing quotes: {e2}. Returning empty dict."
                        )
                else:
                    logger.error(
                        f"Could not parse '{db_value}' as Dict[str, float] for key '{key}': {e1}. Returning empty dict."
                    )
            return parsed_dict
        # Handle List[Dict[str, str]]
        elif target_type == List[Dict[str, str]]:
            try:
                parsed = json.loads(db_value)
                if isinstance(parsed, list):
                    # Validate that each element in the list is a dictionary and that keys and values are strings
                    valid = all(
                        isinstance(item, dict)
                        and all(isinstance(k, str) for k in item.keys())
                        and all(isinstance(v, str) for v in item.values())
                        for item in parsed
                    )
                    if valid:
                        return parsed
                    else:
                        logger.warning(
                            f"Invalid structure in List[Dict[str, str]] for key '{key}'. Value: {db_value}"
                        )
                        return []
                else:
                    logger.warning(
                        f"Parsed DB value for key '{key}' is not a list type. Value: {db_value}"
                    )
                    return []
            except json.JSONDecodeError:
                logger.error(
                    f"Could not parse '{db_value}' as JSON for List[Dict[str, str]] for key '{key}'. Returning empty list."
                )
                return []
            except Exception as e:
                logger.error(
                    f"Error parsing List[Dict[str, str]] for key '{key}': {e}. Value: {db_value}. Returning empty list."
                )
                return []
        # Handle bool
        elif target_type == bool:
            return db_value.lower() in ("true", "1", "yes", "on")
        # Handle int
        elif target_type == int:
            return int(db_value)
        # Handle float
        elif target_type == float:
            return float(db_value)
        # Default to str or other types that Pydantic can handle directly
        else:
            return db_value
    except (ValueError, TypeError, json.JSONDecodeError) as e:
        logger.warning(
            f"Failed to parse db_value '{db_value}' for key '{key}' as type {target_type}: {e}. Using original string value."
        )
        return db_value  # Return the original string on parsing failure


async def sync_initial_settings():
    """
    Synchronize configuration on application startup:
    1. Load settings from the database.
    2. Merge database settings into in-memory settings (database has priority).
    3. Synchronize the final in-memory settings back to the database.
    """
    from app.log.logger import get_config_logger

    logger = get_config_logger()
    # Lazy import to avoid circular dependencies and ensure database connection is initialized
    from app.database.connection import database
    from app.database.models import Settings as SettingsModel

    global settings
    logger.info("Starting initial settings synchronization...")

    if not database.is_connected:
        try:
            await database.connect()
            logger.info("Database connection established for initial sync.")
        except Exception as e:
            logger.error(
                f"Failed to connect to database for initial settings sync: {e}. Skipping sync."
            )
            return

    try:
        # 1. Load settings from the database
        db_settings_raw: List[Dict[str, Any]] = []
        try:
            query = select(SettingsModel.key, SettingsModel.value)
            results = await database.fetch_all(query)
            db_settings_raw = [
                {"key": row["key"], "value": row["value"]} for row in results
            ]
            logger.info(f"Fetched {len(db_settings_raw)} settings from database.")
        except Exception as e:
            logger.error(
                f"Failed to fetch settings from database: {e}. Proceeding with environment/dotenv settings."
            )
            # Even if database read fails, continue to ensure env/dotenv-based config can be synced to the database

        db_settings_map: Dict[str, str] = {
            s["key"]: s["value"] for s in db_settings_raw
        }

        # 2. Merge database settings into in-memory settings (database has priority)
        updated_in_memory = False

        for key, db_value in db_settings_map.items():
            if key == "DATABASE_TYPE":
                logger.debug(
                    f"Skipping update of '{key}' in memory from database. "
                    "This setting is controlled by environment/dotenv."
                )
                continue
            if hasattr(settings, key):
                target_type = Settings.__annotations__.get(key)
                if target_type:
                    try:
                        parsed_db_value = _parse_db_value(key, db_value, target_type)
                        memory_value = getattr(settings, key)

                        # Compare the parsed value with the in-memory value
                        # Note: Direct comparison may not be robust for complex types like lists, but it's simplified here
                        if parsed_db_value != memory_value:
                            # Check for type match to prevent the parsing function from returning an incompatible type
                            type_match = False
                            if target_type == List[str] and isinstance(
                                parsed_db_value, list
                            ):
                                type_match = True
                            elif target_type == Dict[str, float] and isinstance(
                                parsed_db_value, dict
                            ):
                                type_match = True
                            elif target_type not in (
                                List[str],
                                Dict[str, float],
                            ) and isinstance(parsed_db_value, target_type):
                                type_match = True

                            if type_match:
                                setattr(settings, key, parsed_db_value)
                                logger.debug(
                                    f"Updated setting '{key}' in memory from database value ({target_type})."
                                )
                                updated_in_memory = True
                            else:
                                logger.warning(
                                    f"Parsed DB value type mismatch for key '{key}'. Expected {target_type}, got {type(parsed_db_value)}. Skipping update."
                                )

                    except Exception as e:
                        logger.error(
                            f"Error processing database setting for key '{key}': {e}"
                        )
            else:
                logger.warning(
                    f"Database setting '{key}' not found in Settings model definition. Ignoring."
                )

        # If there are updates in memory, re-validate the Pydantic model (optional but recommended)
        if updated_in_memory:
            try:
                # Reload to ensure type conversion and validation
                settings = Settings(**settings.model_dump())
                logger.info(
                    "Settings object re-validated after merging database values."
                )
            except ValidationError as e:
                logger.error(
                    f"Validation error after merging database settings: {e}. Settings might be inconsistent."
                )

        # 3. Synchronize the final in-memory settings back to the database
        final_memory_settings = settings.model_dump()
        settings_to_update: List[Dict[str, Any]] = []
        settings_to_insert: List[Dict[str, Any]] = []
        now = datetime.datetime.now(datetime.timezone.utc)

        existing_db_keys = set(db_settings_map.keys())

        for key, value in final_memory_settings.items():
            if key == "DATABASE_TYPE":
                logger.debug(
                    f"Skipping synchronization of '{key}' to database. "
                    "This setting is controlled by environment/dotenv."
                )
                continue

            # Serialize values to strings or JSON strings
            if isinstance(value, (list, dict)):
                db_value = json.dumps(
                    value, ensure_ascii=False
                )
            elif isinstance(value, bool):
                db_value = str(value).lower()
            elif value is None:
                db_value = ""
            else:
                db_value = str(value)

            data = {
                "key": key,
                "value": db_value,
                "description": f"{key} configuration setting",
                "updated_at": now,
            }

            if key in existing_db_keys:
                # Only update if the value is different from the one in the database
                if db_settings_map[key] != db_value:
                    settings_to_update.append(data)
            else:
                # If the key is not in the database, insert it
                data["created_at"] = now
                settings_to_insert.append(data)

        # Execute batch insert and update in a transaction
        if settings_to_insert or settings_to_update:
            try:
                async with database.transaction():
                    if settings_to_insert:
                        # Get existing descriptions to avoid overwriting them
                        query_existing = select(
                            SettingsModel.key, SettingsModel.description
                        ).where(
                            SettingsModel.key.in_(
                                [s["key"] for s in settings_to_insert]
                            )
                        )
                        existing_desc = {
                            row["key"]: row["description"]
                            for row in await database.fetch_all(query_existing)
                        }
                        for item in settings_to_insert:
                            item["description"] = existing_desc.get(
                                item["key"], item["description"]
                            )

                        query_insert = insert(SettingsModel).values(settings_to_insert)
                        await database.execute(query=query_insert)
                        logger.info(
                            f"Synced (inserted) {len(settings_to_insert)} settings to database."
                        )

                    if settings_to_update:
                        # Get existing descriptions to avoid overwriting them
                        query_existing = select(
                            SettingsModel.key, SettingsModel.description
                        ).where(
                            SettingsModel.key.in_(
                                [s["key"] for s in settings_to_update]
                            )
                        )
                        existing_desc = {
                            row["key"]: row["description"]
                            for row in await database.fetch_all(query_existing)
                        }

                        for setting_data in settings_to_update:
                            setting_data["description"] = existing_desc.get(
                                setting_data["key"], setting_data["description"]
                            )
                            query_update = (
                                update(SettingsModel)
                                .where(SettingsModel.key == setting_data["key"])
                                .values(
                                    value=setting_data["value"],
                                    description=setting_data["description"],
                                    updated_at=setting_data["updated_at"],
                                )
                            )
                            await database.execute(query=query_update)
                        logger.info(
                            f"Synced (updated) {len(settings_to_update)} settings to database."
                        )
            except Exception as e:
                logger.error(
                    f"Failed to sync settings to database during startup: {str(e)}"
                )
        else:
            logger.info(
                "No setting changes detected between memory and database during initial sync."
            )

        # Refresh log level
        Logger.update_log_levels(final_memory_settings.get("LOG_LEVEL"))

    except Exception as e:
        logger.error(f"An unexpected error occurred during initial settings sync: {e}")
    finally:
        if database.is_connected:
            try:
                pass
            except Exception as e:
                logger.error(f"Error disconnecting database after initial sync: {e}")

    logger.info("Initial settings synchronization finished.")
