import json

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.log.logger import get_request_logger

logger = get_request_logger()


# Add middleware class
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log request path
        logger.info(f"Request path: {request.url.path}")

        # Get and log request body
        try:
            body = await request.body()
            if body:
                body_str = body.decode()
                # Try to format JSON
                try:
                    formatted_body = json.loads(body_str)
                    logger.info(
                        f"Formatted request body:\n{json.dumps(formatted_body, indent=2, ensure_ascii=False)}"
                    )
                except json.JSONDecodeError:
                    logger.error("Request body is not valid JSON.")
        except Exception as e:
            logger.error(f"Error reading request body: {str(e)}")

        # Reset the request's receiver so subsequent handlers can still read the request body
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        request._receive = receive

        response = await call_next(request)
        return response