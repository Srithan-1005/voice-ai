"""
test_eligibility_engine.py
==========================
Tests for the EligibilityEngine module (eligibility_engine.py).

Covers:
  - Multi-fact utterance (the canonical "₹1 crore property, ₹50 lakh loan" message)
  - Out-of-order answers
  - Corrections / value overrides
  - Unclear / ambiguous answers
  - Duplicate / redundant information
  - Agricultural property disqualification
  - Missing original documents disqualification
  - Cash-only income disqualification
  - Tenure outside 3-15 years
  - Loan above ₹75 lakh → offer cap
  - Acceptance of ₹75 lakh cap
  - Rejection of ₹75 lakh cap → customer decline
  - Transfer intent (existing loan / EMI reduction)
  - Session state persistence (no checklist reset between messages)
  - next_question ordering
"""

import pytest
from app.schemas.state import QualificationState, QualificationStatus, ConversationMessage, MessageRole
from app.services.eligibility_engine import EligibilityEngine, evaluate_eligibility
from app.services.extraction_service import ExtractionService
from app.services.conversation_service import ConversationService


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_full_state(**kwargs) -> QualificationState:
    """Returns a fully-answered, verified state that is QUALIFIED."""
    defaults = dict(
        customer_name="Test Customer",
        customer_verified=True,
        property_type="Residential",
        ownership_status="Sole ownership",
        original_documents_available=True,
        loan_amount_requested=5000000.0,
        loan_amount_confirmed=5000000.0,
        occupation="Salaried",
        income_mode="Bank",
        market_value=10000000.0,
        tenure_years=10,
    )
    defaults.update(kwargs)
    return QualificationState(**defaults)


def extract_and_apply(message: str, state: QualificationState) -> QualificationState:
    """Convenience: extract facts from message and apply them to a copy of state."""
    updates = ExtractionService.extract_all_facts(message, state)
    for k, v in updates.items():
        setattr(state, k, v)
    return state


# ─────────────────────────────────────────────────────────────────────────────
# 1. Multi-fact utterance — the canonical test message
# ─────────────────────────────────────────────────────────────────────────────

class TestCanonicalMultiFactMessage:
    """
    Message: "It's a residential property jointly owned with my brother,
              worth ₹1 crore, and I need ₹50 lakh."

    Expected extraction:
      property_type    → Residential
      ownership_status → Joint ownership
      market_value     → ₹1,00,00,000  (1 crore)
      loan_amount      → ₹50,00,000    (50 lakh)

    Expected still-pending:
      original_documents, occupation, income_mode, tenure_years

    Next question (assuming property_type & ownership_status already answered
    in priority order) → original_documents
    """

    MESSAGE = (
        "It's a residential property jointly owned with my brother, "
        "worth ₹1 crore, and I need ₹50 lakh."
    )

    def _do_extraction(self) -> dict:
        state = QualificationState(customer_verified=True)
        return ExtractionService.extract_all_facts(self.MESSAGE, state)

    def test_property_type_extracted(self):
        facts = self._do_extraction()
        assert facts.get("property_type") == "Residential"

    def test_ownership_extracted(self):
        facts = self._do_extraction()
        assert facts.get("ownership_status") == "Joint ownership"

    def test_market_value_extracted(self):
        facts = self._do_extraction()
        assert facts.get("market_value") == 10_000_000.0   # 1 crore

    def test_loan_amount_extracted(self):
        facts = self._do_extraction()
        # ₹50 lakh = 5,000,000 — within cap so both fields set
        assert facts.get("loan_amount_requested") == 5_000_000.0
        assert facts.get("loan_amount_confirmed") == 5_000_000.0

    def test_no_invented_fields(self):
        """Engine must not fabricate occupation, income_mode, tenure, or docs."""
        facts = self._do_extraction()
        assert "occupation" not in facts
        assert "income_mode" not in facts
        assert "tenure_years" not in facts
        assert "original_documents_available" not in facts

    def test_pending_fields_after_extraction(self):
        """After the message, original_docs / occupation / income_mode / tenure pending."""
        state = QualificationState(customer_verified=True)
        state = extract_and_apply(self.MESSAGE, state)
        result = evaluate_eligibility(state)
        pending = result.pending_fields
        assert "original_documents" in pending
        assert "occupation_and_income_mode" in pending
        assert "tenure_years" in pending

    def test_next_question_is_original_documents(self):
        """
        With property_type and ownership both answered, the next unanswered
        checklist item in priority order is original_documents.
        """
        state = QualificationState(customer_verified=True)
        state = extract_and_apply(self.MESSAGE, state)
        result = evaluate_eligibility(state)
        assert result.next_question_key == "original_documents"

    def test_qualification_status_in_progress(self):
        state = QualificationState(customer_verified=True)
        state = extract_and_apply(self.MESSAGE, state)
        result = evaluate_eligibility(state)
        assert result.status == QualificationStatus.IN_PROGRESS.value
        assert not result.is_qualified
        assert not result.is_disqualified

    def test_no_reset_of_existing_checklist_items(self):
        """
        Simulate a multi-turn conversation: earlier answers must survive
        when a new message provides additional facts.
        """
        state = QualificationState(customer_verified=True)
        # Turn 1: customer already said original docs are available
        state.original_documents_available = True
        # Turn 2: the canonical multi-fact message
        state = extract_and_apply(self.MESSAGE, state)
        result = evaluate_eligibility(state)
        # original_documents should now be answered
        assert "original_documents" in result.answered_items


# ─────────────────────────────────────────────────────────────────────────────
# 2. Out-of-order answers
# ─────────────────────────────────────────────────────────────────────────────

class TestOutOfOrderAnswers:

    def test_tenure_provided_before_property_type(self):
        """Customer gives tenure first; engine accepts it without complaint."""
        state = QualificationState(customer_verified=True)
        state = extract_and_apply("I want a 10 year tenure", state)
        result = evaluate_eligibility(state)
        assert state.tenure_years == 10
        # property_type still pending → next question is property_type
        assert result.next_question_key == "property_type"

    def test_loan_amount_provided_before_ownership(self):
        state = QualificationState(customer_verified=True)
        state = extract_and_apply("I need 40 lakh", state)
        assert state.loan_amount_confirmed == 4_000_000.0
        result = evaluate_eligibility(state)
        assert result.next_question_key == "property_type"

    def test_all_facts_out_of_order_yields_correct_pending(self):
        """Give income+occupation before ownership; pending must be ownership & docs."""
        state = QualificationState(customer_verified=True)
        state.property_type = "Residential"
        state = extract_and_apply(
            "I am salaried and my salary goes to bank, need 30 lakh for 5 years", state
        )
        result = evaluate_eligibility(state)
        assert "ownership_status" in result.pending_fields


# ─────────────────────────────────────────────────────────────────────────────
# 3. Corrections / value overrides
# ─────────────────────────────────────────────────────────────────────────────

class TestCorrections:

    def test_loan_amount_correction_in_single_utterance(self):
        """'I need 40 lakhs — actually 60 lakhs' should capture 60."""
        val = ExtractionService.parse_currency_amount(
            "I need 40 lakhs - actually 60 lakhs"
        )
        assert val == 6_000_000.0

    def test_tenure_correction_in_single_utterance(self):
        tenure, uncertain = ExtractionService.parse_tenure_years(
            "ten years - actually, twelve years"
        )
        assert tenure == 12
        assert not uncertain

    def test_property_type_overwrite_across_turns(self):
        """Second turn can correct property type without resetting other fields."""
        state = QualificationState(customer_verified=True)
        state.property_type = "Commercial"
        state.ownership_status = "Sole ownership"
        # Customer corrects: "actually it's residential"
        state = extract_and_apply(
            "Wait, I meant a residential house, not commercial", state
        )
        # After correction the type should be Residential
        assert state.property_type == "Residential"
        # Other field must be preserved
        assert state.ownership_status == "Sole ownership"

    def test_income_mode_correction_from_both_to_bank(self):
        """Customer first says 'both cash and bank', then clarifies bank only."""
        state = QualificationState(
            customer_verified=True,
            occupation="Self-employed",
            income_mode="Both",
            income_mode_both_pending=True,
        )
        state = extract_and_apply(
            "My primary qualifying income is via bank transfer", state
        )
        assert state.income_mode == "Bank"
        assert state.income_mode_both_pending is False


