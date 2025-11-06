
"""
ChatterVC OpenAI-compatible TTS server (Chatterbox + RVC)
---------------------------------------------------------

Directory layout (per-voice):
    voices/<voice_name>/
        prompt.wav                 # required (reference voice for Chatterbox; any common audio extension ok)
        my_model.pth               # optional (RVC model)
        my_index.index             # optional (FAISS index)

Endpoints:
  - GET  /v1/audio/models
  - GET  /v1/audio/voices
  - POST /v1/audio/speech

Request body for /v1/audio/speech (minimal OpenAI-compat):
{
  "model": "chatterbox_rvc",     // or "chatterbox"
  "input": "Your text here",
  "voice": "my_voice",           // "voices/my_voice" or "my_voice" or "random"
  "format": "wav",               // wav|flac|ogg (Vorbis)
  "sample_rate": 24000,
  // Chatterbox controls
  "language_id": "en",
  "cfg_weight": 0.5,
  "exaggeration": 0.5,
  // RVC controls (used when model == chatterbox_rvc and a .pth is present)
  "rvc_pitch": 0,
  "rvc_index_rate": 0.75,
  "rvc_protect": 0.33,
  "rvc_f0_method": "rmvpe",
  "rvc_volume_envelope": 1.0,
  "rvc_split_audio": false,
  "rvc_f0_autotune": false,
  "rvc_clean_audio": false
}

This server is **standalone** (no remote API calls). It uses:
  * Chatterbox (pip: chatterbox-tts) for initial TTS
  * RVC (Applio/AllTalk stack) for optional voice conversion

To keep startup simple, RVC is loaded lazily when a voice has a .pth.

"""

import os
import io
import re
import sys
import json
import math
import time
import random
import shutil
import tempfile
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# --- Audio utils ---
try:
    import soundfile as sf
    import librosa
except Exception as e:
    raise RuntimeError("Please install audio deps: pip install soundfile librosa") from e

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


# -----------------------------
# Configuration
# -----------------------------
VOICES_ROOT = Path(os.environ.get("VOICES_ROOT", "voices")).resolve()
VOICES_ROOT.mkdir(parents=True, exist_ok=True)

CACHE_DIR = Path(os.environ.get("CHATTERVC_CACHE", ".chattervc_cache")).resolve()
CACHE_DIR.mkdir(parents=True, exist_ok=True)

DEVICE = os.environ.get("CHATTERBOX_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
DEFAULT_SAMPLE_RATE = int(os.environ.get("CHATTERVC_SAMPLE_RATE", "24000"))

# -----------------------------
# Voice scanning
# -----------------------------
AUDIO_EXTS = (".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac")
def _first_audio_in(folder: Path) -> Optional[Path]:
    for ext in AUDIO_EXTS:
        for p in sorted(folder.glob(f"*{ext}")):
            if p.is_file():
                return p
    return None

def _first_with_suffix(folder: Path, suffixes: Tuple[str, ...]) -> Optional[Path]:
    for s in suffixes:
        for p in sorted(folder.glob(f"*{s}")):
            if p.is_file():
                return p
    return None

@dataclass
class VoiceInfo:
    name: str
    id: str            # e.g., "voices/my_voice"
    prompt: Path       # reference audio file for Chatterbox
    rvc_pth: Optional[Path]
    rvc_index: Optional[Path]

def _scan_voices() -> Tuple[List[dict], Dict[str, VoiceInfo]]:
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
        vid = f"voices/{name}"
        vi = VoiceInfo(name=name, id=vid, prompt=prompt, rvc_pth=rvc_pth, rvc_index=rvc_index)
        voices_json.append({"id": vid, "name": name})
        # Lookup by lowercase name or id
        idx[name.lower()] = vi
        idx[vid.lower()] = vi
    return voices_json, idx

def _resolve_voice(voice: str, voices_idx: Dict[str, VoiceInfo]) -> VoiceInfo:
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
            self.model = _CBModel.from_pretrained(device=DEVICE)
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

CB = CBHandle()

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

RVC = RVCHolder()

# -----------------------------
# I/O helpers
# -----------------------------
def _encode_audio(wave: np.ndarray, sr: int, fmt: str = "wav") -> Tuple[bytes, str]:
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
    if sr_in == sr_out:
        return wave
    return librosa.resample(wave, orig_sr=sr_in, target_sr=sr_out)


# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(title="ChatterVC (Chatterbox+RVC) OpenAI-compatible TTS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "service": "ChatterVC (Chatterbox + RVC) OpenAI-compatible TTS",
        "endpoints": ["/v1/audio/models", "/v1/audio/voices", "/v1/audio/speech"],
        "voices_root": str(VOICES_ROOT),
        "device": DEVICE,
        "models": ["chatterbox", "chatterbox_rvc"],
    }

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/v1/audio/models")
def list_models():
    return {"models": [{"id": "chatterbox"}, {"id": "chatterbox_rvc"}]}

