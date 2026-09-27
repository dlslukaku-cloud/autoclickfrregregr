from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    source_text: str
    translated_text: str = ""

    @property
    def duration(self) -> float:
        return max(0.05, self.end - self.start)
