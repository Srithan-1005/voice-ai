from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class QualificationStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    QUALIFIED = "QUALIFIED"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    LOAN_TRANSFER = "LOAN_TRANSFER"
    CALLBACK_REQUESTED = "CALLBACK_REQUESTED"
    CUSTOMER_DECLINED = "CUSTOMER_DECLINED"

class CallIntent(str, Enum):
    UNKNOWN = "UNKNOWN"
    FRESH_LOAN = "FRESH_LOAN"
    LOAN_TRANSFER = "LOAN_TRANSFER"
    CALLBACK = "CALLBACK"
    DECLINE = "DECLINE"
    PRODUCT_INQUIRY = "PRODUCT_INQUIRY"

class PropertyType(str, Enum):
    RESIDENTIAL = "Residential"
    COMMERCIAL = "Commercial"
    INDUSTRIAL = "Industrial"
    AGRICULTURAL = "Agricultural"
    OTHER = "Other"

class OwnershipStatus(str, Enum):
    SOLE = "Sole ownership"
    JOINT = "Joint ownership"
    UNKNOWN = "Unknown"

class Occupation(str, Enum):
    SALARIED = "Salaried"
    SELF_EMPLOYED = "Self-employed"
    OTHER = "Other"

class IncomeMode(str, Enum):
    BANK = "Bank"
    CASH = "Cash"
    BOTH = "Both"
    UNKNOWN = "Unknown"

class ChecklistItemStatus(str, Enum):
    UNKNOWN = "Unknown"
    ANSWERED = "Answered"
    INVALID = "Invalid"
    CLARIFICATION_NEEDED = "Clarification Needed"

class ChecklistItemDetail(BaseModel):
    item_number: int
    name: str
    status: ChecklistItemStatus = ChecklistItemStatus.UNKNOWN
    captured_value: Optional[str] = None
    interpretation: Optional[str] = None
    clarification_needed: bool = False

class MessageRole(str, Enum):
    SYSTEM = "system"
    AGENT = "agent"
    CUSTOMER = "customer"

class ConversationMessage(BaseModel):
    role: MessageRole
    content: str
    timestamp: Optional[str] = None

