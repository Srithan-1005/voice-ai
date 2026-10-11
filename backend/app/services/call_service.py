import datetime
from typing import Optional, Dict, Any, List
from app.repositories.call_repository import call_repository
from app.schemas.state import QualificationState

class CallService:
    """
    High-level service managing call record lifecycle, saving completed simulation
    and provider calls to persistence.
    """

    @classmethod
    def record_simulation_call(cls, state: QualificationState, duration_seconds: int = 45) -> Dict[str, Any]:
        """
        Saves a completed or in-progress simulation session to SQLite.
        """
        collected = {
            "property_type": state.property_type,
            "ownership_status": state.ownership_status,
            "original_documents_available": state.original_documents_available,
            "loan_amount_requested": state.loan_amount_requested,
            "loan_amount_confirmed": state.loan_amount_confirmed,
            "occupation": state.occupation,
            "income_mode": state.income_mode,
            "market_value": state.market_value,
            "tenure_years": state.tenure_years,
        }

        record = {
            "call_id": state.call_id or f"sim_{int(datetime.datetime.now().timestamp())}",
            "customer_name": state.customer_name or "Valued Customer",
            "timestamp": datetime.datetime.now().isoformat(),
            "duration_seconds": duration_seconds,
            "call_type": "simulation",
            "outcome": state.qualification_status.value,
            "disqualification_reason": state.disqualification_reason,
            "transfer_reason": state.transfer_reason,
            "recording_url": None,  # Simulation does not fabricate audio files
            "transcript": [{"role": m.role.value, "content": m.content} for m in state.conversation_history],
            "collected_fields": collected,
            "decision_explanation": state.decision_explanation,
            "error_message": None
        }

        call_repository.save_call_record(record)
        return record

    @classmethod
    def record_provider_call(cls, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Saves an authentic provider call (from webhook or API) without fabricating missing values.
        """
        call_repository.save_call_record(provider_data)
        return provider_data

    @classmethod
    def update_provider_call(cls, call_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return call_repository.update_call_status(call_id, updates)

    @classmethod
    def get_all_calls(cls, outcome_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        return call_repository.get_all_calls(outcome_filter)

    @classmethod
    def get_call_by_id(cls, call_id: str) -> Optional[Dict[str, Any]]:
        return call_repository.get_call_by_id(call_id)

    @classmethod
    def get_analytics(cls) -> Dict[str, Any]:
        return call_repository.get_analytics_summary()
