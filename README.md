# Chatterbox+RVC OpenAI-Compatible server

Designed for my fully local SillyTavern setup. 
Through trial and error I figured that Chatterbox + RVC yielded the best results for me. This was unfortunately
not supported by existing tools.

**Currently no multi-speaker setup (out of scope for me)**

This server synthesizes speech with **Chatterbox** and (optionally) runs an additional pass with **RVC**.

## Voice folder layout

```
voices/
  my_voice/
    prompt.wav           # required (any common audio format ok)
    my_model.pth         # optional (RVC model)
    my_index.index       # optional (FAISS index)
  jenn/
    jenn.wav
    jenn.pth
    jenn.index
```

The **voice name** is the folder name. The **id** returned to clients is `voices/<voice_name>`.

## Install

```bash
# Setup Python 3.10 (for example with Conda)
conda create --name "chatterbox_rvc_server" python=3.10
conda activate chatterbox_rvc_server

# Install pytorch 2.6 (!) first: https://pytorch.org/get-started/previous-versions/
# Example for CUDA 12.6 - adapt to your system!
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu126

# Install all other requirements
pip install -r requirements.txt
```

## Run

```bash
python -m server
# Serves on http://0.0.0.0:7779 by default
```

Environment overrides:

```bash
export VOICES_ROOT=/path/to/voices
export CHATTERBOX_DEVICE=cuda           # or cpu
export CHATTERBOX_MODEL=english         # or multilingual
export CHATTERVC_SAMPLE_RATE=24000
python chattervc_openai_tts_server.py
```

## SillyTavern setup

- **TTS Provider:** OpenAI Compatible
- **Provider Endpoint:** `http://127.0.0.1:7779/v1/audio/speech`
- **Model:** Either `chatterbox` or `chatterbox_rvc`
- **Available voices:** Folder names within the `voices` directory

## Training RVC

I recommend to use [Applio](https://github.com/IAHispano/Applio) for training and following their provided guidelines.

## OpenAI API

- `GET /v1/audio/models` → `{"models":[{"id":"chatterbox"},{"id":"chatterbox_rvc"}]}`
- `GET /v1/audio/voices` → scans `voices/<voice_name>/` for a prompt and optional RVC files
- `POST /v1/audio/speech` → returns audio (WAV/FLAC/OGG)

```json
{
  "model": "chatterbox_rvc",
  "input": "I can do this all day.",
  "voice": "my_voice",            // or "voices/my_voice" or "random"
  "format": "wav",
  "sample_rate": 24000,

  "language_id": "en",            // multilingual only
  "cfg_weight": 0.5,
  "exaggeration": 0.5,

  "rvc_pitch": 0,
  "rvc_index_rate": 0.75,
  "rvc_protect": 0.33,
  "rvc_f0_method": "rmvpe",
  "rvc_volume_envelope": 1.0,
  "rvc_split_audio": false,
  "rvc_f0_autotune": false,
  "rvc_clean_audio": false
}
```

If `model == "chatterbox_rvc"` and the chosen voice folder contains a `.pth`, the server will run the
RVC pass using your model and (optionally) the `.index`. If the RVC call fails for any reason, the
server safely falls back to raw Chatterbox audio and sets header `X-RVC-Applied: 0`.

### Example usage (CURL)

```bash
# List models
curl http://localhost:7779/v1/audio/models

# List voices
curl http://localhost:7779/v1/audio/voices

# Synthesize (Chatterbox only)
curl -X POST http://localhost:7779/v1/audio/speech \
  -H "Content-Type: application/json" \
  -o out.wav \
  -d '{"model":"chatterbox","voice":"my_voice","input":"Hello from ChatterVC"}'

# Synthesize + RVC (if my_voice has .pth)
curl -X POST http://localhost:7779/v1/audio/speech \
  -H "Content-Type: application/json" \
  -o out_rvc.wav \
  -d '{"model":"chatterbox_rvc","voice":"my_voice","input":"Voice fixed with RVC","rvc_index_rate":0.75}'
```

## Benchmarks

Using the cli's benchmark function

```bash 
python -m cli
connect
set-voice <voice>
benchmark speed
```

### Hardware/Software

* RTX 5070-Ti-SUPER 16GB (580.105.08, CUDA 13.0)
* 5800X3D
* 64 GB RAM
* CachyOS Linux

### Results

Warmup (not counted) + 5 tests, lower is better.

Tested input: `This is a test sentence for benchmarking.`

| Device | Avg     | Min     | Max     |
|--------|---------|---------|---------|
| GPU    | 2.386s  | 2.214s  | 2.631s  |
| CPU    | 13.482s | 12.612s | 14.325s |


## Notes

- The internal sample rate from Chatterbox is kept as‑is; the server resamples only for output.
- Formats: `wav`, `flac`, `ogg` (Vorbis). MP3 is omitted intentionally to avoid extra binaries.
- Concurrency: models are cached; each request is serialized through model locks to keep things stable.
- SillyTavern multi‑speaker is out of scope—this server uses a single prompt per request.
