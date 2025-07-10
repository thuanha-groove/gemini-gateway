"""
Exception handling module, defines custom exceptions and exception handlers used in the application
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.log.logger import get_exceptions_logger

logger = get_exceptions_logger()


class APIError(Exception):
    """Base class for API errors"""

    def __init__(self, status_code: int, detail: str, error_code: str = None):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code or "api_error"
        super().__init__(self.detail)


class AuthenticationError(APIError):
    """Authentication error"""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=401, detail=detail, error_code="authentication_error"
        )


class AuthorizationError(APIError):
    """Authorization error"""

    def __init__(self, detail: str = "Not authorized to access this resource"):
        super().__init__(
            status_code=403, detail=detail, error_code="authorization_error"
        )


class ResourceNotFoundError(APIError):
    """Resource not found error"""



    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=404, detail=detail, error_code="resource_not_found"
        )


class ModelNotSupportedError(APIError):
    """Model not supported error"""

    def __init__(self, model: str):
        super().__init__(
            status_code=400,
            detail=f"Model {model} is not supported",
            error_code="model_not_supported",
        )


class APIKeyError(APIError):
    """API key error"""

    def __init__(self, detail: str = "Invalid or expired API key"):
        super().__init__(status_code=401, detail=detail, error_code="api_key_error")


class ServiceUnavailableError(APIError):
    """Service unavailable error"""

    def __init__(self, detail: str = "Service temporarily unavailable"):
        super().__init__(
            status_code=503, detail=detail, error_code="service_unavailable"
        )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Sets up exception handlers for the application.

    Args:
        app: The FastAPI application instance.
    """

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError):
        """Handles API errors."""
        logger.error(f"API Error: {exc.detail} (Code: {exc.error_code})")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.error_code, "message": exc.detail}},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handles HTTP exceptions."""
        logger.error(f"HTTP Exception: {exc.detail} (Status: {exc.status_code})")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": "http_error", "message": exc.detail}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Handles request validation errors."""
        error_details = []
        for error in exc.errors():
            error_details.append(
                {"loc": error["loc"], "msg": error["msg"], "type": error["type"]}
            )

        logger.error(f"Validation Error: {error_details}")
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed",
                    "details": error_details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handles generic exceptions."""
        logger.exception(f"Unhandled Exception: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_server_error",
                    "message": "An unexpected error occurred",
                }
            },
        )
