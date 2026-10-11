import pytest
from app.services.extraction_service import ExtractionService
from app.schemas.state import QualificationState

def test_currency_parsing_lakhs():
    val = ExtractionService.parse_currency_amount("I need fifty lakhs")
    assert val == 5000000.0

def test_currency_parsing_crores():
    val = ExtractionService.parse_currency_amount("property is worth roughly 1.5 crore")
    assert val == 15000000.0

def test_currency_parsing_corrections():
    val = ExtractionService.parse_currency_amount("I need 40 lakhs - actually 60 lakhs")
    assert val == 6000000.0

def test_tenure_parsing_with_correction():
    tenure, uncertain = ExtractionService.parse_tenure_years("ten years - actually, twelve years")
    assert tenure == 12
    assert uncertain is False

def test_tenure_uncertainty_detection():
    tenure, uncertain = ExtractionService.parse_tenure_years("maybe 5 years or 7 years")
    assert uncertain is True

def test_multi_fact_extraction():
    state = QualificationState(customer_verified=True)
    text = "It's my own commercial property worth 1 crore, and I run a business with bank income."
    extracted = ExtractionService.extract_all_facts(text, state)
    assert extracted.get("property_type") == "Commercial"
    assert extracted.get("ownership_status") == "Sole ownership"
    assert extracted.get("market_value") == 10000000.0
    assert extracted.get("occupation") == "Self-employed"
    assert extracted.get("income_mode") == "Bank"
