"""
Database services module
"""
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from sqlalchemy import func, desc, asc, select, insert, update, delete
import json
from app.database.connection import database
from app.database.models import Settings, ErrorLog, RequestLog
from app.log.logger import get_database_logger

logger = get_database_logger()


async def get_all_settings() -> List[Dict[str, Any]]:
    """
    Get all settings.
    
    Returns:
        List[Dict[str, Any]]: A list of settings.
    """
    try:
        query = select(Settings)
        result = await database.fetch_all(query)
        return [dict(row) for row in result]
    except Exception as e:
        logger.error(f"Failed to get all settings: {str(e)}")
        raise


async def get_setting(key: str) -> Optional[Dict[str, Any]]:
    """
    Get the setting for a specified key.
    
    Args:
        key: The key name of the setting.
    
    Returns:
        Optional[Dict[str, Any]]: The setting information, or None if it does not exist.
    """
    try:
        query = select(Settings).where(Settings.key == key)
        result = await database.fetch_one(query)
        return dict(result) if result else None
    except Exception as e:
        logger.error(f"Failed to get setting {key}: {str(e)}")
        raise


async def update_setting(key: str, value: str, description: Optional[str] = None) -> bool:
    """
    Update a setting.
    
    Args:
        key: The key name of the setting.
        value: The value of the setting.
        description: The description of the setting.
    
    Returns:
        bool: True if the update was successful, otherwise False.
    """
    try:
        # Check if the setting exists
        setting = await get_setting(key)
        
        if setting:
            # Update the setting
            query = (
                update(Settings)
                .where(Settings.key == key)
                .values(
                    value=value,
                    description=description if description else setting["description"],
                    updated_at=datetime.now()
                )
            )
            await database.execute(query)
            logger.info(f"Updated setting: {key}")
            return True
        else:
            # Insert the setting
            query = (
                insert(Settings)
                .values(
                    key=key,
                    value=value,
                    description=description,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            )
            await database.execute(query)
            logger.info(f"Inserted setting: {key}")
            return True
    except Exception as e:
        logger.error(f"Failed to update setting {key}: {str(e)}")
        return False


async def add_error_log(
    gemini_key: Optional[str] = None,
    model_name: Optional[str] = None,
    error_type: Optional[str] = None,
    error_log: Optional[str] = None,
    error_code: Optional[int] = None,
    request_msg: Optional[Union[Dict[str, Any], str]] = None
) -> bool:
    """
    Add an error log.
    
    Args:
        gemini_key: The Gemini API key.
        error_log: The error log message.
        error_code: The error code (e.g., HTTP status code).
        request_msg: The request message.
    
    Returns:
        bool: True if the addition was successful, otherwise False.
    """
    try:
        # If request_msg is a dictionary, convert it to a JSON string
        if isinstance(request_msg, dict):
            request_msg_json = request_msg
        elif isinstance(request_msg, str):
            try:
                request_msg_json = json.loads(request_msg)
            except json.JSONDecodeError:
                request_msg_json = {"message": request_msg}
        else:
            request_msg_json = None
        
        # Insert the error log
        query = (
            insert(ErrorLog)
            .values(
                gemini_key=gemini_key,
                error_type=error_type,
                error_log=error_log,
                model_name=model_name,
                error_code=error_code,
                request_msg=request_msg_json,
                request_time=datetime.now()
            )
        )
        await database.execute(query)
        logger.info(f"Added error log for key: {gemini_key}")
        return True
    except Exception as e:
        logger.error(f"Failed to add error log: {str(e)}")
        return False


async def get_error_logs(
    limit: int = 20,
    offset: int = 0,
    key_search: Optional[str] = None,
    error_search: Optional[str] = None,
    error_code_search: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    sort_by: str = 'id',
    sort_order: str = 'desc'
) -> List[Dict[str, Any]]:
    """
    Get error logs, supporting search, date filtering, and sorting.

    Args:
        limit (int): The number of records to return.
        offset (int): The offset for pagination.
        key_search (Optional[str]): Search term for Gemini key (fuzzy match).
        error_search (Optional[str]): Search term for error type or log content (fuzzy match).
        error_code_search (Optional[str]): Search term for error code (exact match).
        start_date (Optional[datetime]): Start datetime for filtering.
        end_date (Optional[datetime]): End datetime for filtering.
        sort_by (str): The field to sort by (e.g., 'id', 'request_time').
        sort_order (str): The sort order ('asc' or 'desc').

    Returns:
        List[Dict[str, Any]]: A list of error logs.
    """
    try:
        query = select(
            ErrorLog.id,
            ErrorLog.gemini_key,
            ErrorLog.model_name,
            ErrorLog.error_type,
            ErrorLog.error_log,
            ErrorLog.error_code,
            ErrorLog.request_time
        )
        
        if key_search:
            query = query.where(ErrorLog.gemini_key.ilike(f"%{key_search}%"))
        if error_search:
            query = query.where(
                (ErrorLog.error_type.ilike(f"%{error_search}%")) |
                (ErrorLog.error_log.ilike(f"%{error_search}%"))
            )
        if start_date:
            query = query.where(ErrorLog.request_time >= start_date)
        if end_date:
            query = query.where(ErrorLog.request_time < end_date)
        if error_code_search:
            try:
                error_code_int = int(error_code_search)
                query = query.where(ErrorLog.error_code == error_code_int)
            except ValueError:
                logger.warning(f"Invalid format for error_code_search: '{error_code_search}'. Expected an integer. Skipping error code filter.")

        sort_column = getattr(ErrorLog, sort_by, ErrorLog.id)
        if sort_order.lower() == 'asc':
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        query = query.limit(limit).offset(offset)

        result = await database.fetch_all(query)
        return [dict(row) for row in result]
    except Exception as e:
        logger.exception(f"Failed to get error logs with filters: {str(e)}")
        raise


async def get_error_logs_count(
    key_search: Optional[str] = None,
    error_search: Optional[str] = None,
    error_code_search: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> int:
    """
    Get the total count of error logs that meet the criteria.

    Args:
        key_search (Optional[str]): Search term for Gemini key (fuzzy match).
        error_search (Optional[str]): Search term for error type or log content (fuzzy match).
        error_code_search (Optional[str]): Search term for error code (exact match).
        start_date (Optional[datetime]): Start datetime for filtering.
        end_date (Optional[datetime]): End datetime for filtering.

    Returns:
        int: The total number of logs.
    """
    try:
        query = select(func.count()).select_from(ErrorLog)

        if key_search:
            query = query.where(ErrorLog.gemini_key.ilike(f"%{key_search}%"))
        if error_search:
            query = query.where(
                (ErrorLog.error_type.ilike(f"%{error_search}%")) |
                (ErrorLog.error_log.ilike(f"%{error_search}%"))
            )
        if start_date:
            query = query.where(ErrorLog.request_time >= start_date)
        if end_date:
            query = query.where(ErrorLog.request_time < end_date)
        if error_code_search:
            try:
                error_code_int = int(error_code_search)
                query = query.where(ErrorLog.error_code == error_code_int)
            except ValueError:
                logger.warning(f"Invalid format for error_code_search in count: '{error_code_search}'. Expected an integer. Skipping error code filter.")


        count_result = await database.fetch_one(query)
        return count_result[0] if count_result else 0
    except Exception as e:
        logger.exception(f"Failed to count error logs with filters: {str(e)}")
        raise


# New function: get details of a single error log
async def get_error_log_details(log_id: int) -> Optional[Dict[str, Any]]:
    """
    Get detailed information of a single error log by ID.

    Args:
        log_id (int): The ID of the error log.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing the log details, or None if not found.
    """
    try:
        query = select(ErrorLog).where(ErrorLog.id == log_id)
        result = await database.fetch_one(query)
        if result:
            # Convert request_msg (JSONB) to a string for returning in the API
            log_dict = dict(result)
            if 'request_msg' in log_dict and log_dict['request_msg'] is not None:
                # Ensure it can handle None or non-JSON data
                try:
                    log_dict['request_msg'] = json.dumps(log_dict['request_msg'], ensure_ascii=False, indent=2)
                except TypeError:
                    log_dict['request_msg'] = str(log_dict['request_msg'])
            return log_dict
        else:
            return None
    except Exception as e:
        logger.exception(f"Failed to get error log details for ID {log_id}: {str(e)}")
        raise


async def delete_error_logs_by_ids(log_ids: List[int]) -> int:
    """
    Bulk delete error logs by a list of IDs (asynchronous).

    Args:
        log_ids: A list of error log IDs to delete.

    Returns:
        int: The number of logs actually deleted.
    """
    if not log_ids:
        return 0
    try:
        # Use databases to execute the deletion
        query = delete(ErrorLog).where(ErrorLog.id.in_(log_ids))
        # execute returns the number of affected rows, but the databases library's execute doesn't directly return rowcount
        # We would need to query for existence first, or rely on database constraints/triggers (if applicable)
        # Or, we can execute the deletion and assume success unless an exception is thrown
        # For simplicity, we execute the deletion and log it, without precisely returning the number of deletions
        # If a precise count is needed, we would need to run SELECT COUNT(*) first
        await database.execute(query)
        # Note: databases' execute does not return rowcount, so we can't directly return the number of deletions
        # Return the length of log_ids as the number of attempted deletions, or 0/1 to indicate the operation was attempted
        logger.info(f"Attempted bulk deletion for error logs with IDs: {log_ids}")
        return len(log_ids) # Return the number of attempted deletions
    except Exception as e:
        # Database connection or execution error
        logger.error(f"Error during bulk deletion of error logs {log_ids}: {e}", exc_info=True)
        raise

async def delete_error_log_by_id(log_id: int) -> bool:
    """
    Delete a single error log by ID (asynchronous).

    Args:
        log_id: The ID of the error log to delete.

    Returns:
        bool: True if successfully deleted, otherwise False.
    """
    try:
        # Check for existence first (optional, but more explicit)
        check_query = select(ErrorLog.id).where(ErrorLog.id == log_id)
        exists = await database.fetch_one(check_query)

        if not exists:
            logger.warning(f"Attempted to delete non-existent error log with ID: {log_id}")
            return False

        # Execute deletion
        delete_query = delete(ErrorLog).where(ErrorLog.id == log_id)
        await database.execute(delete_query)
        logger.info(f"Successfully deleted error log with ID: {log_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting error log with ID {log_id}: {e}", exc_info=True)
        raise
 
 
async def delete_all_error_logs() -> int:
    """
    Deletes all error log entries.
 
    Returns:
        int: The number of error logs deleted.
    """
    try:
        # 1. Get the total count before deletion
        count_query = select(func.count()).select_from(ErrorLog)
        total_to_delete = await database.fetch_val(count_query)
 
        if total_to_delete == 0:
            logger.info("No error logs found to delete.")
            return 0
 
        # 2. Execute the deletion
        delete_query = delete(ErrorLog)
        await database.execute(delete_query)
        
        logger.info(f"Successfully deleted all {total_to_delete} error logs.")
        return total_to_delete
    except Exception as e:
        logger.error(f"Failed to delete all error logs: {str(e)}", exc_info=True)
        raise
 
 
# New function: add a request log
async def add_request_log(
    model_name: Optional[str],
    api_key: Optional[str],
    is_success: bool,
    status_code: Optional[int] = None,
    latency_ms: Optional[int] = None,
    request_time: Optional[datetime] = None
) -> bool:
    """
    Add an API request log.

    Args:
        model_name: The name of the model.
        api_key: The API key used.
        is_success: Whether the request was successful.
        status_code: The API response status code.
        latency_ms: The request latency in milliseconds.
        request_time: The time the request occurred (if None, the current time is used).

    Returns:
        bool: True if the addition was successful, otherwise False.
    """
    try:
        log_time = request_time if request_time else datetime.now()

        query = insert(RequestLog).values(
            request_time=log_time,
            model_name=model_name,
            api_key=api_key,
            is_success=is_success,
            status_code=status_code,
            latency_ms=latency_ms
        )
        await database.execute(query)
        return True
    except Exception as e:
        logger.error(f"Failed to add request log: {str(e)}")
        return False