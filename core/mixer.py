
from __future__ import annotations

import subprocess
from pathlib import Path

from .models import Segment


def _duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path)
        ],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe lỗi: {result.stderr[-1000:]}")
    return max(0.05, float(result.stdout.strip()))


def _atempo_chain(rate: float) -> str:
    # FFmpeg accepts 0.5..2.0 per atempo filter; chain filters for extremes.
    filters = []
    value = max(0.05, rate)
    while value > 2.0:
        filters.append("atempo=2.0")
        value /= 2.0
    while value < 0.5:
        filters.append("atempo=0.5")
        value /= 0.5
    filters.append(f"atempo={value:.6f}")
    return ",".join(filters)


def render(video: Path, segments: list[Segment], voice_files: list[Path], output: Path, log) -> Path:
    log("5/5  Đồng bộ voice + mix audio + render MP4...")
    output.parent.mkdir(parents=True, exist_ok=True)

    inputs = ["-i", str(video)]
    for voice in voice_files:
        inputs += ["-i", str(voice)]

    filters: list[str] = []
    labels: list[str] = []

    for i, (segment, voice) in enumerate(zip(segments, voice_files)):
        voice_duration = _duration(voice)
        target = segment.duration

        # atempo > 1 speeds up; atempo < 1 slows down.
        # Clamp extreme compression/decompression to keep speech intelligible.
        rate = min(2.0, max(0.5, voice_duration / target))
        delay_ms = max(0, round(segment.start * 1000))

        filters.append(
            f"[{i + 1}:a]aresample=48000,"
            f"{_atempo_chain(rate)},"
            f"adelay={delay_ms}|{delay_ms},volume=1.0[a{i}]"
        )
        labels.append(f"[a{i}]")

    filters.append(
        "".join(labels)
        + f"amix=inputs={len(labels)}:duration=longest:dropout_transition=0,"
        "aresample=48000[dub]"
    )
    filters.append("[0:a]volume=0.16[bg]")
    filters.append("[bg][dub]amix=inputs=2:duration=first:dropout_transition=0[mix]")

    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "0:v:0", "-map", "[mix]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
        "-movflags", "+faststart", str(output),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg render thất bại:\n{result.stderr[-3000:]}")
    return output
