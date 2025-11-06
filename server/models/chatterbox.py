"""
Chatterbox model wrapper for ChatterVC server
"""

import os
import threading
from typing import Optional

import numpy as np
import torch

from ..utils.config import DEVICE

# Chatterbox imports
try:
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


class CBHandle:
    """Chatterbox model handler with lazy loading."""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.model = None
        self.sr = None

    def load(self):
        """Load the Chatterbox model if not already loaded."""
        if self.model is not None:
            return
        with self.lock:
            if self.model is not None:
                return
            # Convert string device to torch.device if needed
            device_param = DEVICE if isinstance(DEVICE, torch.device) else torch.device(DEVICE)
            self.model = _CBModel.from_pretrained(device=device_param)
            # torchaudio.save below expects an integer sr
            self.sr = int(getattr(self.model, "sr", 24000))

    def tts(self, text: str, audio_prompt_path: Optional[str], language_id: Optional[str], cfg_weight: float, exaggeration: float) -> np.ndarray:
        """Generate speech using Chatterbox."""
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

        wav = self.model.generate(text, audio_prompt_path=audio_prompt_path, **kwargs)
        # wav is likely a torch tensor shaped (1, N) or (N,)
        if torch.is_tensor(wav):
            wav = wav.detach().cpu().float().numpy()
        wav = np.asarray(wav, dtype=np.float32)
        if wav.ndim > 1:
            wav = wav.squeeze(0)
        return wav


# Global Chatterbox instance
CB = CBHandle()