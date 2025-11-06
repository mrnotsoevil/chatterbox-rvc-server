"""
Configuration module for ChatterVC server
"""

import os
from pathlib import Path

try:
    import torch
except ImportError:
    torch = None

# Configuration constants
VOICES_ROOT = Path(os.environ.get("VOICES_ROOT", "voices")).resolve()
VOICES_ROOT.mkdir(parents=True, exist_ok=True)

CACHE_DIR = Path(os.environ.get("CHATTERVC_CACHE", ".chattervc_cache")).resolve()
CACHE_DIR.mkdir(parents=True, exist_ok=True)

if torch is not None and torch.cuda.is_available():
    default_device = "cuda"
else:
    default_device = "cpu"
DEVICE = os.environ.get("CHATTERBOX_DEVICE", default_device)
DEFAULT_SAMPLE_RATE = int(os.environ.get("CHATTERVC_SAMPLE_RATE", "24000"))

AUDIO_EXTS = (".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac")