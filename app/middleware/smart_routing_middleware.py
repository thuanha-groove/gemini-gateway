from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.config.config import settings
from app.log.logger import get_main_logger
import re

logger = get_main_logger()

class SmartRoutingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # Simplified routing rules - route directly based on detection results
        pass

    async def dispatch(self, request: Request, call_next):
        if not settings.URL_NORMALIZATION_ENABLED:
            return await call_next(request)
        logger.debug(f"request: {request}")
        original_path = str(request.url.path)
        method = request.method
        
        # Try to fix the URL
        fixed_path, fix_info = self.fix_request_url(original_path, method, request)

        if fixed_path != original_path:
            logger.info(f"URL fixed: {method} {original_path} → {fixed_path}")
            if fix_info:
                logger.debug(f"Fix details: {fix_info}")

            # Rewrite the request path
            request.scope["path"] = fixed_path
            request.scope["raw_path"] = fixed_path.encode()
        
        return await call_next(request)

    def fix_request_url(self, path: str, method: str, request: Request) -> tuple:
        """Simplified URL fixing logic"""

        # First, check if it's already in the correct format; if so, do nothing
        if self.is_already_correct_format(path):
            return path, None

        # 1. Highest priority: contains generateContent → Gemini format
        if "generatecontent" in path.lower() or "v1beta/models" in path.lower():
            return self.fix_gemini_by_operation(path, method, request)

        # 2. Second priority: contains /openai/ → OpenAI format
        if "/openai/" in path.lower():
            return self.fix_openai_by_operation(path, method)

        # 3. Third priority: contains /v1/ → v1 format
        if "/v1/" in path.lower():
            return self.fix_v1_by_operation(path, method)

        # 4. Fourth priority: contains /chat/completions → chat feature
        if "/chat/completions" in path.lower():
            return "/v1/chat/completions", {"type": "v1_chat"}

        # 5. Default: pass through as is
        return path, None

    def is_already_correct_format(self, path: str) -> bool:
        """Check if it's already in the correct API format"""
        # Check if it's already in the correct endpoint format
        correct_patterns = [
            r"^/v1beta/models/[^/:]+:(generate|streamGenerate)Content$",  # Gemini native
            r"^/gemini/v1beta/models/[^/:]+:(generate|streamGenerate)Content$",  # Gemini with prefix
            r"^/v1beta/models$",  # Gemini model list
            r"^/gemini/v1beta/models$",  # Gemini with prefix model list
            r"^/v1/(chat/completions|models|embeddings|images/generations|audio/speech)$",  # v1 format
            r"^/openai/v1/(chat/completions|models|embeddings|images/generations|audio/speech)$",  # OpenAI format
            r"^/hf/v1/(chat/completions|models|embeddings|images/generations|audio/speech)$",  # HF format
            r"^/vertex-express/v1beta/models/[^/:]+:(generate|streamGenerate)Content$",  # Vertex Express Gemini format
            r"^/vertex-express/v1beta/models$",  # Vertex Express model list
            r"^/vertex-express/v1/(chat/completions|models|embeddings|images/generations)$",  # Vertex Express OpenAI format
        ]

        for pattern in correct_patterns:
            if re.match(pattern, path):
                return True

        return False

    def fix_gemini_by_operation(
        self, path: str, method: str, request: Request
    ) -> tuple:
        """Fix Gemini based on operation, considering endpoint preferences"""
        if method == "GET":
            return "/v1beta/models", {
                "role": "gemini_models",
            }

        # Extract model name
        try:
            model_name = self.extract_model_name(path, request)
        except ValueError:
            # Cannot extract model name, return original path without processing
            return path, None

        # Detect if it's a stream request
        is_stream = self.detect_stream_request(path, request)

        # Check for vertex-express preference
        if "/vertex-express/" in path.lower():
            if is_stream:
                target_url = (
                    f"/vertex-express/v1beta/models/{model_name}:streamGenerateContent"
                )
            else:
                target_url = (
                    f"/vertex-express/v1beta/models/{model_name}:generateContent"
                )

            fix_info = {
                "rule": (
                    "vertex_express_generate"
                    if not is_stream
                    else "vertex_express_stream"
                ),
                "preference": "vertex_express_format",
                "is_stream": is_stream,
                "model": model_name,
            }
        else:
            # Standard Gemini endpoint
            if is_stream:
                target_url = f"/v1beta/models/{model_name}:streamGenerateContent"
            else:
                target_url = f"/v1beta/models/{model_name}:generateContent"

            fix_info = {
                "rule": "gemini_generate" if not is_stream else "gemini_stream",
                "preference": "gemini_format",
                "is_stream": is_stream,
                "model": model_name,
            }

        return target_url, fix_info

    def fix_openai_by_operation(self, path: str, method: str) -> tuple:
        """Fix OpenAI format based on operation type"""
        if method == "POST":
            if "chat" in path.lower() or "completion" in path.lower():
                return "/openai/v1/chat/completions", {"type": "openai_chat"}
            elif "embedding" in path.lower():
                return "/openai/v1/embeddings", {"type": "openai_embeddings"}
            elif "image" in path.lower():
                return "/openai/v1/images/generations", {"type": "openai_images"}
            elif "audio" in path.lower():
                return "/openai/v1/audio/speech", {"type": "openai_audio"}
        elif method == "GET":
            if "model" in path.lower():
                return "/openai/v1/models", {"type": "openai_models"}

        return path, None

    def fix_v1_by_operation(self, path: str, method: str) -> tuple:
        """Fix v1 format based on operation type"""
        if method == "POST":
            if "chat" in path.lower() or "completion" in path.lower():
                return "/v1/chat/completions", {"type": "v1_chat"}
            elif "embedding" in path.lower():
                return "/v1/embeddings", {"type": "v1_embeddings"}
            elif "image" in path.lower():
                return "/v1/images/generations", {"type": "v1_images"}
            elif "audio" in path.lower():
                return "/v1/audio/speech", {"type": "v1_audio"}
        elif method == "GET":
            if "model" in path.lower():
                return "/v1/models", {"type": "v1_models"}

        return path, None

    def detect_stream_request(self, path: str, request: Request) -> bool:
        """Detect if it's a stream request"""
        # 1. Path contains 'stream' keyword
        if "stream" in path.lower():
            return True

        # 2. Query parameters
        if request.query_params.get("stream") == "true":
            return True

        return False

    def extract_model_name(self, path: str, request: Request) -> str:
        """Extract model name from the request to build the Gemini API URL"""
        # 1. Extract from request body
        try:
            if hasattr(request, "_body") and request._body:
                import json

                body = json.loads(request._body.decode())
                if "model" in body and body["model"]:
                    return body["model"]
        except Exception:
            pass

        # 2. Extract from query parameters
        model_param = request.query_params.get("model")
        if model_param:
            return model_param

        # 3. Extract from path (for paths that already contain the model name)
        match = re.search(r"/models/([^/:]+)", path, re.IGNORECASE)
        if match:
            return match.group(1)

        # 4. If model name cannot be extracted, raise an exception
        raise ValueError("Unable to extract model name from request")