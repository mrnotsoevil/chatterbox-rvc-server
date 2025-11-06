"""
API endpoint functions for ChatterVC server.

This module contains all the endpoint functions extracted from the original server.py file,
refactored to use the modular structure and imported dependencies.
"""

import os
import io
import time
import uuid
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import soundfile as sf

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    SpeechRequest,
    ServerInfo,
    HealthResponse,
    ModelsResponse,
    OpenAICompatModelsResponse,
    VoicesResponse,
    ModelInfo,
    VoiceInfo
)

# Import from other server modules
from ..models.chatterbox import CB
from ..models.rvc import RVC
from ..utils.config import (
    VOICES_ROOT,
    CACHE_DIR,
    DEVICE,
    DEFAULT_SAMPLE_RATE,
    AUDIO_EXTS
)
from ..utils.voice_scanning import (
    _scan_voices,
    _resolve_voice,
    VoiceInfo as VoiceInfoData,
    _first_audio_in,
    _first_with_suffix
)
from ..utils.audio import (
    _encode_audio,
    _resample
)


# Create FastAPI app
app = FastAPI(title="ChatterVC (Chatterbox+RVC) OpenAI-compatible TTS")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> ServerInfo:
    """Root endpoint with server information."""
    return ServerInfo(
        service="ChatterVC (Chatterbox + RVC) OpenAI-compatible TTS",
        endpoints=["/v1/audio/models", "/v1/audio/voices", "/v1/audio/speech"],
        voices_root=str(VOICES_ROOT),
        device=DEVICE,
        models=["chatterbox", "chatterbox_rvc"]
    )


@app.get("/health")
def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(ok=True)


@app.get("/v1/audio/models")
def list_models() -> ModelsResponse:
    """List available TTS models."""
    return ModelsResponse(models=[
        ModelInfo(id="chatterbox"),
        ModelInfo(id="chatterbox_rvc")
    ])


@app.get("/v1/models")
def list_models_compat() -> OpenAICompatModelsResponse:
    """OpenAI-compatible models list endpoint."""
    return OpenAICompatModelsResponse(data=[
        ModelInfo(id="chatterbox"),
        ModelInfo(id="chatterbox_rvc")
    ])


@app.get("/v1/audio/voices")
def list_voices() -> VoicesResponse:
    """List available voices."""
    voices_json, _ = _scan_voices()
    # Convert to VoiceInfo objects
    voices = [VoiceInfo(id=voice["id"], name=voice["name"]) for voice in voices_json]
    return VoicesResponse(voices=voices)


@app.post("/v1/audio/speech")
def audio_speech(req: SpeechRequest) -> Response:
    """Main TTS endpoint - OpenAI compatible speech synthesis."""
    text = req.input.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Field 'input' (text) is empty.")

    start_time = time.time()
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
            audio_prompt_path=str(vi.prompt) if vi.prompt else None,
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

    end_time = time.time()
    print(" -> Took ", end_time - start_time)

    return Response(content=payload, media_type=mime, headers=headers)