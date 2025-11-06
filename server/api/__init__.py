"""
ChatterVC API module.

This module provides the FastAPI application and all API endpoints
for the ChatterVC OpenAI-compatible TTS server.
"""

import os

# Import the FastAPI app instance
from .endpoints import app

# Import individual endpoint functions for potential direct use
from .endpoints import (
    root,
    health,
    list_models,
    list_models_compat,
    list_voices,
    audio_speech
)

# Import schemas for external use
from .schemas import (
    SpeechRequest,
    ServerInfo,
    HealthResponse,
    ModelsResponse,
    OpenAICompatModelsResponse,
    VoicesResponse,
    ModelInfo,
    VoiceInfo
)

# Make the module runnable with `python -m server.api`
if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "7779"))
    uvicorn.run("server.api:app", host=host, port=port, reload=False)