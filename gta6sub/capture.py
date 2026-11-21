"""Frame sources: a screen region (Remote Play / OBS preview window) or a
video device (capture card / OBS Virtual Camera)."""
from __future__ import annotations

import numpy as np


def crop_region(frame: np.ndarray, region: dict) -> np.ndarray:
    h, w = frame.shape[:2]
    x0 = int(max(0.0, region["left"]) * w)
    y0 = int(max(0.0, region["top"]) * h)
    x1 = int(min(1.0, region["left"] + region["width"]) * w)
    y1 = int(min(1.0, region["top"] + region["height"]) * h)
    return frame[y0:y1, x0:x1]


class ScreenSource:
    def __init__(self, monitor: int = 1):
        import mss

        self._sct = mss.mss()
        self._monitor = self._sct.monitors[monitor]

    def read(self) -> np.ndarray | None:
        shot = self._sct.grab(self._monitor)
        return np.asarray(shot)[:, :, :3]  # BGRA -> BGR

    def close(self) -> None:
        self._sct.close()


class DeviceSource:
    def __init__(self, index: int = 0):
        import cv2

        self._cap = cv2.VideoCapture(index)
        if not self._cap.isOpened():
            raise RuntimeError(
                f"เปิดอุปกรณ์วิดีโอ index={index} ไม่ได้ — ลองเปลี่ยน device_index ใน config.yaml"
            )
        # Ask for 1080p; capture cards usually honour it.
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    def read(self) -> np.ndarray | None:
        ok, frame = self._cap.read()
        return frame if ok else None

    def close(self) -> None:
        self._cap.release()


def open_source(cfg: dict):
    if cfg["source"] == "device":
        return DeviceSource(cfg["device_index"])
    return ScreenSource(cfg["monitor"])
