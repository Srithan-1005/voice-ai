from fastapi import APIRouter, Request, Header, HTTPException, status
from typing import Optional
import json
import logging
from app.core.config import settings
from app.core.security import verify_retell_webhook_signature
from app.integrations.retell_provider import retell_provider
from app.services.call_service import CallService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])

@router.post("/retell")
async def retell_webhook(request: Request, x_retell_signature: Optional[str] = Header(None)):
    """
    Receives and processes incoming Retell AI webhook events.
    Verifies cryptographic signature if secret is configured.
    """
    body_bytes = await request.body()
    
    if settings.RETELL_WEBHOOK_SECRET:
        if not retell_provider.verify_webhook(body_bytes, x_retell_signature):
            logger.warning("Invalid Retell webhook signature received.")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    event_type = payload.get("event", "unknown")
    logger.info(f"Received Retell webhook event: {event_type}")

    if event_type in ("call_started", "call_ended", "call_analyzed"):
        record_data = retell_provider.parse_webhook_payload(event_type, payload)
        call_id = record_data.get("call_id")
        
        # Merge with existing record if it already exists (idempotent / duplicate-safe)
        existing = CallService.get_call_by_id(call_id) if call_id else None
        if existing:
            # Keep existing collected_fields if webhook didn't supply them
            if not record_data.get("collected_fields") and existing.get("collected_fields"):
                record_data["collected_fields"] = existing["collected_fields"]
            CallService.update_provider_call(call_id, record_data)
        else:
            CallService.record_provider_call(record_data)

    return {"status": "success", "event_received": event_type}

@router.post("/bolna")
async def bolna_webhook(request: Request):
    """
    Bolna webhook endpoint documented as an unimplemented extension in this build.
    """
    return {
        "status": "unimplemented_extension",
        "message": "Bolna webhook receiver is configured as a future modular extension."
    }
