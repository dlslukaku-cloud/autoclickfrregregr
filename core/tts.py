from __future__ import annotations

import asyncio
from pathlib import Path

import edge_tts

from .models import Segment


VOICE = "vi-VN-HoaiMyNeural"


async def _synthesize(text: str, output: Path) -> None:
    communicator = edge_tts.Communicate(text, VOICE)
    await communicator.save(str(output))


def synthesize(segments: list[Segment], directory: Path, log) -> list[Path]:
    log("4/5  Tạo giọng Việt...")
    directory.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []

    for index, segment in enumerate(segments):
        path = directory / f"voice_{index:05d}.mp3"
        try:
            asyncio.run(_synthesize(segment.translated_text, path))
        except Exception as exc:
            raise RuntimeError(f"TTS lỗi ở segment {index}.") from exc
        outputs.append(path)

    return outputs
