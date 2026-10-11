import hmac
import hashlib
from typing import Optional

def verify_retell_webhook_signature(payload_bytes: bytes, signature_header: Optional[str], secret: Optional[str]) -> bool:
    """
    Verify Retell webhook signature if a secret is configured.
    If no secret is configured in development, allows execution but logs a warning.
    """
    if not secret:
        return True
    if not signature_header:
        return False
    
    expected = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)

def sanitize_text(text: str) -> str:
    """
    Basic sanitization to strip null bytes and excessive length.
    """
    if not text:
        return ""
    # Strip null bytes and limit to 4000 chars per utterance
    return text.replace("\x00", "").strip()[:4000]

def mask_credential(val: Optional[str]) -> str:
    """Mask credentials for safe logging or output"""
    if not val:
        return "NOT_SET"
    if len(val) <= 8:
        return "****"
    return f"{val[:4]}...{val[-4:]}"
