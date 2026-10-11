from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.integrations.retell_provider import retell_provider
from app.services.prompt_service import PromptService
from app.core.config import settings

router = APIRouter(prefix="/api/voice", tags=["Voice Provider"])

class SyncAgentRequest(BaseModel):
    agent_name: Optional[str] = None
    voice_id: Optional[str] = None
    language: Optional[str] = None

class CreateWebCallRequest(BaseModel):
    customer_name: Optional[str] = "Valued Customer"

@router.get("/status")
def get_voice_status():
    """Returns configuration status for voice integrations."""
    return {
        "primary_provider": "retell",
        "retell_configured": retell_provider.is_configured(),
        "retell_agent_id": retell_provider.agent_id if retell_provider.agent_id else None,
        "sandbox_mode": not retell_provider.is_configured(),
        "notes": (
            "Retell AI is integrated. If RETELL_API_KEY is not provided, local simulation "
            "and all deterministic verification runs seamlessly in sandbox mode."
        )
    }

@router.post("/sync-agent")
async def sync_retell_agent(req: SyncAgentRequest):
    """
    Syncs the current production system prompt and agent configuration with Retell AI.
    """
    agent_name = req.agent_name or settings.AGENT_NAME
    voice_id = req.voice_id or settings.VOICE_ID
    language = req.language or settings.DEFAULT_LANGUAGE
    prompt = PromptService.render_prompt(
        agent_name=agent_name,
        language=language
    )

    result = await retell_provider.create_agent(
        agent_name=agent_name,
        system_prompt=prompt,
        voice_id=voice_id,
        language=language
    )
    return result

@router.post("/web-call")
async def start_web_call(req: CreateWebCallRequest):
    """
    Initiates a web-based test voice call using Retell AI SDK/Web client.
    """
    result = await retell_provider.initiate_web_call(
        metadata={"customer_name": req.customer_name, "test_call": True}
    )
    return result
