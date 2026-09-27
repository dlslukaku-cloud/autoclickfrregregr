
from __future__ import annotations

import asyncio
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright


class DownloadError(RuntimeError):
    pass


def validate_douyin_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"www.douyin.com", "v.douyin.com"}:
        raise ValueError("Chỉ chấp nhận URL https://www.douyin.com hoặc https://v.douyin.com")


def _run_ytdlp(url: str, output: Path) -> bool:
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "yt-dlp", "--no-playlist", "--restrict-filenames",
        "-f", "bv*+ba/b", "--merge-output-format", "mp4",
        "-o", str(output), url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    return result.returncode == 0 and output.exists() and output.stat().st_size > 100_000


async def _playwright_download(url: str, output: Path) -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/131 Safari/537.36"
            )
        )
        try:
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(4000)

            candidates = await page.locator("video").evaluate_all(
                """els => els.map(v => v.currentSrc || v.src).filter(Boolean)"""
            )

            if not candidates:
                html = await page.content()
                candidates = re.findall(
                    r'https?[^"\\\']+\.(?:mp4|m3u8)(?:[^"\\\']*)?',
                    html, flags=re.I
                )

            candidates = [x.replace("\\u0026", "&") for x in candidates]
            candidates = [x for x in candidates if x.startswith(("http://", "https://"))]

            if not candidates:
                raise DownloadError(
                    "Không tìm thấy media URL. Video có thể yêu cầu đăng nhập hoặc bị anti-bot."
                )

            media_url = candidates[0]
            headers = {"Referer": "https://www.douyin.com/"}

            # Reuse the browser session/cookies for the media request.
            response = await context.request.get(
                media_url,
                headers=headers,
                timeout=120000,
            )
            if not response.ok:
                raise DownloadError(f"Media request HTTP {response.status}")

            body = await response.body()
            content_type = response.headers.get("content-type", "").lower()

            if media_url.lower().split("?", 1)[0].endswith(".m3u8") or "mpegurl" in content_type:
                # Save playlist and let FFmpeg resolve it with the browser referer.
                playlist = output.with_suffix(".m3u8")
                playlist.write_bytes(body)
                result = subprocess.run(
                    [
                        "ffmpeg", "-y",
                        "-headers", "Referer: https://www.douyin.com/\r\n",
                        "-i", str(playlist),
                        "-c", "copy", str(output),
                    ],
                    capture_output=True, text=True, timeout=1800,
                )
                playlist.unlink(missing_ok=True)
                if result.returncode != 0:
                    raise DownloadError(f"FFmpeg không đọc được HLS: {result.stderr[-1500:]}")
            else:
                if len(body) < 100_000:
                    raise DownloadError("Media response quá nhỏ, có thể là trang lỗi/anti-bot.")
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(body)
        finally:
            await context.close()
            await browser.close()


def download(url: str, output: Path, log) -> Path:
    validate_douyin_url(url)
    log("1/5  Đang tải video...")

    if _run_ytdlp(url, output):
        log("✓ yt-dlp tải thành công.")
        return output

    log("yt-dlp không lấy được video; chuyển sang Playwright fallback...")
    try:
        asyncio.run(_playwright_download(url, output))
    except Exception as exc:
        raise DownloadError(
            "Không thể tải video Douyin. Hãy kiểm tra URL, quyền truy cập và đăng nhập "
            "Douyin trong trình duyệt nếu video yêu cầu tài khoản."
        ) from exc

    log("✓ Playwright fallback tải thành công.")
    return output
