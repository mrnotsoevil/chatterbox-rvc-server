"""
Pydantic schemas for ChatterVC API requests and responses.

This module contains all the data models used by the API endpoints,
extracted from the original server.py file.
"""

from pydantic import BaseModel, Field
from typing import Optional


class SpeechRequest(BaseModel):
    """Request model for speech synthesis endpoint."""
    model: str = Field(..., description="chatterbox or chatterbox_rvc")
    input: str = Field(..., description="Text to synthesize")
    voice: str = Field(..., description="Voice id (voices/<name>) or folder name; 'random' allowed.")
    format: str = Field("wav", description="wav | flac | ogg")
    sample_rate: int = Field(24000, description="Output sample rate (default 24000)")

    # Chatterbox controls
    language_id: str = Field("en", description="Language id (for multilingual model).")
    cfg_weight: float = Field(0.5, ge=0.0, le=1.0)
    exaggeration: float = Field(0.5, ge=0.0, le=1.0)

    # RVC controls (used only with chatterbox_rvc when voice has .pth)
    rvc_pitch: int = Field(0, description="Semitone shift for F0.")
    rvc_index_rate: float = Field(0.75, ge=0.0, le=1.0)
    rvc_protect: float = Field(0.33, ge=0.0, le=0.5)
    rvc_f0_method: str = Field("rmvpe")
    rvc_volume_envelope: float = Field(1.0, ge=0.0, le=1.0)
    rvc_split_audio: bool = Field(False)
    rvc_f0_autotune: bool = Field(False)
    rvc_clean_audio: bool = Field(False)
    rvc_sid: int = Field(0)


class ModelInfo(BaseModel):
    """Model information for OpenAI-compatible response."""
    id: str


class VoiceInfo(BaseModel):
    """Voice information for API response."""
    id: str
    name: str


class ServerInfo(BaseModel):
    """Server information for root endpoint."""
    service: str
    endpoints: list
    voices_root: str
    device: str
    models: list


class HealthResponse(BaseModel):
    """Health check response."""
    ok: bool


class ModelsResponse(BaseModel):
    """Models list response."""
    models: list[ModelInfo]


class OpenAICompatModelsResponse(BaseModel):
    """OpenAI-compatible models list response."""
    data: list[ModelInfo]


class VoicesResponse(BaseModel):
    """Voices list response."""
    voices: list[VoiceInfo]