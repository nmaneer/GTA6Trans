"""Pipeline: capture -> OCR -> stabilise -> translate (Claude) -> overlay."""
from __future__ import annotations

import argparse
import logging
import queue
import threading
import time

from .capture import crop_region, open_source
from .config import load_config
from .stabilizer import SubtitleStabilizer

log = logging.getLogger("gta6sub")


def ocr_loop(cfg: dict, lines: "queue.Queue[str]", stop: threading.Event) -> None:
    from .ocr import SubtitleOCR

    source = open_source(cfg)
    ocr = SubtitleOCR(cfg["min_confidence"])
    stab = SubtitleStabilizer(cfg["stable_frames"])
    interval = 1.0 / max(0.5, float(cfg["fps"]))
    log.info("OCR started (source=%s, %.1f fps)", cfg["source"], cfg["fps"])
    try:
        while not stop.is_set():
            t0 = time.monotonic()
            frame = source.read()
            if frame is not None:
                line = stab.feed(ocr.read(crop_region(frame, cfg["subtitle_region"])))
                if line:
                    log.info("EN: %s", line)
                    lines.put(line)
            time.sleep(max(0.0, interval - (time.monotonic() - t0)))
    finally:
        source.close()


def translate_loop(cfg: dict, lines: "queue.Queue[str]", out: "queue.Queue[tuple[str, str]]",
                   stop: threading.Event) -> None:
    from .translator import Translator

    t = cfg["translator"]
    translator = Translator(t["model"], t["effort"], t["context_lines"], t["timeout_seconds"])
    while not stop.is_set():
        try:
            line = lines.get(timeout=0.2)
        except queue.Empty:
            continue
        # Stay real-time: if several lines queued up, jump to the newest.
        while not lines.empty():
            line = lines.get_nowait()
        t0 = time.monotonic()
        thai = translator.translate(line)
        if thai:
            log.info("TH: %s  (%.1fs)", thai, time.monotonic() - t0)
            out.put((line, thai))


def main() -> None:
    ap = argparse.ArgumentParser(description="Realtime Thai subtitles for GTA 6 on PS5")
    ap.add_argument("-c", "--config", default="config.yaml")
    ap.add_argument("--no-overlay", action="store_true", help="print subtitles to console only")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

    cfg = load_config(args.config)
    stop = threading.Event()
    lines: queue.Queue[str] = queue.Queue()
    out: queue.Queue[tuple[str, str]] = queue.Queue()

    threads = [
        threading.Thread(target=ocr_loop, args=(cfg, lines, stop), daemon=True),
        threading.Thread(target=translate_loop, args=(cfg, lines, out, stop), daemon=True),
    ]
    if cfg["audio"]["enabled"]:
        from .audio import run_audio_loop

        threads.append(threading.Thread(target=run_audio_loop,
                                        args=(cfg["audio"], lines.put, stop), daemon=True))
    for th in threads:
        th.start()

    try:
        if args.no_overlay:
            while True:
                en, th = out.get()
                print(f"\n  {en}\n  >> {th}")
        else:
            from .overlay import SubtitleOverlay

            SubtitleOverlay(cfg["overlay"], out).run()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()


if __name__ == "__main__":
    main()
