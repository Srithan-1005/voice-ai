import pytest
from app.schemas.state import QualificationState, QualificationStatus
from app.services.eligibility_service import EligibilityService

def make_valid_state() -> QualificationState:
    return QualificationState(
        customer_name="Anita Roy",
        customer_verified=True,
        property_type="Residential",
        ownership_status="Sole ownership",
        original_documents_available=True,
        loan_amount_requested=5000000.0,
        loan_amount_confirmed=5000000.0,
        occupation="Salaried",
        income_mode="Bank",
        market_value=10000000.0,
        tenure_years=10
    )

def test_successful_residential_qualification():
    state = make_valid_state()
    evaluated = EligibilityService.evaluate_state(state)
    assert evaluated.qualification_status == QualificationStatus.QUALIFIED
    assert evaluated.call_ended is True
    assert evaluated.disqualified is False

def test_commercial_property_qualification():
    state = make_valid_state()
    state.property_type = "Commercial"
    evaluated = EligibilityService.evaluate_state(state)
    assert evaluated.qualification_status == QualificationStatus.QUALIFIED

def test_industrial_property_qualification():
    state = make_valid_state()
    state.property_type = "Industrial"
    evaluated = EligibilityService.evaluate_state(state)
    assert evaluated.qualification_status == QualificationStatus.QUALIFIED

def test_joint_ownership_qualification():
    state = make_valid_state()
    state.ownership_status = "Joint ownership"
    evaluated = EligibilityService.evaluate_state(state)
    assert evaluated.qualification_status == QualificationStatus.QUALIFIED

def test_agricultural_property_disqualified():
    state = make_valid_state()
    state.property_type = "Agricultural"
    evaluated = EligibilityService.evaluate_state(state)
    assert evaluated.qualification_status == QualificationStatus.NOT_ELIGIBLE
    assert evaluated.disqualified is True
    assert "Agricultural property is not eligible" in evaluated.disqualification_reason

def test_original_documents_unavailable_disqualified():
    state = make_valid_state()
    state.original_documents_available = False
    evaluated = EligibilityService.evaluate_state(state)
    assert evaluated.qualification_status == QualificationStatus.NOT_ELIGIBLE
    assert evaluated.disqualified is True
    assert "Original property documents are mandatory" in evaluated.disqualification_reason

def test_original_documents_uncertain_clarification():
    state = make_valid_state()
    state.original_documents_available = None
    state.original_documents_uncertain = True
    evaluated = EligibilityService.evaluate_state(state)
    assert evaluated.qualification_status == QualificationStatus.NEEDS_CLARIFICATION
    assert len(evaluated.pending_clarifications) > 0

def test_salaried_with_bank_income():
    state = make_valid_state()
    state.occupation = "Salaried"
    state.income_mode = "Bank"
    evaluated = EligibilityService.evaluate_state(state)
    assert evaluated.qualification_status == QualificationStatus.QUALIFIED

def test_self_employed_with_bank_income():
    state = make_valid_state()
    state.occupation = "Self-employed"
    state.income_mode = "Bank"
    evaluated = EligibilityService.evaluate_state(state)
    assert evaluated.qualification_status == QualificationStatus.QUALIFIED

def test_cash_income_disqualified():
    state = make_valid_state()
    state.income_mode = "Cash"
    evaluated = EligibilityService.evaluate_state(state)
    assert evaluated.qualification_status == QualificationStatus.NOT_ELIGIBLE
    assert evaluated.disqualified is True
    assert "cash" in evaluated.disqualification_reason.lower()

def test_tenure_boundary_3_years_passes():
    state = make_valid_state()
    state.tenure_years = 3
    evaluated = EligibilityService.evaluate_state(state)
    assert evaluated.qualification_status == QualificationStatus.QUALIFIED

def test_tenure_boundary_15_years_passes():
    state = make_valid_state()
    state.tenure_years = 15
    evaluated = EligibilityService.evaluate_state(state)
    assert evaluated.qualification_status == QualificationStatus.QUALIFIED

def test_tenure_boundary_2_years_fails():
    state = make_valid_state()
    state.tenure_years = 2
    evaluated = EligibilityService.evaluate_state(state)
    assert evaluated.qualification_status == QualificationStatus.NOT_ELIGIBLE
    assert evaluated.disqualified is True

def test_tenure_boundary_16_years_fails():
    state = make_valid_state()
    state.tenure_years = 16
    evaluated = EligibilityService.evaluate_state(state)
    assert evaluated.qualification_status == QualificationStatus.NOT_ELIGIBLE
    assert evaluated.disqualified is True
