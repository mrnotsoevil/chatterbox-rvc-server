"""
Voice management module for ChatterVC server

This module provides a clean, object-oriented interface for voice operations
by encapsulating the voice scanning and resolution logic from server.utils.voice_scanning.
"""

import logging
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from threading import Lock

from ..utils.config import AUDIO_EXTS
from ..utils.voice_scanning import (
    _first_audio_in,
    _first_with_suffix,
    _scan_voices,
    _resolve_voice,
    VoiceInfo as VoiceInfoUtils,
)


@dataclass
class VoiceInfo:
    """Information about a voice."""
    name: str
    id: str            # e.g., "voices/my_voice"
    prompt: Path       # reference audio file for Chatterbox
    rvc_pth: Optional[Path]
    rvc_index: Optional[Path]


class VoiceManager:
    """
    Voice management class that provides a clean interface for voice operations.
    
    This class encapsulates the voice scanning and resolution logic, providing
    thread-safe access to voice information and operations.
    """
    
    def __init__(self):
        """Initialize the VoiceManager."""
        self._logger = logging.getLogger(__name__)
        self._voices_json: List[dict] = []
        self._voices_idx: Dict[str, VoiceInfo] = {}
        self._lock = Lock()
        self._scanned = False
        
        # Scan voices on initialization
        self.scan_voices()
    
    def scan_voices(self) -> Tuple[List[dict], Dict[str, VoiceInfo]]:
        """
        Scan and index available voices.
        
        Returns:
            Tuple containing (voices_json, voices_idx)
        """
        with self._lock:
            if self._scanned:
                return self._voices_json, self._voices_idx
            
            try:
                self._voices_json, self._voices_idx = _scan_voices()
                # Convert VoiceInfoUtils to VoiceInfo for internal consistency
                converted_idx = {}
                for key, voice_info in self._voices_idx.items():
                    converted_idx[key] = VoiceInfo(
                        name=voice_info.name,
                        id=voice_info.id,
                        prompt=voice_info.prompt,
                        rvc_pth=voice_info.rvc_pth,
                        rvc_index=voice_info.rvc_index
                    )
                self._voices_idx = converted_idx
                self._scanned = True
                self._logger.info(f"Scanned {len(self._voices_idx)} voices")
                return self._voices_json, self._voices_idx
            except Exception as e:
                self._logger.error(f"Error scanning voices: {e}")
                raise
    
    def get_voice(self, voice: str) -> VoiceInfo:
        """
        Get voice by name or ID.
        
        Args:
            voice: Voice name, ID, or "random"
            
        Returns:
            VoiceInfo object
            
        Raises:
            HTTPException: If voice is not found
        """
        with self._lock:
            if not self._scanned:
                self.scan_voices()
            
            try:
                # Convert VoiceInfo to VoiceInfoUtils for _resolve_voice
                utils_idx = {}
                for key, voice_info in self._voices_idx.items():
                    utils_idx[key] = VoiceInfoUtils(
                        name=voice_info.name,
                        id=voice_info.id,
                        prompt=voice_info.prompt,
                        rvc_pth=voice_info.rvc_pth,
                        rvc_index=voice_info.rvc_index
                    )
                result = _resolve_voice(voice, utils_idx)
                # Convert back to VoiceInfo
                return VoiceInfo(
                    name=result.name,
                    id=result.id,
                    prompt=result.prompt,
                    rvc_pth=result.rvc_pth,
                    rvc_index=result.rvc_index
                )
            except Exception as e:
                self._logger.error(f"Error resolving voice '{voice}': {e}")
                raise
    
    def list_voices(self) -> List[dict]:
        """
        List all available voices.
        
        Returns:
            List of voice dictionaries with id and name
        """
        with self._lock:
            if not self._scanned:
                self.scan_voices()
            
            return self._voices_json.copy()
    
    def find_voice_by_name(self, name: str) -> Optional[VoiceInfo]:
        """
        Find voice by name (case-insensitive).
        
        Args:
            name: Voice name to search for
            
        Returns:
            VoiceInfo object if found, None otherwise
        """
        with self._lock:
            if not self._scanned:
                self.scan_voices()
            
            return self._voices_idx.get(name.lower())
    
    def find_voice_by_id(self, voice_id: str) -> Optional[VoiceInfo]:
        """
        Find voice by ID (case-insensitive).
        
        Args:
            voice_id: Voice ID to search for
            
        Returns:
            VoiceInfo object if found, None otherwise
        """
        with self._lock:
            if not self._scanned:
                self.scan_voices()
            
            return self._voices_idx.get(voice_id.lower())
    
    def get_random_voice(self) -> VoiceInfo:
        """
        Get a random voice.
        
        Returns:
            Random VoiceInfo object
            
        Raises:
            HTTPException: If no voices are available
        """
        with self._lock:
            if not self._scanned:
                self.scan_voices()
            
            if not self._voices_idx:
                from fastapi import HTTPException
                from ..utils.config import VOICES_ROOT
                raise HTTPException(status_code=404, detail=f"No voices found in {VOICES_ROOT}.")
            
            return random.choice(list(self._voices_idx.values()))
    
    def refresh_voices(self) -> Tuple[List[dict], Dict[str, VoiceInfo]]:
        """
        Refresh the voice index by re-scanning the voices directory.
        
        Returns:
            Tuple containing (voices_json, voices_idx)
        """
        with self._lock:
            self._scanned = False
            return self.scan_voices()
    
    def get_voice_count(self) -> int:
        """
        Get the number of available voices.
        
        Returns:
            Number of voices available
        """
        with self._lock:
            if not self._scanned:
                self.scan_voices()
            
            return len(self._voices_idx)
    
    def has_voice(self, voice: str) -> bool:
        """
        Check if a voice exists.
        
        Args:
            voice: Voice name, ID, or "random"
            
        Returns:
            True if voice exists, False otherwise
        """
        try:
            self.get_voice(voice)
            return True
        except Exception:
            return False