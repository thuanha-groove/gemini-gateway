from sqlalchemy.orm import sessionmaker, Session
from app.database.connection import engine

# The sessionmaker is now configured in get_db to ensure the engine is initialized.
session_factory = None

def get_db() -> Session:
    """
    Provide a database session to a dependency.
    """
    global session_factory
    if session_factory is None:
        # Initialize the session factory if it hasn't been already.
        # This will use the engine created during the application's startup.
        session_factory = sessionmaker(
            autocommit=False, autoflush=False, bind=engine
        )
    
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
