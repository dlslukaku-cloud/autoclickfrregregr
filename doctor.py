
from __future__ import annotations

import shutil
import sys

REQUIRED = ["ffmpeg", "ffprobe", "yt-dlp"]

print("=== Douyin Smart Dubber Doctor ===")
print(f"Python: {sys.version.split()[0]}")

ok = True
for command in REQUIRED:
    path = shutil.which(command)
    status = f"OK  {path}" if path else "MISSING"
    print(f"{command:8} {status}")
    ok &= bool(path)

try:
    import PySide6
    print(f"PySide6   OK  {PySide6.__version__}")
except Exception:
    print("PySide6   MISSING")
    ok = False

try:
    import faster_whisper
    print("Whisper   OK")
except Exception:
    print("Whisper   MISSING")
    ok = False

try:
    from playwright.sync_api import sync_playwright
    print("Playwright OK")
except Exception:
    print("Playwright MISSING")
    ok = False

print("\nRESULT:", "READY" if ok else "NOT READY")
raise SystemExit(0 if ok else 1)
