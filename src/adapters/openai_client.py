from __future__ import annotations
from typing import Dict, Any, Optional
import os, json, time, random, asyncio

from openai import OpenAI
from openai import APIError, APIConnectionError, APIStatusError, RateLimitError

from ..common.config import settings

SYSTEM_PROMPT = """Jesteś klasyfikatorem intencji dla siłowni/fitness klubu.
Zwracaj JSON o kluczach: intent (reserve_class|faq|handover|clarify), confidence (0..1), slots (dict).
faq slots: {"topic": one of [hours, price, location, contact]}
reserve_class slots: {"class_id": optional, "member_id": optional}
"""

_VALID_INTENTS = {"reserve_class", "faq", "handover", "clarify"}


class OpenAIClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "openai_api_key", None)
        self.enabled = bool(self.api_key)
        self.model = model or getattr(settings, "llm_model", "gpt-4o-mini")
        self.client = OpenAI(api_key=self.api_key) if self.enabled else None

    # ---------- niskopoziomowe wywołanie (sync) ----------
    def _chat_once(self, messages: list[dict], model: Optional[str] = None, max_tokens: int = 256) -> str:
        if not self.enabled or not self.client:
            # tryb „bez AI” — bezpieczny fallback
            user_msg = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
            return json.dumps({"intent": "clarify", "confidence": 0.49, "slots": {"echo": user_msg[:80]}})

        mdl = model or self.model
        resp = self.client.chat.completions.create(
            model=mdl,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or "{}"

    def chat(self, messages: list[dict], model: Optional[str] = None, max_tokens: int = 256) -> str:
        # retry z backoffem + jitterem
        for attempt in range(5):
            try:
                return self._chat_once(messages, model=model, max_tokens=max_tokens)
            except RateLimitError:
                time.sleep(min(2 ** attempt, 8) + random.uniform(0, 0.3))
            except APIStatusError as e:
                # 429/5xx -> retry, inne statusy -> raise
                if getattr(e, "status_code", 0) in (429, 500, 502, 503):
                    time.sleep(min(2 ** attempt, 8) + random.uniform(0, 0.3))
                else:
                    raise
            except (APIConnectionError, APIError):
                time.sleep(1.0 + random.uniform(0, 0.3))

        # ostateczny fallback (json, żeby parser po drugiej stronie nie padł)
        return json.dumps({
            "intent": "clarify",
            "confidence": 0.3,
            "slots": {"note": "LLM unavailable (retries exhausted)"}
        })

    # ---------- wariant async (na potrzeby async workerów) ----------
    async def chat_async(self, messages: list[dict], model: Optional[str] = None, max_tokens: int = 256) -> str:
        # wykonaj sync wywołanie w wątku, żeby nie blokować event loopa
        return await asyncio.to_thread(self.chat, messages, model, max_tokens)

    # ---------- wysoki poziom: klasyfikacja ----------
    def classify(self, text: str, lang: str = "pl") -> Dict[str, Any]:
        """
        Synchronous convenience wrapper.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"LANG={lang}\nTEXT={text}"},
        ]
        content = self.chat(messages, model=self.model, max_tokens=256)
        return self._parse_classification(content)

    async def classify_async(self, text: str, lang: str = "pl") -> Dict[str, Any]:
        """
        Async counterpart.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"LANG={lang}\nTEXT={text}"},
        ]
        content = await self.chat_async(messages, model=self.model, max_tokens=256)
        return self._parse_classification(content)

    # ---------- pomocnicze: normalizacja JSON ----------
    def _parse_classification(self, content: str) -> Dict[str, Any]:
        try:
            data = json.loads(content or "{}")
        except Exception:
            return {"intent": "clarify", "confidence": 0.3, "slots": {}}

        intent = str(data.get("intent", "clarify")).strip()
        if intent not in _VALID_INTENTS:
            intent = "clarify"

        # confidence -> float 0..1
        try:
            conf = float(data.get("confidence", 0.5))
        except Exception:
            conf = 0.5
        conf = max(0.0, min(1.0, conf))

        slots = data.get("slots") or {}
        if not isinstance(slots, dict):
            slots = {}

        return {"intent": intent, "confidence": conf, "slots": slots}
