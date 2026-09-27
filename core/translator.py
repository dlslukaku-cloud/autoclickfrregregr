from __future__ import annotations

import json
import os

import httpx

from .models import Segment


class TranslationError(RuntimeError):
    pass


class SmartTranslator:
    def __init__(self):
        self.base_url = os.getenv("DUB_LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.api_key = os.getenv("DUB_LLM_API_KEY", "").strip()
        self.model = os.getenv("DUB_LLM_MODEL", "").strip()

        if not self.api_key or not self.model:
            raise TranslationError(
                "Thiếu DUB_LLM_API_KEY hoặc DUB_LLM_MODEL. "
                "Đây là lớp dịch AI có thể dùng bất kỳ OpenAI-compatible endpoint nào."
            )

    def translate(self, segments: list[Segment], log) -> list[Segment]:
        log("3/5  Dịch Trung → Việt theo ngữ cảnh...")
        # Keep chunks small enough for reliable JSON responses.
        chunks = [segments[i:i + 20] for i in range(0, len(segments), 20)]
        translated: list[Segment] = []

        for chunk in chunks:
            payload = {
                "model": self.model,
                "temperature": 0.2,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Bạn là biên tập viên lồng tiếng Trung-Việt. "
                            "Dịch tự nhiên, nói như người Việt, giữ nguyên tên riêng "
                            "và ý nghĩa. Không thêm giải thích. Trả JSON array, mỗi phần "
                            "tử có duy nhất trường translated_text."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            [{"text": s.source_text} for s in chunk],
                            ensure_ascii=False,
                        ),
                    },
                ],
            }

            try:
                with httpx.Client(timeout=120) as client:
                    response = client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json=payload,
                    )
                    response.raise_for_status()
                    content = response.json()["choices"][0]["message"]["content"]
                    data = json.loads(content)
                    texts = [str(x["translated_text"]).strip() for x in data]
            except (httpx.HTTPError, KeyError, IndexError, json.JSONDecodeError) as exc:
                raise TranslationError("LLM translation trả về dữ liệu không hợp lệ.") from exc

            if len(texts) != len(chunk):
                raise TranslationError("LLM không trả đủ số câu dịch.")

            translated.extend(
                Segment(s.start, s.end, s.source_text, t)
                for s, t in zip(chunk, texts)
            )

        return translated
