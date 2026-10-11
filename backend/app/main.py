import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import config, prompt, simulations, calls, tests, webhooks, voice

app = FastAPI(
    title=settings.APP_NAME,
    description="Deterministic Qualification and Conversational Voice Engine for Home Credit Loan Against Property.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(config.router)
app.include_router(prompt.router)
app.include_router(simulations.router)
app.include_router(simulations.simulator_router)
app.include_router(calls.router)
app.include_router(tests.router)
app.include_router(webhooks.router)
app.include_router(voice.router)

@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "primary_voice_provider": settings.VOICE_PLATFORM
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
