from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.service.update.update_service import check_for_updates
from app.utils.helpers import get_current_version
from app.log.logger import get_update_logger

router = APIRouter(prefix="/api/version", tags=["Version"])
logger = get_update_logger()

class VersionInfo(BaseModel):
    current_version: str = Field(..., description="Current application version")
    latest_version: Optional[str] = Field(None, description="Latest available version")
    update_available: bool = Field(False, description="Whether an update is available")
    error_message: Optional[str] = Field(None, description="Error message that occurred while checking for updates")

@router.get("/check", response_model=VersionInfo, summary="Check for application updates")
async def get_version_info():
    """
    Check the current application version against the latest GitHub release version.
    """
    try:
        current_version = get_current_version()
        update_available, latest_version, error_message = await check_for_updates()

        logger.info(f"Version check API result: current={current_version}, latest={latest_version}, available={update_available}, error='{error_message}'")

        return VersionInfo(
            current_version=current_version,
            latest_version=latest_version,
            update_available=update_available,
            error_message=error_message
        )
    except Exception as e:
        logger.error(f"Error in /api/version/check endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error occurred while checking version information")
