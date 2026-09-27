from __future__ import annotations

from faster_whisper import WhisperModel

from .models import Segment


class SpeechToText:
    def __init__(self, model_size: str = "base"):
        # CPU + int8 is intentionally selected for 8 GB RAM machines.
        self.model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
            cpu_threads=4,
            num_workers=1,
        )

    def transcribe(self, audio_path: str, log) -> list[Segment]:
        log("2/5  Nhận diện giọng nói bằng Whisper...")
        segments, _ = self.model.transcribe(
            audio_path,
            language="zh",
            beam_size=3,
            vad_filter=True,
            condition_on_previous_text=True,
        )

        result: list[Segment] = []
        for item in segments:
            text = item.text.strip()
            if text:
                result.append(Segment(float(item.start), float(item.end), text))

        if not result:
            raise RuntimeError("Không nhận diện được lời thoại.")
        return result
