from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from copy import deepcopy
import asyncio
from app.config.config import settings
from app.log.logger import get_gemini_logger
from app.core.security import SecurityService
from app.domain.gemini_models import GeminiContent, GeminiRequest, ResetSelectedKeysRequest, VerifySelectedKeysRequest
from app.service.chat.gemini_chat_service import GeminiChatService
from app.service.key.key_manager import KeyManager, get_key_manager_instance
from app.service.model.model_service import ModelService
from app.handler.retry_handler import RetryHandler
from app.handler.error_handler import handle_route_errors
from app.core.constants import API_VERSION

router = APIRouter(prefix=f"/gemini/{API_VERSION}")
router_v1beta = APIRouter(prefix=f"/{API_VERSION}")
logger = get_gemini_logger()

security_service = SecurityService()
model_service = ModelService()


async def get_key_manager():
    """Get key manager instance"""
    return await get_key_manager_instance()


async def get_next_working_key(key_manager: KeyManager = Depends(get_key_manager)):
    """Get the next available API key"""
    return await key_manager.get_next_working_key()


async def get_chat_service(key_manager: KeyManager = Depends(get_key_manager)):
    """Get Gemini chat service instance"""
    return GeminiChatService(settings.BASE_URL, key_manager)


@router.get("/models")
@router_v1beta.get("/models")
async def list_models(
    _=Depends(security_service.verify_key_or_goog_api_key),
    key_manager: KeyManager = Depends(get_key_manager)
):
    """Get a list of available Gemini models and add derivative models (search, image, non-thinking) based on configuration."""
    operation_name = "list_gemini_models"
    logger.info("-" * 50 + operation_name + "-" * 50)
    logger.info("Handling Gemini models list request")

    try:
        api_key = await key_manager.get_first_valid_key()
        if not api_key:
            raise HTTPException(status_code=503, detail="No valid API keys available to fetch models.")
        logger.info(f"Using API key: {api_key}")

        models_data = await model_service.get_gemini_models(api_key)
        if not models_data or "models" not in models_data:
            raise HTTPException(status_code=500, detail="Failed to fetch base models list.")

        models_json = deepcopy(models_data)
        model_mapping = {x.get("name", "").split("/", maxsplit=1)[-1]: x for x in models_json.get("models", [])}

        def add_derived_model(base_name, suffix, display_suffix):
            model = model_mapping.get(base_name)
            if not model:
                logger.warning(f"Base model '{base_name}' not found for derived model '{suffix}'.")
                return
            item = deepcopy(model)
            item["name"] = f"models/{base_name}{suffix}"
            display_name = f'{item.get("displayName", base_name)}{display_suffix}'
            item["displayName"] = display_name
            item["description"] = display_name
            models_json["models"].append(item)

        if settings.SEARCH_MODELS:
            for name in settings.SEARCH_MODELS:
                add_derived_model(name, "-search", " For Search")
        if settings.IMAGE_MODELS:
            for name in settings.IMAGE_MODELS:
                 add_derived_model(name, "-image", " For Image")
        if settings.THINKING_MODELS:
            for name in settings.THINKING_MODELS:
                add_derived_model(name, "-non-thinking", " Non Thinking")

        logger.info("Gemini models list request successful")
        return models_json
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error getting Gemini models list: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error while fetching Gemini models list"
        ) from e


@router.post("/models/{model_name}:generateContent")
@router_v1beta.post("/models/{model_name}:generateContent")
@RetryHandler(key_arg="api_key")
async def generate_content(
    model_name: str,
    request: GeminiRequest,
    _=Depends(security_service.verify_key_or_goog_api_key),
    api_key: str = Depends(get_next_working_key),
    key_manager: KeyManager = Depends(get_key_manager),
    chat_service: GeminiChatService = Depends(get_chat_service)
):
    """Handles Gemini non-streaming content generation requests."""
    operation_name = "gemini_generate_content"
    async with handle_route_errors(logger, operation_name, failure_message="Content generation failed"):
        logger.info(f"Handling Gemini content generation request for model: {model_name}")
        logger.debug(f"Request: \n{request.model_dump_json(indent=2)}")
        logger.info(f"Using API key: {api_key}")

        if not await model_service.check_model_support(model_name):
            raise HTTPException(status_code=400, detail=f"Model {model_name} is not supported")

        response = await chat_service.generate_content(
            model=model_name,
            request=request,
            api_key=api_key
        )
        return response


@router.post("/models/{model_name}:streamGenerateContent")
@router_v1beta.post("/models/{model_name}:streamGenerateContent")
@RetryHandler(key_arg="api_key")
async def stream_generate_content(
    model_name: str,
    request: GeminiRequest,
    _=Depends(security_service.verify_key_or_goog_api_key),
    api_key: str = Depends(get_next_working_key),
    key_manager: KeyManager = Depends(get_key_manager),
    chat_service: GeminiChatService = Depends(get_chat_service)
):
    """Handles Gemini streaming content generation requests."""
    operation_name = "gemini_stream_generate_content"
    async with handle_route_errors(logger, operation_name, failure_message="Streaming request initiation failed"):
        logger.info(f"Handling Gemini streaming content generation for model: {model_name}")
        logger.debug(f"Request: \n{request.model_dump_json(indent=2)}")
        logger.info(f"Using API key: {api_key}")

        if not await model_service.check_model_support(model_name):
            raise HTTPException(status_code=400, detail=f"Model {model_name} is not supported")

        response_stream = chat_service.stream_generate_content(
            model=model_name,
            request=request,
            api_key=api_key
        )
        return StreamingResponse(response_stream, media_type="text/event-stream")


