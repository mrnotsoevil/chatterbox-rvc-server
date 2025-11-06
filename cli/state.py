"""
State management for the RVC CLI Interface
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class ConnectionState:
    """Connection state management"""
    server_url: str = "http://localhost:7779"
    connected: bool = False
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None

    def reset(self):
        """Reset connection state"""
        self.connected = False
        self.last_check = None
        self.error_message = None


@dataclass
class VoiceSettings:
    """Voice settings management"""
    current_voice: Optional[str] = None
    available_voices: Dict[str, str] = field(default_factory=dict)
    last_updated: Optional[datetime] = None

    def reset(self):
        """Reset voice settings"""
        self.current_voice = None
        self.available_voices = {}
        self.last_updated = None


@dataclass
class ModelSettings:
    """Model settings management"""
    current_model: Optional[str] = None
    available_models: Dict[str, str] = field(default_factory=dict)
    last_updated: Optional[datetime] = None

    def reset(self):
        """Reset model settings"""
        self.current_model = None
        self.available_models = {}
        self.last_updated = None


@dataclass
class AudioSettings:
    """Audio settings management"""
    sample_rate: int = 24000
    format: str = "wav"
    volume: float = 1.0
    last_audio_data: Optional[bytes] = None
    last_audio_path: Optional[str] = None

    def reset(self):
        """Reset audio settings"""
        self.sample_rate = 24000
        self.format = "wav"
        self.volume = 1.0
        self.last_audio_data = None
        self.last_audio_path = None


@dataclass
class AppState:
    """Main application state"""
    connection: ConnectionState = field(default_factory=ConnectionState)
    voice: VoiceSettings = field(default_factory=VoiceSettings)
    model: ModelSettings = field(default_factory=ModelSettings)
    audio: AudioSettings = field(default_factory=AudioSettings)

    def reset(self):
        """Reset all state to defaults"""
        self.connection.reset()
        self.voice.reset()
        self.model.reset()
        self.audio.reset()

    def get_status_summary(self) -> Dict[str, Any]:
        """Get summary of current state for display"""
        return {
            "connected": self.connection.connected,
            "server_url": self.connection.server_url,
            "current_voice": self.voice.current_voice,
            "current_model": self.model.current_model,
            "sample_rate": self.audio.sample_rate,
            "format": self.audio.format,
            "has_audio_data": self.audio.last_audio_data is not None,
        }

    def is_ready_for_synthesis(self) -> bool:
        """Check if state is ready for speech synthesis"""
        return (
            self.connection.connected and
            self.model.current_model is not None and
            self.voice.current_voice is not None
        )

    def update_server_info(self, models: Dict[str, str], voices: Dict[str, str]):
        """Update server information"""
        self.model.available_models = models
        self.voice.available_voices = voices
        self.model.last_updated = datetime.now()
        self.voice.last_updated = datetime.now()

        # Set defaults if available
        if models and not self.model.current_model:
            self.model.current_model = next(iter(models.keys()))
        if voices and not self.voice.current_voice:
            self.voice.current_voice = next(iter(voices.keys()))