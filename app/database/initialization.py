"""
Database initialization module
"""
from dotenv import dotenv_values

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import engine, Base, async_session_factory
from app.database.models import Settings
from app.log.logger import get_database_logger

logger = get_database_logger()


async def create_tables():
    """
    Create database tables asynchronously.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise


async def import_env_to_settings():
    """
    Import configuration items from the .env file into the t_settings table asynchronously.
    """
    try:
        env_values = dotenv_values(".env")

        def get_table_names(conn):
            inspector = inspect(conn)
            return inspector.get_table_names()

        async with engine.connect() as conn:
            table_names = await conn.run_sync(get_table_names)

        if "t_settings" in table_names:
            async with async_session_factory() as session:
                result = await session.execute(select(Settings))
                current_settings = {setting.key: setting for setting in result.scalars()}

                for key, value in env_values.items():
                    if key not in current_settings:
                        new_setting = Settings(key=key, value=value)
                        session.add(new_setting)
                        logger.info(f"Inserted setting: {key}")

                await session.commit()

        logger.info("Environment variables imported to settings table successfully")
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
