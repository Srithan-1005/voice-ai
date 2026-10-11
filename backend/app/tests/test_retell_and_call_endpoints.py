import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.call_service import CallService
from app.repositories.call_repository import call_repository

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_config_state():
    """Ensure settings are preserved across tests."""
    orig_key = settings.RETELL_API_KEY
    orig_agent = settings.RETELL_AGENT_ID
    orig_from = settings.RETELL_FROM_NUMBER
    orig_secret = settings.RETELL_WEBHOOK_SECRET
    orig_auth = settings.AUTHORIZED_TEST_NUMBERS

    yield

    settings.RETELL_API_KEY = orig_key
    settings.RETELL_AGENT_ID = orig_agent
    settings.RETELL_FROM_NUMBER = orig_from
    settings.RETELL_WEBHOOK_SECRET = orig_secret
    settings.AUTHORIZED_TEST_NUMBERS = orig_auth

# ============================================================================
# 1. Validation & Safety Tests
# ============================================================================

def test_unconfirmed_destination_rejected():
    """Requires explicit user confirmation before placing call."""
    res = client.post("/api/calls/start", json={
        "customer_phone": "+919876543210",
        "confirmed_destination": False
    })
    assert res.status_code == 400
    assert "Explicit user confirmation is required" in res.json()["detail"]

def test_invalid_phone_numbers():
    """Rejects malformed or non-E.164 phone numbers."""
    invalid_numbers = ["1234", "abcdef", "+0000000", ""]
    for num in invalid_numbers:
        res = client.post("/api/calls/start", json={
            "customer_phone": num,
            "confirmed_destination": True
        })
        assert res.status_code == 400
        assert "phone number" in res.json()["detail"].lower()

def test_unauthorized_destination_number():
    """Blocks destination when not in AUTHORIZED_TEST_NUMBERS list."""
    settings.AUTHORIZED_TEST_NUMBERS = "+919876543210,+919876543211"
    res = client.post("/api/calls/start", json={
        "customer_phone": "+919999999999",
        "confirmed_destination": True
    })
    assert res.status_code == 403
    assert "authorized test numbers" in res.json()["detail"].lower()

def test_missing_retell_api_credentials():
    """Returns clear configuration error when RETELL_API_KEY is empty."""
    settings.RETELL_API_KEY = ""
    settings.AUTHORIZED_TEST_NUMBERS = ""
    res = client.post("/api/calls/start", json={
        "customer_phone": "+919876543210",
        "confirmed_destination": True
    })
    assert res.status_code == 400
    assert "RETELL_API_KEY is not configured" in res.json()["detail"]

def test_missing_retell_agent_id():
    """Returns clear configuration error when RETELL_AGENT_ID is empty."""
    settings.RETELL_API_KEY = "test_key_123"
    settings.RETELL_AGENT_ID = ""
    settings.AUTHORIZED_TEST_NUMBERS = ""
    res = client.post("/api/calls/start", json={
        "customer_phone": "+919876543210",
        "confirmed_destination": True
    })
    assert res.status_code == 400
    assert "RETELL_AGENT_ID is not configured" in res.json()["detail"]

def test_missing_from_number_in_phone_mode():
    """Returns clear requirement when RETELL_FROM_NUMBER is missing."""
    settings.RETELL_API_KEY = "test_key_123"
    settings.RETELL_AGENT_ID = "agent_test_456"
    settings.RETELL_FROM_NUMBER = ""
    settings.AUTHORIZED_TEST_NUMBERS = ""
    res = client.post("/api/calls/start", json={
        "customer_phone": "+919876543210",
        "call_mode": "phone",
        "confirmed_destination": True
    })
    assert res.status_code == 400
    assert "RETELL_FROM_NUMBER is not configured" in res.json()["detail"]

# ============================================================================
# 2. Mocked Call Initiation Tests (Never calls real phone numbers in tests)
# ============================================================================

