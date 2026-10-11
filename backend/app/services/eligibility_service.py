from typing import Tuple, Optional, List
from app.schemas.state import QualificationState, QualificationStatus

class EligibilityService:
    """
    Deterministic business rule validation service for Home Credit LAP Qualification.
    The LLM is NOT the final authority on decisions; all rules are strictly evaluated here.
    """

    ALLOWED_PROPERTY_TYPES = {"residential", "commercial", "industrial"}
    DISQUALIFYING_PROPERTY_TYPES = {"agricultural"}
    
    ALLOWED_OWNERSHIP_TYPES = {"sole ownership", "joint ownership", "sole", "joint"}
    
    MAX_LOAN_AMOUNT = 7500000.0  # ₹75 Lakh
    
    ALLOWED_OCCUPATIONS = {"salaried", "self-employed", "salaried employee", "business owner", "self employed"}
    
    MIN_TENURE_YEARS = 3
    MAX_TENURE_YEARS = 15

    @classmethod
    def validate_property_type(cls, prop_type: Optional[str]) -> Tuple[bool, Optional[str], bool]:
        """
        Returns: (is_valid, error_reason, needs_clarification)
        """
        if not prop_type:
            return False, None, False
        cleaned = prop_type.strip().lower()
        if cleaned in cls.DISQUALIFYING_PROPERTY_TYPES:
            return False, "Agricultural property is not eligible for this offer.", False
        if cleaned in cls.ALLOWED_PROPERTY_TYPES:
            return True, None, False
        return False, None, True  # Unclear type (e.g. mixed-use, garden) needs clarification

    @classmethod
    def validate_ownership(cls, ownership: Optional[str]) -> Tuple[bool, Optional[str], bool]:
        """
        Both sole ownership and joint ownership are eligible.
        """
        if not ownership:
            return False, None, False
        cleaned = ownership.strip().lower()
        if cleaned in cls.ALLOWED_OWNERSHIP_TYPES:
            return True, None, False
        return False, None, True

    @classmethod
    def validate_original_documents(cls, available: Optional[bool], uncertain: bool = False) -> Tuple[bool, Optional[str], bool]:
        """
        Must have physical original property documents.
        """
        if uncertain:
            return False, None, True
        if available is None:
            return False, None, False
        if available:
            return True, None, False
        return False, "Original property documents are mandatory. Copies or pledged documents are ineligible.", False

    @classmethod
    def validate_loan_amount(cls, requested: Optional[float], confirmed: Optional[float], pending_alternative: bool = False) -> Tuple[bool, Optional[str], bool]:
        """
        Max ₹75,00,000 inclusive.
        If requested > 75L, pending_alternative is True until confirmed or declined.
        """
        if confirmed is not None:
            if confirmed <= cls.MAX_LOAN_AMOUNT and confirmed > 0:
                return True, None, False
            else:
                return False, f"Confirmed loan amount ₹{confirmed:,.0f} exceeds maximum offer limit of ₹75 Lakh.", False
        
        if requested is not None:
            if requested <= cls.MAX_LOAN_AMOUNT and requested > 0:
                return True, None, False
            if pending_alternative:
                return False, None, True  # Clarification/Alternative acceptance pending
            return False, f"Requested loan amount ₹{requested:,.0f} exceeds maximum offer limit of ₹75 Lakh.", False

        return False, None, False

    @classmethod
    def validate_occupation_and_income_mode(cls, occupation: Optional[str], income_mode: Optional[str], both_pending: bool = False) -> Tuple[bool, Optional[str], bool]:
        """
        Occupation: Salaried or Self-employed.
        Income mode: Bank strictly required. Cash is immediately disqualified.
        Both: Needs clarification on whether loan-qualifying income is in bank.
        """
        # Income mode check first (disqualifier)
        if income_mode:
            cleaned_mode = income_mode.strip().lower()
            if cleaned_mode == "cash":
                return False, "Income received strictly in cash is ineligible. Bank credit is mandatory.", False
            if cleaned_mode == "both" or both_pending:
                return False, None, True  # Clarification needed
            if cleaned_mode != "bank":
                return False, None, True

        # Occupation check
        if occupation:
            cleaned_occ = occupation.strip().lower()
            if cleaned_occ not in cls.ALLOWED_OCCUPATIONS:
                return False, f"Occupation '{occupation}' is not within eligible salaried or self-employed categories.", False

        # If both are present and valid
        if occupation and income_mode:
            cleaned_mode = income_mode.strip().lower()
            cleaned_occ = occupation.strip().lower()
            if cleaned_occ in cls.ALLOWED_OCCUPATIONS and cleaned_mode == "bank":
                return True, None, False

        return False, None, False

    @classmethod
    def validate_market_value(cls, market_value: Optional[float]) -> Tuple[bool, Optional[str], bool]:
        """
        No minimum threshold, but must be recorded and positive.
        """
        if market_value is not None:
            if market_value > 0:
                return True, None, False
            return False, "Market value must be a positive number.", False
        return False, None, False

    @classmethod
    def validate_tenure(cls, tenure_years: Optional[int], uncertain: bool = False) -> Tuple[bool, Optional[str], bool]:
        """
        Allowed tenure: 3 to 15 years inclusive.
        """
        if uncertain:
            return False, None, True
        if tenure_years is None:
            return False, None, False
        if cls.MIN_TENURE_YEARS <= tenure_years <= cls.MAX_TENURE_YEARS:
            return True, None, False
        return False, f"Tenure of {tenure_years} years is outside the eligible range of 3 to 15 years.", False

    @classmethod
    def evaluate_state(cls, state: QualificationState) -> QualificationState:
        """
        Full deterministic evaluation of the qualification state.
        Enforces exact priority order:
        1. Customer busy -> CALLBACK_REQUESTED
        2. Customer declined -> CUSTOMER_DECLINED
        3. Existing loan / EMI reduction -> LOAN_TRANSFER
        4. Immediate disqualification -> NOT_ELIGIBLE
        5. Pending clarifications -> NEEDS_CLARIFICATION
        6. All 7 items complete and valid -> QUALIFIED
        7. Otherwise -> IN_PROGRESS
        """
        answered_items = []
        pending_clarifications = []

        # 1. Customer Busy Check
        if state.customer_busy:
            state.qualification_status = QualificationStatus.CALLBACK_REQUESTED
            state.call_ended = True
            state.decision_explanation = f"Customer requested a callback for {state.callback_time or 'a later time'}."
            return state

        # 2. Customer Declined Check
        if state.call_intent == "DECLINE" or state.qualification_status == QualificationStatus.CUSTOMER_DECLINED:
            state.qualification_status = QualificationStatus.CUSTOMER_DECLINED
            state.call_ended = True
            state.decision_explanation = "Customer explicitly declined to proceed with the Loan Against Property offer."
            return state

        # 3. Transfer Intent Check (Existing property loan or EMI reduction)
        if state.transfer_required:
            state.qualification_status = QualificationStatus.LOAN_TRANSFER
            state.call_ended = True
            reason = state.transfer_reason or "Customer has an existing loan on property or requested EMI reduction."
            state.decision_explanation = f"Routed to Loan-Transfer Specialist: {reason}"
            return state

        # 4. Evaluate Item 1: Property Type
        if state.property_type:
            valid, err, needs_clar = cls.validate_property_type(state.property_type)
            if err:
                state.disqualified = True
                state.disqualification_reason = err
                state.qualification_status = QualificationStatus.NOT_ELIGIBLE
                state.call_ended = True
                state.decision_explanation = f"Disqualified: {err}"
                return state
            if needs_clar:
                pending_clarifications.append("Property Type classification")
            elif valid:
                answered_items.append("property_type")

        # 5. Evaluate Item 2: Ownership Status
        if state.ownership_status:
            valid, err, needs_clar = cls.validate_ownership(state.ownership_status)
            if err:
                state.disqualified = True
                state.disqualification_reason = err
                state.qualification_status = QualificationStatus.NOT_ELIGIBLE
                state.call_ended = True
                state.decision_explanation = f"Disqualified: {err}"
                return state
            if needs_clar:
                pending_clarifications.append("Ownership Status clarification")
            elif valid:
                answered_items.append("ownership_status")

        # 6. Evaluate Item 3: Original Documents
        if state.original_documents_available is not None or state.original_documents_uncertain:
            valid, err, needs_clar = cls.validate_original_documents(
                state.original_documents_available, 
                state.original_documents_uncertain
            )
            if err:
                state.disqualified = True
                state.disqualification_reason = err
                state.qualification_status = QualificationStatus.NOT_ELIGIBLE
                state.call_ended = True
                state.decision_explanation = f"Disqualified: {err}"
                return state
            if needs_clar:
                pending_clarifications.append("Availability of original property documents")
            elif valid:
                answered_items.append("original_documents")

        # 7. Evaluate Item 4: Loan Amount
        if state.loan_amount_confirmed is not None or state.loan_amount_requested is not None:
            valid, err, needs_clar = cls.validate_loan_amount(
                state.loan_amount_requested, 
                state.loan_amount_confirmed, 
                state.excess_loan_offer_pending
            )
            if err and not state.excess_loan_offer_pending:
                state.disqualified = True
                state.disqualification_reason = err
                state.qualification_status = QualificationStatus.NOT_ELIGIBLE
                state.call_ended = True
                state.decision_explanation = f"Disqualified: {err}"
                return state
            if needs_clar:
                pending_clarifications.append("Desired loan amount within ₹75 Lakh cap")
            elif valid:
                answered_items.append("loan_amount")

        # 8. Evaluate Item 5: Occupation and Income Mode
        if state.occupation or state.income_mode or state.income_mode_both_pending:
            valid, err, needs_clar = cls.validate_occupation_and_income_mode(
                state.occupation, 
                state.income_mode, 
                state.income_mode_both_pending
            )
            if err:
                state.disqualified = True
                state.disqualification_reason = err
                state.qualification_status = QualificationStatus.NOT_ELIGIBLE
                state.call_ended = True
                state.decision_explanation = f"Disqualified: {err}"
                return state
            if needs_clar:
                pending_clarifications.append("Occupation & primary bank income mode")
            elif valid and state.occupation and state.income_mode:
                answered_items.append("occupation_and_income_mode")

        # 9. Evaluate Item 6: Market Value
        if state.market_value is not None:
            valid, err, needs_clar = cls.validate_market_value(state.market_value)
            if err:
                pending_clarifications.append("Property market value estimate")
            elif valid:
                answered_items.append("market_value")

        # 10. Evaluate Item 7: Tenure
        if state.tenure_years is not None or state.tenure_uncertain:
            valid, err, needs_clar = cls.validate_tenure(state.tenure_years, state.tenure_uncertain)
            if err:
                state.disqualified = True
                state.disqualification_reason = err
                state.qualification_status = QualificationStatus.NOT_ELIGIBLE
                state.call_ended = True
                state.decision_explanation = f"Disqualified: {err}"
                return state
            if needs_clar:
                pending_clarifications.append("Repayment tenure (3-15 years)")
            elif valid:
                answered_items.append("tenure_years")

        state.answered_items = answered_items
        state.pending_clarifications = pending_clarifications

        # 11. Final Handoff Gate Evaluation
        # Checklist must contain all 7 items:
        all_7_items = {
            "property_type",
            "ownership_status",
            "original_documents",
            "loan_amount",
            "occupation_and_income_mode",
            "market_value",
            "tenure_years"
        }
        
        is_complete = all_7_items.issubset(set(answered_items))

        if pending_clarifications:
            state.qualification_status = QualificationStatus.NEEDS_CLARIFICATION
            state.decision_explanation = f"Clarification pending on: {', '.join(pending_clarifications)}"
            return state

        if is_complete and state.customer_verified and not state.disqualified:
            state.qualification_status = QualificationStatus.QUALIFIED
            state.call_ended = True
            state.decision_explanation = (
                f"Preliminary qualification PASSED! All 7 checklist items validated successfully. "
                f"Customer requested ₹{state.loan_amount_confirmed or state.loan_amount_requested:,.0f} "
                f"for {state.tenure_years} years on {state.property_type.lower()} property. Senior Loan Expert will follow up."
            )
            return state

        # If still in progress
        state.qualification_status = QualificationStatus.IN_PROGRESS
        missing = list(all_7_items - set(answered_items))
        state.decision_explanation = f"Qualification in progress ({len(answered_items)} of 7 items completed). Missing: {', '.join(missing)}"
        return state

    @classmethod
    def get_earliest_unanswered_item(cls, state: QualificationState) -> Optional[str]:
        """
        Determines the earliest unanswered checklist item in standard order:
        1. verification (if not verified)
        2. property_type
        3. ownership_status
        4. original_documents
        5. loan_amount
        6. occupation_and_income_mode
        7. market_value
        8. tenure_years
        """
        if not state.customer_verified:
            return "verification"

        if state.pending_clarifications:
            return "clarification"

        if "property_type" not in state.answered_items:
            return "property_type"
        if "ownership_status" not in state.answered_items:
            return "ownership_status"
        if "original_documents" not in state.answered_items:
            return "original_documents"
        if "loan_amount" not in state.answered_items:
            return "loan_amount"
        if "occupation_and_income_mode" not in state.answered_items:
            if not state.occupation:
                return "occupation"
            if not state.income_mode:
                return "income_mode"
            return "occupation_and_income_mode"
        if "market_value" not in state.answered_items:
            return "market_value"
        if "tenure_years" not in state.answered_items:
            return "tenure_years"

        return None
