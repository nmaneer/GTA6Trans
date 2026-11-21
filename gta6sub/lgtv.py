"""Show subtitles on an LG webOS TV as on-screen toast notifications.

Works like a phone "TV remote" app: the PC talks to the TV over Wi-Fi/LAN with
LG's SSAP WebSocket API. Toasts are drawn by the TV itself on top of every
input, including the HDMI input the PS5 is plugged into.

Limits (set by the TV, not this code): the toast position, font and size are
fixed and it stays on screen for a few seconds.
"""
from __future__ import annotations

import asyncio
import copy
import logging
import threading
from pathlib import Path

log = logging.getLogger(__name__)
KEY_FILE = Path("lgtv_key.txt")


def load_key(path: Path = KEY_FILE) -> str | None:
    return path.read_text().strip() if path.exists() else None


class SSAPClient:
    """Minimal LG SSAP client: pair, then send toasts. Nothing else.

    Uses the same registration manifest as Home Assistant's LG integration
    (aiowebostv), so the TV asks for the same "allow connection" permission.
    """

    def __init__(self, host: str, key: str | None, timeout: float = 60):
        self.host, self.key, self.timeout = host, key, timeout
        self._session = None
        self._ws = None
        self._next_id = 0

    def is_connected(self) -> bool:
        return self._ws is not None and not self._ws.closed

    async def _open(self):
        import aiohttp

        self._session = self._session or aiohttp.ClientSession()
        # Newer firmware wants wss://:3001 (self-signed cert), older only ws://:3000.
        for uri in (f"wss://{self.host}:3001/", f"ws://{self.host}:3000/"):
            try:
                return await self._session.ws_connect(uri, ssl=False, timeout=aiohttp.ClientWSTimeout(ws_close=5),
                                                      heartbeat=20)
            except (aiohttp.ClientError, OSError, asyncio.TimeoutError) as e:
                log.debug("connect %s failed: %s", uri, e)
        raise ConnectionError(f"ต่อทีวี {self.host} ไม่ได้ (เปิดทีวีและอยู่ Wi-Fi เดียวกันหรือยัง?)")

    def _registration(self, signed: bool) -> dict:
        from aiowebostv.handshake import REGISTRATION_MESSAGE

        msg = copy.deepcopy(REGISTRATION_MESSAGE)
        if not signed:  # newer firmware rejects the signed manifest
            manifest = msg["payload"]["manifest"]
            manifest.pop("signatures")
            manifest["permissions"] = sorted(
                {*manifest["permissions"], *manifest.pop("signed")["permissions"]})
        msg["payload"]["client-key"] = self.key
        msg["id"] = "register"
        return msg

    async def connect(self) -> None:
        self._ws = await self._open()
        for signed in (True, False):
            await self._ws.send_json(self._registration(signed))
            async with asyncio.timeout(self.timeout):  # user may need to press Accept
                while True:
                    msg = await self._ws.receive_json()
                    if msg.get("type") == "registered":
                        new_key = msg.get("payload", {}).get("client-key")
                        if new_key and new_key != self.key:
                            self.key = new_key
                            KEY_FILE.write_text(new_key)
                            log.info("Paired with TV; key saved to %s", KEY_FILE)
                        return
                    if msg.get("type") == "error":
                        break  # try the unsigned manifest
                    # {"type":"response","payload":{"pairingType":"PROMPT"}} -> keep waiting
        raise PermissionError("ทีวีไม่อนุญาตการเชื่อมต่อ (กด Accept บนทีวีหรือยัง?)")

    async def toast(self, message: str) -> None:
        self._next_id += 1
        await self._ws.send_json({
            "id": f"toast_{self._next_id}",
            "type": "request",
            "uri": "ssap://system.notifications/createToast",
            "payload": {"message": message},
        })

    async def close(self) -> None:
        if self._ws is not None:
            await self._ws.close()
        if self._session is not None:
            await self._session.close()


async def _connect(host: str, key: str | None) -> SSAPClient:
    client = SSAPClient(host, key)
    await client.connect()
    return client


class LGToastSender:
    """Thread-safe: call send() from any thread."""

    def __init__(self, host: str, max_chars: int = 120):
        self.host = host
        self.max_chars = max_chars
        self._loop = asyncio.new_event_loop()
        self._client = None
        threading.Thread(target=self._loop.run_forever, daemon=True).start()
        asyncio.run_coroutine_threadsafe(self._ensure(), self._loop).result(timeout=60)

    async def _ensure(self):
        if self._client is None or not self._client.is_connected():
            self._client = await _connect(self.host, load_key())
        return self._client

    async def _send(self, text: str) -> None:
        try:  # toasts are queued in order by this single event loop
            client = await self._ensure()
            await client.toast(text)
        except Exception as e:  # TV off, Wi-Fi drop... keep the game going
            log.warning("LG TV toast failed: %s", e)
            self._client = None

    def send(self, text: str) -> None:
        if len(text) > self.max_chars:
            text = text[: self.max_chars - 1] + "…"
        asyncio.run_coroutine_threadsafe(self._send(text), self._loop)


def pair(host: str) -> None:
    """One-time pairing: the TV shows an 'allow connection' prompt."""

    async def run():
        print(f"กำลังเชื่อมต่อทีวี {host} ... กด 'ยอมรับ/Accept' ที่หน้าจอทีวีด้วยรีโมท")
        client = await _connect(host, load_key())
        await client.toast("GTA6Trans เชื่อมต่อแล้ว ✓ ซับไทยจะขึ้นตรงนี้")
        print("สำเร็จ! คีย์บันทึกไว้ใน", KEY_FILE)
        await asyncio.sleep(0.5)
        await client.close()

    asyncio.run(run())
