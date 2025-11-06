"""
Model wrapper classes for ChatterVC server.

This module contains the extracted model wrapper classes from the original server.py file:
- CBHandle: Chatterbox model wrapper with lazy loading and thread safety
- RVCHolder: RVC model wrapper with lazy loading and thread safety
"""

import os
import threading
from pathlib import Path
from typing import Optional

import numpy as np

# --- Chatterbox imports ---
try:
    import torch
    import torchaudio as ta
    # Prefer English-only model unless CHATTERBOX_MODEL=multilingual
    CHATTERBOX_MODEL_FLAVOR = os.environ.get("CHATTERBOX_MODEL", "english").lower()
    if CHATTERBOX_MODEL_FLAVOR == "multilingual":
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS as _CBModel
    else:
        from chatterbox.tts import ChatterboxTTS as _CBModel
except Exception as e:
    raise RuntimeError(
        "Could not import Chatterbox. Install it with: pip install chatterbox-tts"
    ) from e

# --- RVC imports (Applio/AllTalk) ---
from rvc.infer.infer import VoiceConverter as _RVCConverter

# Import configuration
from ..config import config


# -----------------------------
# Chatterbox model holder
# -----------------------------
class CBHandle:
    def __init__(self):
        self.lock = threading.Lock()
        self.model = None
        self.sr = None

    def load(self):
        if self.model is not None:
            return
        with self.lock:
            if self.model is not None:
                return
            self.model = _CBModel.from_pretrained(device=config.device)
            # torchaudio.save below expects an integer sr
            self.sr = int(getattr(self.model, "sr", 24000))

    def tts(self, text: str, audio_prompt_path: Optional[Path], language_id: Optional[str], cfg_weight: float, exaggeration: float) -> np.ndarray:
        self.load()
        kwargs = {}
        # Multilingual model supports language_id
        if hasattr(self.model, "generate") and "language_id" in self.model.generate.__code__.co_varnames:
            if language_id:
                kwargs["language_id"] = language_id
        # Optional style controls (if supported)
        for k, v in [("cfg_weight", cfg_weight), ("exaggeration", exaggeration)]:
            if "generate" in dir(self.model) and k in self.model.generate.__code__.co_varnames:
                kwargs[k] = v

        wav = self.model.generate(text, audio_prompt_path=str(audio_prompt_path) if audio_prompt_path else None, **kwargs)
        # wav is likely a torch tensor shaped (1, N) or (N,)
        if torch.is_tensor(wav):
            wav = wav.detach().cpu().float().numpy()
        wav = np.asarray(wav, dtype=np.float32)
        if wav.ndim > 1:
            wav = wav.squeeze(0)
        return wav


# -----------------------------
# RVC wrapper (optional)
# -----------------------------
class RVCHolder:
    def __init__(self):
        self.lock = threading.Lock()
        self.vc = None

    def ensure_loaded(self):
        if _RVCConverter is None:
            raise RuntimeError("RVC stack is not importable. Please install Applio/AllTalk RVC so `from rvc.infer.infer import VoiceConverter` works.")
        if self.vc is not None:
            return
        with self.lock:
            if self.vc is None:
                self.vc = _RVCConverter()

    def convert_file(self, input_wav: Path, output_wav: Path, pth_path: Path, index_path: Optional[Path], **kwargs):
        self.ensure_loaded()
        # Map minimal kwargs to VoiceConverter.convert_audio
        self.vc.convert_audio(
            audio_input_path=str(input_wav),
            audio_output_path=str(output_wav),
            model_path=str(pth_path),
            index_path=str(index_path) if index_path else "",
            pitch=kwargs.get("pitch", 0),
            f0_method=kwargs.get("f0_method", "rmvpe"),
            index_rate=kwargs.get("index_rate", 0.75),
            volume_envelope=kwargs.get("volume_envelope", 1.0),
            protect=kwargs.get("protect", 0.33),
            split_audio=kwargs.get("split_audio", False),
            f0_autotune=kwargs.get("f0_autotune", False),
            clean_audio=kwargs.get("clean_audio", False),
            export_format="WAV",
            sid=kwargs.get("sid", 0),
        )


# Global instances (maintaining compatibility with original server.py)
CB = CBHandle()
RVC = RVCHolder()