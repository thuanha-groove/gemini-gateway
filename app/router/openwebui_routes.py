from fastapi import APIRouter, Request, Response
from app.service.openai_compatiable.openai_compatiable_service import OpenAICompatiableService

router = APIRouter()

@router.post("/hf/v1/chat/completions")
async def hf_chat_completions(request: Request):
    """
    Handle chat completions for Hugging Face.
    """
    openai_service = OpenAICompatiableService()
    return await openai_service.chat_completions(request)

@router.get("/hf/v1/models")
async def hf_list_models(request: Request):
    """
    Handle list models for Hugging Face.
    """
    openai_service = OpenAICompatiableService()
    return await openai_service.list_models(request)
