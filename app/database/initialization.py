"""
Database initialization module
"""
from dotenv import dotenv_values

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.database.connection import engine, Base
from app.database.models import Settings
from app.log.logger import get_database_logger

logger = get_database_logger()


def create_tables():
    """
    Create database tables.
    """
    try:
        # Create all tables
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise


def import_env_to_settings():
    """
    Import configuration items from the .env file into the t_settings table.
    """
    try:
        # Get all configuration items from the .env file
        env_values = dotenv_values(".env")
        
        # Get the inspector
        inspector = inspect(engine)
        
         # Check if the t_settings table exists
        if "t_settings" in inspector.get_table_names():
            # Use a Session for database operations
            with Session(engine) as session:
                # Get all existing configuration items
                current_settings = {setting.key: setting for setting in session.query(Settings).all()}
                
                # Iterate over all configuration items
                for key, value in env_values.items():
                    # Check if the configuration item already exists
                    if key not in current_settings:
                        # Insert the configuration item
                        new_setting = Settings(key=key, value=value)
                        session.add(new_setting)
                        logger.info(f"Inserted setting: {key}")
                
                # Commit the transaction
                session.commit()
                
        logger.info("Environment variables imported to settings table successfully")
    except Exception as e:
        logger.error(f"Failed to import environment variables to settings table: {str(e)}")
        raise


def initialize_database():
    """
    Initialize the database.
    """
    try:
        # Create tables
        create_tables()
        
        # Import environment variables
        import_env_to_settings()
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise