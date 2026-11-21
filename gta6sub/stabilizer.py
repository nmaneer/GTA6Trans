"""Decide when an on-screen subtitle is a *new, complete* line worth translating.

OCR on a live video is noisy: text fades in, the same line is read slightly
differently across frames, and a line stays on screen for several seconds.
"""
from __future__ import annotations

from difflib import SequenceMatcher


def similar(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


class SubtitleStabilizer:
    def __init__(self, stable_frames: int = 2, same_threshold: float = 0.85, min_chars: int = 3):
        self.stable_frames = max(1, stable_frames)
        self.same_threshold = same_threshold
        self.min_chars = min_chars
        self._candidate = ""
        self._count = 0
        self._last_emitted = ""

    def feed(self, text: str) -> str | None:
        """Feed one OCR reading. Returns a line to translate, or None."""
        text = text.strip()
        if len(text) < self.min_chars:
            self._candidate, self._count = "", 0
            if not text:
                self._last_emitted = ""  # subtitle cleared; same line may legitimately repeat later
            return None

        if similar(text, self._candidate) >= self.same_threshold:
            self._count += 1
            # Prefer the longer reading (text that finished fading in).
            if len(text) > len(self._candidate):
                self._candidate = text
        else:
            self._candidate, self._count = text, 1

        if self._count < self.stable_frames:
            return None
        if similar(self._candidate, self._last_emitted) >= self.same_threshold:
            return None
        self._last_emitted = self._candidate
        return self._candidate
