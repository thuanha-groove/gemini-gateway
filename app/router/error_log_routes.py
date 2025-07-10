"""
Log routing module
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    Response,
    status,
)
from pydantic import BaseModel
from databases import Database

from app.core.security import verify_auth_token
from app.database.connection import get_db
from app.log.logger import get_log_routes_logger
from app.service.error_log import error_log_service

router = APIRouter(prefix="/api/logs", tags=["logs"])

logger = get_log_routes_logger()


class ErrorLogListItem(BaseModel):
    id: int
    gemini_key: Optional[str] = None
    error_type: Optional[str] = None
    error_code: Optional[int] = None
    model_name: Optional[str] = None
    request_time: Optional[datetime] = None


class ErrorLogListResponse(BaseModel):
    logs: List[ErrorLogListItem]
    total: int


@router.get("/errors", response_model=ErrorLogListResponse)
async def get_error_logs_api(
    request: Request,
    db: Database = Depends(get_db),
    limit: int = Query(10, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    key_search: Optional[str] = Query(
        None, description="Search term for Gemini key (partial match)"
    ),
    error_search: Optional[str] = Query(
        None, description="Search term for error type or log message"
    ),
    error_code_search: Optional[str] = Query(
        None, description="Search term for error code"
    ),
    start_date: Optional[datetime] = Query(
        None, description="Start datetime for filtering"
    ),
    end_date: Optional[datetime] = Query(
        None, description="End datetime for filtering"
    ),
    sort_by: str = Query(
        "id", description="Field to sort by (e.g., 'id', 'request_time')"
    ),
    sort_order: str = Query("desc", description="Sort order ('asc' or 'desc')"),
):
    """
    Get a list of error logs (returns error codes), supports filtering and sorting

    Args:
        request: request object
        db: The database connection.
        limit: limit number
        offset: offset
        key_search: key search
        error_search: error search (may search type or log content, determined by the DB layer)
        error_code_search: error code search
        start_date: start date
        end_date: end date
        sort_by: sort field
        sort_order: sort order

    Returns:
        ErrorLogListResponse: An object containing the list of logs (with error_code) and the total count.
    """
    auth_token = request.cookies.get("auth_token")
    if not auth_token or not verify_auth_token(auth_token):
        logger.warning("Unauthorized access attempt to error logs list")
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        result = await error_log_service.process_get_error_logs(
            db=db,
            limit=limit,
            offset=offset,
            key_search=key_search,
            error_search=error_search,
            error_code_search=error_code_search,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        logs_data = result["logs"]
        total_count = result["total"]

        validated_logs = [ErrorLogListItem(**log) for log in logs_data]
        return ErrorLogListResponse(logs=validated_logs, total=total_count)
    except Exception as e:
        logger.exception(f"Failed to get error logs list: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get error logs list: {str(e)}"
        )


class ErrorLogDetailResponse(BaseModel):
    id: int
    gemini_key: Optional[str] = None
    error_type: Optional[str] = None
    error_log: Optional[str] = None
    request_msg: Optional[str] = None
    model_name: Optional[str] = None
    request_time: Optional[datetime] = None


@router.get("/errors/{log_id}/details", response_model=ErrorLogDetailResponse)
async def get_error_log_detail_api(
    request: Request,
    db: Database = Depends(get_db),
    log_id: int = Path(..., ge=1),
):
    """
    Get detailed information of error logs based on log ID (including error_log and request_msg)
    """
    auth_token = request.cookies.get("auth_token")
    if not auth_token or not verify_auth_token(auth_token):
        logger.warning(
            f"Unauthorized access attempt to error log details for ID: {log_id}"
        )
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        log_details = await error_log_service.process_get_error_log_details(
            db=db, log_id=log_id
        )
        if not log_details:
            raise HTTPException(status_code=404, detail="Error log not found")

        return ErrorLogDetailResponse(**log_details)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Failed to get error log details for ID {log_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get error log details: {str(e)}"
        )


@router.delete("/errors", status_code=status.HTTP_204_NO_CONTENT)
async def delete_error_logs_bulk_api(
    request: Request,
    db: Database = Depends(get_db),
    payload: Dict[str, List[int]] = Body(...),
):
    """
    Batch delete error logs (asynchronous)
    """
    auth_token = request.cookies.get("auth_token")
    if not auth_token or not verify_auth_token(auth_token):
        logger.warning("Unauthorized access attempt to bulk delete error logs")
        raise HTTPException(status_code=401, detail="Not authenticated")

    log_ids = payload.get("ids")
    if not log_ids:
        raise HTTPException(status_code=400, detail="No log IDs provided for deletion.")

    try:
        deleted_count = await error_log_service.process_delete_error_logs_by_ids(
            db=db, log_ids=log_ids
        )
        # Note: Async function returns the number of attempted deletions, may not be exact
        logger.info(
            f"Attempted bulk deletion for {deleted_count} error logs with IDs: {log_ids}"
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.exception(f"Error bulk deleting error logs with IDs {log_ids}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error during bulk deletion"
        )


@router.delete("/errors/all", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_error_logs_api(
    request: Request, db: Database = Depends(get_db)
):
    """
    Delete all error logs (asynchronous)
    """
    auth_token = request.cookies.get("auth_token")
    if not auth_token or not verify_auth_token(auth_token):
        logger.warning("Unauthorized access attempt to delete all error logs")
        raise HTTPException(status_code=401, detail="Not authenticated")
 
    try:
        deleted_count = await error_log_service.process_delete_all_error_logs(db=db)
        logger.info(f"Successfully deleted all {deleted_count} error logs.")
        # No body needed for 204 response
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.exception(f"Error deleting all error logs: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error during deletion of all logs"
        )
 
 
@router.delete("/errors/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_error_log_api(
    request: Request,
    db: Database = Depends(get_db),
    log_id: int = Path(..., ge=1),
):
    """
    Delete a single error log (asynchronous)
    """
    auth_token = request.cookies.get("auth_token")
    if not auth_token or not verify_auth_token(auth_token):
        logger.warning(f"Unauthorized access attempt to delete error log ID: {log_id}")
        raise HTTPException(status_code=401, detail="Not authenticated")
 
    try:
        success = await error_log_service.process_delete_error_log_by_id(
            db=db, log_id=log_id
        )
        if not success:
            # Service layer now returns False when not found, we convert it to 404 here
            raise HTTPException(
                status_code=404, detail=f"Error log with ID {log_id} not found"
            )
        logger.info(f"Successfully deleted error log with ID: {log_id}")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Error deleting error log with ID {log_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error during deletion"
        )
