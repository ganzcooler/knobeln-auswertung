"""OpenRouter-Client und gemeinsame LLM-Schnittstelle."""

from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass
from typing import Any, Protocol

from openai import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)
from pydantic import ValidationError

from .cache import LLMCache
from .models import BogenLLM
from .prompt import PROMPT_VERSION, SYSTEM_PROMPT, USER_PROMPT
from .schema import response_format

# Preise von OpenRouter (DeepSeek V4.1 Flash, Stand der Modellliste).
PROMPT_PRICE_PER_TOKEN = 0.000000051
COMPLETION_PRICE_PER_TOKEN = 0.00000041
DEFAULT_MAX_TOKENS = 262144
MAX_TOKENS_LIMIT = 524288

RETRYABLE = (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError)


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    cost_usd: float = 0.0

    def add(self, other: "Usage") -> None:
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.reasoning_tokens += other.reasoning_tokens
        self.cost_usd += other.cost_usd


class LLMError(RuntimeError):
    pass


class LLMJSONError(LLMError):
    def __init__(
        self,
        message: str,
        *,
        raw_content: str = "",
        usage: Usage | None = None,
    ) -> None:
        super().__init__(message)
        self.raw_content = raw_content
        self.usage = usage or Usage()


class LLMLengthError(LLMError):
    def __init__(self, message: str, *, usage: Usage | None = None) -> None:
        super().__init__(message)
        self.usage = usage or Usage()


@dataclass
class LLMResult:
    bogen: BogenLLM
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    cost_usd: float = 0.0
    cached: bool = False


class LLMClient(Protocol):
    def extract_bogen(
        self,
        *,
        bogen_id: str,
        quelle: str,
        image_bytes: bytes,
        mime_type: str,
    ) -> LLMResult: ...


class OpenRouterClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        reasoning: str = "max",
        cache: LLMCache | None = None,
        no_cache: bool = False,
        timeout: float = 180.0,
    ) -> None:
        self.model = model
        self.reasoning = reasoning
        self.cache = cache
        self.no_cache = no_cache
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            timeout=timeout,
            max_retries=0,
        )

    def extract_bogen(
        self,
        *,
        bogen_id: str,
        quelle: str,
        image_bytes: bytes,
        mime_type: str,
    ) -> LLMResult:
        cache_key = None
        if self.cache is not None:
            cache_key = self.cache.make_key(
                bogen_id=bogen_id,
                model=self.model,
                prompt_version=PROMPT_VERSION,
                reasoning=self.reasoning,
            )
            if not self.no_cache:
                cached = self.cache.get(cache_key)
                if cached is not None:
                    try:
                        return LLMResult(
                            bogen=BogenLLM.model_validate(cached["bogen"]),
                            prompt_tokens=int(cached.get("prompt_tokens", 0)),
                            completion_tokens=int(cached.get("completion_tokens", 0)),
                            reasoning_tokens=int(cached.get("reasoning_tokens", 0)),
                            cost_usd=float(cached.get("cost_usd", 0.0)),
                            cached=True,
                        )
                    except (KeyError, ValueError, ValidationError):
                        pass

        data_url = (
            f"data:{mime_type};base64,"
            + base64.b64encode(image_bytes).decode("ascii")
        )
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": USER_PROMPT},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ]

        carry = Usage()
        try:
            result = self._request_with_length_retry(messages, carry=carry)
        except LLMJSONError as exc:
            carry.add(exc.usage)
            repair_messages = list(messages) + [
                {"role": "assistant", "content": exc.raw_content},
                {
                    "role": "user",
                    "content": (
                        "Deine vorherige Antwort war kein gültiges JSON nach dem "
                        f"Schema. Fehler: {exc}. Antworte erneut ausschließlich "
                        "mit JSON, ohne Markdown und ohne Erklärtext."
                    ),
                },
            ]
            try:
                result = self._request_with_length_retry(
                    repair_messages,
                    carry=carry,
                )
            except LLMJSONError as exc2:
                carry.add(exc2.usage)
                raise LLMError(
                    "LLM lieferte auch nach dem Reparaturversuch ungültiges JSON: "
                    f"{exc2} (Kosten bisher ca. ${carry.cost_usd:.4f})"
                ) from exc2

        if cache_key is not None and self.cache is not None:
            self.cache.set(
                cache_key,
                {
                    "bogen": result.bogen.model_dump(mode="json"),
                    "prompt_tokens": result.prompt_tokens,
                    "completion_tokens": result.completion_tokens,
                    "reasoning_tokens": result.reasoning_tokens,
                    "cost_usd": result.cost_usd,
                    "model": self.model,
                    "quelle": quelle,
                },
            )
        return result

    def _request_with_length_retry(
        self,
        messages: list[dict[str, Any]],
        *,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        carry: Usage | None = None,
    ) -> LLMResult:
        total = carry if carry is not None else Usage()
        current = max_tokens
        while True:
            try:
                result = self._request_with_retries(
                    messages,
                    max_tokens=current,
                )
                _add_usage(result, total)
                return result
            except LLMLengthError as exc:
                total.add(exc.usage)
                if current >= MAX_TOKENS_LIMIT:
                    raise LLMError(
                        "LLM-Antwort nach "
                        f"{current} Tokens abgeschnitten "
                        f"(Kosten bisher ca. ${total.cost_usd:.4f})."
                    ) from exc
                current = min(current * 2, MAX_TOKENS_LIMIT)

    def _request_with_retries(
        self,
        messages: list[dict[str, Any]],
        *,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> LLMResult:
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0,
                    max_tokens=max_tokens,
                    response_format=response_format(),
                    extra_body={
                        "reasoning": {
                            "effort": self.reasoning,
                            "exclude": True,
                        }
                    },
                )
                return self._parse_response(response)
            except RETRYABLE as exc:
                if attempt < 2:
                    time.sleep(2**attempt)
                    continue
                raise LLMError(f"OpenRouter nicht erreichbar: {exc}") from exc
            except LLMError:
                raise
            except Exception as exc:
                raise LLMError(f"LLM-Aufruf fehlgeschlagen: {exc}") from exc
        raise LLMError("LLM-Aufruf fehlgeschlagen.")

    def _parse_response(self, response: Any) -> LLMResult:
        choice = response.choices[0]
        content = choice.message.content
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )
        content = (content or "").strip()

        usage = getattr(response, "usage", None)
        prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        details = getattr(usage, "completion_tokens_details", None)
        reasoning_tokens = int(getattr(details, "reasoning_tokens", 0) or 0)
        usage_info = Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            reasoning_tokens=reasoning_tokens,
            cost_usd=(
                prompt_tokens * PROMPT_PRICE_PER_TOKEN
                + completion_tokens * COMPLETION_PRICE_PER_TOKEN
            ),
        )

        finish_reason = getattr(choice, "finish_reason", "")
        if not content:
            if finish_reason == "length":
                raise LLMLengthError(
                    "Leere LLM-Antwort: das Token-Limit wurde vor dem JSON "
                    "erreicht (finish_reason=length).",
                    usage=usage_info,
                )
            raise LLMError(f"Leere LLM-Antwort (finish_reason={finish_reason}).")

        try:
            data = json.loads(content)
            bogen = BogenLLM.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            if finish_reason == "length":
                raise LLMLengthError(
                    "Abgeschnittene LLM-Antwort: das Token-Limit wurde vor "
                    "einem gültigen JSON erreicht (finish_reason=length).",
                    usage=usage_info,
                ) from exc
            raise LLMJSONError(
                f"Ungültige LLM-JSON-Antwort: {exc}",
                raw_content=content,
                usage=usage_info,
            ) from exc

        return LLMResult(
            bogen=bogen,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            reasoning_tokens=reasoning_tokens,
            cost_usd=usage_info.cost_usd,
        )


def _add_usage(result: LLMResult, usage: Usage) -> None:
    result.prompt_tokens += usage.prompt_tokens
    result.completion_tokens += usage.completion_tokens
    result.reasoning_tokens += usage.reasoning_tokens
    result.cost_usd += usage.cost_usd