# ─────────────────────────────────────────────────────────────────────────────
# 4. Unclear / ambiguous answers
# ─────────────────────────────────────────────────────────────────────────────

class TestAmbiguousAnswers:

    def test_tenure_uncertain_flag(self):
        """'Maybe 5 or 7 years' → tenure_uncertain flag, clarification needed."""
        tenure, uncertain = ExtractionService.parse_tenure_years(
            "maybe 5 years or 7 years"
        )
        assert uncertain is True

    def test_ambiguous_tenure_triggers_clarification(self):
        state = QualificationState(customer_verified=True)
        state.tenure_uncertain = True
        result = evaluate_eligibility(state)
        assert "Repayment tenure" in " ".join(result.pending_clarifications)

    def test_both_income_mode_triggers_clarification(self):
        state = QualificationState(
            customer_verified=True,
            occupation="Self-employed",
            income_mode="Both",
            income_mode_both_pending=True,
        )
        result = evaluate_eligibility(state)
        assert result.status == QualificationStatus.NEEDS_CLARIFICATION.value
        assert any("bank" in c.lower() for c in result.pending_clarifications)

    def test_unknown_property_type_triggers_clarification(self):
        """A garden property type is not in the allowed set → clarification."""
        valid, err, needs_clar = EligibilityEngine.validate_property_type("garden")
        assert needs_clar is True
        assert err is None

    def test_no_value_invented_for_ambiguous_docs(self):
        """Engine must not invent original_documents_available = True."""
        state = QualificationState(customer_verified=True, original_documents_uncertain=True)
        result = evaluate_eligibility(state)
        # Must not be answered
        assert "original_documents" not in result.answered_items
        assert "original_documents" in result.pending_fields


# ─────────────────────────────────────────────────────────────────────────────
# 5. Duplicate / redundant information
# ─────────────────────────────────────────────────────────────────────────────

class TestDuplicateInformation:

    def test_repeated_property_type_no_side_effect(self):
        """Providing the same value again should not break state."""
        state = QualificationState(customer_verified=True)
        state.property_type = "Residential"
        state = extract_and_apply("It is residential", state)
        assert state.property_type == "Residential"
        result = evaluate_eligibility(state)
        # property_type should be answered
        assert "property_type" in result.answered_items

    def test_duplicate_loan_amount_stays_same(self):
        state = QualificationState(
            customer_verified=True,
            loan_amount_requested=5_000_000.0,
            loan_amount_confirmed=5_000_000.0,
        )
        # Send same value again
        state = extract_and_apply("I need 50 lakh", state)
        assert state.loan_amount_confirmed == 5_000_000.0


# ─────────────────────────────────────────────────────────────────────────────
# 6. Agricultural property — immediate disqualification
# ─────────────────────────────────────────────────────────────────────────────

