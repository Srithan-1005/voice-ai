from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class VoiceProvider(ABC):
    """
    Abstract interface for Voice Platform integrations (Retell AI, Bolna).
    Allows pluggable voice engines while maintaining strict boundaries.
    """

    @abstractmethod
    def is_configured(self) -> bool:
        """Checks if required API credentials exist."""
        pass

    @abstractmethod
    async def create_agent(self, agent_name: str, system_prompt: str, voice_id: str, language: str) -> Dict[str, Any]:
        """Registers or configures an agent with the voice provider."""
        pass

    @abstractmethod
    async def initiate_web_call(self, agent_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Initiates an authorized web-based test call session."""
        pass

    @abstractmethod
    async def initiate_phone_call(self, to_number: str, agent_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Initiates a phone call to an authorized test number."""
        pass

    @abstractmethod
    def parse_webhook_payload(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parses webhook event into standardized call record structure."""
        pass
