import re
import datetime
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status
from app.services.call_service import CallService
from app.schemas.api import StartCallRequest, StartCallResponse
from app.integrations.retell_provider import retell_provider
from app.core.config import settings
from app.services.prompt_service import PromptService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/calls", tags=["Call Management"])

def validate_and_normalize_phone(phone: str) -> str:
    if not phone or not phone.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Destination phone number is required."
        )
    cleaned = re.sub(r"[\s\-\(\)]", "", phone.strip())
    # Format 10-digit Indian numbers automatically
    if re.match(r"^[6-9]\d{9}$", cleaned):
        cleaned = f"+91{cleaned}"
    elif cleaned.startswith("0") and len(cleaned) == 11 and re.match(r"^0[6-9]\d{9}$", cleaned):
        cleaned = f"+91{cleaned[1:]}"
    elif not cleaned.startswith("+"):
        cleaned = f"+{cleaned}"

    # E.164 check: + followed by 7 to 15 digits
    if not re.match(r"^\+[1-9]\d{6,14}$", cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format. Must be an international E.164 format (e.g. +919876543210 or +12345678901)."
        )
    return cleaned

def check_authorized_number(phone: str) -> None:
    allowed_str = settings.AUTHORIZED_TEST_NUMBERS.strip()
    if not allowed_str:
        return  # In development, any validated E.164 number is accepted
    allowed_list = [re.sub(r"[\s\-\(\)]", "", n.strip()) for n in allowed_str.split(",") if n.strip()]
    if "*" in allowed_list:
        return
    if phone not in allowed_list:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Phone number {phone} is not in the configured authorized test numbers list. Authorized numbers: {', '.join(allowed_list)}"
        )

@router.post("/start", response_model=StartCallResponse)
async def start_call(req: StartCallRequest):
    """
    Initiates a real voice call via Retell AI to an authorized test destination.
    Requires explicit user action (confirmed_destination=True).
    """
    if not req.confirmed_destination:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explicit user confirmation is required to initiate a real outbound phone call."
        )

    # Validate destination phone number
    normalized_phone = validate_and_normalize_phone(req.customer_phone)
    check_authorized_number(normalized_phone)

    # Check Retell configuration
    if not settings.RETELL_API_KEY or not settings.RETELL_API_KEY.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "RETELL_API_KEY is not configured in backend environment variables. "
                "Please add RETELL_API_KEY to your .env file."
            )
        )

    agent_id = settings.RETELL_AGENT_ID
    if not agent_id or not agent_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "RETELL_AGENT_ID is not configured in backend environment variables. "
                "Please create an agent on the Retell dashboard and configure RETELL_AGENT_ID in .env."
            )
        )

    call_mode = (req.call_mode or "phone").lower()
    if call_mode == "phone":
        if not settings.RETELL_FROM_NUMBER or not settings.RETELL_FROM_NUMBER.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "RETELL_FROM_NUMBER is not configured. Retell outbound phone calls require "
                    "a purchased or imported phone number. Configure RETELL_FROM_NUMBER in your .env "
                    "or select 'Web Call' mode to test in the browser."
                )
            )

    # Build dynamic variables
    now = datetime.datetime.now()
    c_name = req.customer_name or settings.DEFAULT_CUSTOMER_NAME or "Valued Customer"
    a_name = req.agent_name or settings.AGENT_NAME
    a_gender = req.agent_gender or settings.AGENT_GENDER
    lang = req.language or settings.DEFAULT_LANGUAGE

    dynamic_vars: Dict[str, str] = {
        "company_name": settings.COMPANY_NAME,
        "customer_name": c_name,
        "agent_name": a_name,
        "agent_gender": a_gender,
        "current_date": now.strftime("%Y-%m-%d"),
        "current_day": now.strftime("%A"),
        "current_time": now.strftime("%H:%M:%S"),
        "additional_context_from_rag": settings.ADDITIONAL_CONTEXT_FROM_RAG,
        "language_to_speak": lang,
        "conversation_history": "(Call initiated from web test console)",
        "customer_utterance": "(Customer answered)",
        "property_type": req.property_type or "unknown",
        "ownership": req.ownership_status or "unknown",
        "original_documents": req.original_documents_available or "unknown",
        "requested_loan_amount": str(req.loan_amount_requested) if req.loan_amount_requested else "unknown",
        "occupation": req.occupation or "unknown",
        "income_mode": req.income_mode or "unknown",
        "property_market_value": str(req.market_value) if req.market_value else "unknown",
        "loan_tenure": str(req.tenure_years) if req.tenure_years else "unknown",
        "existing_property_loan": req.existing_loan or "unknown",
        "emi_reduction_request": req.emi_reduction_request or "unknown",
    }

    metadata = {
        "app": "Home Credit LAP Voice Qualification",
        "customer_name": c_name,
        "to_number": normalized_phone,
        "language": lang
    }

    collected = {
        "property_type": req.property_type,
        "ownership_status": req.ownership_status,
        "original_documents_available": req.original_documents_available,
        "loan_amount_requested": req.loan_amount_requested,
        "occupation": req.occupation,
        "income_mode": req.income_mode,
        "market_value": req.market_value,
        "tenure_years": req.tenure_years,
        "existing_loan": req.existing_loan,
        "emi_reduction_request": req.emi_reduction_request,
    }

    if call_mode == "phone":
        result = await retell_provider.initiate_phone_call(
            to_number=normalized_phone,
            agent_id=agent_id,
            dynamic_variables=dynamic_vars,
            metadata=metadata
        )
    else:
        result = await retell_provider.initiate_web_call(
            agent_id=agent_id,
            dynamic_variables=dynamic_vars,
            metadata=metadata
        )

    if not result.get("success"):
        raise HTTPException(
            status_code=result.get("status_code", status.HTTP_502_BAD_GATEWAY),
            detail=result.get("error", "Failed to initiate call on Retell AI.")
        )

    call_id = result.get("call_id")
    call_status_str = result.get("call_status", "registered")

    # Record initial provider call
    record_data = {
        "call_id": call_id,
        "customer_name": c_name,
        "phone_number": normalized_phone,
        "timestamp": now.isoformat(),
        "start_time": now.isoformat(),
        "end_time": None,
        "duration_seconds": None,
        "call_type": "provider_call" if call_mode == "phone" else "web_call",
        "call_status": call_status_str,
        "outcome": "IN_PROGRESS",
        "disqualification_reason": None,
        "transfer_reason": None,
        "recording_url": None,
        "transcript": [],
        "collected_fields": collected,
        "decision_explanation": f"Call initiated via Retell AI ({call_mode} mode). Awaiting live progress/webhook.",
        "error_message": None
    }
    CallService.record_provider_call(record_data)

    return StartCallResponse(
        call_id=call_id,
        call_status=call_status_str,
        customer_name=c_name,
        phone_number=normalized_phone,
        call_type="provider_call" if call_mode == "phone" else "web_call",
        message=f"Outbound call initiated successfully to {normalized_phone}.",
        access_token=result.get("access_token"),
        raw=result.get("raw")
    )

