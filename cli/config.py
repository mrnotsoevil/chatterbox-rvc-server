"""
Configuration management for the RVC CLI Interface
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class Config:
    """Configuration management"""
    
    # Server settings
    server_url: str = "http://localhost:7779"
    
    # Audio settings
    sample_rate: int = 24000
    audio_format: str = "wav"
    volume: float = 1.0
    
    # UI settings
    show_progress: bool = True
    verbose_output: bool = False
    
    # File paths
    config_dir: str = "~/.chattervc-cli"
    config_file: str = "config.json"
    
    @classmethod
    def load(cls) -> 'Config':
        """Load configuration from file"""
        config_path = Path(cls._get_config_path())
        
        if not config_path.exists():
            return cls()
        
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
                return cls(**data)
        except (json.JSONDecodeError, TypeError, ValueError):
            # If config is corrupted, return default
            return cls()
    
    def save(self) -> None:
        """Save configuration to file"""
        config_path = Path(self._get_config_path())
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(asdict(self), f, indent=2)
    
    @staticmethod
    def _get_config_path() -> str:
        """Get configuration file path"""
        config_dir = Path(os.path.expanduser("~/.chattervc-cli"))
        return str(config_dir / "config.json")
    
    def update(self, **kwargs) -> None:
        """Update configuration values"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create configuration from dictionary"""
        return cls(**data)