class TestAgriculturalProperty:

    def test_agricultural_extraction(self):
        state = QualificationState(customer_verified=True)
        facts = ExtractionService.extract_all_facts(
            "It is an agricultural farmland", state
        )
        assert facts.get("property_type") == "Agricultural"

    def test_agricultural_engine_disqualifies(self):
        state = QualificationState(customer_verified=True, property_type="Agricultural")
        result = evaluate_eligibility(state)
        assert result.is_disqualified is True
        assert result.status == QualificationStatus.NOT_ELIGIBLE.value
        assert result.call_ended is True
        assert "Agricultural" in (result.disqualification_reason or "")

    def test_agricultural_conversation_flow(self):
        state, _ = ConversationService.initialize_conversation("Farmer")
        state.customer_verified = True
        state, resp = ConversationService.process_utterance(
            state, "It is agricultural farmland"
        )
        assert state.disqualified is True
        assert state.call_ended is True
        assert "won't be able to proceed" in resp.lower()


# ─────────────────────────────────────────────────────────────────────────────
# 7. Missing original documents — immediate disqualification
# ─────────────────────────────────────────────────────────────────────────────

class TestMissingOriginalDocuments:

    def test_no_originals_extraction(self):
        state = QualificationState(customer_verified=True)
        facts = ExtractionService.extract_all_facts(
            "I only have photocopies, the originals are with the bank", state
        )
        assert facts.get("original_documents_available") is False

    def test_no_originals_engine_disqualifies(self):
        state = QualificationState(
            customer_verified=True,
            property_type="Residential",
            ownership_status="Sole ownership",
            original_documents_available=False,
        )
        result = evaluate_eligibility(state)
        assert result.is_disqualified is True
        assert result.status == QualificationStatus.NOT_ELIGIBLE.value
        assert "mandatory" in (result.disqualification_reason or "").lower()

    def test_originals_available_passes(self):
        valid, err, needs_clar = EligibilityEngine.validate_original_documents(
            available=True
        )
        assert valid is True
        assert err is None


# ─────────────────────────────────────────────────────────────────────────────
# 8. Cash-only income — immediate disqualification
# ─────────────────────────────────────────────────────────────────────────────

class TestCashOnlyIncome:

    def test_cash_income_extraction(self):
        state = QualificationState(customer_verified=True)
        facts = ExtractionService.extract_all_facts(
            "I run a small shop and all income is cash", state
        )
        assert facts.get("income_mode") == "Cash"

    def test_cash_income_engine_disqualifies(self):
        state = make_full_state(income_mode="Cash")
        result = evaluate_eligibility(state)
        assert result.is_disqualified is True
        assert "cash" in (result.disqualification_reason or "").lower()

    def test_bank_income_passes(self):
        valid, err, needs_clar = EligibilityEngine.validate_occupation_and_income_mode(
            occupation="Salaried", income_mode="Bank"
        )
        assert valid is True
        assert err is None


# ─────────────────────────────────────────────────────────────────────────────
# 9. Tenure outside 3–15 years
# ─────────────────────────────────────────────────────────────────────────────

class TestTenureOutsideRange:

    @pytest.mark.parametrize("years", [1, 2, 16, 20, 25])
    def test_invalid_tenure_disqualifies(self, years: int):
        state = make_full_state(tenure_years=years)
        result = evaluate_eligibility(state)
        assert result.is_disqualified is True
        assert result.status == QualificationStatus.NOT_ELIGIBLE.value

    @pytest.mark.parametrize("years", [3, 5, 10, 15])
    def test_valid_tenure_passes(self, years: int):
        state = make_full_state(tenure_years=years)
        result = evaluate_eligibility(state)
        assert result.is_qualified is True

    def test_tenure_2_years_engine_message(self):
        valid, err, _ = EligibilityEngine.validate_tenure(2)
        assert not valid
        assert "2 years" in (err or "")

    def test_tenure_16_years_engine_message(self):
        valid, err, _ = EligibilityEngine.validate_tenure(16)
        assert not valid
        assert "16 years" in (err or "")


# ─────────────────────────────────────────────────────────────────────────────
# 10. Loan above ₹75 lakh — offer cap
# ─────────────────────────────────────────────────────────────────────────────

