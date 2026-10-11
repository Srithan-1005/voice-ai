from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from app.schemas.api import StartSimulationRequest, SimulationMessageRequest, SimulationMessageResponse
from app.schemas.state import QualificationState
from app.services.conversation_service import ConversationService
from app.services.eligibility_service import EligibilityService
from app.services.call_service import CallService

router = APIRouter(prefix="/api/simulations", tags=["Conversation Simulations"])
simulator_router = APIRouter(prefix="/api/simulator/sessions", tags=["Simulator Sessions"])

# In-memory active simulation store (session_id -> QualificationState)
_active_simulations: Dict[str, QualificationState] = {}
_session_languages: Dict[str, str] = {}

def _handle_start_simulation(req: StartSimulationRequest):
    language = req.language or "English"
    state, initial_msg = ConversationService.initialize_conversation(
        customer_name=req.customer_name,
        language=language,
        initial_fields=req.model_dump()
    )
    session_id = state.call_id
    _active_simulations[session_id] = state
    _session_languages[session_id] = language

    all_7_items = {
        "property_type", "ownership_status", "original_documents",
        "loan_amount", "occupation_and_income_mode", "market_value", "tenure_years"
    }
    missing = list(all_7_items - set(state.answered_items))

    return {
        "session_id": session_id,
        "initial_message": initial_msg,
        "state": state,
        "checklist": state.get_checklist_details(),
        "missing_items": missing,
        "outcome": state.qualification_status,
        "call_ended": state.call_ended,
        "decision_explanation": state.decision_explanation
    }

@router.post("")
def start_simulation(req: StartSimulationRequest):
    """Starts a new simulated conversation session."""
    return _handle_start_simulation(req)

@simulator_router.post("")
def start_simulator_session(req: StartSimulationRequest):
    """Starts a new simulated conversation session (alias endpoint)."""
    return _handle_start_simulation(req)


@router.get("/{session_id}")
def get_simulation(session_id: str):
    """Returns current state and history of an active simulation."""
    if session_id not in _active_simulations:
        raise HTTPException(status_code=404, detail="Simulation session not found.")
    
    state = _active_simulations[session_id]
    all_7_items = {
        "property_type", "ownership_status", "original_documents",
        "loan_amount", "occupation_and_income_mode", "market_value", "tenure_years"
    }
    missing = list(all_7_items - set(state.answered_items))

    return {
        "session_id": session_id,
        "state": state,
        "checklist": state.get_checklist_details(),
        "missing_items": missing,
        "outcome": state.qualification_status,
        "call_ended": state.call_ended,
        "decision_explanation": state.decision_explanation
    }

@router.post("/{session_id}/messages", response_model=SimulationMessageResponse)
def process_message(session_id: str, req: SimulationMessageRequest):
    """
    Processes a customer utterance in the simulation session.
    """
    if session_id not in _active_simulations:
        raise HTTPException(status_code=404, detail="Simulation session not found.")
    
    state = _active_simulations[session_id]
    language = _session_languages.get(session_id, "English")

    # If call already ended, reject further utterances or prompt to reset
    if state.call_ended:
        return SimulationMessageResponse(
            agent_response="The qualification call has concluded. Please reset to start a new simulation.",
            state=state,
            checklist=state.get_checklist_details(),
            outcome=state.qualification_status,
            missing_items=[],
            call_ended=True,
            decision_explanation=state.decision_explanation or "Call already concluded."
        )

    # Process utterance
    updated_state, agent_resp = ConversationService.process_utterance(
        state=state,
        customer_utterance=req.message,
        language=language
    )
    _active_simulations[session_id] = updated_state

    all_7_items = {
        "property_type", "ownership_status", "original_documents",
        "loan_amount", "occupation_and_income_mode", "market_value", "tenure_years"
    }
    missing = list(all_7_items - set(updated_state.answered_items))

    # If terminal outcome reached, save to CallRepository
    if updated_state.call_ended:
        CallService.record_simulation_call(updated_state)

    return SimulationMessageResponse(
        agent_response=agent_resp,
        state=updated_state,
        checklist=updated_state.get_checklist_details(),
        outcome=updated_state.qualification_status,
        missing_items=missing,
        call_ended=updated_state.call_ended,
        decision_explanation=updated_state.decision_explanation or "Evaluation in progress."
    )

@router.post("/{session_id}/reset")
def reset_simulation(session_id: str):
    """
    Resets the conversation simulator to starting state.
    """
    old_state = _active_simulations.get(session_id)
    c_name = old_state.customer_name if old_state else "Valued Customer"
    language = _session_languages.get(session_id, "English")

    new_state, initial_msg = ConversationService.initialize_conversation(
        customer_name=c_name,
        language=language
    )
    new_state.call_id = session_id
    _active_simulations[session_id] = new_state

    all_7_items = {
        "property_type", "ownership_status", "original_documents",
        "loan_amount", "occupation_and_income_mode", "market_value", "tenure_years"
    }

    return {
        "session_id": session_id,
        "initial_message": initial_msg,
        "state": new_state,
        "checklist": new_state.get_checklist_details(),
        "missing_items": list(all_7_items),
        "outcome": new_state.qualification_status,
        "call_ended": False,
        "decision_explanation": new_state.decision_explanation
    }

# Register handlers for simulator_router aliases
simulator_router.add_api_route("/{session_id}", get_simulation, methods=["GET"])
simulator_router.add_api_route("/{session_id}/messages", process_message, methods=["POST"], response_model=SimulationMessageResponse)
simulator_router.add_api_route("/{session_id}/reset", reset_simulation, methods=["POST"])

