import httpx
from packaging import version
from typing import Optional, Tuple

from app.config.config import settings
from app.log.logger import get_update_logger

logger = get_update_logger()

VERSION_FILE_PATH = "VERSION"

async def check_for_updates() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check for application updates by comparing the current version with the latest GitHub release.

    Returns:
        Tuple[bool, Optional[str], Optional[str]]: A tuple containing:
            - bool: True if an update is available, otherwise False.
            - Optional[str]: The latest version string if an update is available, otherwise None.
            - Optional[str]: An error message if the check fails, otherwise None.
    """
    try:
        with open(VERSION_FILE_PATH, 'r', encoding='utf-8') as f:
            current_v = f.read().strip()
        if not current_v:
            logger.error(f"VERSION file ('{VERSION_FILE_PATH}') is empty.")
            return False, None, f"VERSION file ('{VERSION_FILE_PATH}') is empty."
    except FileNotFoundError:
        logger.error(f"VERSION file not found at '{VERSION_FILE_PATH}'. Make sure it exists in the project root.")
        return False, None, f"VERSION file not found at '{VERSION_FILE_PATH}'."
    except IOError as e:
        logger.error(f"Error reading VERSION file ('{VERSION_FILE_PATH}'): {e}")
        return False, None, f"Error reading VERSION file ('{VERSION_FILE_PATH}')."

    logger.info(f"Current application version (from {VERSION_FILE_PATH}): {current_v}")

    if not settings.GITHUB_REPO_OWNER or not settings.GITHUB_REPO_NAME or \
       settings.GITHUB_REPO_OWNER == "your_owner" or settings.GITHUB_REPO_NAME == "your_repo":
        logger.warning("GitHub repository owner/name not configured in settings. Skipping update check.")
        return False, None, "Update check skipped: Repository not configured in settings."

    github_api_url = f"https://api.github.com/repos/{settings.GITHUB_REPO_OWNER}/{settings.GITHUB_REPO_NAME}/releases/latest"
    logger.debug(f"Checking for updates at URL: {github_api_url}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": f"{settings.GITHUB_REPO_NAME}-UpdateChecker/1.0"
            }
            response = await client.get(github_api_url, headers=headers)
            response.raise_for_status()

            latest_release = response.json()
            latest_v_str = latest_release.get("tag_name")

            if not latest_v_str:
                logger.warning("Could not find 'tag_name' in the latest GitHub release response.")
                return False, None, "Could not parse the latest version from GitHub."

            if latest_v_str.startswith('v'):
                latest_v_str = latest_v_str[1:]

            logger.info(f"Latest version found on GitHub: {latest_v_str}")

            # Compare versions
            current_version = version.parse(current_v)
            latest_version = version.parse(latest_v_str)

            if latest_version > current_version:
                logger.info(f"Update available: {current_v} -> {latest_v_str}")
                return True, latest_v_str, None
            else:
                logger.info("The application is up to date.")
                return False, None, None

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred while checking for updates: {e.response.status_code} - {e.response.text}")
        # Avoid showing detailed error text to the user
        error_msg = f"Failed to get update information (HTTP {e.response.status_code})."
        if e.response.status_code == 404:
            error_msg += " Please check if the repository name is correct or if the repository has a release version."
        elif e.response.status_code == 403:
             error_msg += " API rate limit or permission issue."
        return False, None, error_msg
    except httpx.RequestError as e:
        logger.error(f"Network error occurred while checking for updates: {e}")
        return False, None, "A network error occurred during the update check."
    except version.InvalidVersion:
        latest_v_str_for_log = latest_v_str if 'latest_v_str' in locals() else 'N/A'
        logger.error(f"Invalid version format found. Current (from {VERSION_FILE_PATH}): '{current_v}', Latest: '{latest_v_str_for_log}'")
        return False, None, "An invalid version format was encountered."
    except Exception as e:
        logger.error(f"An unexpected error occurred during the update check: {e}", exc_info=True)
        return False, None, "An unexpected error occurred."
