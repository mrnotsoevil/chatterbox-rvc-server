"""
ChatterVC Server Utilities Module

This module provides utility functions for voice management and audio processing.
"""

# Import voice management functions and classes
from .voice_scanning import (
    VoiceInfo,
    _first_audio_in,
    _first_with_suffix,
    _scan_voices,
    _resolve_voice,
)

# Import audio processing functions
from .audio import (
    _encode_audio,
    _resample,
)

# Import configuration
from .config import (
    VOICES_ROOT,
    CACHE_DIR,
    DEVICE,
    DEFAULT_SAMPLE_RATE,
    AUDIO_EXTS,
)

# Export all public functions and classes
__all__ = [
    # Voice management
    "VoiceInfo",
    "_first_audio_in",
    "_first_with_suffix", 
    "_scan_voices",
    "_resolve_voice",
    
    # Audio processing
    "_encode_audio",
    "_resample",
    
    # Configuration
    "VOICES_ROOT",
    "CACHE_DIR", 
    "DEVICE",
    "DEFAULT_SAMPLE_RATE",
    "AUDIO_EXTS",
]