@router.post("/models/{model_name}:countTokens")
@router_v1beta.post("/models/{model_name}:countTokens")
@RetryHandler(key_arg="api_key")
async def count_tokens(
    model_name: str,
    request: GeminiRequest,
    _=Depends(security_service.verify_key_or_goog_api_key),
    api_key: str = Depends(get_next_working_key),
    key_manager: KeyManager = Depends(get_key_manager),
    chat_service: GeminiChatService = Depends(get_chat_service)
):
    """Handles Gemini token counting requests."""
    operation_name = "gemini_count_tokens"
    async with handle_route_errors(logger, operation_name, failure_message="Token counting failed"):
        logger.info(f"Handling Gemini token count request for model: {model_name}")
        logger.debug(f"Request: \n{request.model_dump_json(indent=2)}")
        logger.info(f"Using API key: {api_key}")

        if not await model_service.check_model_support(model_name):
            raise HTTPException(status_code=400, detail=f"Model {model_name} is not supported")

        response = await chat_service.count_tokens(
            model=model_name,
            request=request,
            api_key=api_key
        )
        return response


@router.post("/reset-all-fail-counts")
async def reset_all_key_fail_counts(key_type: str = None, key_manager: KeyManager = Depends(get_key_manager)):
    """Batch reset the failure count of Gemini API keys, optionally resetting only valid or invalid keys"""
    logger.info("-" * 50 + "reset_all_gemini_key_fail_counts" + "-" * 50)
    logger.info(f"Received reset request with key_type: {key_type}")
    
    try:
        # Get categorized keys
        keys_by_status = await key_manager.get_keys_by_status()
        valid_keys = keys_by_status.get("valid_keys", {})
        invalid_keys = keys_by_status.get("invalid_keys", {})
        
        # Select keys to reset based on type
        keys_to_reset = []
        if key_type == "valid":
            keys_to_reset = list(valid_keys.keys())
            logger.info(f"Resetting only valid keys, count: {len(keys_to_reset)}")
        elif key_type == "invalid":
            keys_to_reset = list(invalid_keys.keys())
            logger.info(f"Resetting only invalid keys, count: {len(keys_to_reset)}")
        else:
            # Reset all keys
            await key_manager.reset_failure_counts()
            return JSONResponse({"success": True, "message": "Failure count for all keys has been reset"})
        
        # Batch reset specified types of keys
        for key in keys_to_reset:
            await key_manager.reset_key_failure_count(key)
        
        return JSONResponse({
            "success": True,
            "message": f"Failure count for {key_type} keys has been reset",
            "reset_count": len(keys_to_reset)
        })
    except Exception as e:
        logger.error(f"Failed to reset key failure counts: {str(e)}")
        return JSONResponse({"success": False, "message": f"Batch reset failed: {str(e)}"}, status_code=500)
    
    
@router.post("/reset-selected-fail-counts")
async def reset_selected_key_fail_counts(
    request: ResetSelectedKeysRequest,
    key_manager: KeyManager = Depends(get_key_manager)
):
    """Batch reset the failure count of selected Gemini API keys"""
    logger.info("-" * 50 + "reset_selected_gemini_key_fail_counts" + "-" * 50)
    keys_to_reset = request.keys
    key_type = request.key_type
    logger.info(f"Received reset request for {len(keys_to_reset)} selected {key_type} keys.")

    if not keys_to_reset:
        return JSONResponse({"success": False, "message": "No keys provided to reset"}, status_code=400)

    reset_count = 0
    errors = []

    try:
        for key in keys_to_reset:
            try:
                result = await key_manager.reset_key_failure_count(key)
                if result:
                    reset_count += 1
                else:
                    logger.warning(f"Key not found during selective reset: {key}")
            except Exception as key_error:
                logger.error(f"Error resetting key {key}: {str(key_error)}")
                errors.append(f"Key {key}: {str(key_error)}")

        if errors:
             error_message = f"Batch reset completed, but errors occurred: {'; '.join(errors)}"
             final_success = reset_count > 0
             status_code = 207 if final_success and errors else 500
             return JSONResponse({
                 "success": final_success,
                 "message": error_message,
                 "reset_count": reset_count
             }, status_code=status_code)

        return JSONResponse({
            "success": True,
            "message": f"Successfully reset the failure count of {reset_count} selected {key_type} keys",
            "reset_count": reset_count
        })
    except Exception as e:
        logger.error(f"Failed to process reset selected key failure counts request: {str(e)}")
        return JSONResponse({"success": False, "message": f"Batch reset processing failed: {str(e)}"}, status_code=500)


