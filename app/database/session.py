from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database.connection import engine

# The sessionmaker is now configured in get_session to ensure the engine is initialized.
async_session_factory = None

async def get_session() -> AsyncSession:
    """
    Provide a database session to a dependency.
    """
    global async_session_factory
    if async_session_factory is None:
        # Initialize the session factory if it hasn't been already.
        # This will use the engine created during the application's startup.
        async_session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async with async_session_factory() as session:
        yield session
