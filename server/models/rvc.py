"""
RVC (Applio/AllTalk) wrapper for ChatterVC server
"""

import threading
from pathlib import Path
from typing import Optional

from rvc.infer.infer import VoiceConverter as _RVCConverter


class RVCHolder:
    """RVC model handler with lazy loading."""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.vc = None

    def ensure_loaded(self):
        """Ensure RVC converter is loaded."""
        if _RVCConverter is None:
            raise RuntimeError("RVC stack is not importable. Please install Applio/AllTalk RVC so `from rvc.infer.infer import VoiceConverter` works.")
        if self.vc is not None:
            return
        with self.lock:
            if self.vc is None:
                self.vc = _RVCConverter()

    def convert_file(self, input_wav: Path, output_wav: Path, pth_path: Path, index_path: Optional[Path], **kwargs):
        """Convert audio file using RVC."""
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


# Global RVC instance
RVC = RVCHolder()