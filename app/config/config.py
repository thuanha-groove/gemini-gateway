"""
Application configuration module.
"""

import datetime
import json
from functools import lru_cache
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
    DATABASE_TYPE: str = "postgres"  # sqlite, mysql or postgres
    SQLITE_DATABASE: str = "default_db"
    
    # PostgreSQL Configuration
    POSTGRES_URL: str = ""
    POSTGRES_HOST: str = ""
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    # Validate PostgreSQL Configuration
    @field_validator(
        "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"
    )
    def validate_postgres_config(cls, v: Any, info: ValidationInfo) -> Any:
        if info.data.get("POSTGRES_URL"):
            return v
        # Defer validation to runtime
        if info.context and info.context.get("runtime"):
            if info.data.get("DATABASE_TYPE") == "postgres" and (v is None or v == ""):
                raise ValueError("PostgreSQL configuration is required when DATABASE_TYPE is 'postgres'")
        return v

    # API Related Configuration
    API_KEYS: List[str] = []
    ALLOWED_TOKENS: List[str] = []
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
@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()


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