class QualificationState(BaseModel):
    call_id: Optional[str] = None
    customer_name: Optional[str] = "Valued Customer"
    customer_verified: bool = False
    customer_busy: bool = False
    callback_time: Optional[str] = None
    call_intent: CallIntent = CallIntent.UNKNOWN
    
    # 7 Checklist Items fields
    property_type: Optional[str] = None
    ownership_status: Optional[str] = None
    original_documents_available: Optional[bool] = None
    original_documents_uncertain: bool = False
    
    loan_amount_requested: Optional[float] = None
    loan_amount_confirmed: Optional[float] = None
    excess_loan_offer_pending: bool = False  # Set to True when customer asked >75L and we offered 75L
    
    occupation: Optional[str] = None
    income_mode: Optional[str] = None
    income_mode_both_pending: bool = False  # Set to True when both bank and cash, needs clarification on primary
    
    market_value: Optional[float] = None
    tenure_years: Optional[int] = None
    tenure_uncertain: bool = False

    # Status & Flags
    disqualified: bool = False
    disqualification_reason: Optional[str] = None
    transfer_required: bool = False
    transfer_reason: Optional[str] = None
    qualification_status: QualificationStatus = QualificationStatus.IN_PROGRESS
    
    answered_items: List[str] = Field(default_factory=list)
    pending_clarifications: List[str] = Field(default_factory=list)
    conversation_history: List[ConversationMessage] = Field(default_factory=list)
    call_ended: bool = False
    decision_explanation: Optional[str] = "Call in progress. Awaiting customer responses."

    def get_checklist_details(self) -> List[ChecklistItemDetail]:
        """Returns details for the 7 standard checklist items"""
        details = []

        # 1. Property Type
        prop_status = ChecklistItemStatus.UNKNOWN
        prop_val = self.property_type
        prop_interp = None
        if self.property_type:
            if self.property_type.lower() == "agricultural":
                prop_status = ChecklistItemStatus.INVALID
                prop_interp = "Disqualified: Agricultural property is not eligible"
            elif self.property_type.lower() in ["residential", "commercial", "industrial"]:
                prop_status = ChecklistItemStatus.ANSWERED
                prop_interp = "Eligible property classification"
            else:
                prop_status = ChecklistItemStatus.CLARIFICATION_NEEDED
                prop_interp = "Clarification needed on property classification"
        details.append(ChecklistItemDetail(
            item_number=1,
            name="Property Type",
            status=prop_status,
            captured_value=prop_val,
            interpretation=prop_interp,
            clarification_needed=(prop_status == ChecklistItemStatus.CLARIFICATION_NEEDED)
        ))

        # 2. Ownership Status
        own_status = ChecklistItemStatus.UNKNOWN
        own_val = self.ownership_status
        own_interp = None
        if self.ownership_status:
            if self.ownership_status.lower() in ["sole ownership", "joint ownership"]:
                own_status = ChecklistItemStatus.ANSWERED
                own_interp = "Eligible ownership structure"
            else:
                own_status = ChecklistItemStatus.CLARIFICATION_NEEDED
                own_interp = "Clarification needed: Sole or Joint"
        details.append(ChecklistItemDetail(
            item_number=2,
            name="Ownership Status",
            status=own_status,
            captured_value=own_val,
            interpretation=own_interp,
            clarification_needed=(own_status == ChecklistItemStatus.CLARIFICATION_NEEDED)
        ))

        # 3. Original Documents
        doc_status = ChecklistItemStatus.UNKNOWN
        doc_val = None
        doc_interp = None
        if self.original_documents_uncertain:
            doc_status = ChecklistItemStatus.CLARIFICATION_NEEDED
            doc_val = "Uncertain / Unconfirmed"
            doc_interp = "Clarification required on physical availability of original documents"
        elif self.original_documents_available is not None:
            if self.original_documents_available:
                doc_status = ChecklistItemStatus.ANSWERED
                doc_val = "Available"
                doc_interp = "Original papers available for physical verification"
            else:
                doc_status = ChecklistItemStatus.INVALID
                doc_val = "Only copies / Unavailable"
                doc_interp = "Disqualified: Original property deeds are strictly mandatory"
        details.append(ChecklistItemDetail(
            item_number=3,
            name="Original Property Documents",
            status=doc_status,
            captured_value=doc_val,
            interpretation=doc_interp,
            clarification_needed=self.original_documents_uncertain
        ))

        # 4. Desired Loan Amount
        loan_status = ChecklistItemStatus.UNKNOWN
        loan_val = None
        loan_interp = None
        if self.loan_amount_confirmed is not None:
            loan_status = ChecklistItemStatus.ANSWERED
            loan_val = f"₹{self.loan_amount_confirmed:,.0f}"
            loan_interp = "Within maximum limit of ₹75,00,000"
        elif self.loan_amount_requested is not None:
            loan_val = f"₹{self.loan_amount_requested:,.0f}"
            if self.loan_amount_requested > 7500000:
                loan_status = ChecklistItemStatus.CLARIFICATION_NEEDED
                loan_interp = "Exceeds ₹75 Lakh cap. Offered alternative cap of ₹75,00,000"
            else:
                loan_status = ChecklistItemStatus.ANSWERED
                loan_interp = "Within limit"
        details.append(ChecklistItemDetail(
            item_number=4,
            name="Desired Loan Amount",
            status=loan_status,
            captured_value=loan_val,
            interpretation=loan_interp,
            clarification_needed=self.excess_loan_offer_pending
        ))

        # 5. Occupation and Income Mode
        occ_status = ChecklistItemStatus.UNKNOWN
        occ_val = None
        occ_interp = None
        if self.occupation or self.income_mode:
            occ_parts = []
            if self.occupation:
                occ_parts.append(f"Occupation: {self.occupation}")
            if self.income_mode:
                occ_parts.append(f"Income Mode: {self.income_mode}")
            occ_val = ", ".join(occ_parts)

            if self.occupation and self.income_mode:
                if self.income_mode.lower() == "cash":
                    occ_status = ChecklistItemStatus.INVALID
                    occ_interp = "Disqualified: Cash income mode is ineligible. Bank transfer required."
                elif self.income_mode_both_pending:
                    occ_status = ChecklistItemStatus.CLARIFICATION_NEEDED
                    occ_interp = "Clarification needed: confirm if primary qualifying income is routed through bank"
                elif self.occupation.lower() in ["salaried", "self-employed"] and self.income_mode.lower() == "bank":
                    occ_status = ChecklistItemStatus.ANSWERED
                    occ_interp = "Eligible occupation and bank income credit"
                else:
                    occ_status = ChecklistItemStatus.CLARIFICATION_NEEDED
                    occ_interp = "Clarification needed on occupation or income mode"
            else:
                occ_status = ChecklistItemStatus.CLARIFICATION_NEEDED
                missing = "income mode" if not self.income_mode else "occupation"
                occ_interp = f"Incomplete: Missing {missing}"
        details.append(ChecklistItemDetail(
            item_number=5,
            name="Occupation & Income Mode",
            status=occ_status,
            captured_value=occ_val,
            interpretation=occ_interp,
            clarification_needed=(occ_status == ChecklistItemStatus.CLARIFICATION_NEEDED)
        ))

        # 6. Market Value
        mv_status = ChecklistItemStatus.UNKNOWN
        mv_val = None
        mv_interp = None
        if self.market_value is not None:
            mv_status = ChecklistItemStatus.ANSWERED
            mv_val = f"₹{self.market_value:,.0f}"
            mv_interp = "Estimated property market value recorded (no minimum threshold applied)"
        details.append(ChecklistItemDetail(
            item_number=6,
            name="Estimated Property Market Value",
            status=mv_status,
            captured_value=mv_val,
            interpretation=mv_interp,
            clarification_needed=False
        ))

        # 7. Desired Tenure
        ten_status = ChecklistItemStatus.UNKNOWN
        ten_val = None
        ten_interp = None
        if self.tenure_years is not None:
            ten_val = f"{self.tenure_years} Years"
            if 3 <= self.tenure_years <= 15:
                ten_status = ChecklistItemStatus.ANSWERED
                ten_interp = "Eligible tenure (allowed range: 3 to 15 years)"
            else:
                ten_status = ChecklistItemStatus.INVALID
                ten_interp = f"Ineligible tenure: {self.tenure_years} years outside allowable 3-15 years"
        elif self.tenure_uncertain:
            ten_status = ChecklistItemStatus.CLARIFICATION_NEEDED
            ten_interp = "Clarification needed: tenure must be confirmed between 3 and 15 years"
        details.append(ChecklistItemDetail(
            item_number=7,
            name="Desired Repayment Tenure",
            status=ten_status,
            captured_value=ten_val,
            interpretation=ten_interp,
            clarification_needed=self.tenure_uncertain
        ))

        return details