def test_successful_call_start_mocked():
    """Verifies successful call launch with mocked Retell SDK."""
    settings.RETELL_API_KEY = "test_key_123"
    settings.RETELL_AGENT_ID = "agent_test_456"
    settings.RETELL_FROM_NUMBER = "+12025550100"
    settings.AUTHORIZED_TEST_NUMBERS = ""

    mock_resp = {
        "success": True,
        "call_id": "call_mocked_success_789",
        "call_status": "registered",
        "raw": {"call_id": "call_mocked_success_789", "call_status": "registered"}
    }

    with patch("app.integrations.retell_provider.retell_provider.initiate_phone_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_resp

        res = client.post("/api/calls/start", json={
            "customer_name": "Rajesh Sharma",
            "customer_phone": "+919876543210",
            "property_type": "Residential",
            "ownership_status": "Sole",
            "original_documents_available": "Yes",
            "loan_amount_requested": 4500000,
            "occupation": "Salaried",
            "income_mode": "Bank",
            "market_value": 12000000,
            "tenure_years": 10,
            "confirmed_destination": True
        })

        assert res.status_code == 200
        data = res.json()
        assert data["call_id"] == "call_mocked_success_789"
        assert data["call_status"] == "registered"
        assert data["phone_number"] == "+919876543210"

        # Verify call is persisted in SQLite
        saved = CallService.get_call_by_id("call_mocked_success_789")
        assert saved is not None
        assert saved["customer_name"] == "Rajesh Sharma"
        assert saved["outcome"] == "IN_PROGRESS"
        assert saved["collected_fields"]["property_type"] == "Residential"

def test_provider_api_error_handling():
    """Handles downstream provider errors and returns appropriate error."""
    settings.RETELL_API_KEY = "test_key_123"
    settings.RETELL_AGENT_ID = "agent_test_456"
    settings.RETELL_FROM_NUMBER = "+12025550100"
    settings.AUTHORIZED_TEST_NUMBERS = ""

    mock_error_resp = {
        "success": False,
        "error": "Retell Provider Timeout",
        "status_code": 502
    }

    with patch("app.integrations.retell_provider.retell_provider.initiate_phone_call", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_error_resp

        res = client.post("/api/calls/start", json={
            "customer_phone": "+919876543210",
            "confirmed_destination": True
        })
        assert res.status_code == 502
        assert "Retell Provider Timeout" in res.json()["detail"]

# ============================================================================
# 3. Transcript & Recording Endpoint Tests
# ============================================================================

def test_calls_with_no_transcript_or_recording_yet():
    """Correctly indicates pending status when no transcript or recording exists."""
    record = {
        "call_id": "call_pending_001",
        "customer_name": "Test Customer",
        "phone_number": "+919876543210",
        "timestamp": "2026-10-11T12:00:00",
        "call_type": "simulation",
        "call_status": "registered",
        "outcome": "IN_PROGRESS",
        "recording_url": None,
        "transcript": [],
        "collected_fields": {},
        "decision_explanation": "Pending",
        "error_message": None
    }
    call_repository.save_call_record(record)

    # Transcript endpoint
    t_res = client.get("/api/calls/call_pending_001/transcript")
    assert t_res.status_code == 200
    t_data = t_res.json()
    assert t_data["available"] is False
    assert t_data["transcript"] == []
    assert "not available yet" in t_data["message"].lower()

    # Recording endpoint
    r_res = client.get("/api/calls/call_pending_001/recording")
    assert r_res.status_code == 200
    r_data = r_res.json()
    assert r_data["available"] is False
    assert r_data["recording_url"] is None
    assert "not available yet" in r_data["message"].lower()

def test_calls_with_actual_transcript_and_recording():
    """Returns authentic transcript turns and recording URL when present."""
    record = {
        "call_id": "call_completed_002",
        "customer_name": "Sunil Rao",
        "phone_number": "+919876543210",
        "timestamp": "2026-10-11T12:05:00",
        "call_type": "provider_call",
        "call_status": "ended",
        "outcome": "QUALIFIED",
        "recording_url": "https://api.retellai.com/recordings/call_completed_002.wav",
        "transcript": [
            {"role": "agent", "content": "Hello Sunil, this is Home Credit."},
            {"role": "customer", "content": "Hello, I am interested in LAP."}
        ],
        "collected_fields": {"property_type": "Residential"},
        "decision_explanation": "Qualified applicant.",
        "error_message": None
    }
    call_repository.save_call_record(record)

    t_res = client.get("/api/calls/call_completed_002/transcript")
    assert t_res.status_code == 200
    t_data = t_res.json()
    assert t_data["available"] is True
    assert len(t_data["transcript"]) == 2

    r_res = client.get("/api/calls/call_completed_002/recording")
    assert r_res.status_code == 200
    r_data = r_res.json()
    assert r_data["available"] is True
    assert r_data["recording_url"] == "https://api.retellai.com/recordings/call_completed_002.wav"

# ============================================================================
# 4. Webhook & Idempotency Tests
# ============================================================================

def test_webhook_duplicate_events_idempotent():
    """Duplicate webhook events update state without duplicate entries or error."""
    payload_1 = {
        "event": "call_started",
        "call": {
            "call_id": "call_webhook_idem_100",
            "call_status": "ongoing",
            "customer_name": "Arun Kumar",
            "to_number": "+919876543210",
            "start_timestamp": "2026-10-11T12:10:00"
        }
    }

    # First event
    res1 = client.post("/api/webhooks/retell", json=payload_1)
    assert res1.status_code == 200

    rec1 = CallService.get_call_by_id("call_webhook_idem_100")
    assert rec1 is not None
    assert rec1["call_status"] == "ongoing"

    # Second event (call ended with duration and recording)
    payload_2 = {
        "event": "call_ended",
        "call": {
            "call_id": "call_webhook_idem_100",
            "call_status": "ended",
            "customer_name": "Arun Kumar",
            "duration_ms": 75000,
            "recording_url": "https://api.retellai.com/recordings/call_webhook_idem_100.wav",
            "transcript": "Agent: Hello Arun\nCustomer: Hi Ananya",
            "call_analysis": {
                "custom_analysis_data": {
                    "qualification_status": "QUALIFIED"
                }
            }
        }
    }

    res2 = client.post("/api/webhooks/retell", json=payload_2)
    assert res2.status_code == 200

    rec2 = CallService.get_call_by_id("call_webhook_idem_100")
    assert rec2 is not None
    assert rec2["call_status"] == "ended"
    assert rec2["duration_seconds"] == 75
    assert rec2["recording_url"] == "https://api.retellai.com/recordings/call_webhook_idem_100.wav"
    assert rec2["outcome"] == "QUALIFIED"

def test_webhook_invalid_signature_rejected():
    """Rejects webhooks with invalid signatures when secret is set."""
    settings.RETELL_WEBHOOK_SECRET = "super_secret_webhook_key"

    with patch("app.integrations.retell_provider.retell_provider.verify_webhook", return_value=False):
        res = client.post(
            "/api/webhooks/retell",
            content=b'{"event": "call_ended"}',
            headers={"x-retell-signature": "invalid_sig_123"}
        )
        assert res.status_code == 401
        assert "Invalid signature" in res.json()["detail"]

# ============================================================================
# 5. Simulator Endpoints & Multi-fact / Out-of-order Initialization
# ============================================================================

def test_simulator_session_endpoint_aliases():
    """Verifies both /api/simulations and /api/simulator/sessions work."""
    res1 = client.post("/api/simulations", json={"customer_name": "User 1"})
    assert res1.status_code == 200
    assert "session_id" in res1.json()

    res2 = client.post("/api/simulator/sessions", json={"customer_name": "User 2"})
    assert res2.status_code == 200
    assert "session_id" in res2.json()

def test_simulator_initialized_with_prefilled_facts():
    """Initializes simulator session with form fields and updates checklist."""
    res = client.post("/api/simulator/sessions", json={
        "customer_name": "Deepak Patel",
        "property_type": "Residential",
        "ownership_status": "Joint",
        "original_documents_available": "Yes",
        "loan_amount_requested": 4000000,
        "occupation": "Salaried",
        "income_mode": "Bank"
    })
    assert res.status_code == 200
    data = res.json()
    checklist = data["checklist"]

    # Verify residential was captured
    prop_item = next(item for item in checklist if item["name"] == "Property Type")
    assert prop_item["status"] == "Answered"
    assert "Residential" in prop_item["captured_value"]