class TestLoanAboveCap:

    def test_loan_above_cap_extraction(self):
        state = QualificationState(customer_verified=True)
        facts = ExtractionService.extract_all_facts("I need 1 crore", state)
        assert facts.get("loan_amount_requested") == 10_000_000.0
        assert facts.get("excess_loan_offer_pending") is True

    def test_loan_above_cap_triggers_offer_pending(self):
        state = QualificationState(
            customer_verified=True,
            property_type="Residential",
            loan_amount_requested=10_000_000.0,
            excess_loan_offer_pending=True,
        )
        result = evaluate_eligibility(state)
        # Should not hard-disqualify yet — pending cap acceptance
        assert result.status in (
            QualificationStatus.IN_PROGRESS.value,
            QualificationStatus.NEEDS_CLARIFICATION.value,
        )
        assert not result.is_disqualified

    def test_loan_exactly_75_lakh_passes(self):
        valid, err, _ = EligibilityEngine.validate_loan_amount(
            requested=7_500_000.0, confirmed=7_500_000.0
        )
        assert valid is True
        assert err is None

    def test_loan_above_cap_then_disqualify(self):
        """Confirmed amount > ₹75L should disqualify."""
        state = make_full_state(
            loan_amount_requested=10_000_000.0,
            loan_amount_confirmed=10_000_000.0,
            excess_loan_offer_pending=False,
        )
        result = evaluate_eligibility(state)
        assert result.is_disqualified is True


# ─────────────────────────────────────────────────────────────────────────────
# 11. Acceptance of ₹75 lakh cap
# ─────────────────────────────────────────────────────────────────────────────

class TestCapAcceptance:

    def _state_with_excess_pending(self) -> QualificationState:
        return QualificationState(
            customer_verified=True,
            property_type="Residential",
            ownership_status="Sole ownership",
            original_documents_available=True,
            loan_amount_requested=10_000_000.0,
            excess_loan_offer_pending=True,
            occupation="Salaried",
            income_mode="Bank",
            market_value=15_000_000.0,
            tenure_years=10,
        )

    def test_acceptance_phrase_accepted(self):
        state = self._state_with_excess_pending()
        state, resp = ConversationService.process_utterance(
            state, "Yes, 75 lakh is fine with me"
        )
        assert state.loan_amount_confirmed == 7_500_000.0
        assert state.excess_loan_offer_pending is False
        assert state.qualification_status == QualificationStatus.QUALIFIED

    def test_acceptance_via_okay(self):
        state = self._state_with_excess_pending()
        state, _ = ConversationService.process_utterance(state, "Okay that works")
        assert state.loan_amount_confirmed == 7_500_000.0

    def test_acceptance_engine_result_is_qualified(self):
        state = make_full_state(
            loan_amount_requested=10_000_000.0,
            loan_amount_confirmed=7_500_000.0,
            excess_loan_offer_pending=False,
        )
        result = evaluate_eligibility(state)
        assert result.is_qualified is True


# ─────────────────────────────────────────────────────────────────────────────
# 12. Rejection of ₹75 lakh cap
# ─────────────────────────────────────────────────────────────────────────────

class TestCapRejection:

    def _state_with_excess_pending(self) -> QualificationState:
        return QualificationState(
            customer_verified=True,
            property_type="Residential",
            ownership_status="Sole ownership",
            original_documents_available=True,
            loan_amount_requested=10_000_000.0,
            excess_loan_offer_pending=True,
            occupation="Salaried",
            income_mode="Bank",
            market_value=15_000_000.0,
            tenure_years=10,
        )

    def test_rejection_phrase_declines(self):
        state = self._state_with_excess_pending()
        state, resp = ConversationService.process_utterance(
            state, "No, 75 lakh is not enough, cancel this"
        )
        assert state.call_ended is True
        assert state.qualification_status == QualificationStatus.CUSTOMER_DECLINED

    def test_rejection_via_need_more(self):
        state = self._state_with_excess_pending()
        state, _ = ConversationService.process_utterance(
            state, "No, I need more than that"
        )
        assert state.call_ended is True


