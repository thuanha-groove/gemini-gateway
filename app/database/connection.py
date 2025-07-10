"""
Database connection pool module.
"""
import asyncio
from pathlib import Path
from urllib.parse import quote_plus
from databases import Database
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config.config import get_settings
from app.log.logger import get_database_logger
from app.database.base import Base
# --- Explicitly import all models to ensure they are registered with the Base ---
from app.database.models import Settings, ErrorLog, RequestLog

logger = get_database_logger()

# Create the database engine
# pool_pre_ping=True: Executes a simple "ping" test before getting a connection from the pool to ensure the connection is valid.
engine = None
async_session_factory = None
database = None
DATABASE_URL = None

def initialize_database():
    settings = get_settings()
    global engine, async_session_factory, database, DATABASE_URL
    if database is not None:
        return

    if settings.POSTGRES_URL:
        DATABASE_URL = settings.POSTGRES_URL.replace("postgres://", "postgresql+asyncpg://")
    elif settings.DATABASE_TYPE == "sqlite":
        # Ensure the data directory exists
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        db_path = data_dir / settings.SQLITE_DATABASE
        DATABASE_URL = f"sqlite:///{db_path}"
    elif settings.DATABASE_TYPE == "postgres":
        DATABASE_URL = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{quote_plus(settings.POSTGRES_PASSWORD)}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    else:
        raise ValueError("Unsupported database type. Please set DATABASE_TYPE to 'sqlite' or 'postgres'.")

    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    async_session_factory = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    if settings.DATABASE_TYPE == "sqlite":
        database = Database(DATABASE_URL)
    else:
        database = Database(DATABASE_URL, min_size=5, max_size=20)


_db_connection_lock = asyncio.Lock()

async def get_database() -> Database:
    """
    Returns the database instance, initializing and connecting it if necessary.
    This function is now responsible for creating tables on first connect.
    """
    global database
    if database is None:
        initialize_database()

    # Use a lock to prevent race conditions when connecting
    async with _db_connection_lock:
        if not database.is_connected:
            logger.info("Database not connected. Connecting now...")
            try:
                await database.connect()
                logger.info(f"Connected to {get_settings().DATABASE_TYPE}")

                # --- Create tables immediately after first connect ---
                logger.info("Creating database tables...")
                async with engine.begin() as conn:
                    # Use the imported Base's metadata
                    await conn.run_sync(Base.metadata.create_all)
                logger.info("Database tables created successfully.")

            except Exception as e:
                logger.error(f"Failed to connect to database or create tables: {str(e)}")
                raise
    return database


async def connect_to_db():
    """
    Connect to the database.
    """
    await get_database()


async def disconnect_from_db():
    """
    Disconnect from the database.
    """
    global database
    if database and database.is_connected:
        settings = get_settings()
        try:
            await database.disconnect()
            logger.info(f"Disconnected from {settings.DATABASE_TYPE}")
        except Exception as e:
            logger.error(f"Failed to disconnect from database: {str(e)}")
