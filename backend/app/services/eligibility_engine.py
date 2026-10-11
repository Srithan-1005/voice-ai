"""
eligibility_engine.py
=====================
Deterministic eligibility engine for Home Credit LAP Qualification.

Responsibilities:
  - Accept a structured QualificationState object.
  - Validate all 7 checklist items against Home Credit LAP rules.
  - Identify which fields are still missing or need clarification.
  - Return the next appropriate question or terminal action label.
  - Return a rich EligibilityResult without touching any LLM code.

The LLM / NLP extraction layer (ExtractionService) is intentionally kept
completely separate: this module contains ONLY deterministic rule evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from app.schemas.state import QualificationState, QualificationStatus
from app.services.eligibility_service import EligibilityService


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class EligibilityResult:
    """
    Rich result produced by the eligibility engine after evaluating the full
    qualification state.
    """

    # Final qualification status (mirrors QualificationStatus enum values)
    status: str

    # True only when all 7 items pass and customer is verified
    is_qualified: bool

    # True when a hard disqualification rule fired
    is_disqualified: bool

    # Human-readable reason for disqualification (if any)
    disqualification_reason: Optional[str]

    # True when the session should be handed to a loan-transfer specialist
    transfer_required: bool

    # Human-readable reason for transfer routing (if any)
    transfer_reason: Optional[str]

    # True when the call is over (qualified / disqualified / declined / callback)
    call_ended: bool

    # Verbose explanation of the current decision state
    decision_explanation: str

    # Names of checklist items that have been successfully answered
    answered_items: List[str]

    # Names of fields that have not yet been provided by the customer
    pending_fields: List[str]

    # Items that need clarification (ambiguous / conflicting answers)
    pending_clarifications: List[str]

    # The field / question that the agent should ask next (None = call is done)
    next_question_key: Optional[str]

    # Human-readable text of the next question to ask the customer
    next_question_text: Optional[str]


# ---------------------------------------------------------------------------
# Field ordering used throughout the engine
# ---------------------------------------------------------------------------

_ORDERED_ITEMS = [
    "property_type",
    "ownership_status",
    "original_documents",
    "loan_amount",
    "occupation_and_income_mode",
    "market_value",
    "tenure_years",
]

_ALL_7_ITEMS = set(_ORDERED_ITEMS)

# ---------------------------------------------------------------------------
# Human-readable question templates
# ---------------------------------------------------------------------------

_QUESTION_TEXT: dict[str, str] = {
    "verification": (
        "May I confirm I'm speaking with {customer_name}?"
    ),
    "property_type": (
        "What type of property do you own — residential, commercial, or industrial?"
    ),
    "ownership_status": (
        "Are you the sole owner of the property, or is it jointly owned?"
    ),
    "original_documents": (
        "Do you have the physical original property title documents available for verification?"
    ),
    "loan_amount": (
        "How much loan amount are you looking for?"
    ),
    "occupation": (
        "Could you tell me your occupation — are you salaried or self-employed?"
    ),
    "income_mode": (
        "Is your income received directly through your bank account?"
    ),
    "occupation_and_income_mode": (
        "Could you tell me your occupation, and whether your income is received in your bank account?"
    ),
    "market_value": (
        "What is the approximate current market value of your property?"
    ),
    "tenure_years": (
        "What repayment tenure were you considering — between 3 and 15 years?"
    ),
    "clarification": (
        "Could you please clarify the details we discussed?"
    ),
}


# ---------------------------------------------------------------------------
# Main engine class
# ---------------------------------------------------------------------------

class EligibilityEngine:
    """
    Stateless deterministic eligibility engine.

    Usage
    -----
    >>> result = EligibilityEngine.evaluate(state)
    >>> print(result.next_question_text)
    'Do you have the physical original property title documents available for verification?'
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @classmethod
    def evaluate(cls, state: QualificationState) -> EligibilityResult:
        """
        Full deterministic evaluation of a QualificationState.

        1. Delegates rule validation to EligibilityService.evaluate_state()
           (which mutates the state in-place with answered_items and statuses).
        2. Computes pending_fields from the 7-item ordered list.
        3. Determines the next question to ask.
        4. Returns an EligibilityResult without altering the state further.

        Parameters
        ----------
        state:
            The current QualificationState (may be mutated by EligibilityService
            — callers should treat the returned state as authoritative).

        Returns
        -------
        EligibilityResult
        """
        # Run the core deterministic rule evaluation (mutates state in-place)
        evaluated = EligibilityService.evaluate_state(state)

        # Compute pending fields
        pending_fields = cls._identify_pending_fields(evaluated)

        # Determine next question
        next_key = EligibilityService.get_earliest_unanswered_item(evaluated)
        next_text = cls._question_text(next_key, evaluated)

        return EligibilityResult(
            status=evaluated.qualification_status.value,
            is_qualified=(
                evaluated.qualification_status == QualificationStatus.QUALIFIED
            ),
            is_disqualified=evaluated.disqualified,
            disqualification_reason=evaluated.disqualification_reason,
            transfer_required=evaluated.transfer_required,
            transfer_reason=evaluated.transfer_reason,
            call_ended=evaluated.call_ended,
            decision_explanation=evaluated.decision_explanation or "",
            answered_items=list(evaluated.answered_items),
            pending_fields=pending_fields,
            pending_clarifications=list(evaluated.pending_clarifications),
            next_question_key=next_key,
            next_question_text=next_text,
        )

    # ------------------------------------------------------------------
    # Field-level validators (expose individual rule results)
    # ------------------------------------------------------------------

    @classmethod
    def validate_property_type(cls, prop_type: Optional[str]):
        """Returns (is_valid, error_reason, needs_clarification)."""
        return EligibilityService.validate_property_type(prop_type)

    @classmethod
    def validate_ownership(cls, ownership: Optional[str]):
        """Returns (is_valid, error_reason, needs_clarification)."""
        return EligibilityService.validate_ownership(ownership)

    @classmethod
    def validate_original_documents(
        cls, available: Optional[bool], uncertain: bool = False
    ):
        """Returns (is_valid, error_reason, needs_clarification)."""
        return EligibilityService.validate_original_documents(available, uncertain)

    @classmethod
    def validate_loan_amount(
        cls,
        requested: Optional[float],
        confirmed: Optional[float],
        pending_alternative: bool = False,
    ):
        """Returns (is_valid, error_reason, needs_clarification)."""
        return EligibilityService.validate_loan_amount(
            requested, confirmed, pending_alternative
        )

    @classmethod
    def validate_occupation_and_income_mode(
        cls,
        occupation: Optional[str],
        income_mode: Optional[str],
        both_pending: bool = False,
    ):
        """Returns (is_valid, error_reason, needs_clarification)."""
        return EligibilityService.validate_occupation_and_income_mode(
            occupation, income_mode, both_pending
        )

    @classmethod
    def validate_market_value(cls, market_value: Optional[float]):
        """Returns (is_valid, error_reason, needs_clarification)."""
        return EligibilityService.validate_market_value(market_value)

    @classmethod
    def validate_tenure(
        cls, tenure_years: Optional[int], uncertain: bool = False
    ):
        """Returns (is_valid, error_reason, needs_clarification)."""
        return EligibilityService.validate_tenure(tenure_years, uncertain)

    # ------------------------------------------------------------------
    # Helper: pending fields
    # ------------------------------------------------------------------

    @classmethod
    def _identify_pending_fields(cls, state: QualificationState) -> List[str]:
        """
        Returns the ordered list of checklist item keys that have NOT yet been
        successfully answered.  Clarification items are included because they
        are still unresolved.
        """
        answered = set(state.answered_items)
        pending: List[str] = []

        for item in _ORDERED_ITEMS:
            if item not in answered:
                # Only add if not already a hard disqualifier (call already ended)
                if not (state.call_ended and state.disqualified):
                    pending.append(item)

        return pending

    # ------------------------------------------------------------------
    # Helper: question text
    # ------------------------------------------------------------------

    @classmethod
    def _question_text(
        cls, key: Optional[str], state: QualificationState
    ) -> Optional[str]:
        if key is None:
            return None
        tmpl = _QUESTION_TEXT.get(key)
        if tmpl is None:
            return None
        customer_name = state.customer_name or "valued customer"
        return tmpl.format(customer_name=customer_name)


# ---------------------------------------------------------------------------
# Convenience function (module-level shorthand)
# ---------------------------------------------------------------------------

def evaluate_eligibility(state: QualificationState) -> EligibilityResult:
    """
    Module-level shorthand for EligibilityEngine.evaluate(state).

    >>> from app.services.eligibility_engine import evaluate_eligibility
    >>> result = evaluate_eligibility(state)
    """
    return EligibilityEngine.evaluate(state)
