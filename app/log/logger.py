import logging
import platform
import sys
from typing import Dict, Optional

# ANSI escape sequence color codes
LEVEL_COLORS = {
    "DEBUG": "\033[34m",    # Blue
    "INFO": "\033[32m",     # Green
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",    # Red
    "CRITICAL": "\033[1;31m"  # Bold Red
}

# Enable ANSI support for Windows systems
if platform.system() == "Windows":
    import ctypes

    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


class ColorFormatter(logging.Formatter):
    """
    Custom log formatter with color support
    """

    def format(self, record):
        # Get the color code for the corresponding level
        color_code = LEVEL_COLORS.get(record.levelname, "")
        # Add color code and reset code
        record.levelname = f"{color_code}{record.levelname}\033[0m"
        # Create fixed width string containing filename and line number
        record.fileloc = f"[{record.filename}:{record.lineno}]"
        return super().format(record)


# Log format - using fileloc with fixed width (e.g., 30)
FORMATTER = ColorFormatter(
    "%(asctime)s | %(levelname)-17s | %(fileloc)-30s | %(message)s"
)

# Log level mapping
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


class Logger:
    def __init__(self):
        pass

    _loggers: Dict[str, logging.Logger] = {}

    @staticmethod
    def setup_logger(name: str) -> logging.Logger:
        """
        Set up and get logger
        :param name: logger name
        :return: logger instance
        """
        # Import settings object
        from app.config.config import settings

        # Get log level from global configuration
        log_level_str = settings.LOG_LEVEL.lower()
        level = LOG_LEVELS.get(log_level_str, logging.INFO)

        if name in Logger._loggers:
            # If logger exists, check and update its level (if needed)
            existing_logger = Logger._loggers[name]
            if existing_logger.level != level:
                existing_logger.setLevel(level)
            return existing_logger

        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = False

        # Add console output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(FORMATTER)
        logger.addHandler(console_handler)

        Logger._loggers[name] = logger
        return logger

    @staticmethod
    def get_logger(name: str) -> Optional[logging.Logger]:
        """
        Get an existing logger
        :param name: logger name
        :return: logger instance or None
        """
        return Logger._loggers.get(name)

    @staticmethod
    def update_log_levels(log_level: str):
        """
        Update the log level of all created loggers based on the current global configuration.
        """
        log_level_str = log_level.lower()
        new_level = LOG_LEVELS.get(log_level_str, logging.INFO)

        updated_count = 0
        for logger_name, logger_instance in Logger._loggers.items():
            if logger_instance.level != new_level:
                logger_instance.setLevel(new_level)
                # Optional: log level change logs, but be careful to avoid too many logs within the logging module
                # print(f"Updated log level for logger '{logger_name}' to {log_level_str.upper()}")
                updated_count += 1


# Predefined loggers
def get_openai_logger():
    return Logger.setup_logger("openai")


def get_gemini_logger():
    return Logger.setup_logger("gemini")


def get_chat_logger():
    return Logger.setup_logger("chat")


def get_model_logger():
    return Logger.setup_logger("model")


def get_security_logger():
    return Logger.setup_logger("security")


def get_key_manager_logger():
    return Logger.setup_logger("key_manager")


def get_main_logger():
    return Logger.setup_logger("main")


def get_embeddings_logger():
    return Logger.setup_logger("embeddings")


def get_request_logger():
    return Logger.setup_logger("request")


def get_retry_logger():
    return Logger.setup_logger("retry")


def get_image_create_logger():
    return Logger.setup_logger("image_create")


def get_exceptions_logger():
    return Logger.setup_logger("exceptions")


def get_application_logger():
    return Logger.setup_logger("application")


def get_initialization_logger():
    return Logger.setup_logger("initialization")


def get_middleware_logger():
    return Logger.setup_logger("middleware")


def get_routes_logger():
    return Logger.setup_logger("routes")


def get_config_routes_logger():
    return Logger.setup_logger("config_routes")


def get_config_logger():
    return Logger.setup_logger("config")


def get_database_logger():
    return Logger.setup_logger("database")


def get_log_routes_logger():
    return Logger.setup_logger("log_routes")


def get_stats_logger():
    return Logger.setup_logger("stats")


def get_update_logger():
    return Logger.setup_logger("update_service")


def get_scheduler_routes():
    return Logger.setup_logger("scheduler_routes")


def get_message_converter_logger():
    return Logger.setup_logger("message_converter")


def get_api_client_logger():
    return Logger.setup_logger("api_client")


def get_openai_compatible_logger():
    return Logger.setup_logger("openai_compatible")


def get_error_log_logger():
    return Logger.setup_logger("error_log")


def get_request_log_logger():
    return Logger.setup_logger("request_log")


def get_vertex_express_logger():
    return Logger.setup_logger("vertex_express")

