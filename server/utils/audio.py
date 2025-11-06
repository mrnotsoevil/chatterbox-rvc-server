"""
Audio processing utilities for ChatterVC server
"""

import io
from typing import Tuple

import numpy as np
from fastapi import HTTPException

try:
    import soundfile as sf
    import librosa
except Exception as e:
    raise RuntimeError("Please install audio deps: pip install soundfile librosa") from e


def _encode_audio(wave: np.ndarray, sr: int, fmt: str = "wav") -> Tuple[bytes, str]:
    """Encode audio to WAV/FLAC/OGG format.
    
    Args:
        wave: Audio waveform as numpy array
        sr: Sample rate
        fmt: Output format ('wav', 'flac', 'ogg')
        
    Returns:
        Tuple of (audio_bytes, mime_type)
        
    Raises:
        HTTPException: If format is not supported
    """
    fmt = fmt.lower()
    buf = io.BytesIO()
    if fmt == "wav":
        sf.write(buf, wave, sr, format="WAV", subtype="PCM_16")
        mime = "audio/wav"
    elif fmt == "flac":
        sf.write(buf, wave, sr, format="FLAC")
        mime = "audio/flac"
    elif fmt == "ogg":
        sf.write(buf, wave, sr, format="OGG", subtype="VORBIS")
        mime = "audio/ogg"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format '{fmt}'. Use wav|flac|ogg.")
    return buf.getvalue(), mime


def _resample(wave: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    """Resample audio using librosa.
    
    Args:
        wave: Audio waveform as numpy array
        sr_in: Input sample rate
        sr_out: Output sample rate
        
    Returns:
        Resampled audio waveform
    """
    if sr_in == sr_out:
        return wave
    return librosa.resample(wave, orig_sr=sr_in, target_sr=sr_out)