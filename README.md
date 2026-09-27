# Douyin Smart Dubber

Windows 10 x64 app: paste a Douyin URL -> download -> Chinese speech recognition -> AI translation -> Vietnamese TTS -> synchronized voice-over -> MP4.

## Designed for
- Windows 10 x64
- 8 GB RAM
- CPU-only operation
- No CUDA required

## Pipeline
1. URL validation
2. Download with yt-dlp
3. Playwright browser fallback for Douyin when yt-dlp cannot extract the video
4. Faster-Whisper STT (CPU/int8)
5. Context-aware translation through an OpenAI-compatible API
6. Vietnamese Edge TTS
7. FFmpeg segment timing + audio mix
8. Final MP4

## Important
Only download/use videos you are authorized to process. Douyin can change its anti-bot behavior; the downloader intentionally has a browser fallback.

## Install

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements.txt
playwright install chromium
```

Install FFmpeg and put `ffmpeg.exe` + `ffprobe.exe` on PATH. The official FFmpeg site links current Windows builds:
https://ffmpeg.org/download.html

## AI translation configuration

Set these environment variables:

```bat
set DUB_LLM_BASE_URL=https://api.openai.com/v1
set DUB_LLM_API_KEY=YOUR_KEY
set DUB_LLM_MODEL=YOUR_MODEL
```

The application only sends recognized transcript text to the configured translation endpoint.

## Run

```bat
python app.py
```

## Tests

```bat
python -m pytest -q
```

## Architecture

```text
PySide6 UI
   |
   v
JobController
   |
   +--> Downloader
   |      +--> yt-dlp
   |      +--> Playwright fallback
   |
   +--> STT (faster-whisper)
   |
   +--> Translator (OpenAI-compatible HTTP)
   |
   +--> TTS (edge-tts)
   |
   +--> FFmpeg Mixer
   |
   v
output/*.mp4
```
