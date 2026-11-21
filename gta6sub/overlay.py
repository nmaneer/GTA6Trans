"""Transparent, always-on-top, click-through subtitle window (tkinter)."""
from __future__ import annotations

import queue
import sys
import time
import tkinter as tk

TRANSPARENT = "#010101"  # colour keyed out as transparent on Windows


class SubtitleOverlay:
    def __init__(self, cfg: dict, messages: "queue.Queue[tuple[str, str]]"):
        self.cfg = cfg
        self.messages = messages
        self.root = tk.Tk()
        self.root.title("GTA6 Thai Subtitles")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.width, self.height = sw, cfg["font_size"] * 6
        y = cfg["margin_px"] if cfg["position"] == "top" else sh - self.height - cfg["margin_px"]
        self.root.geometry(f"{self.width}x{self.height}+0+{y}")

        if sys.platform == "win32":
            self.root.configure(bg=TRANSPARENT)
            self.root.attributes("-transparentcolor", TRANSPARENT)
        elif sys.platform == "darwin":
            self.root.configure(bg="systemTransparent")
            self.root.attributes("-transparent", True)
        else:
            self.root.configure(bg=TRANSPARENT)
            self.root.attributes("-alpha", 0.85)

        bg = self.root.cget("bg")
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height,
                                bg=bg, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self._last_update = 0.0
        self.root.bind("<Escape>", lambda _e: self.root.destroy())
        self.root.after(50, self._make_click_through)
        self.root.after(50, self._poll)

    def _make_click_through(self) -> None:
        if sys.platform != "win32":
            return
        try:
            import ctypes

            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            GWL_EXSTYLE, WS_EX_LAYERED, WS_EX_TRANSPARENT = -20, 0x80000, 0x20
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(
                hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
        except Exception:
            pass

    def _draw_outlined(self, x: int, y: int, text: str, size: int) -> None:
        font = (self.cfg["font_family"], size, "bold")
        o = max(1, size // 12)
        for dx in (-o, 0, o):
            for dy in (-o, 0, o):
                if dx or dy:
                    self.canvas.create_text(x + dx, y + dy, text=text, font=font,
                                            fill=self.cfg["outline_color"],
                                            width=self.width * 0.8, justify="center")
        self.canvas.create_text(x, y, text=text, font=font, fill=self.cfg["text_color"],
                                width=self.width * 0.8, justify="center")

    def show(self, english: str, thai: str) -> None:
        self.canvas.delete("all")
        cx, size = self.width // 2, self.cfg["font_size"]
        if self.cfg["show_english"] and english:
            self._draw_outlined(cx, int(size * 1.2), english, max(10, size // 2))
            self._draw_outlined(cx, int(size * 3.4), thai, size)
        else:
            self._draw_outlined(cx, self.height // 2, thai, size)
        self._last_update = time.monotonic()

    def _poll(self) -> None:
        try:
            while True:
                english, thai = self.messages.get_nowait()
                self.show(english, thai)
        except queue.Empty:
            pass
        hide = self.cfg["hide_after_seconds"]
        if hide and self._last_update and time.monotonic() - self._last_update > hide:
            self.canvas.delete("all")
            self._last_update = 0.0
        self.root.after(50, self._poll)

    def run(self) -> None:
        self.root.mainloop()
