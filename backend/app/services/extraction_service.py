import re
from typing import Dict, Any, Optional, Tuple, List
from app.schemas.state import QualificationState, CallIntent

class ExtractionService:
    """
    Structured extraction service that extracts qualification facts from customer utterances.
    Supports Indian financial conventions (Lakhs, Crores), multi-fact utterances,
    corrections ('actually...'), busy intent, transfer intent, and ambiguity detection.
    """

    # Indian number conversion
    WORD_TO_NUM = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
        "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
        "twenty five": 25, "thirty": 30, "thirty five": 35, "forty": 40, "forty five": 45,
        "fifty": 50, "fifty five": 55, "sixty": 60, "sixty five": 65, "seventy": 70,
        "seventy five": 75, "eighty": 80, "ninety": 90, "hundred": 100
    }

    @classmethod
    def parse_currency_amount(cls, text: str) -> Optional[float]:
        """
        Parses currency amounts from text including '50 lakh', '₹75,00,000', '1.5 crore', '80L', '1 cr'.
        Handles corrections like 'fifty lakhs - actually seventy lakh'.
        """
        lower = text.lower().replace(",", "")

        # Look for explicit corrections first
        if "actually" in lower or "wait" in lower or "rather" in lower:
            parts = re.split(r'\b(?:actually|wait|rather|no)\b', lower)
            if len(parts) > 1 and parts[-1].strip():
                # Try parsing from corrected part
                val = cls._parse_single_currency(parts[-1])
                if val:
                    return val

        return cls._parse_single_currency(lower)

    NUM_WORD_PATTERN = (
        r'(?:\d+(?:\.\d+)?|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|'
        r'eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|'
        r'twenty\s*five|thirty|thirty\s*five|forty|forty\s*five|fifty|fifty\s*five|sixty|'
        r'sixty\s*five|seventy|seventy\s*five|eighty|eighty\s*five|ninety|hundred)\b)'
    )

    @classmethod
    def _parse_single_currency(cls, text: str) -> Optional[float]:
        # Crores: e.g. "1.5 crore", "1 crore", "2 cr", "one crore"
        cr_match = re.search(rf'({cls.NUM_WORD_PATTERN})\s*(?:crore|crores|cr)\b', text)
        if cr_match:
            raw = cr_match.group(1).strip()
            num = cls.WORD_TO_NUM.get(raw, float(raw) if raw.replace(".", "").isdigit() else None)
            if num:
                return num * 10000000.0

        # Lakhs: e.g. "50 lakh", "75 lakhs", "50l", "fifty lakhs"
        lakh_match = re.search(rf'({cls.NUM_WORD_PATTERN})\s*(?:lakh|lakhs|lacs|lac|l)\b', text)
        if lakh_match:
            raw = lakh_match.group(1).strip()
            num = cls.WORD_TO_NUM.get(raw, float(raw) if raw.replace(".", "").isdigit() else None)
            if num:
                return num * 100000.0

        # Raw numeric strings with rupee symbol or large numbers e.g. "₹5000000", "50,00,000", "7500000"
        num_match = re.search(r'(?:rs\.?|inr|₹)?\s*([1-9]\d{4,9})\b', text)
        if num_match:
            return float(num_match.group(1))

        return None

    @classmethod
    def parse_tenure_years(cls, text: str) -> Tuple[Optional[int], bool]:
        """
        Parses tenure in years. Returns (tenure_int, is_uncertain).
        Handles corrections like 'ten years - actually twelve years'.
        """
        lower = text.lower()
        
        # Check for uncertainty
        uncertain = False
        if any(w in lower for w in ["maybe", "perhaps", "not sure", "around", "probably", "between"]):
            # If customer says 'ten years, maybe twelve', it's ambiguous
            if "maybe" in lower or "between" in lower or "not sure" in lower:
                uncertain = True

        # Check for correction
        target_text = lower
        if "actually" in lower or "wait" in lower:
            parts = re.split(r'\b(?:actually|wait)\b', lower)
            if len(parts) > 1 and parts[-1].strip():
                target_text = parts[-1]

        # Extract number followed by year(s) or just year context
        match = re.search(r'(\d+|\b[a-z]+\b)\s*(?:years?|yrs?|yr)\b', target_text)
        if match:
            raw = match.group(1).strip()
            if raw.isdigit():
                return int(raw), uncertain
            if raw in cls.WORD_TO_NUM:
                return cls.WORD_TO_NUM[raw], uncertain

        # Standalone numbers if the context is about tenure
        stand_match = re.search(r'\b([2-9]|1[0-9]|20)\b', target_text)
        if stand_match and ("year" in lower or "tenure" in lower or len(lower.split()) <= 4):
            val = int(stand_match.group(1))
            return val, uncertain

        return None, uncertain

    @classmethod
    def extract_customer_intent(cls, text: str) -> CallIntent:
        lower = text.lower()

        # Busy / Callback request
        if any(w in lower for w in ["busy", "call back", "callback", "driving", "in a meeting", "call later", "call me tomorrow", "not a good time", "call after"]):
            return CallIntent.CALLBACK

        # Decline / Not interested
        if any(w in lower for w in ["not interested", "dont call", "don't call", "stop calling", "decline", "no need", "cancel"]):
            return CallIntent.DECLINE

        # Existing Loan / Transfer / EMI reduction
        if any(w in lower for w in [
            "already have a loan", "existing loan", "reduce emi", "lower emi",
            "balance transfer", "loan on the property", "current emi", "takeover",
            "transfer loan", "transfer my loan", "loan transfer", "transfer my existing",
            "mortgage transfer", "switch my loan",
        ]):
            return CallIntent.LOAN_TRANSFER

        # Product inquiries
        if any(w in lower for w in ["interest rate", "what is the rate", "roi", "charges", "processing fee", "who are you", "what company"]):
            return CallIntent.PRODUCT_INQUIRY

        return CallIntent.FRESH_LOAN

    @classmethod
    def extract_callback_time(cls, text: str) -> Optional[str]:
        lower = text.lower()
        time_patterns = [
            r'(?:tomorrow|today|evening|morning|afternoon|later)(?:\s+at\s+\d+(?::\d+)?\s*(?:am|pm)?)?',
            r'\d+(?::\d+)?\s*(?:am|pm)',
            r'after\s+\d+\s*(?:hours?|pm|am)?',
            r'in\s+\d+\s*(?:minutes?|hours?)'
        ]
        for pat in time_patterns:
            m = re.search(pat, lower)
            if m:
                return m.group(0).strip()
        return "at customer's earliest convenience"

    @classmethod
    def extract_all_facts(cls, text: str, current_state: QualificationState) -> Dict[str, Any]:
        """
        Multi-fact extractor that handles full natural language utterances,
        corrections, and updates the state dictionary.
        """
        lower = text.lower()
        updates: Dict[str, Any] = {}

        # 1. Customer Verification check
        if not current_state.customer_verified:
            if any(w in lower for w in [
                "yes speaking", "this is", "speaking", "yes please", "yes i am", 
                "yeah speaking", "yep", "yes that is me", "yes i'm", "yes it is", "correct"
            ]):
                updates["customer_verified"] = True
            elif lower in ["yes", "yeah", "yep", "ha", "haan"]:
                updates["customer_verified"] = True

        # 2. Intent Detection
        intent = cls.extract_customer_intent(text)
        if intent == CallIntent.CALLBACK:
            updates["customer_busy"] = True
            updates["callback_time"] = cls.extract_callback_time(text)
            updates["call_intent"] = CallIntent.CALLBACK
            return updates
        elif intent == CallIntent.DECLINE:
            updates["call_intent"] = CallIntent.DECLINE
            return updates
        elif intent == CallIntent.LOAN_TRANSFER:
            updates["transfer_required"] = True
            updates["transfer_reason"] = "Customer indicated existing property loan or EMI reduction requirement."
            updates["call_intent"] = CallIntent.LOAN_TRANSFER
            return updates

        # Check for affirmative/negative to excess loan offer
        if current_state.excess_loan_offer_pending:
            if any(w in lower for w in ["yes", "agree", "okay", "fine", "proceed", "75 lakh is fine", "sure", "that works"]):
                updates["loan_amount_confirmed"] = 7500000.0
                updates["excess_loan_offer_pending"] = False
            elif any(w in lower for w in ["no", "never", "not enough", "decline", "cancel", "need more"]):
                updates["call_intent"] = CallIntent.DECLINE
                updates["excess_loan_offer_pending"] = False

        # 3. Property Type extraction
        # Handle corrections like "wait, I meant residential, not commercial".
        # When a negation phrase appears next to a type keyword, that type is EXCLUDED.
        # We extract the final intended type by:
        #   (a) detecting which types are explicitly negated via "not <type>" / "no <type>"
        #   (b) choosing the type that remains after removing negated ones.

        negated_types: set[str] = set()
        # Detect negation patterns: "not commercial", "no commercial", "it's not a shop"
        import re as _re
        for _neg_pat in [
            (r'\bnot\s+(?:a\s+)?commercial\b', "commercial"),
            (r'\bnot\s+(?:a\s+)?residential\b', "residential"),
            (r'\bnot\s+(?:a\s+)?industrial\b', "industrial"),
            (r'\bnot\s+(?:an?\s+)?agricultural\b', "agricultural"),
        ]:
            if _re.search(_neg_pat[0], lower):
                negated_types.add(_neg_pat[1])

        if "agricultural" in lower or "farmland" in lower or "farm land" in lower or "agriculture" in lower:
            if "agricultural" not in negated_types:
                updates["property_type"] = "Agricultural"
        elif ("commercial" in lower or "shop" in lower or "office space" in lower or "retail store" in lower) and "commercial" not in negated_types:
            updates["property_type"] = "Commercial"
        elif ("industrial" in lower or "factory" in lower or "warehouse" in lower or "shed" in lower) and "industrial" not in negated_types:
            updates["property_type"] = "Industrial"
        elif "residential" in lower or "house" in lower or "flat" in lower or "apartment" in lower or "own house" in lower or "home" in lower:
            if "residential" not in negated_types:
                updates["property_type"] = "Residential"

        # 4. Ownership Status extraction
        if any(w in lower for w in ["joint", "jointly", "together", "with my wife", "with my brother", "with my father", "co-owner", "both of us"]):
            updates["ownership_status"] = "Joint ownership"
        elif any(w in lower for w in ["sole", "alone", "own house", "my own", "single owner", "only me", "in my name"]):
            updates["ownership_status"] = "Sole ownership"

        # 5. Original Documents extraction
        # Order matters: disqualifying patterns checked before affirmative ones
        if any(w in lower for w in ["probably", "maybe", "not sure if original", "might have", "check and confirm"]):
            updates["original_documents_uncertain"] = True
        elif any(w in lower for w in [
            "only copies", "xerox only", "photocopy only", "no originals",
            "don't have original", "do not have original",
            # Bank/lender holding originals means customer does NOT have them
            "bank has them", "bank has the original", "with the bank",
            "pledged", "kept with lender", "lender has",
            "lost originals", "original not available",
        ]):
            updates["original_documents_available"] = False
            updates["original_documents_uncertain"] = False
        elif any(w in lower for w in [
            "original papers are at home", "originals are with me",
            "original documents are available", "yes original", "i have original",
            "papers at home", "all clear documents",
        ]) or (
            # Bare 'original' only when NOT followed by an unavailability phrase
            "original" in lower
            and not any(w in lower for w in ["no original", "not have", "bank has", "with the bank", "pledged"])
        ):
            updates["original_documents_available"] = True
            updates["original_documents_uncertain"] = False
        elif lower in ["yes", "yes available", "available"] and "original" in current_state.conversation_history[-1].content.lower() if current_state.conversation_history else False:
            updates["original_documents_available"] = True
            updates["original_documents_uncertain"] = False

        # 6. Occupation and Income Mode extraction
        # Occupation
        if any(w in lower for w in ["self employed", "self-employed", "business", "own business", "shopkeeper", "run a business", "trader", "contractor"]):
            updates["occupation"] = "Self-employed"
        elif any(w in lower for w in ["salaried", "job", "private company", "working in", "software engineer", "employee", "corporate"]):
            updates["occupation"] = "Salaried"

        # Income Mode
        if "both bank and cash" in lower or ("bank" in lower and "cash" in lower):
            updates["income_mode"] = "Both"
            updates["income_mode_both_pending"] = True
        elif "cash" in lower and "bank" not in lower:
            updates["income_mode"] = "Cash"
        elif any(w in lower for w in ["bank", "salary account", "account transfer", "direct deposit", "cheque", "neft", "rtgs", "into my bank"]):
            updates["income_mode"] = "Bank"
            updates["income_mode_both_pending"] = False

        # Clarification answer for both bank and cash
        if current_state.income_mode_both_pending:
            if any(w in lower for w in ["bank", "yes into bank", "primary is bank", "qualifying income is bank", "in bank"]):
                updates["income_mode"] = "Bank"
                updates["income_mode_both_pending"] = False

        # 7. Loan Amount vs Market Value disambiguation
        # Often user says: "property is worth roughly 1 crore, I need 50 lakhs"
        # Or: "looking for 50 lakh loan, market value is 80 lakh"
        mv_match = re.search(r'(?:worth|market value|valued at|valuation of)\s*(?:roughly|around|approx)?\s*([^\,\.]+)', lower)
        loan_match = re.search(r'(?:need|looking for|require|loan of|want|loan amount)\s*(?:roughly|around|approx)?\s*([^\,\.]+)', lower)

        if mv_match:
            mv_val = cls.parse_currency_amount(mv_match.group(1))
            if mv_val:
                updates["market_value"] = mv_val

        if loan_match:
            loan_val = cls.parse_currency_amount(loan_match.group(1))
            if loan_val:
                if loan_val > 7500000:
                    updates["loan_amount_requested"] = loan_val
                    updates["excess_loan_offer_pending"] = True
                else:
                    updates["loan_amount_requested"] = loan_val
                    updates["loan_amount_confirmed"] = loan_val

        # If general currency was found and not yet mapped
        if "market_value" not in updates and "loan_amount_requested" not in updates:
            parsed_curr = cls.parse_currency_amount(text)
            if parsed_curr:
                # Disambiguate based on which question was last asked
                last_agent_msg = current_state.conversation_history[-1].content.lower() if current_state.conversation_history else ""
                if "market value" in last_agent_msg or "worth" in last_agent_msg or "property value" in last_agent_msg:
                    updates["market_value"] = parsed_curr
                elif "loan amount" in last_agent_msg or "how much" in last_agent_msg or "amount" in last_agent_msg:
                    if parsed_curr > 7500000:
                        updates["loan_amount_requested"] = parsed_curr
                        updates["excess_loan_offer_pending"] = True
                    else:
                        updates["loan_amount_requested"] = parsed_curr
                        updates["loan_amount_confirmed"] = parsed_curr
                else:
                    # If loan amount already confirmed and market value empty, assign to market value
                    if current_state.loan_amount_confirmed and not current_state.market_value:
                        updates["market_value"] = parsed_curr
                    elif not current_state.loan_amount_requested:
                        if parsed_curr > 7500000:
                            updates["loan_amount_requested"] = parsed_curr
                            updates["excess_loan_offer_pending"] = True
                        else:
                            updates["loan_amount_requested"] = parsed_curr
                            updates["loan_amount_confirmed"] = parsed_curr

        # 8. Tenure extraction
        tenure, ten_uncertain = cls.parse_tenure_years(text)
        if tenure is not None:
            updates["tenure_years"] = tenure
            updates["tenure_uncertain"] = ten_uncertain
        elif ten_uncertain:
            updates["tenure_uncertain"] = True

        return updates
