"""English -> Thai subtitle translation with Claude."""
from __future__ import annotations

import logging
from collections import OrderedDict, deque

import anthropic

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You translate live English video-game subtitles into natural, spoken Thai for a \
Thai player watching in real time. The game is a modern open-world crime drama set \
in a fictional Florida-style state, full of street slang, jokes and swearing.

Rules:
- Reply with the Thai subtitle only: no quotes, notes, romanisation or English.
- Keep it short and easy to read in about two seconds; match the speaker's tone \
(casual, rude, funny, tense). Swearing may stay rude in Thai.
- If the line starts with a speaker name such as "LUCIA:" keep the name as-is in \
Latin letters, followed by ": " and the Thai line.
- Keep names of people, places, brands, cars and weapons in English.
- The text comes from OCR and may contain small errors; translate what was \
obviously meant. If it is not dialogue at all (random letters, HUD noise), reply \
with exactly: -
"""


class Translator:
    def __init__(self, model: str, effort: str = "low", context_lines: int = 6,
                 timeout_seconds: float = 15):
        self._client = anthropic.Anthropic(timeout=timeout_seconds, max_retries=1)
        self._model = model
        self._effort = effort
        self._history: deque[tuple[str, str]] = deque(maxlen=max(0, context_lines))
        self._cache: OrderedDict[str, str] = OrderedDict()

    def _build_user_message(self, line: str) -> str:
        if not self._history:
            return f"Subtitle:\n{line}"
        ctx = "\n".join(f"EN: {en}\nTH: {th}" for en, th in self._history)
        return (
            "Previous lines, for context only (do not translate them again):\n"
            f"{ctx}\n\nTranslate this new subtitle:\n{line}"
        )

    def translate(self, line: str) -> str | None:
        key = line.lower()
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]

        try:
            response = self._client.beta.messages.create(
                model=self._model,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                output_config={"effort": self._effort},
                messages=[{"role": "user", "content": self._build_user_message(line)}],
                # Crime-game dialogue can occasionally trip a safety classifier;
                # let the API retry on Anthropic's recommended fallback model.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except anthropic.RateLimitError:
            log.warning("Rate limited; skipping line: %s", line)
            return None
        except anthropic.APIStatusError as e:
            log.error("API error %s: %s", e.status_code, e.message)
            return None
        except anthropic.APIConnectionError as e:
            log.error("Connection error: %s", e)
            return None

        if response.stop_reason == "refusal":
            log.info("Translation declined for: %s", line)
            return None

        thai = "".join(b.text for b in response.content if b.type == "text").strip()
        if not thai or thai == "-":
            return None

        self._history.append((line, thai))
        self._cache[key] = thai
        if len(self._cache) > 500:
            self._cache.popitem(last=False)
        return thai
