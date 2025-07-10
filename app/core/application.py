from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config.config import settings
from app.database.connection import disconnect_from_db, get_database
from app.exception.exceptions import setup_exception_handlers
from app.log.logger import get_application_logger
from app.middleware.middleware import setup_middlewares
from app.router.routes import setup_routers
from app.scheduler.scheduled_tasks import start_scheduler, stop_scheduler
from app.service.key.key_manager import get_key_manager_instance
from app.service.update.update_service import check_for_updates
from app.utils.helpers import get_current_version

logger = get_application_logger()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = PROJECT_ROOT / "app" / "static"
TEMPLATES_DIR = PROJECT_ROOT / "app" / "templates"

# Initialize the template engine and add global variables
templates = Jinja2Templates(directory="app/templates")


# Define a function to update template global variables
def update_template_globals(app: FastAPI, update_info: dict):
    # Jinja2Templates instances don't have a direct method to update global variables
    # We need to pass these variables in the request context or modify the Jinja environment
    # A simpler method is to store it in app.state and pass it during rendering
    app.state.update_info = update_info
    logger.info(f"Update info stored in app.state: {update_info}")


# --- Helper functions for lifespan ---
async def _shutdown_database():
    """Disconnects from the database."""
    await disconnect_from_db()


def _start_scheduler():
    """Starts the background scheduler."""
    try:
        start_scheduler()
        logger.info("Scheduler started successfully.")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")


def _stop_scheduler():
    """Stops the background scheduler."""
    stop_scheduler()


async def _perform_update_check(app: FastAPI):
    """Checks for updates and stores the info in app.state."""
    update_available, latest_version, error_message = await check_for_updates()
    current_version = get_current_version()
    update_info = {
        "update_available": update_available,
        "latest_version": latest_version,
        "error_message": error_message,
        "current_version": current_version,
    }
    if not hasattr(app, "state"):
        from starlette.datastructures import State

        app.state = State()
    app.state.update_info = update_info
    logger.info(f"Update check completed. Info: {update_info}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application startup and shutdown events.
    """
    logger.info("Application starting up...")
    try:
        # Step 1: Initialize database connection and create tables.
        # This is now a single, atomic operation.
        await get_database()
        logger.info("Database connection and tables initialized.")

        # Step 2: Initialize the KeyManager.
        await get_key_manager_instance(settings.API_KEYS, settings.VERTEX_API_KEYS)
        logger.info("KeyManager initialized.")

        # Step 3: Perform update check.
        await _perform_update_check(app)

        # Step 4: Start the scheduler.
        _start_scheduler()

        logger.info("Application startup complete.")

    except Exception as e:
        logger.critical(
            f"Critical error during application startup: {str(e)}", exc_info=True
        )

    yield

    logger.info("Application shutting down...")
    _stop_scheduler()
    await _shutdown_database()


def create_app() -> FastAPI:
    """
    Creates and configures a FastAPI application instance.

    Returns:
        FastAPI: The configured FastAPI application instance.
    """

    # Create FastAPI application
    current_version = get_current_version()
    app = FastAPI(
        title="Gemini Balance API",
        description="Gemini API proxy service, supporting load balancing and key management.",
        version=current_version,
        lifespan=lifespan,
    )

    if not hasattr(app, "state"):
        from starlette.datastructures import State

        app.state = State()
    app.state.update_info = {
        "update_available": False,
        "latest_version": None,
        "error_message": "Initializing...",
        "current_version": current_version,
    }

    # Configure static files
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Configure middleware
    setup_middlewares(app)

    # Configure exception handlers
    setup_exception_handlers(app)

    # Configure routers
    setup_routers(app)

    return app
