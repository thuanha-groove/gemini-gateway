import uvicorn
from dotenv import load_dotenv

# Load .env file into environment variables before importing application configuration
load_dotenv()

from app.core.application import create_app
from app.log.logger import get_main_logger

app = create_app()

if __name__ == "__main__":
    logger = get_main_logger()
    logger.info("Starting application server...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
