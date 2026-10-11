from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.state import QualificationState, QualificationStatus, ChecklistItemDetail

class StartSimulationRequest(BaseModel):
    customer_name: Optional[str] = "Valued Customer"
    customer_phone: Optional[str] = None
    language: Optional[str] = "English"
    scenario_preset: Optional[str] = None
    agent_name: Optional[str] = None
    agent_gender: Optional[str] = None
    property_type: Optional[str] = None
    ownership_status: Optional[str] = None
    original_documents_available: Optional[str] = None
    loan_amount_requested: Optional[float] = None
    occupation: Optional[str] = None
    income_mode: Optional[str] = None
    market_value: Optional[float] = None
    tenure_years: Optional[int] = None
    existing_loan: Optional[str] = None
    emi_reduction_request: Optional[str] = None

class StartCallRequest(BaseModel):
    customer_name: Optional[str] = "Valued Customer"
    customer_phone: str
    language: Optional[str] = "English"
    agent_name: Optional[str] = None
    agent_gender: Optional[str] = None
    property_type: Optional[str] = None
    ownership_status: Optional[str] = None
    original_documents_available: Optional[str] = None
    loan_amount_requested: Optional[float] = None
    occupation: Optional[str] = None
    income_mode: Optional[str] = None
    market_value: Optional[float] = None
    tenure_years: Optional[int] = None
    existing_loan: Optional[str] = None
    emi_reduction_request: Optional[str] = None
    call_mode: Optional[str] = "phone"  # "phone" or "web"
    confirmed_destination: bool = False

class StartCallResponse(BaseModel):
    call_id: str
    call_status: str
    customer_name: str
    phone_number: str
    call_type: str
    message: str
    access_token: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None

class SimulationMessageRequest(BaseModel):
    message: str

class SimulationMessageResponse(BaseModel):
    agent_response: str
    state: QualificationState
    checklist: List[ChecklistItemDetail]
    outcome: QualificationStatus
    missing_items: List[str]
    call_ended: bool
    decision_explanation: str

class UpdateConfigRequest(BaseModel):
    company_name: Optional[str] = None
    agent_name: Optional[str] = None
    agent_gender: Optional[str] = None
    default_customer_name: Optional[str] = None
    default_language: Optional[str] = None
    voice_platform: Optional[str] = None
    voice_id: Optional[str] = None
    retell_agent_id: Optional[str] = None
    retell_from_number: Optional[str] = None
    authorized_test_numbers: Optional[str] = None
    additional_context_from_rag: Optional[str] = None

class UpdatePromptRequest(BaseModel):
    prompt: str

class TestCaseResult(BaseModel):
    test_id: str
    name: str
    category: str
    passed: bool
    expected_outcome: str
    actual_outcome: str
    expected_state: Dict[str, Any]
    actual_state: Dict[str, Any]
    details: str

class TestSuiteResponse(BaseModel):
    total_tests: int
    passed_tests: int
    failed_tests: int
    results: List[TestCaseResult]

class CallRecordSchema(BaseModel):
    call_id: str
    customer_name: str
    phone_number: Optional[str] = None
    timestamp: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[int] = None
    call_type: str  # "simulation" or "provider_call"
    call_status: Optional[str] = "completed"
    outcome: QualificationStatus
    disqualification_reason: Optional[str] = None
    transfer_reason: Optional[str] = None
    recording_url: Optional[str] = None
    transcript: List[Dict[str, str]]
    collected_fields: Dict[str, Any]
    decision_explanation: str
    error_message: Optional[str] = None