# ─────────────────────────────────────────────────────────────────────────────
# 13. Transfer requests (existing loan / EMI reduction)
# ─────────────────────────────────────────────────────────────────────────────

class TestTransferRequests:

    @pytest.mark.parametrize("utterance", [
        "I already have a loan on this property",
        "I want to reduce my current EMI",
        "I have an existing loan on this property with HDFC Bank",
        "Can you do a balance transfer for my existing mortgage?",
        "I want to transfer my loan",
    ])
    def test_transfer_intent_extracted(self, utterance: str):
        from app.services.extraction_service import ExtractionService as ES, CallIntent
        intent = ES.extract_customer_intent(utterance)
        assert intent == CallIntent.LOAN_TRANSFER, (
            f"Expected LOAN_TRANSFER for: '{utterance}'"
        )

    def test_transfer_engine_routes_correctly(self):
        state = QualificationState(
            customer_verified=True,
            transfer_required=True,
            transfer_reason="Customer has existing property loan.",
        )
        result = evaluate_eligibility(state)
        assert result.transfer_required is True
        assert result.status == QualificationStatus.LOAN_TRANSFER.value
        assert result.call_ended is True

    def test_transfer_conversation_flow(self):
        state, _ = ConversationService.initialize_conversation("Rahul")
        state.customer_verified = True
        state, resp = ConversationService.process_utterance(
            state, "I already have a loan on this property and want to reduce EMI"
        )
        assert state.transfer_required is True
        assert state.call_ended is True
        assert "loan-transfer specialist" in resp.lower()


# ─────────────────────────────────────────────────────────────────────────────
# 14. Session state persistence — no checklist reset between messages
# ─────────────────────────────────────────────────────────────────────────────

class TestSessionStatePersistence:

    def test_facts_accumulate_across_turns(self):
        """Multi-turn conversation: facts must accumulate, not reset."""
        state, _ = ConversationService.initialize_conversation("Priya Sharma")
        # Turn 1 – verification
        state, _ = ConversationService.process_utterance(state, "Yes, speaking")
        assert state.customer_verified is True

        # Turn 2 – property + ownership (multi-fact)
        state, _ = ConversationService.process_utterance(
            state,
            "It's a residential property jointly owned with my brother, "
            "worth ₹1 crore, and I need ₹50 lakh."
        )
        assert state.property_type == "Residential"
        assert state.ownership_status == "Joint ownership"
        assert state.market_value == 10_000_000.0
        assert state.loan_amount_confirmed == 5_000_000.0

        # Turn 3 – original documents
        state, _ = ConversationService.process_utterance(
            state, "Yes, I have the original papers at home"
        )
        assert state.original_documents_available is True

        # Verify property_type still intact (not reset)
        assert state.property_type == "Residential"
        assert state.ownership_status == "Joint ownership"

    def test_no_repeat_question_after_answered(self):
        """Agent must not ask for property_type after it is answered."""
        state, _ = ConversationService.initialize_conversation("Test")
        state, _ = ConversationService.process_utterance(state, "Yes, speaking")
        state, _ = ConversationService.process_utterance(
            state, "It is a residential house"
        )
        next_item = __import__(
            "app.services.eligibility_service",
            fromlist=["EligibilityService"]
        ).EligibilityService.get_earliest_unanswered_item(state)
        # Should NOT ask for property_type again
        assert next_item != "property_type"

    def test_pending_fields_decrease_with_each_answer(self):
        """Each additional answer should reduce the pending field count."""
        state = QualificationState(customer_verified=True)
        result0 = evaluate_eligibility(state)
        initial_pending = len(result0.pending_fields)

        state.property_type = "Residential"
        result1 = evaluate_eligibility(state)
        assert len(result1.pending_fields) < initial_pending

        state.ownership_status = "Sole ownership"
        result2 = evaluate_eligibility(state)
        assert len(result2.pending_fields) < len(result1.pending_fields)


