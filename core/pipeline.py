from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .downloader import download
from .mixer import render
from .stt import SpeechToText
from .translator import SmartTranslator
from .tts import synthesize


@dataclass(frozen=True)
class PipelineConfig:
    workspace: Path
    output_dir: Path


class DubPipeline:
    def __init__(self, config: PipelineConfig, log, progress):
        self.config = config
        self.log = log
        self.progress = progress

    def _extract_audio(self, video: Path, audio: Path) -> None:
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(video),
                "-vn", "-ac", "1", "-ar", "16000",
                "-c:a", "pcm_s16le", str(audio),
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Không tách được audio:\n{result.stderr[-2000:]}")

    def run(self, url: str) -> Path:
        self.config.workspace.mkdir(parents=True, exist_ok=True)
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        video = self.config.workspace / "source.mp4"
        audio = self.config.workspace / "speech.wav"
        voices = self.config.workspace / "voices"
        output = self.config.output_dir / "dubbed_vi.mp4"

        self.progress.emit(5)
        download(url, video, self.log)

        self.progress.emit(20)
        self._extract_audio(video, audio)

        self.progress.emit(30)
        segments = SpeechToText(model_size="base").transcribe(str(audio), self.log)

        self.progress.emit(55)
        segments = SmartTranslator().translate(segments, self.log)

        self.progress.emit(70)
        voice_files = synthesize(segments, voices, self.log)

        self.progress.emit(85)
        result = render(video, segments, voice_files, output, self.log)

        self.progress.emit(100)
        return result
