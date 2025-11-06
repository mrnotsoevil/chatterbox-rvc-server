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
    current_model: Optional[str] = "chatterbox_rvc"
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

    def update_server_info(self, models: Dict[str, str], voices_response: Any):
        """Update server information"""
        # Handle models (simple dict)
        self.model.available_models = models
        
        # Handle voices (can be dict with 'voices' key or list)
        if isinstance(voices_response, dict) and 'voices' in voices_response:
            voices_list = voices_response['voices']
        elif isinstance(voices_response, list):
            voices_list = voices_response
        else:
            voices_list = []
        
        # Convert voices list to dict format {id: name}
        self.voice.available_voices = {}
        for voice in voices_list:
            if isinstance(voice, dict):
                voice_id = voice.get('id')
                voice_name = voice.get('name', voice_id)
                if voice_id:
                    self.voice.available_voices[voice_id] = voice_name or voice_id
        
        self.model.last_updated = datetime.now()
        self.voice.last_updated = datetime.now()

        # Set defaults if available
        if models and not self.model.current_model:
            self.model.current_model = next(iter(models.keys()))
        if self.voice.available_voices and not self.voice.current_voice:
            self.voice.current_voice = next(iter(self.voice.available_voices.keys()))
    
    async def set_voice(self, voice_input: str, http_client=None) -> None:
        """Set the current voice by ID or name
        
        Args:
            voice_input: Voice ID or name to set as current voice
            http_client: Optional HTTP client to fetch voices if not available
        """
        # If we don't have voices and have an http_client, try to fetch them
        if not self.voice.available_voices and http_client:
            try:
                voices_response = await http_client.get_voices()
                models = self.model.available_models or {}
                self.update_server_info(models, voices_response)
            except Exception as e:
                # If fetching fails, continue with available voices (empty)
                pass
        
        # If voice_input is already a valid ID, use it directly
        if voice_input in self.voice.available_voices:
            self.voice.current_voice = voice_input
            return
        
        # If voice_input is a name, find the corresponding ID
        for voice_id, voice_name in self.voice.available_voices.items():
            if voice_name == voice_input:
                self.voice.current_voice = voice_id
                return
        
        # If not found, raise an error
        available_voices_list = [f"{vid} ({name})" for vid, name in self.voice.available_voices.items()]
        raise ValueError(f"Voice '{voice_input}' not found. Available voices: {', '.join(available_voices_list) or 'None'}")
    
    def get_voice_info(self) -> Dict[str, Any]:
        """Get current voice information"""
        if not self.voice.current_voice:
            return {"current_voice": None, "current_voice_name": None}
        
        current_name = self.voice.available_voices.get(self.voice.current_voice, "Unknown")
        return {
            "current_voice": self.voice.current_voice,
            "current_voice_name": current_name
        }