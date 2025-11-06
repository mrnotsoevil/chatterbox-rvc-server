"""
ChatterVC Server Voices Module

This module provides voice management functionality through a clean,
object-oriented interface. It encapsulates the voice scanning and resolution
logic from server.utils.voice_scanning.
"""

from .manager import VoiceManager, VoiceInfo

# Create a default instance for easy import
voice_manager = VoiceManager()

# Export all public classes and functions
__all__ = [
    "VoiceManager",
    "VoiceInfo",
    "voice_manager",
]