# ─────────────────────────────────────────────────────────────────────────────
# 15. Engine — next_question ordering
# ─────────────────────────────────────────────────────────────────────────────

class TestNextQuestionOrdering:

    def test_first_question_is_property_type_when_verified(self):
        state = QualificationState(customer_verified=True)
        result = evaluate_eligibility(state)
        assert result.next_question_key == "property_type"

    def test_after_property_type_is_ownership(self):
        state = QualificationState(
            customer_verified=True, property_type="Residential"
        )
        result = evaluate_eligibility(state)
        assert result.next_question_key == "ownership_status"

    def test_after_property_and_ownership_is_documents(self):
        state = QualificationState(
            customer_verified=True,
            property_type="Residential",
            ownership_status="Sole ownership",
        )
        result = evaluate_eligibility(state)
        assert result.next_question_key == "original_documents"

    def test_after_documents_is_loan_amount(self):
        state = QualificationState(
            customer_verified=True,
            property_type="Residential",
            ownership_status="Sole ownership",
            original_documents_available=True,
        )
        result = evaluate_eligibility(state)
        assert result.next_question_key == "loan_amount"

    def test_after_all_answered_no_next_question(self):
        state = make_full_state()
        result = evaluate_eligibility(state)
        assert result.is_qualified is True
        assert result.next_question_key is None

    def test_next_question_text_not_empty(self):
        """Engine always provides human-readable text for each question key."""
        state = QualificationState(customer_verified=True)
        result = evaluate_eligibility(state)
        assert result.next_question_text
        assert len(result.next_question_text) > 10

    def test_unverified_customer_next_question_is_verification(self):
        state = QualificationState(customer_verified=False)
        result = evaluate_eligibility(state)
        assert result.next_question_key == "verification"


# ─────────────────────────────────────────────────────────────────────────────
# 16. Individual field validators through the engine facade
# ─────────────────────────────────────────────────────────────────────────────

class TestEngineFieldValidators:

    def test_validate_property_type_residential(self):
        valid, err, needs_clar = EligibilityEngine.validate_property_type("residential")
        assert valid and not err and not needs_clar

    def test_validate_property_type_agricultural_disqualifies(self):
        valid, err, needs_clar = EligibilityEngine.validate_property_type("agricultural")
        assert not valid and err and not needs_clar

    def test_validate_ownership_joint(self):
        valid, err, needs_clar = EligibilityEngine.validate_ownership("joint")
        assert valid

    def test_validate_docs_false_disqualifies(self):
        valid, err, needs_clar = EligibilityEngine.validate_original_documents(
            available=False
        )
        assert not valid and err

    def test_validate_docs_uncertain_needs_clar(self):
        valid, err, needs_clar = EligibilityEngine.validate_original_documents(
            available=None, uncertain=True
        )
        assert needs_clar

    def test_validate_loan_within_cap(self):
        valid, err, _ = EligibilityEngine.validate_loan_amount(
            requested=5_000_000.0, confirmed=5_000_000.0
        )
        assert valid

    def test_validate_market_value_positive(self):
        valid, err, _ = EligibilityEngine.validate_market_value(10_000_000.0)
        assert valid

    def test_validate_market_value_zero_invalid(self):
        valid, err, _ = EligibilityEngine.validate_market_value(0.0)
        assert not valid

    def test_validate_tenure_boundary_values(self):
        for yr in [3, 15]:
            valid, err, _ = EligibilityEngine.validate_tenure(yr)
            assert valid, f"Expected valid for {yr} years"
        for yr in [2, 16]:
            valid, err, _ = EligibilityEngine.validate_tenure(yr)
            assert not valid, f"Expected invalid for {yr} years"
