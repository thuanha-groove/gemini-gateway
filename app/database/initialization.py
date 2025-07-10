"""
Database initialization module
"""
from dotenv import dotenv_values

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import connection
from app.database.models import Settings
from app.log.logger import get_database_logger

logger = get_database_logger()


async def create_tables():
    """
    Create database tables asynchronously.
    This function is idempotent and safe to run on every startup.
    """
    try:
        # Ensure the engine is initialized by calling get_database, which is now self-sufficient
        await connection.get_database()
        # Now that we're sure the engine exists, we can use it.
        async with connection.engine.begin() as conn:
            await conn.run_sync(connection.Base.metadata.create_all)
        logger.info("Database tables checked and created if they didn't exist.")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise


async def import_env_to_settings():
    """
    Import configuration items from the .env file into the t_settings table asynchronously.
    This is intended for local development and will be skipped if .env is not found.
    """
    try:
        env_values = dotenv_values(".env")
        if not env_values:
            logger.info("No .env file found or it is empty. Skipping import to settings table.")
            return

        # Ensure engine is initialized
        await connection.get_database()

        def get_table_names(conn):
            inspector = inspect(conn)
            return inspector.get_table_names()

        async with connection.engine.connect() as conn:
            table_names = await conn.run_sync(get_table_names)

        if "t_settings" in table_names:
            async with connection.async_session_factory() as session:
                result = await session.execute(select(Settings))
                current_settings = {setting.key: setting for setting in result.scalars()}

                for key, value in env_values.items():
                    if key not in current_settings:
                        new_setting = Settings(key=key, value=value)
                        session.add(new_setting)
                        logger.info(f"Inserted setting from .env: {key}")

                await session.commit()
            logger.info("Environment variables from .env imported to settings table successfully.")
        else:
            logger.warning("t_settings table not found, skipping import from .env.")
    except Exception as e:
        logger.error(f"Failed to import environment variables to settings table: {str(e)}")
        raise


async def initialize_database():
    """
    Initialize the database asynchronously.
    """
    try:
        await create_tables()
        await import_env_to_settings()
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
