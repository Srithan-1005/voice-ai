from typing import Dict, Any, Optional
from app.integrations.voice_provider import VoiceProvider
from app.core.config import settings

class BolnaVoiceProvider(VoiceProvider):
    """
    Bolna Voice Platform integration stub.
    Configured as a modular extension. Retell AI serves as the primary live integration.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.BOLNA_API_KEY

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def create_agent(self, agent_name: str, system_prompt: str, voice_id: str, language: str) -> Dict[str, Any]:
        return {
            "success": False,
            "error": "Bolna provider is an alternative extension. Retell AI is configured as primary.",
            "status": "UNIMPLEMENTED_EXTENSION"
        }

    async def initiate_web_call(self, agent_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "success": False,
            "error": "Bolna web calling is not configured in this build."
        }

    async def initiate_phone_call(self, to_number: str, agent_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "success": False,
            "error": "Bolna outbound calling is not configured in this build."
        }

    def parse_webhook_payload(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "call_id": payload.get("call_id", "bolna_ext"),
            "call_type": "bolna_extension",
            "outcome": "IN_PROGRESS"
        }

bolna_provider = BolnaVoiceProvider()
