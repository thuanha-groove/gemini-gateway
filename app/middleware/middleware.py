"""
Middleware configuration module, responsible for setting up and configuring the application's middleware.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

# from app.middleware.request_logging_middleware import RequestLoggingMiddleware
from app.middleware.smart_routing_middleware import SmartRoutingMiddleware
from app.core.constants import API_VERSION
from app.core.security import verify_auth_token
from app.log.logger import get_middleware_logger

logger = get_middleware_logger()


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware, handles unauthenticated requests.
    """

    async def dispatch(self, request: Request, call_next):
        # Allow specific paths to bypass authentication
        if (
            request.url.path not in ["/", "/auth"]
            and not request.url.path.startswith("/static")
            and not request.url.path.startswith("/gemini")
            and not request.url.path.startswith("/v1")
            and not request.url.path.startswith(f"/{API_VERSION}")
            and not request.url.path.startswith("/health")
            and not request.url.path.startswith("/hf")
            and not request.url.path.startswith("/openai")
            and not request.url.path.startswith("/api/version/check")
            and not request.url.path.startswith("/vertex-express")
        ):

            auth_token = request.cookies.get("auth_token")
            if not auth_token or not verify_auth_token(auth_token):
                logger.warning(f"Unauthorized access attempt to {request.url.path}")
                return RedirectResponse(url="/")
            logger.debug("Request authenticated successfully")

        response = await call_next(request)
        return response


def setup_middlewares(app: FastAPI) -> None:
    """
    Sets up the application's middleware.

    Args:
        app: FastAPI application instance.
    """
    # Add Smart Routing Middleware (must be before authentication middleware)
    app.add_middleware(SmartRoutingMiddleware)

    # Add Authentication Middleware
    app.add_middleware(AuthMiddleware)

    # Add Request Logging Middleware (optional, commented out by default)
    # app.add_middleware(RequestLoggingMiddleware)

    # Configure CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=[
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "OPTIONS",
        ],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=600,
    )