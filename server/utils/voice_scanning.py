"""
Voice scanning utilities for ChatterVC server
"""

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import AUDIO_EXTS


@dataclass
class VoiceInfo:
    name: str
    id: str            # e.g., "voices/my_voice"
    prompt: Path       # reference audio file for Chatterbox
    rvc_pth: Optional[Path]
    rvc_index: Optional[Path]


def _first_audio_in(folder: Path) -> Optional[Path]:
    """Find the first audio file in a folder."""
    for ext in AUDIO_EXTS:
        for p in sorted(folder.glob(f"*{ext}")):
            if p.is_file():
                return p
    return None


def _first_with_suffix(folder: Path, suffixes: Tuple[str, ...]) -> Optional[Path]:
    """Find the first file with one of the given suffixes."""
    for s in suffixes:
        for p in sorted(folder.glob(f"*{s}")):
            if p.is_file():
                return p
    return None


def _scan_voices() -> Tuple[List[dict], Dict[str, VoiceInfo]]:
    """Scan voices directory and return voice list and index."""
    from .config import VOICES_ROOT
    
    voices_json = [{"id": "random", "name": "Random"}]
    idx: Dict[str, VoiceInfo] = {}
    if not VOICES_ROOT.exists():
        return voices_json, idx

    for sub in sorted([p for p in VOICES_ROOT.iterdir() if p.is_dir()]):
        name = sub.name
        prompt = _first_audio_in(sub)
        if not prompt:
            # Skip folders without an audio prompt
            continue
        rvc_pth = _first_with_suffix(sub, (".pth",))
        rvc_index = _first_with_suffix(sub, (".index", ".faiss", ".idx"))
        vid = f"{name}"
        vi = VoiceInfo(name=name, id=vid, prompt=prompt, rvc_pth=rvc_pth, rvc_index=rvc_index)
        voices_json.append({"id": vid, "name": name})
        # Lookup by lowercase name or id
        idx[name.lower()] = vi
        idx[vid.lower()] = vi
    return voices_json, idx


def _resolve_voice(voice: str, voices_idx: Dict[str, VoiceInfo]) -> VoiceInfo:
    """Resolve a voice string to VoiceInfo object."""
    from fastapi import HTTPException
    from .config import VOICES_ROOT
    
    v = voice.strip().lower()
    if v == "random":
        # random among voices that have a prompt
        names = [vi for vi in voices_idx.values()]
        if not names:
            raise HTTPException(status_code=404, detail=f"No voices found in {VOICES_ROOT}.")
        return random.choice(names)
    if v in voices_idx:
        return voices_idx[v]
    # allow raw folder name
    folder = (VOICES_ROOT / voice).resolve()
    if folder.exists():
        prompt = _first_audio_in(folder)
        if not prompt:
            raise HTTPException(status_code=404, detail=f"No audio prompt file found in {folder}.")
        rvc_pth = _first_with_suffix(folder, (".pth",))
        rvc_index = _first_with_suffix(folder, (".index", ".faiss", ".idx"))
        return VoiceInfo(name=folder.name, id=f"voices/{folder.name}", prompt=prompt, rvc_pth=rvc_pth, rvc_index=rvc_index)
    raise HTTPException(status_code=404, detail=f"Voice '{voice}' not found under {VOICES_ROOT}.")