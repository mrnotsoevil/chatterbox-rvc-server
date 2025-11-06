"""
ChatterVC OpenAI-compatible TTS server (Chatterbox + RVC)
---------------------------------------------------------

This module provides a refactored version of the original server.py
with improved structure and maintainability.

It serves as the main entry point and coordinates all the modules.
"""

import os
import sys
from pathlib import Path

# Import configuration
from .config import config

# Import model wrappers with global instances
from .models.chatterbox import CB
from .models.rvc import RVC

# Import utilities
from .utils import (
    VOICES_ROOT,
    CACHE_DIR,
    DEVICE,
    DEFAULT_SAMPLE_RATE,
    AUDIO_EXTS,
    _scan_voices,
    _resolve_voice,
    VoiceInfo,
    _first_audio_in,
    _first_with_suffix,
    _encode_audio,
    _resample
)

# Import voice management
from .voices import voice_manager

# Import API components
from .api import app, list_models, list_voices, audio_speech

# Export all important components for external use
__all__ = [
    # Configuration
    "config",
    
    # Model instances
    "CB",
    "RVC",
    
    # Voice management
    "voice_manager",
    
    # API components
    "app",
    "list_models",
    "list_voices",
    "audio_speech",
    
    # Utilities
    "VOICES_ROOT",
    "CACHE_DIR",
    "DEVICE",
    "DEFAULT_SAMPLE_RATE",
    "AUDIO_EXTS",
    "_scan_voices",
    "_resolve_voice",
    "VoiceInfo",
    "_first_audio_in",
    "_first_with_suffix",
    "_encode_audio",
    "_resample",
]


def main():
    """
    Main entry point for the ChatterVC server.
    
    This function downloads prerequisites and starts the FastAPI server.
    """
    # Download all models
    print("[i] Download prerequisites ...")
    from rvc.lib.tools.prerequisites_download import prequisites_download_pipeline
    prequisites_download_pipeline(
        pretraineds_hifigan=True,
        models=True,
        exe=True,
    )
    print("[i] Download prerequisites ... done")

    # Start server
    print("[i] Starting server ...")
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "7779"))
    uvicorn.run("server:app", host=host, port=port, reload=False)


# Make the module runnable with `python -m server`
if __name__ == "__main__":
    main()