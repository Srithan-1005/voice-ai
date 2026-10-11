import logging
from typing import Dict, Any, Optional, List
from retell import Retell
from retell.lib.webhook_auth import verify as verify_retell_webhook
import retell
from app.integrations.voice_provider import VoiceProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

class RetellVoiceProvider(VoiceProvider):
    """
    Retell AI implementation adhering strictly to the official Retell SDK and API standards.
    Supports:
    - Outbound phone calls with dynamic variables via Retell SDK
    - Web-call session creation for in-browser testing
    - Fetching live call status, transcript, and authentic recording URL
    - Webhook signature verification and payload normalization
    """

    def __init__(self, api_key: Optional[str] = None, agent_id: Optional[str] = None):
        self.api_key = api_key or settings.RETELL_API_KEY
        self.agent_id = agent_id or settings.RETELL_AGENT_ID

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def get_client(self) -> Optional[Retell]:
        if not self.is_configured():
            return None
        return Retell(api_key=self.api_key)

    async def create_agent(
        self,
        agent_name: str,
        system_prompt: str,
        voice_id: str = "11labs-Adrian",
        language: str = "en-US"
    ) -> Dict[str, Any]:
        """
        Registers or updates an agent with Retell AI using the official SDK.
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "RETELL_API_KEY is not configured in backend environment variables.",
                "configuration_required": True
            }

        client = self.get_client()
        lang_code = "hi-IN" if str(language).lower() == "hindi" else "en-US"
        try:
            llm_resp = client.llm.create(general_prompt=system_prompt)
            llm_id = getattr(llm_resp, "llm_id", None) or getattr(llm_resp, "id", None) or llm_resp.get("llm_id")

            agent_resp = client.agent.create(
                response_engine={"type": "retell-llm", "llm_id": llm_id},
                voice_id=voice_id or "11labs-Adrian",
                agent_name=agent_name,
                language=lang_code
            )
            data = agent_resp.model_dump() if hasattr(agent_resp, "model_dump") else dict(agent_resp)
            self.agent_id = data.get("agent_id")
            return {
                "success": True,
                "agent_id": self.agent_id,
                "raw": data
            }
        except Exception as e:
            logger.error(f"Error creating Retell agent: {e}")
            return {"success": False, "error": str(e)}


    async def initiate_phone_call(
        self,
        to_number: str,
        from_number: Optional[str] = None,
        agent_id: Optional[str] = None,
        dynamic_variables: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initiates an outbound phone call using the official Retell SDK.
        Requires:
        - RETELL_API_KEY
        - Valid Agent ID
        - Valid Outbound Phone Number (from_number) registered in Retell
        - E.164 Destination Number (to_number)
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "RETELL_API_KEY is not configured in backend environment variables.",
                "configuration_required": True,
                "suggested_action": "Add your Retell secret API key to .env (RETELL_API_KEY)."
            }

        target_agent = agent_id or self.agent_id or settings.RETELL_AGENT_ID
        if not target_agent or not target_agent.strip():
            return {
                "success": False,
                "error": "Retell Agent ID is missing.",
                "configuration_required": True,
                "suggested_action": "Configure RETELL_AGENT_ID in .env or provide an active Retell Agent ID."
            }

        outbound_number = from_number or settings.RETELL_FROM_NUMBER
        if not outbound_number or not outbound_number.strip():
            return {
                "success": False,
                "error": "Retell Outbound Phone Number (from_number) is not configured.",
                "configuration_required": True,
                "suggested_action": (
                    "Retell outbound phone calls require a purchased or imported phone number. "
                    "Set RETELL_FROM_NUMBER in .env (e.g. +1234567890) or bind an outbound number in your Retell dashboard."
                )
            }

        client = self.get_client()
        try:
            logger.info(f"Initiating Retell outbound call: from {outbound_number} to {to_number} (agent: {target_agent})")
            
            # Format dynamic variables ensuring all values are strings
            clean_dynamic_vars = {}
            if dynamic_variables:
                for k, v in dynamic_variables.items():
                    clean_dynamic_vars[str(k)] = "" if v is None else str(v)

            phone_call_response = client.call.create_phone_call(
                from_number=outbound_number,
                to_number=to_number,
                override_agent_id=target_agent,
                retell_llm_dynamic_variables=clean_dynamic_vars if clean_dynamic_vars else retell.Omit(),
                metadata=metadata or {"app": "Home Credit LAP Qualification"}
            )

            call_dict = phone_call_response.model_dump() if hasattr(phone_call_response, "model_dump") else dict(phone_call_response)
            return {
                "success": True,
                "call_id": call_dict.get("call_id"),
                "call_status": call_dict.get("call_status", "registered"),
                "raw": call_dict
            }
        except retell.AuthenticationError as e:
            logger.error(f"Retell Authentication Error: {e}")
            return {
                "success": False,
                "error": f"Retell Authentication Failed: Invalid API key ({e.message if hasattr(e, 'message') else e})",
                "status_code": 401
            }
        except retell.BadRequestError as e:
            logger.error(f"Retell BadRequest Error: {e}")
            return {
                "success": False,
                "error": f"Retell Request Rejected: {e.message if hasattr(e, 'message') else e}",
                "status_code": 400
            }
        except retell.APIError as e:
            logger.error(f"Retell API Error: {e}")
            return {
                "success": False,
                "error": f"Retell Provider Error ({getattr(e, 'status_code', 500)}): {getattr(e, 'message', str(e))}",
                "status_code": getattr(e, 'status_code', 500)
            }
        except Exception as e:
            logger.error(f"Unexpected error creating Retell phone call: {e}")
            return {"success": False, "error": str(e)}

    async def initiate_web_call(
        self,
        agent_id: Optional[str] = None,
        dynamic_variables: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Creates a web call session for in-browser testing using Retell Web Client.
        Official SDK method: client.call.create_web_call
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "RETELL_API_KEY is not configured.",
                "configuration_required": True,
                "suggested_action": "Add your Retell API key to .env. Or use Conversation Simulator for zero-cost local testing."
            }

        target_agent = agent_id or self.agent_id or settings.RETELL_AGENT_ID
        if not target_agent or not target_agent.strip():
            return {
                "success": False,
                "error": "No Retell Agent ID provided or configured. Please set RETELL_AGENT_ID in .env."
            }

        client = self.get_client()
        try:
            clean_dynamic_vars = {}
            if dynamic_variables:
                for k, v in dynamic_variables.items():
                    clean_dynamic_vars[str(k)] = "" if v is None else str(v)

            web_call_resp = client.call.create_web_call(
                agent_id=target_agent,
                retell_llm_dynamic_variables=clean_dynamic_vars if clean_dynamic_vars else retell.Omit(),
                metadata=metadata or {"app": "Home Credit LAP Qualification"}
            )
            data = web_call_resp.model_dump() if hasattr(web_call_resp, "model_dump") else dict(web_call_resp)
            return {
                "success": True,
                "call_id": data.get("call_id"),
                "access_token": data.get("access_token"),
                "raw": data
            }
        except Exception as e:
            logger.error(f"Error creating Retell web call: {e}")
            return {"success": False, "error": str(e)}

    async def get_call_details(self, call_id: str) -> Dict[str, Any]:
        """
        Retrieves actual call status, duration, recording URL, and transcript directly from Retell.
        Official SDK method: client.call.retrieve(call_id)
        """
        if not self.is_configured():
            return {"success": False, "error": "Retell API key not configured."}

        client = self.get_client()
        try:
            call_resp = client.call.retrieve(call_id)
            call_dict = call_resp.model_dump() if hasattr(call_resp, "model_dump") else dict(call_resp)
            return {"success": True, "call_data": call_dict}
        except retell.NotFoundError:
            return {"success": False, "error": "Call not found on Retell provider.", "status_code": 404}
        except Exception as e:
            logger.error(f"Error retrieving Retell call {call_id}: {e}")
            return {"success": False, "error": str(e)}

    def verify_webhook(self, body_bytes: bytes, signature_header: Optional[str]) -> bool:
        """
        Validates Retell webhook signature using the official SDK verifier,
        falling back to HMAC SHA256 if needed.
        """
        secret = settings.RETELL_WEBHOOK_SECRET or settings.RETELL_API_KEY
        if not secret:
            # If no secret configured in dev mode, log warning and allow
            logger.warning("No RETELL_WEBHOOK_SECRET configured; skipping signature verification.")
            return True

        if not signature_header:
            return False

        try:
            # Official Retell SDK webhook verify
            return verify_retell_webhook(body_bytes.decode("utf-8"), secret, signature_header)
        except Exception as e:
            logger.warning(f"Retell official signature verification failed: {e}. Trying fallback HMAC.")
            import hmac
            import hashlib
            expected = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, signature_header)

    def parse_webhook_payload(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses incoming Retell webhook data (event: 'call_started', 'call_ended', 'call_analyzed')
        into the standardized CallRecord schema. Never fabricates audio links or transcripts.
        """
        call_obj = payload.get("call", payload)
        call_id = call_obj.get("call_id")
        duration_ms = call_obj.get("duration_ms")
        duration_sec = int(duration_ms / 1000) if duration_ms is not None else None

        recording_url = call_obj.get("recording_url")
        transcript_raw = call_obj.get("transcript", "")
        call_status = call_obj.get("call_status", "ended" if event_type in ("call_ended", "call_analyzed") else "ongoing")

        # Parse transcript turns
        formatted_transcript = []
        transcript_object = call_obj.get("transcript_object")
        if isinstance(transcript_object, list):
            for turn in transcript_object:
                role = turn.get("role", "customer")
                content = turn.get("content", turn.get("message", ""))
                formatted_transcript.append({"role": role, "content": content})
        elif isinstance(transcript_raw, list):
            for turn in transcript_raw:
                formatted_transcript.append({
                    "role": turn.get("role", "customer"),
                    "content": turn.get("content", turn.get("message", ""))
                })
        elif isinstance(transcript_raw, str) and transcript_raw.strip():
            lines = transcript_raw.strip().split("\n")
            for line in lines:
                if ":" in line:
                    r, text = line.split(":", 1)
                    role = "agent" if "agent" in r.lower() else "customer"
                    formatted_transcript.append({"role": role, "content": text.strip()})
                else:
                    formatted_transcript.append({"role": "customer", "content": line.strip()})

        # Extraction from call analysis if supplied by Retell
        analysis = call_obj.get("call_analysis", {})
        custom_analysis = analysis.get("custom_analysis_data", {})
        
        outcome = "IN_PROGRESS"
        if call_status in ("ended", "completed"):
            outcome = custom_analysis.get("qualification_status", "QUALIFIED")

        meta = call_obj.get("metadata", {})
        customer_name = meta.get("customer_name") or call_obj.get("customer_name") or "Valued Customer"
        phone_number = call_obj.get("to_number") or meta.get("to_number")

        return {
            "call_id": call_id,
            "customer_name": customer_name,
            "phone_number": phone_number,
            "timestamp": call_obj.get("start_timestamp") or call_obj.get("created_at"),
            "start_time": call_obj.get("start_timestamp"),
            "end_time": call_obj.get("end_timestamp"),
            "duration_seconds": duration_sec,
            "call_type": call_obj.get("call_type", "provider_call"),
            "call_status": call_status,
            "outcome": outcome,
            "disqualification_reason": custom_analysis.get("disqualification_reason"),
            "transfer_reason": custom_analysis.get("transfer_reason"),
            "recording_url": recording_url,  # Authentic URL from Retell only
            "transcript": formatted_transcript,
            "collected_fields": custom_analysis.get("collected_fields", {}),
            "decision_explanation": custom_analysis.get("decision_explanation", "Call executed on Retell AI voice platform."),
            "error_message": call_obj.get("disconnection_reason")
        }

retell_provider = RetellVoiceProvider()
