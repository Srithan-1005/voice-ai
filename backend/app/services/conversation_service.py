import datetime
from typing import Tuple, Optional, Dict, Any, List
from app.schemas.state import (
    QualificationState, 
    QualificationStatus, 
    ConversationMessage, 
    MessageRole, 
    CallIntent
)
from app.services.extraction_service import ExtractionService
from app.services.eligibility_service import EligibilityService
from app.core.config import settings

class ConversationService:
    """
    Orchestrates the 9-step conversation loop, combining natural language entity
    extraction, deterministic eligibility validation, state updates, and concise
    dialogue generation adhering to Home Credit requirements.
    """

    @classmethod
    def initialize_conversation(
        cls, 
        customer_name: Optional[str] = None, 
        language: str = "English",
        initial_fields: Optional[Dict[str, Any]] = None
    ) -> Tuple[QualificationState, str]:
        """
        Starts a new qualification session with the standard opening verification line,
        or opens with the next pending question if pre-filled details are supplied.
        """
        c_name = customer_name or settings.DEFAULT_CUSTOMER_NAME or "Valued Customer"
        a_name = settings.AGENT_NAME
        company = settings.COMPANY_NAME

        state = QualificationState(
            customer_name=c_name,
            call_id=f"sim_{int(datetime.datetime.now().timestamp()*1000)}"
        )

        if initial_fields:
            if initial_fields.get("customer_verified") is True or str(initial_fields.get("customer_verified")).lower() == "true":
                state.customer_verified = True
            
            prop = initial_fields.get("property_type")
            if prop:
                state.property_type = str(prop).strip().capitalize()
            
            own = initial_fields.get("ownership_status")
            if own:
                state.ownership_status = str(own).strip().capitalize()
            
            docs = initial_fields.get("original_documents_available")
            if docs is not None:
                if isinstance(docs, bool):
                    state.original_documents_available = docs
                elif str(docs).lower() in ("yes", "true", "available"):
                    state.original_documents_available = True
                elif str(docs).lower() in ("no", "false", "unavailable", "copies only"):
                    state.original_documents_available = False
                elif str(docs).lower() in ("unknown", "unsure"):
                    state.original_documents_uncertain = True

            loan = initial_fields.get("loan_amount_requested")
            if loan:
                try:
                    state.loan_amount_requested = float(loan)
                    state.loan_amount_confirmed = float(loan)
                except (ValueError, TypeError):
                    pass

            occ = initial_fields.get("occupation")
            if occ:
                state.occupation = str(occ).strip().capitalize()

            inc = initial_fields.get("income_mode")
            if inc:
                state.income_mode = str(inc).strip().capitalize()

            val = initial_fields.get("market_value")
            if val:
                try:
                    state.market_value = float(val)
                except (ValueError, TypeError):
                    pass

            ten = initial_fields.get("tenure_years")
            if ten:
                try:
                    state.tenure_years = int(ten)
                except (ValueError, TypeError):
                    pass

            existing_loan = initial_fields.get("existing_loan")
            emi_red = initial_fields.get("emi_reduction_request")
            if str(existing_loan).lower() in ("yes", "true") or str(emi_red).lower() in ("yes", "true"):
                state.transfer_required = True
                state.transfer_reason = "Customer has existing property loan or requested EMI reduction; routing to Loan Transfer Specialist."

            # Evaluate state rules with deterministic engine
            from app.services.eligibility_engine import EligibilityEngine
            engine_res = EligibilityEngine.evaluate(state)
            
            if engine_res.next_question_text and state.customer_verified:
                greeting = f"Namaste {c_name} ji." if language.lower() == "hindi" else f"Hello {c_name}."
                initial_msg = f"{greeting} {engine_res.next_question_text}"
            elif engine_res.call_ended:
                initial_msg = engine_res.decision_explanation
            else:
                initial_msg = (
                    f"Namaste, kya main {c_name} ji se baat kar sakti hoon?" if language.lower() == "hindi"
                    else f"Hello, may I speak with {c_name}?"
                )
        else:
            if language.lower() == "hindi":
                initial_msg = f"Namaste, kya main {c_name} ji se baat kar sakti hoon?"
            else:
                initial_msg = f"Hello, may I speak with {c_name}?"

        state.conversation_history.append(
            ConversationMessage(
                role=MessageRole.AGENT,
                content=initial_msg,
                timestamp=datetime.datetime.now().isoformat()
            )
        )
        return state, initial_msg

    @classmethod
    def process_utterance(
        cls, 
        state: QualificationState, 
        customer_utterance: str,
        language: str = "English"
    ) -> Tuple[QualificationState, str]:
        """
        Executes Steps 1 through 9 defined in Section 7.
        """
        # Append customer message to history
        state.conversation_history.append(
            ConversationMessage(
                role=MessageRole.CUSTOMER,
                content=customer_utterance,
                timestamp=datetime.datetime.now().isoformat()
            )
        )

        c_name = state.customer_name or "Valued Customer"
        a_name = settings.AGENT_NAME
        company = settings.COMPANY_NAME
        is_hindi = (language.lower() == "hindi")

        # Handle questions about who is calling if unverified
        lower_utt = customer_utterance.lower()
        if not state.customer_verified and any(q in lower_utt for q in ["who is this", "who are you", "who is calling", "kaun bol rahe ho"]):
            if is_hindi:
                agent_resp = f"Namaste, main {company} ki taraf se {a_name} bol rahi hoon, Loan Against Property offer ke sambandh mein. Kya main {c_name} ji se baat kar rahi hoon?"
            else:
                agent_resp = f"Hello, I'm {a_name}, calling on behalf of {company} regarding a potential Loan Against Property offer. Am I speaking with {c_name}?"
            state.conversation_history.append(ConversationMessage(role=MessageRole.AGENT, content=agent_resp))
            return state, agent_resp

        # Handle rate questions (interruptions)
        rate_interruption = any(r in lower_utt for r in ["interest rate", "what is the rate", "roi", "byaaj", "rate of interest"])

        # STEP 1 & 2: Extract all facts and intent
        extracted = ExtractionService.extract_all_facts(customer_utterance, state)

        # STEP 3 & 4 & 5: Update state with extracted facts
        if "customer_verified" in extracted:
            state.customer_verified = extracted["customer_verified"]
        if "customer_busy" in extracted:
            state.customer_busy = extracted["customer_busy"]
        if "callback_time" in extracted:
            state.callback_time = extracted["callback_time"]
        if "call_intent" in extracted:
            state.call_intent = extracted["call_intent"]
        if "transfer_required" in extracted:
            state.transfer_required = extracted["transfer_required"]
            state.transfer_reason = extracted.get("transfer_reason")

        if "property_type" in extracted:
            state.property_type = extracted["property_type"]
        if "ownership_status" in extracted:
            state.ownership_status = extracted["ownership_status"]
        if "original_documents_available" in extracted:
            state.original_documents_available = extracted["original_documents_available"]
            state.original_documents_uncertain = False
        elif "original_documents_uncertain" in extracted:
            state.original_documents_uncertain = extracted["original_documents_uncertain"]

        if "loan_amount_requested" in extracted:
            state.loan_amount_requested = extracted["loan_amount_requested"]
        if "loan_amount_confirmed" in extracted:
            state.loan_amount_confirmed = extracted["loan_amount_confirmed"]
        if "excess_loan_offer_pending" in extracted:
            state.excess_loan_offer_pending = extracted["excess_loan_offer_pending"]

        if "occupation" in extracted:
            state.occupation = extracted["occupation"]
        if "income_mode" in extracted:
            state.income_mode = extracted["income_mode"]
            state.income_mode_both_pending = extracted.get("income_mode_both_pending", False)

        if "market_value" in extracted:
            state.market_value = extracted["market_value"]
        if "tenure_years" in extracted:
            state.tenure_years = extracted["tenure_years"]
            state.tenure_uncertain = extracted.get("tenure_uncertain", False)
        elif "tenure_uncertain" in extracted:
            state.tenure_uncertain = extracted["tenure_uncertain"]

        # STEP 6: Deterministic business evaluation
        state = EligibilityService.evaluate_state(state)

        # STEP 7 & 8: Generate appropriate agent response
        # Branch A: Terminal outcomes
        if state.customer_busy:
            if is_hindi:
                agent_resp = f"Ji main samajh sakti hoon. Hum aapko {state.callback_time or 'baad mein'} sampark karenge. Aapka din shubh rahe."
            else:
                agent_resp = f"Of course, I understand. We will call you back {state.callback_time or 'at your convenience'}. Thank you for your time and have a wonderful day."
            state.conversation_history.append(ConversationMessage(role=MessageRole.AGENT, content=agent_resp))
            return state, agent_resp

        if state.call_intent == CallIntent.DECLINE or state.qualification_status == QualificationStatus.CUSTOMER_DECLINED:
            if is_hindi:
                agent_resp = "Main aapki baat samajh sakti hoon. Aapka samay dene ke liye dhanyavaad. Namaste."
            else:
                agent_resp = "I completely understand. Thank you for your time today, and have a good day."
            state.conversation_history.append(ConversationMessage(role=MessageRole.AGENT, content=agent_resp))
            return state, agent_resp

        if state.transfer_required or state.qualification_status == QualificationStatus.LOAN_TRANSFER:
            if is_hindi:
                agent_resp = (
                    "Batane ke liye dhanyavaad. Kyunki aapki property par pehle se loan hai ya aap EMI kam karwana chahte hain, "
                    "iski jaankari humare Loan-Transfer Specialist denge. Wo aapse jald hi sampark karenge. Aapka samay dene ke liye dhanyavaad."
                )
            else:
                agent_resp = (
                    "Thank you for clarifying. Since you already have a loan on the property or would like to reduce your current EMI, "
                    "this needs to be handled by our loan-transfer specialist. A specialist will contact you regarding the available next steps. Thank you for your time."
                )
            state.conversation_history.append(ConversationMessage(role=MessageRole.AGENT, content=agent_resp))
            return state, agent_resp

        if state.disqualified or state.qualification_status == QualificationStatus.NOT_ELIGIBLE:
            if is_hindi:
                agent_resp = (
                    "Jaankari dene ke liye dhanyavaad. Is vishesh offer ke niyam anusar, hum abhi aage nahi badh payenge. "
                    "Aapka samay dene ke liye bahut dhanyavaad."
                )
            else:
                agent_resp = (
                    "Thank you for sharing that information. Based on the criteria for this specific offer, "
                    "we won't be able to proceed with this application at the moment. Thank you for your time."
                )
            state.conversation_history.append(ConversationMessage(role=MessageRole.AGENT, content=agent_resp))
            return state, agent_resp

        # Branch B: Excess Loan Amount Offer (> 75 Lakh)
        if state.excess_loan_offer_pending:
            if is_hindi:
                agent_resp = "Yeh vartamaan offer adhiktam ₹75 lakh tak uplabdh hai. Kya aap ₹75 lakh ke saath aage badhna chahenge?"
            else:
                agent_resp = "The current offer is available for amounts up to ₹75 lakh. Would you like to proceed with the maximum offer amount of ₹75 lakh?"
            state.conversation_history.append(ConversationMessage(role=MessageRole.AGENT, content=agent_resp))
            return state, agent_resp

        # Branch C: Qualified Lead
        if state.qualification_status == QualificationStatus.QUALIFIED:
            if is_hindi:
                agent_resp = (
                    "Sabhi prashnon ke uttar dene ke liye dhanyavaad. Aapki jaankari ke aadhar par, aap is offer ke prathmik criteria ko pura karte hain. "
                    "Humare Senior Loan Expert jald hi aapse aage ki prakriya aur exact interest rate batane ke liye sampark karenge."
                )
            else:
                agent_resp = (
                    "Thank you for answering those questions. Based on the information you've shared, you meet the preliminary criteria for this offer. "
                    "A senior loan expert will contact you shortly to discuss the next steps and exact interest rates."
                )
            state.conversation_history.append(ConversationMessage(role=MessageRole.AGENT, content=agent_resp))
            return state, agent_resp

        # Branch D: Handle Rate Interruption prefix if customer asked about interest rate mid-call
        interruption_prefix = ""
        if rate_interruption:
            if is_hindi:
                interruption_prefix = "Exact interest rate humare Senior Loan Expert prathmik qualification ke baad batayenge. Main pehle bache hue zaroori prashn pure kar leti hoon. "
            else:
                interruption_prefix = "The exact interest rate will be explained by our senior loan expert after the preliminary qualification. Let me complete the remaining basic questions first. "

        # Branch E: Pending Clarifications
        if state.pending_clarifications:
            clar = state.pending_clarifications[0]
            if "Property Type" in clar:
                resp = "Could you please clarify if the property is residential, commercial, or industrial?"
            elif "documents" in clar:
                resp = "Could you please confirm whether the physical original property documents are available with you for verification?"
            elif "bank income" in clar or "Occupation" in clar:
                if not state.occupation:
                    resp = "Could you clarify whether you are salaried or self-employed?"
                else:
                    resp = "Just to confirm, is the primary income you wish to use for this loan credited directly into your bank account?"
            elif "tenure" in clar.lower():
                resp = "Could you please specify your preferred repayment tenure between 3 and 15 years?"
            else:
                resp = f"Could you please clarify details regarding {clar}?"
            agent_resp = interruption_prefix + resp
            state.conversation_history.append(ConversationMessage(role=MessageRole.AGENT, content=agent_resp))
            return state, agent_resp

        # Branch F: Continue Checklist (Earliest unanswered question)
        next_item = EligibilityService.get_earliest_unanswered_item(state)

        # If customer just got verified, present the offer
        if next_item == "property_type" and len([m for m in state.conversation_history if m.role == MessageRole.CUSTOMER]) == 1:
            if is_hindi:
                agent_resp = interruption_prefix + (
                    f"Namaste {c_name} ji, humare vishesh customer hone ke naate, aap ₹75 lakh tak ke Loan Against Property offer ke patra ho sakte hain. "
                    "Iski eligibility janne ke liye kya main 2 prashn pooch sakti hoon? Aapki property kis prakar ki hai—residential, commercial, ya industrial?"
                )
            else:
                agent_resp = interruption_prefix + (
                    f"As one of our valued customers, you may be eligible for a special Loan Against Property offer of up to ₹75 lakh. "
                    "I'd like to ask a few questions to understand whether the offer may be suitable for you. "
                    "First, what type of property do you own—residential, commercial, or industrial?"
                )
            state.conversation_history.append(ConversationMessage(role=MessageRole.AGENT, content=agent_resp))
            return state, agent_resp

        if next_item == "property_type":
            agent_resp = interruption_prefix + "What type of property do you own—residential, commercial, or industrial?"
        elif next_item == "ownership_status":
            agent_resp = interruption_prefix + "Understood. Are you the sole owner of the property, or is it jointly owned?"
        elif next_item == "original_documents":
            agent_resp = interruption_prefix + "Do you have the physical original property title documents available for verification?"
        elif next_item == "loan_amount":
            agent_resp = interruption_prefix + "How much loan amount are you looking for?"
        elif next_item == "occupation":
            agent_resp = interruption_prefix + "Could you tell me your occupation—are you salaried or self-employed?"
        elif next_item == "income_mode":
            agent_resp = interruption_prefix + "Is your income received directly through your bank account?"
        elif next_item == "occupation_and_income_mode":
            agent_resp = interruption_prefix + "Could you tell me your occupation, and whether your income is received in your bank account?"
        elif next_item == "market_value":
            agent_resp = interruption_prefix + "What is the approximate current market value of your property?"
        elif next_item == "tenure_years":
            agent_resp = interruption_prefix + "What repayment tenure were you considering between 3 and 15 years?"
        else:
            # Fallback if evaluation didn't trigger complete
            agent_resp = interruption_prefix + "Thank you. Let me finalize your preliminary qualification details."

        state.conversation_history.append(ConversationMessage(role=MessageRole.AGENT, content=agent_resp))
        return state, agent_resp
