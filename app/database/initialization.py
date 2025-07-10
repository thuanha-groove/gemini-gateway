"""
Database initialization module
"""
from app.database import connection
from app.log.logger import get_database_logger

logger = get_database_logger()


async def create_tables():
    """
    Create database tables asynchronously.
    This function assumes the database engine is already initialized.
    """
    try:
        # The engine must be initialized before this function is called.
        async with connection.engine.begin() as conn:
            await conn.run_sync(connection.Base.metadata.create_all)
        logger.info("Database tables checked and created if they didn't exist.")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise
