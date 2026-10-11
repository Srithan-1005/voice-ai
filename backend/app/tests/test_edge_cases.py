import pytest
from app.services.conversation_service import ConversationService
from app.services.eligibility_service import EligibilityService
from app.services.extraction_service import ExtractionService
from app.schemas.state import QualificationState, QualificationStatus

def test_excess_loan_offer_acceptance():
    state = QualificationState(
        customer_verified=True,
        property_type="Residential",
        ownership_status="Sole ownership",
        original_documents_available=True,
        loan_amount_requested=9000000.0,
        excess_loan_offer_pending=True,
        occupation="Salaried",
        income_mode="Bank",
        market_value=15000000.0,
        tenure_years=10
    )
    # Customer agrees to ₹75 Lakh alternative
    state, resp = ConversationService.process_utterance(state, "Yes, 75 lakh is fine with me")
    assert state.loan_amount_confirmed == 7500000.0
    assert state.excess_loan_offer_pending is False
    assert state.qualification_status == QualificationStatus.QUALIFIED

def test_excess_loan_offer_declined():
    state = QualificationState(
        customer_verified=True,
        property_type="Residential",
        ownership_status="Sole ownership",
        original_documents_available=True,
        loan_amount_requested=9000000.0,
        excess_loan_offer_pending=True,
        occupation="Salaried",
        income_mode="Bank",
        market_value=15000000.0,
        tenure_years=10
    )
    # Customer declines alternative
    state, resp = ConversationService.process_utterance(state, "No, 75 lakh is not enough, cancel this")
    assert state.call_ended is True
    assert state.qualification_status == QualificationStatus.CUSTOMER_DECLINED

def test_interest_rate_interruption():
    state = QualificationState(customer_verified=True, property_type="Residential")
    state, resp = ConversationService.process_utterance(state, "What is your interest rate?")
    assert "senior loan expert" in resp.lower()
    # Does not end call
    assert state.call_ended is False

def test_contradictory_income_mode():
    state = QualificationState(
        customer_verified=True,
        property_type="Residential",
        ownership_status="Sole ownership",
        original_documents_available=True,
        loan_amount_confirmed=5000000.0,
        occupation="Self-employed",
        income_mode="Both",
        income_mode_both_pending=True,
        market_value=10000000.0,
        tenure_years=10
    )
    evaluated = EligibilityService.evaluate_state(state)
    assert evaluated.qualification_status == QualificationStatus.NEEDS_CLARIFICATION
    assert "Occupation & primary bank income mode" in evaluated.pending_clarifications
