import os
import datetime
from typing import Optional, Dict, Any
from app.core.config import settings

class PromptService:
    """
    Manages loading, updating, and safely rendering the production system prompt
    with dynamic variables.
    """
    
    PROMPT_PATH = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "prompts",
        "lap_qualification_system_prompt.txt"
    )

    @classmethod
    def get_prompt_text(cls) -> str:
        if os.path.exists(cls.PROMPT_PATH):
            with open(cls.PROMPT_PATH, "r", encoding="utf-8") as f:
                return f.read()
        return "System prompt file not found."

    @classmethod
    def save_prompt_text(cls, new_prompt: str) -> None:
        os.makedirs(os.path.dirname(cls.PROMPT_PATH), exist_ok=True)
        with open(cls.PROMPT_PATH, "w", encoding="utf-8") as f:
            f.write(new_prompt)

    @classmethod
    def render_prompt(
        cls,
        customer_name: Optional[str] = None,
        language: Optional[str] = None,
        agent_name: Optional[str] = None,
        agent_gender: Optional[str] = None,
        company_name: Optional[str] = None,
        rag_context: Optional[str] = None,
        conversation_history_text: str = "",
        customer_utterance: str = ""
    ) -> str:
        prompt = cls.get_prompt_text()
        
        now = datetime.datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_day = now.strftime("%A")
        current_time = now.strftime("%H:%M:%S")

        # Fallbacks for safe substitution
        c_name = customer_name or settings.DEFAULT_CUSTOMER_NAME or "Valued Customer"
        c_company = company_name or settings.COMPANY_NAME or "Home Credit"
        a_name = agent_name or settings.AGENT_NAME or "Ananya"
        a_gender = agent_gender or settings.AGENT_GENDER or "female"
        lang = language or settings.DEFAULT_LANGUAGE or "English"
        rag = rag_context or settings.ADDITIONAL_CONTEXT_FROM_RAG or "No additional context."

        substitutions: Dict[str, str] = {
            "{{company_name}}": c_company,
            "{{customer_name}}": c_name,
            "{{agent_name}}": a_name,
            "{{agent_gender}}": a_gender,
            "{{current_date}}": current_date,
            "{{current_day}}": current_day,
            "{{current_time}}": current_time,
            "{{additional_context_from_rag}}": rag,
            "{{language_to_speak}}": lang,
            "{{conversation_history}}": conversation_history_text if conversation_history_text else "(No previous history)",
            "{{customer_utterance}}": customer_utterance if customer_utterance else "(Call initiated)"
        }

        rendered = prompt
        for var, val in substitutions.items():
            rendered = rendered.replace(var, str(val))

        return rendered
