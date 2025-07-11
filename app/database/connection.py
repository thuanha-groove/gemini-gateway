"""
Database connection pool module.
"""
import asyncio
from pathlib import Path
from urllib.parse import quote_plus, urlparse, urlunparse, parse_qs, urlencode
from databases import Database
from sqlalchemy.ext.asyncio import create_async_engine
from app.config.config import get_settings
from app.log.logger import get_database_logger
from app.database.base import Base
# --- Explicitly import all models to ensure they are registered with the Base ---
from app.database.models import Settings, ErrorLog, RequestLog

logger = get_database_logger()

# Create the database engine
# pool_pre_ping=True: Executes a simple "ping" test before getting a connection from the pool to ensure the connection is valid.
engine = None
database = None
DATABASE_URL = None

def initialize_database():
    settings = get_settings()
    global engine, database, DATABASE_URL
    if database is not None:
        return

    db_url = settings.POSTGRES_URL
    db_type = settings.DATABASE_TYPE

    connect_args = {}
    if db_url or db_type == "postgres":
        connect_args["statement_cache_size"] = 0

    logger.info(f"Using connect_args: {connect_args}")

    if db_url:
        parsed_url = urlparse(db_url)
        query_params = parse_qs(parsed_url.query)
        if 'sslmode' in query_params:
            query_params['ssl'] = query_params.pop('sslmode')[0]
        if 'supa' in query_params:
            query_params.pop('supa')
        
        new_query = urlencode(query_params, doseq=True)
        db_url_obj = parsed_url._replace(scheme='postgresql+asyncpg', query=new_query)
        DATABASE_URL = urlunparse(db_url_obj)
    elif db_type == "sqlite":
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        db_path = data_dir / settings.SQLITE_DATABASE
        DATABASE_URL = f"sqlite:///{db_path}"
    elif db_type == "postgres":
        DATABASE_URL = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{quote_plus(settings.POSTGRES_PASSWORD)}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    else:
        raise ValueError("Unsupported database type. Please set DATABASE_TYPE to 'sqlite' or 'postgres'.")

    engine = create_async_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        connect_args=connect_args
    )

    if db_type == "sqlite":
        database = Database(DATABASE_URL)
    else:
        logger.info(f"Initializing Database with connect_args: {connect_args}")
        database = Database(DATABASE_URL, min_size=5, max_size=20, force_rollback=True, **connect_args)


async def connect_to_db():
    """
    Connect to the database and create tables.
    """
    global database, engine
    if database is None:
        initialize_database()
    
    if not database.is_connected:
        logger.info("Database not connected. Connecting now...")
        try:
            await database.connect()
            logger.info(f"Connected to {get_settings().DATABASE_TYPE}")

            # --- Create tables immediately after first connect ---
            logger.info("Creating database tables...")
            async with engine.begin() as conn:
                # Use checkfirst=True to prevent race conditions during table creation
                await conn.run_sync(Base.metadata.create_all, checkfirst=True)
            logger.info("Database tables created successfully.")

        except Exception as e:
            logger.error(f"Failed to connect to database or create tables: {str(e)}")
            raise


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


async def get_db() -> Database:
    """
    FastAPI dependency to get a database connection.
    """
    global database
    if not database or not database.is_connected:
        # This should not happen in a properly configured application
        # where connect_to_db is called on startup.
        await connect_to_db()
    return database
