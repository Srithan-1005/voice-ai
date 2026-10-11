import pytest
from app.services.conversation_service import ConversationService
from app.schemas.state import QualificationState, QualificationStatus, MessageRole

def test_initial_conversation_state():
    state, msg = ConversationService.initialize_conversation("Sanjay Gupta")
    assert state.customer_name == "Sanjay Gupta"
    assert "Sanjay Gupta" in msg
    assert state.customer_verified is False
    assert state.call_ended is False

def test_customer_verification_dialogue():
    state, _ = ConversationService.initialize_conversation("Sanjay Gupta")
    state, resp = ConversationService.process_utterance(state, "Yes, speaking")
    assert state.customer_verified is True
    assert "₹75 lakh" in resp or "Loan Against Property" in resp

def test_busy_customer_dialogue():
    state, _ = ConversationService.initialize_conversation("Pooja")
    state, resp = ConversationService.process_utterance(state, "I am driving, please call me back tomorrow at 2 pm")
    assert state.customer_busy is True
    assert state.qualification_status == QualificationStatus.CALLBACK_REQUESTED
    assert state.call_ended is True
    assert "call you back" in resp.lower()

def test_existing_loan_transfer_flow():
    state, _ = ConversationService.initialize_conversation("Rahul")
    state.customer_verified = True
    state, resp = ConversationService.process_utterance(state, "Actually I already have a loan on this property and want to reduce EMI")
    assert state.transfer_required is True
    assert state.qualification_status == QualificationStatus.LOAN_TRANSFER
    assert state.call_ended is True
    assert "loan-transfer specialist" in resp.lower()

def test_disqualification_dialogue():
    state, _ = ConversationService.initialize_conversation("Manoj")
    state.customer_verified = True
    state, resp = ConversationService.process_utterance(state, "It is an agricultural farmland")
    assert state.disqualified is True
    assert state.qualification_status == QualificationStatus.NOT_ELIGIBLE
    assert state.call_ended is True
    assert "won't be able to proceed" in resp.lower()
