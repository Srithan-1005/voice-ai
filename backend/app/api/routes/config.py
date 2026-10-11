from fastapi import APIRouter
from app.core.config import settings
from app.schemas.api import UpdateConfigRequest

router = APIRouter(prefix="/api/config", tags=["Configuration"])

@router.get("")
def get_config():
    """Returns safe, non-sensitive configuration."""
    return settings.get_safe_config()

@router.put("")
def update_config(req: UpdateConfigRequest):
    """Updates dynamic agent variables and settings."""
    if req.company_name is not None:
        settings.COMPANY_NAME = req.company_name
    if req.agent_name is not None:
        settings.AGENT_NAME = req.agent_name
    if req.agent_gender is not None:
        settings.AGENT_GENDER = req.agent_gender
    if req.default_customer_name is not None:
        settings.DEFAULT_CUSTOMER_NAME = req.default_customer_name
    if req.default_language is not None:
        settings.DEFAULT_LANGUAGE = req.default_language
    if req.voice_platform is not None:
        settings.VOICE_PLATFORM = req.voice_platform
    if req.voice_id is not None:
        settings.VOICE_ID = req.voice_id
    if req.retell_agent_id is not None:
        settings.RETELL_AGENT_ID = req.retell_agent_id
    if req.retell_from_number is not None:
        settings.RETELL_FROM_NUMBER = req.retell_from_number
    if req.authorized_test_numbers is not None:
        settings.AUTHORIZED_TEST_NUMBERS = req.authorized_test_numbers
    if req.additional_context_from_rag is not None:
        settings.ADDITIONAL_CONTEXT_FROM_RAG = req.additional_context_from_rag

    return {
        "success": True,
        "message": "Configuration updated successfully.",
        "config": settings.get_safe_config()
    }
