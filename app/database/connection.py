"""
Database connection pool module.
"""
from pathlib import Path
from urllib.parse import quote_plus
from databases import Database
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base

from app.config.config import settings
from app.log.logger import get_database_logger

logger = get_database_logger()

# Database URL
if settings.DATABASE_TYPE == "sqlite":
    # Ensure the data directory exists
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    db_path = data_dir / settings.SQLITE_DATABASE
    DATABASE_URL = f"sqlite:///{db_path}"
elif settings.DATABASE_TYPE == "mysql":
    if settings.MYSQL_SOCKET:
        DATABASE_URL = f"mysql+pymysql://{settings.MYSQL_USER}:{quote_plus(settings.MYSQL_PASSWORD)}@/{settings.MYSQL_DATABASE}?unix_socket={settings.MYSQL_SOCKET}"
    else:
        DATABASE_URL = f"mysql+pymysql://{settings.MYSQL_USER}:{quote_plus(settings.MYSQL_PASSWORD)}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
else:
    raise ValueError("Unsupported database type. Please set DATABASE_TYPE to 'sqlite' or 'mysql'.")

# Create the database engine
# pool_pre_ping=True: Executes a simple "ping" test before getting a connection from the pool to ensure the connection is valid.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create a metadata object
metadata = MetaData()

# Create a base class
Base = declarative_base(metadata=metadata)

# Create a database connection pool and configure its parameters; connection pool is not used in SQLite.
# min_size/max_size: The minimum/maximum number of connections in the connection pool.
# pool_recycle=1800: The maximum number of seconds a connection can exist in the pool (lifecycle).
#                    Set to 1800 seconds (30 minutes) to ensure connections are recycled before the MySQL default wait_timeout (usually 8 hours) or other network timeouts.
#                    If you encounter connection failures, you can try lowering this value to be less than the actual wait_timeout or network timeout.
# The databases library automatically handles reconnection attempts after a connection becomes invalid.
if settings.DATABASE_TYPE == "sqlite":
    database = Database(DATABASE_URL)
else:
    database = Database(DATABASE_URL, min_size=5, max_size=20, pool_recycle=1800)

async def connect_to_db():
    """
    Connect to the database.
    """
    try:
        await database.connect()
        logger.info(f"Connected to {settings.DATABASE_TYPE}")
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise


async def disconnect_from_db():
    """
    Disconnect from the database.
    """
    try:
        await database.disconnect()
        logger.info(f"Disconnected from {settings.DATABASE_TYPE}")
    except Exception as e:
        logger.error(f"Failed to disconnect from database: {str(e)}")