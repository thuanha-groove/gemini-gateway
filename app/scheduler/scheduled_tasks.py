from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config.config import settings
from app.domain.gemini_models import GeminiContent, GeminiRequest
from app.log.logger import Logger
from app.service.chat.gemini_chat_service import GeminiChatService
from app.service.error_log.error_log_service import delete_old_error_logs
from app.service.key.key_manager import get_key_manager_instance
from app.service.request_log.request_log_service import delete_old_request_logs_task

logger = Logger.setup_logger("scheduler")


async def check_failed_keys():
    """
    Periodically checks API keys with failure counts greater than 0 and attempts to validate them.
    If validation is successful, the failure count is reset; if it fails, the failure count is incremented.
    """
    logger.info("Starting scheduled check for failed API keys...")
    try:
        key_manager = await get_key_manager_instance()
        # Ensure KeyManager is initialized
        if not key_manager or not hasattr(key_manager, "key_failure_counts"):
            logger.warning(
                "KeyManager instance not available or not initialized. Skipping check."
            )
            return

        # Create a GeminiChatService instance for validation
        # Note: An instance is created directly here, not through dependency injection, as this is a background task
        chat_service = GeminiChatService(settings.BASE_URL, key_manager)

        # Get the list of keys to check (failure count > 0)
        keys_to_check = []
        async with key_manager.failure_count_lock:  # Lock is required to access shared data
            # Create a copy to avoid modifying the dictionary while iterating
            failure_counts_copy = key_manager.key_failure_counts.copy()
            keys_to_check = [
                key for key, count in failure_counts_copy.items() if count > 0
            ]  # Check all keys with a failure count > 0

        if not keys_to_check:
            logger.info("No keys with failure count > 0 found. Skipping verification.")
            return

        logger.info(
            f"Found {len(keys_to_check)} keys with failure count > 0 to verify."
        )

        for key in keys_to_check:
            # Hide part of the key for logging
            log_key = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else key
            logger.info(f"Verifying key: {log_key}...")
            try:
                # Construct a test request
                gemini_request = GeminiRequest(
                    contents=[
                        GeminiContent(
                            role="user",
                            parts=[{"text": "hi"}],
                        )
                    ]
                )
                await chat_service.generate_content(
                    settings.TEST_MODEL, gemini_request, key
                )
                logger.info(
                    f"Key {log_key} verification successful. Resetting failure count."
                )
                await key_manager.reset_key_failure_count(key)
            except Exception as e:
                logger.warning(
                    f"Key {log_key} verification failed: {str(e)}. Incrementing failure count."
                )
                # Directly manipulate the counter, requires a lock
                async with key_manager.failure_count_lock:
                    # Re-check if the key exists and its failure count is not at max
                    if (
                        key in key_manager.key_failure_counts
                        and key_manager.key_failure_counts[key]
                        < key_manager.MAX_FAILURES
                    ):
                        key_manager.key_failure_counts[key] += 1
                        logger.info(
                            f"Failure count for key {log_key} incremented to {key_manager.key_failure_counts[key]}."
                        )
                    elif key in key_manager.key_failure_counts:
                        logger.warning(
                            f"Key {log_key} reached MAX_FAILURES ({key_manager.MAX_FAILURES}). Not incrementing further."
                        )

    except Exception as e:
        logger.error(
            f"An error occurred during the scheduled key check: {str(e)}", exc_info=True
        )


def setup_scheduler():
    """Sets up and starts APScheduler"""
    scheduler = AsyncIOScheduler(timezone=str(settings.TIMEZONE))  # Read timezone from config
    # Add a scheduled task to check failed keys
    scheduler.add_job(
        check_failed_keys,
        "interval",
        hours=settings.CHECK_INTERVAL_HOURS,
        id="check_failed_keys_job",
        name="Check Failed API Keys",
    )
    logger.info(
        f"Key check job scheduled to run every {settings.CHECK_INTERVAL_HOURS} hour(s)."
    )

    # New: Add a scheduled task to auto-delete error logs, runs daily at 3:00 AM
    scheduler.add_job(
        delete_old_error_logs,
        "cron",
        hour=3,
        minute=0,
        id="delete_old_error_logs_job",
        name="Delete Old Error Logs",
    )
    logger.info("Auto-delete error logs job scheduled to run daily at 3:00 AM.")

    # New: Add a scheduled task to auto-delete request logs, runs daily at 3:05 AM
    scheduler.add_job(
        delete_old_request_logs_task,
        "cron",
        hour=3,
        minute=5,
        id="delete_old_request_logs_job",
        name="Delete Old Request Logs",
    )
    logger.info(
        f"Auto-delete request logs job scheduled to run daily at 3:05 AM, if enabled and AUTO_DELETE_REQUEST_LOGS_DAYS is set to {settings.AUTO_DELETE_REQUEST_LOGS_DAYS} days."
    )

    scheduler.start()
    logger.info("Scheduler started with all jobs.")
    return scheduler


# A global scheduler instance can be added here to be gracefully stopped when the application closes
scheduler_instance = None


def start_scheduler():
    global scheduler_instance
    if scheduler_instance is None or not scheduler_instance.running:
        logger.info("Starting scheduler...")
        scheduler_instance = setup_scheduler()
    logger.info("Scheduler is already running.")


def stop_scheduler():
    global scheduler_instance
    if scheduler_instance and scheduler_instance.running:
        scheduler_instance.shutdown()
        logger.info("Scheduler stopped.")