@router.post("/reset-fail-count/{api_key}")
async def reset_key_fail_count(api_key: str, key_manager: KeyManager = Depends(get_key_manager)):
    """Reset the failure count of the specified Gemini API key"""
    logger.info("-" * 50 + "reset_gemini_key_fail_count" + "-" * 50)
    logger.info(f"Resetting failure count for API key: {api_key}")
    
    try:
        result = await key_manager.reset_key_failure_count(api_key)
        if result:
            return JSONResponse({"success": True, "message": "Failure count has been reset"})
        return JSONResponse({"success": False, "message": "Specified key not found"}, status_code=404)
    except Exception as e:
        logger.error(f"Failed to reset key failure count: {str(e)}")
        return JSONResponse({"success": False, "message": f"Reset failed: {str(e)}"}, status_code=500)


@router.post("/verify-key/{api_key}")
async def verify_key(api_key: str, chat_service: GeminiChatService = Depends(get_chat_service), key_manager: KeyManager = Depends(get_key_manager)):
    """Verify the validity of the Gemini API key"""
    logger.info("-" * 50 + "verify_gemini_key" + "-" * 50)
    logger.info("Verifying API key validity")
    
    try:
        gemini_request = GeminiRequest(
            contents=[
                GeminiContent(
                    role="user",
                    parts=[{"text": "hi"}],
                )
            ],
            generation_config={"temperature": 0.7, "top_p": 1.0, "max_output_tokens": 10}
        )
        
        response = await chat_service.generate_content(
            settings.TEST_MODEL,
            gemini_request,
            api_key
        )
        
        if response:
            return JSONResponse({"status": "valid"})        
    except Exception as e:
        logger.error(f"Key verification failed: {str(e)}")
        
        async with key_manager.failure_count_lock:
            if api_key in key_manager.key_failure_counts:
                key_manager.key_failure_counts[api_key] += 1
                logger.warning(f"Verification exception for key: {api_key}, incrementing failure count")
        
        return JSONResponse({"status": "invalid", "error": str(e)})


@router.post("/verify-selected-keys")
async def verify_selected_keys(
    request: VerifySelectedKeysRequest,
    chat_service: GeminiChatService = Depends(get_chat_service),
    key_manager: KeyManager = Depends(get_key_manager)
):
    """Batch verify the validity of selected Gemini API keys"""
    logger.info("-" * 50 + "verify_selected_gemini_keys" + "-" * 50)
    keys_to_verify = request.keys
    logger.info(f"Received verification request for {len(keys_to_verify)} selected keys.")

    if not keys_to_verify:
        return JSONResponse({"success": False, "message": "No keys provided for verification"}, status_code=400)

    successful_keys = []
    failed_keys = {}

    async def _verify_single_key(api_key: str):
        """Internal function to verify a single key and handle exceptions"""
        nonlocal successful_keys, failed_keys
        try:
            gemini_request = GeminiRequest(
                contents=[GeminiContent(role="user", parts=[{"text": "hi"}])],
                generation_config={"temperature": 0.7, "top_p": 1.0, "max_output_tokens": 10}
            )
            await chat_service.generate_content(
                settings.TEST_MODEL,
                gemini_request,
                api_key
            )
            successful_keys.append(api_key)
            return api_key, "valid", None
        except Exception as e:
            error_message = str(e)
            logger.warning(f"Key verification failed for {api_key}: {error_message}")
            async with key_manager.failure_count_lock:
                if api_key in key_manager.key_failure_counts:
                    key_manager.key_failure_counts[api_key] += 1
                    logger.warning(f"Bulk verification exception for key: {api_key}, incrementing failure count")
                else:
                     key_manager.key_failure_counts[api_key] = 1
                     logger.warning(f"Bulk verification exception for key: {api_key}, initializing failure count to 1")
            failed_keys[api_key] = error_message
            return api_key, "invalid", error_message

    tasks = [_verify_single_key(key) for key in keys_to_verify]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            logger.error(f"An unexpected error occurred during bulk verification task: {result}")
        elif result:
             if not isinstance(result, Exception) and result:
                 key, status, error = result
             elif isinstance(result, Exception):
                 logger.error(f"Task execution error during bulk verification: {result}")

    valid_count = len(successful_keys)
    invalid_count = len(failed_keys)
    logger.info(f"Bulk verification finished. Valid: {valid_count}, Invalid: {invalid_count}")

    if failed_keys:
        message = f"Batch verification complete. Success: {valid_count}, Failure: {invalid_count}."
        return JSONResponse({
            "success": True,
            "message": message,
            "successful_keys": successful_keys,
            "failed_keys": failed_keys,
            "valid_count": valid_count,
            "invalid_count": invalid_count
        })
    else:
        message = f"Batch verification successfully completed. All {valid_count} keys are valid."
        return JSONResponse({
            "success": True,
            "message": message,
            "successful_keys": successful_keys,
            "failed_keys": {},
            "valid_count": valid_count,
            "invalid_count": 0
        })
