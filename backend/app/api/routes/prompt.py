from fastapi import APIRouter, HTTPException
from app.services.prompt_service import PromptService
from app.schemas.api import UpdatePromptRequest

router = APIRouter(prefix="/api/prompt", tags=["System Prompt"])

@router.get("")
def get_prompt():
    """Returns the production system prompt text."""
    prompt_text = PromptService.get_prompt_text()
    rendered_preview = PromptService.render_prompt()
    return {
        "raw_prompt": prompt_text,
        "rendered_preview": rendered_preview
    }

@router.put("")
def update_prompt(req: UpdatePromptRequest):
    """Updates the production system prompt after validation."""
    if not req.prompt or len(req.prompt.strip()) < 100:
        raise HTTPException(status_code=400, detail="Prompt must be at least 100 characters.")
    
    PromptService.save_prompt_text(req.prompt)
    return {
        "success": True,
        "message": "Production system prompt updated successfully."
    }
