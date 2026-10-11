from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os
from pathlib import Path

class Settings(BaseSettings):
    APP_NAME: str = "Home Credit LAP Voice Qualification Agent"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Agent defaults
    COMPANY_NAME: str = "Home Credit"
    AGENT_NAME: str = "Ananya"
    AGENT_GENDER: str = "female"
    DEFAULT_CUSTOMER_NAME: str = "Valued Customer"
    DEFAULT_LANGUAGE: str = "English"  # "English" or "Hindi"
    VOICE_PLATFORM: str = "retell"     # "retell" or "bolna"
    VOICE_ID: str = "11labs-Adrian"
    
    # RAG Context
    ADDITIONAL_CONTEXT_FROM_RAG: str = (
        "Home Credit Loan Against Property (LAP) is a secured loan offering funds up to ₹75,00,000 "
        "against clear residential, commercial, or industrial properties. Repayment tenure ranges from 3 to 15 years. "
        "Original property documents are mandatory for verification. Exact interest rates and personalized terms "
        "are determined post preliminary qualification by a Senior Loan Expert. Disbursal requires full physical verification."
    )

    # Provider Keys (Never expose to clients)
    RETELL_API_KEY: str = Field(default="", description="Retell AI secret API key")
    RETELL_AGENT_ID: str = Field(default="", description="Configured Retell Agent ID")
    RETELL_FROM_NUMBER: str = Field(default="", description="Retell registered outbound phone number")
    RETELL_WEBHOOK_SECRET: str = Field(default="", description="Webhook verification secret")
    AUTHORIZED_TEST_NUMBERS: str = Field(default="", description="Comma-separated authorized destination test numbers")
    BOLNA_API_KEY: str = Field(default="", description="Bolna API key")
    BOLNA_AGENT_ID: str = Field(default="", description="Bolna Agent ID")

    # Security & CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    DATABASE_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "lap_voice_agent.db")

    class Config:
        env_file = Path(__file__).resolve().parents[3] / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    def get_safe_config(self) -> dict:
        return {
            "app_name": self.APP_NAME,
            "environment": self.ENVIRONMENT,
            "debug": self.DEBUG,
            "company_name": self.COMPANY_NAME,
            "agent_name": self.AGENT_NAME,
            "agent_gender": self.AGENT_GENDER,
            "default_customer_name": self.DEFAULT_CUSTOMER_NAME,
            "default_language": self.DEFAULT_LANGUAGE,
            "voice_platform": self.VOICE_PLATFORM,
            "voice_id": self.VOICE_ID,
            "has_retell_key": bool(self.RETELL_API_KEY),
            "retell_agent_id": self.RETELL_AGENT_ID if self.RETELL_AGENT_ID else None,
            "retell_from_number": self.RETELL_FROM_NUMBER if self.RETELL_FROM_NUMBER else None,
            "authorized_test_numbers": [n.strip() for n in self.AUTHORIZED_TEST_NUMBERS.split(",") if n.strip()] if self.AUTHORIZED_TEST_NUMBERS else [],
            "has_webhook_secret": bool(self.RETELL_WEBHOOK_SECRET),
            "has_bolna_key": bool(self.BOLNA_API_KEY),
            "additional_context_from_rag": self.ADDITIONAL_CONTEXT_FROM_RAG,
        }

settings = Settings()
