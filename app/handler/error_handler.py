from contextlib import asynccontextmanager
from fastapi import HTTPException
import logging

@asynccontextmanager
async def handle_route_errors(logger: logging.Logger, operation_name: str, success_message: str = None, failure_message: str = None):
    """
    An asynchronous context manager for unified handling of common errors and logging in FastAPI routes.

    Args:
        logger: A Logger instance for logging.
        operation_name: The name of the operation, used for logging and error details.
        success_message: A custom message to log on successful operation (optional).
        failure_message: A custom message to log on failed operation (optional).
    """
    default_success_msg = f"{operation_name} request successful"
    default_failure_msg = f"{operation_name} request failed"

    logger.info("-" * 50 + operation_name + "-" * 50)
    try:
        yield
        logger.info(success_message or default_success_msg)
    except HTTPException as http_exc:
        # If it's already an HTTPException, re-raise it directly to preserve the original status code and detail
        logger.error(f"{failure_message or default_failure_msg}: {http_exc.detail} (Status: {http_exc.status_code})")
        raise http_exc
    except Exception as e:
        # For all other exceptions, log the error and raise a standard 500 error
        logger.error(f"{failure_message or default_failure_msg}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Internal server error during {operation_name}"
        ) from e