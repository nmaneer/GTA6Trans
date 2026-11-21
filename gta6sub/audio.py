"""Optional audio mode: transcribe PC audio output with faster-whisper.

Useful for dialogue that has no on-screen subtitle (radio, ambient chatter).
Requires: pip install faster-whisper soundcard
"""
from __future__ import annotations

import logging
from typing import Callable

import numpy as np

log = logging.getLogger(__name__)
SAMPLE_RATE = 16000


def run_audio_loop(cfg: dict, on_line: Callable[[str], None], stop) -> None:
    import soundcard as sc
    from faster_whisper import WhisperModel

    model = WhisperModel(cfg["whisper_model"], device=cfg["device"],
                         compute_type="float16" if cfg["device"] == "cuda" else "int8")
    speaker = sc.default_speaker()
    mic = sc.get_microphone(id=str(speaker.name), include_loopback=True)
    frames = int(SAMPLE_RATE * cfg["chunk_seconds"])
    log.info("Audio mode: listening to %s", speaker.name)

    with mic.recorder(samplerate=SAMPLE_RATE, channels=1) as rec:
        while not stop.is_set():
            chunk = rec.record(numframes=frames).reshape(-1).astype(np.float32)
            if np.sqrt(np.mean(chunk ** 2)) < 0.005:  # silence
                continue
            segments, _ = model.transcribe(chunk, language="en", vad_filter=True,
                                           beam_size=1)
            text = " ".join(s.text.strip() for s in segments).strip()
            if len(text) > 3:
                on_line(text)
