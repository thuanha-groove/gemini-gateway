"""
Service for request log operations.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from databases import Database

from app.config.config import settings
from app.database.models import RequestLog
from app.log.logger import get_request_log_logger

logger = get_request_log_logger()


async def delete_old_request_logs(db: Database):
    """
    Periodically delete old request logs.
    
    Args:
        db: The database connection.
    """
    if not settings.AUTO_DELETE_REQUEST_LOGS_ENABLED:
        logger.info(
            "Auto-delete for request logs is disabled by settings. Skipping task."
        )
        return

    days_to_keep = settings.AUTO_DELETE_REQUEST_LOGS_DAYS
    logger.info(
        f"Starting scheduled task to delete old request logs older than {days_to_keep} days."
    )

    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

        query = delete(RequestLog).where(RequestLog.request_time < cutoff_date)

        await db.execute(query)
        logger.info(
            f"Request logs older than {cutoff_date} were targeted for deletion."
        )

    except Exception as e:
        logger.error(
            f"An error occurred during the scheduled request log deletion: {str(e)}",
            exc_info=True,
        )
