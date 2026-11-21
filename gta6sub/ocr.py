"""Read English subtitle text from a cropped frame."""
from __future__ import annotations

import re

import numpy as np


def preprocess(img: np.ndarray) -> np.ndarray:
    """Game subtitles are bright (white) text with a dark outline/shadow.
    Keep only near-white pixels and render them as black text on white, which
    removes the busy game background that confuses OCR."""
    import cv2

    h = img.shape[0]
    if h < 120:
        scale = 120 / max(h, 1)
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # bright and low-saturation = white subtitle text
    mask = cv2.inRange(hsv, (0, 0, 190), (180, 70, 255))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    out = np.full_like(img, 255)
    out[mask > 0] = 0
    return pad(out, 255)


def pad(img: np.ndarray, value: int, px: int = 40) -> np.ndarray:
    """OCR misses text that touches the crop edge, so add a margin."""
    return np.pad(img, ((px, px), (px, px), (0, 0)), constant_values=value)


def join_lines(results: list, min_conf: float) -> str:
    """Sort OCR boxes top-to-bottom, left-to-right and join them into one string."""
    boxes = []
    for box, text, conf in results or []:
        if float(conf) < min_conf or not text.strip():
            continue
        ys = [p[1] for p in box]
        xs = [p[0] for p in box]
        boxes.append((sum(ys) / len(ys), min(xs), max(ys) - min(ys), text.strip()))
    if not boxes:
        return ""
    boxes.sort()
    lines: list[list[tuple]] = []
    for b in boxes:
        if lines and abs(b[0] - lines[-1][0][0]) < max(b[2], lines[-1][0][2]) * 0.6:
            lines[-1].append(b)
        else:
            lines.append([b])
    text = " ".join(" ".join(t for *_, t in sorted(line, key=lambda b: b[1])) for line in lines)
    return normalize(text)


def normalize(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    return text


class SubtitleOCR:
    def __init__(self, min_confidence: float = 0.6):
        from rapidocr_onnxruntime import RapidOCR

        self._engine = RapidOCR()
        self._min_conf = min_confidence

    def read(self, crop: np.ndarray) -> str:
        if crop is None or crop.size == 0:
            return ""
        result, _ = self._engine(preprocess(crop))
        text = join_lines(result, self._min_conf)
        if not text:  # e.g. coloured/yellow subtitles: try the raw crop
            result, _ = self._engine(pad(crop, 0))
            text = join_lines(result, self._min_conf)
        return text