@router.get("")
def list_calls(outcome: Optional[str] = Query(None, description="Filter by outcome e.g. QUALIFIED, NOT_ELIGIBLE")):
    """Returns stored call records from SQLite repository."""
    records = CallService.get_all_calls(outcome_filter=outcome)
    return {
        "total": len(records),
        "calls": records
    }

@router.get("/analytics")
def get_analytics():
    """Returns overall statistics and distribution data calculated from real stored records."""
    return CallService.get_analytics()

@router.get("/{call_id}")
async def get_call_detail(call_id: str):
    """
    Returns detailed call record.
    If the call is an active provider call, attempts to query Retell API for latest status,
    transcript, and recording URL (polling fallback).
    """
    record = CallService.get_call_by_id(call_id)
    if not record:
        raise HTTPException(status_code=404, detail="Call record not found.")

    # Polling sync from Retell provider if call is active or missing transcript/recording
    if record.get("call_type") in ("provider_call", "web_call") and retell_provider.is_configured():
        if record.get("call_status") not in ("ended", "completed", "failed") or not record.get("recording_url"):
            try:
                live_res = await retell_provider.get_call_details(call_id)
                if live_res.get("success"):
                    live_call = live_res.get("call_data", {})
                    updates: Dict[str, Any] = {}
                    
                    if live_call.get("call_status"):
                        updates["call_status"] = live_call["call_status"]
                    if live_call.get("duration_ms"):
                        updates["duration_seconds"] = int(live_call["duration_ms"] / 1000)
                    if live_call.get("recording_url"):
                        updates["recording_url"] = live_call["recording_url"]
                    if live_call.get("end_timestamp"):
                        updates["end_time"] = live_call["end_timestamp"]

                    # Extract transcript
                    transcript_raw = live_call.get("transcript")
                    transcript_obj = live_call.get("transcript_object")
                    if isinstance(transcript_obj, list) and transcript_obj:
                        updates["transcript"] = [
                            {"role": t.get("role", "customer"), "content": t.get("content", t.get("message", ""))}
                            for t in transcript_obj
                        ]
                    elif isinstance(transcript_raw, str) and transcript_raw.strip():
                        turns = []
                        for line in transcript_raw.split("\n"):
                            if ":" in line:
                                r, txt = line.split(":", 1)
                                role = "agent" if "agent" in r.lower() else "customer"
                                turns.append({"role": role, "content": txt.strip()})
                            elif line.strip():
                                turns.append({"role": "customer", "content": line.strip()})
                        if turns:
                            updates["transcript"] = turns

                    # Extract analysis
                    analysis = live_call.get("call_analysis", {}).get("custom_analysis_data", {})
                    if analysis.get("qualification_status"):
                        updates["outcome"] = analysis["qualification_status"]
                    if analysis.get("disqualification_reason"):
                        updates["disqualification_reason"] = analysis["disqualification_reason"]
                    if analysis.get("transfer_reason"):
                        updates["transfer_reason"] = analysis["transfer_reason"]

                    if updates:
                        updated_rec = CallService.update_provider_call(call_id, updates)
                        if updated_rec:
                            record = updated_rec
            except Exception as e:
                logger.warning(f"Failed to poll live Retell call status for {call_id}: {e}")

    return record

@router.get("/{call_id}/transcript")
async def get_call_transcript(call_id: str):
    """Returns actual transcript turns for the call if available."""
    record = await get_call_detail(call_id)
    transcript = record.get("transcript", [])
    has_transcript = bool(transcript and len(transcript) > 0)
    return {
        "call_id": call_id,
        "available": has_transcript,
        "transcript": transcript,
        "message": "Transcript retrieved successfully." if has_transcript else "Transcript not available yet. Call may still be in progress or being analyzed."
    }

@router.get("/{call_id}/recording")
async def get_call_recording(call_id: str):
    """Returns authentic provider recording URL for the call if available."""
    record = await get_call_detail(call_id)
    rec_url = record.get("recording_url")
    has_recording = bool(rec_url and rec_url.strip())
    return {
        "call_id": call_id,
        "available": has_recording,
        "recording_url": rec_url if has_recording else None,
        "message": "Recording available." if has_recording else "Recording not available yet. Provider has not generated the recording file."
    }
