"""
Constants definition module.
"""

# API related constants
API_VERSION = "v1beta"
DEFAULT_TIMEOUT = 300  # seconds
MAX_RETRIES = 3  # Maximum retry attempts

# Model related constants
SUPPORTED_ROLES = ["user", "model", "system"]
DEFAULT_MODEL = "gemini-1.5-flash"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 8192
DEFAULT_TOP_P = 0.9
DEFAULT_TOP_K = 40
DEFAULT_FILTER_MODELS = [
        "gemini-1.0-pro-vision-latest", 
        "gemini-pro-vision", 
        "chat-bison-001", 
        "text-bison-001", 
        "embedding-gecko-001"
    ]
DEFAULT_CREATE_IMAGE_MODEL = "imagen-3.0-generate-002"

# Image generation related constants
VALID_IMAGE_RATIOS = ["1:1", "3:4", "4:3", "9:16", "16:9"]

# Upload providers
UPLOAD_PROVIDERS = ["smms", "picgo", "cloudflare_imgbed"]
DEFAULT_UPLOAD_PROVIDER = "smms"

# Stream output related constants
DEFAULT_STREAM_MIN_DELAY = 0.016
DEFAULT_STREAM_MAX_DELAY = 0.024
DEFAULT_STREAM_SHORT_TEXT_THRESHOLD = 10
DEFAULT_STREAM_LONG_TEXT_THRESHOLD = 50
DEFAULT_STREAM_CHUNK_SIZE = 5

# Regular expression patterns
IMAGE_URL_PATTERN = r'!\[(.*?)\]\((.*?)\)'
DATA_URL_PATTERN = r'data:([^;]+);base64,(.+)'

# Audio/Video Settings
SUPPORTED_AUDIO_FORMATS = ["wav", "mp3", "flac", "ogg"]
SUPPORTED_VIDEO_FORMATS = ["mp4", "mov", "avi", "webm"]
MAX_AUDIO_SIZE_BYTES = 50 * 1024 * 1024  # Example: 50MB limit for Base64 payload
MAX_VIDEO_SIZE_BYTES = 200 * 1024 * 1024 # Example: 200MB limit

# Optional: Define MIME type mappings if needed, or handle directly in converter
AUDIO_FORMAT_TO_MIMETYPE = {
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "flac": "audio/flac",
    "ogg": "audio/ogg",
}

VIDEO_FORMAT_TO_MIMETYPE = {
    "mp4": "video/mp4",
    "mov": "video/quicktime",
    "avi": "video/x-msvideo",
    "webm": "video/webm",
}

GEMINI_2_FLASH_EXP_SAFETY_SETTINGS = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "OFF"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "OFF"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "OFF"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "OFF"},
            {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "OFF"},
        ]

DEFAULT_SAFETY_SETTINGS = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "OFF"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "OFF"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "OFF"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "OFF"},
        {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "BLOCK_NONE"},
    ]