@app.get("/v1/models")
def list_models_compat():
    return {"data": [{"id": "chatterbox"}, {"id": "chatterbox_rvc"}]}

@app.get("/v1/audio/voices")
def list_voices():
    voices_json, _ = _scan_voices()
    return {"voices": voices_json}


# ---- Request schema ----
class SpeechRequest(BaseModel):
    model: str = Field(..., description="chatterbox or chatterbox_rvc")
    input: str = Field(..., description="Text to synthesize")
    voice: str = Field(..., description="Voice id (voices/<name>) or folder name; 'random' allowed.")
    format: str = Field("wav", description="wav | flac | ogg")
    sample_rate: int = Field(DEFAULT_SAMPLE_RATE, description="Output sample rate (default 24000)")

    # Chatterbox controls
    language_id: str = Field("en", description="Language id (for multilingual model).")
    cfg_weight: float = Field(0.5, ge=0.0, le=1.0)
    exaggeration: float = Field(0.5, ge=0.0, le=1.0)

    # RVC controls (used only with chatterbox_rvc when voice has .pth)
    rvc_pitch: int = Field(0, description="Semitone shift for F0.")
    rvc_index_rate: float = Field(0.75, ge=0.0, le=1.0)
    rvc_protect: float = Field(0.33, ge=0.0, le=0.5)
    rvc_f0_method: str = Field("rmvpe")
    rvc_volume_envelope: float = Field(1.0, ge=0.0, le=1.0)
    rvc_split_audio: bool = Field(False)
    rvc_f0_autotune: bool = Field(False)
    rvc_clean_audio: bool = Field(False)
    rvc_sid: int = Field(0)

@app.post("/v1/audio/speech")
def audio_speech(req: SpeechRequest):
    text = req.input.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Field 'input' (text) is empty.")

    print("[i] New request")
    print(" - text: ", text)
    print(" - model: ", req.model)
    print(" - voice: ", req.voice)

    # Resolve voice
    _, idx = _scan_voices()
    vi = _resolve_voice(req.voice, idx)

    # 1) Chatterbox TTS
    try:
        print(" [i] Chatterbox TTS inference ...")
        wave = CB.tts(
            text=text,
            audio_prompt_path=vi.prompt,
            language_id=req.language_id,
            cfg_weight=req.cfg_weight,
            exaggeration=req.exaggeration,
        )
        tts_sr = CB.sr or DEFAULT_SAMPLE_RATE
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatterbox synthesis failed: {e}")

    # 2) Optional RVC pass
    applied_rvc = False
    if req.model.lower() == "chatterbox_rvc" and vi.rvc_pth is not None:
        try:
            print(" [i] RVC enhancement ... [model=", vi.rvc_pth, ", index=", vi.rvc_index,"]")
            tmp_in = CACHE_DIR / f"tts_{uuid.uuid4().hex}.wav"
            tmp_out = CACHE_DIR / f"rvc_{uuid.uuid4().hex}.wav"
            # Write TTS to disk
            sf.write(tmp_in, wave, tts_sr, format="WAV", subtype="PCM_16")
            # Run RVC
            RVC.convert_file(
                input_wav=tmp_in,
                output_wav=tmp_out,
                pth_path=vi.rvc_pth,
                index_path=vi.rvc_index,
                pitch=req.rvc_pitch,
                f0_method=req.rvc_f0_method,
                index_rate=req.rvc_index_rate,
                volume_envelope=req.rvc_volume_envelope,
                protect=req.rvc_protect,
                split_audio=req.rvc_split_audio,
                f0_autotune=req.rvc_f0_autotune,
                clean_audio=req.rvc_clean_audio,
                sid=req.rvc_sid,
            )
            # Read back
            wave, tts_sr = sf.read(tmp_out)
            if wave.ndim > 1:
                wave = wave.mean(axis=1)
            wave = wave.astype(np.float32)
            applied_rvc = True
            print(" [i] RVC enhancement ... successful")
        except Exception as e:
            # If RVC fails, fall back to raw TTS to avoid breaking ST
            print(" [i] RVC enhancement ... FAILED", e)
            applied_rvc = False

    # 3) Resample to requested output rate
    out_wave = _resample(wave, sr_in=tts_sr, sr_out=req.sample_rate)

    # 4) Encode
    try:
        payload, mime = _encode_audio(out_wave, sr=req.sample_rate, fmt=req.format)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    headers = {
        "Content-Type": mime,
        "Cache-Control": "no-store",
        "X-Model": req.model,
        "X-Voice": vi.name,
        "X-RVC-Applied": "1" if applied_rvc else "0",
        "X-Chatterbox-SR": str(tts_sr),
    }
    return Response(content=payload, media_type=mime, headers=headers)


def main():
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "7779"))
    uvicorn.run("server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
