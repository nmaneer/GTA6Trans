from __future__ import annotations

import copy
from pathlib import Path

import yaml

DEFAULTS: dict = {
    "source": "screen",
    "device_index": 0,
    "monitor": 1,
    "subtitle_region": {"left": 0.15, "top": 0.80, "width": 0.70, "height": 0.15},
    "fps": 4,
    "min_confidence": 0.6,
    "stable_frames": 2,
    "translator": {
        "model": "claude-opus-5-5",
        "effort": "low",
        "context_lines": 6,
        "timeout_seconds": 15,
    },
    "overlay": {
        "font_family": "Tahoma",
        "font_size": 30,
        "text_color": "#FFFFFF",
        "outline_color": "#000000",
        "show_english": False,
        "position": "bottom",
        "margin_px": 80,
        "hide_after_seconds": 6,
    },
    "audio": {
        "enabled": False,
        "whisper_model": "small.en",
        "device": "cpu",
        "chunk_seconds": 4,
    },
}


def _merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config(path: str | Path = "config.yaml") -> dict:
    p = Path(path)
    if not p.exists():
        return copy.deepcopy(DEFAULTS)
    with p.open(encoding="utf-8") as f:
        return _merge(DEFAULTS, yaml.safe_load(f) or {})


def save_region(path: str | Path, region: dict) -> None:
    p = Path(path)
    data = {}
    if p.exists():
        with p.open(encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    data["subtitle_region"] = {k: round(float(v), 4) for k, v in region.items()}
    with p.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
