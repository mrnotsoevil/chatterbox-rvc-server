"""
Configuration management for ChatterVC server.

This module extracts and manages all configuration from the original server.py file,
providing type-safe access to configuration values with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional
import torch


class Config:
    """Configuration class for ChatterVC server."""
    
    def __init__(self):
        # Environment variables with defaults
        self.voices_root: Path = self._get_path_env("VOICES_ROOT", "voices")
        self.cache_dir: Path = self._get_path_env("CHATTERVC_CACHE", ".chattervc_cache")
        self.device: str = self._get_device_env()
        self.sample_rate: int = int(os.environ.get("CHATTERVC_SAMPLE_RATE", "24000"))
        self.model_flavor: str = os.environ.get("CHATTERBOX_MODEL", "english").lower()
        
        # Ensure directories exist
        self.voices_root.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_path_env(self, env_var: str, default: str) -> Path:
        """Get a path from environment variable with default."""
        path_str = os.environ.get(env_var, default)
        return Path(path_str).resolve()
    
    def _get_device_env(self) -> str:
        """Get device from environment variable with CUDA fallback."""
        device = os.environ.get("CHATTERBOX_DEVICE")
        if device is not None:
            return device
        
        # Auto-detect CUDA availability if not specified
        return "cuda" if torch.cuda.is_available() else "cpu"
    
    @property
    def voices_root_str(self) -> str:
        """Get voices root as string."""
        return str(self.voices_root)
    
    @property
    def cache_dir_str(self) -> str:
        """Get cache directory as string."""
        return str(self.cache_dir)
    
    def validate(self) -> bool:
        """Validate configuration values."""
        # Check if voices root exists or can be created
        if not self.voices_root.exists():
            try:
                self.voices_root.mkdir(parents=True, exist_ok=True)
            except Exception:
                return False
        
        # Check if cache directory exists or can be created
        if not self.cache_dir.exists():
            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                return False
        
        # Validate device
        if self.device not in ["cpu", "cuda"]:
            return False
        
        # Validate sample rate
        if self.sample_rate <= 0:
            return False
        
        # Validate model flavor
        if self.model_flavor not in ["english", "multilingual"]:
            return False
        
        return True
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "voices_root": self.voices_root_str,
            "cache_dir": self.cache_dir_str,
            "device": self.device,
            "sample_rate": self.sample_rate,
            "model_flavor": self.model_flavor,
        }


# Global configuration instance
config = Config()