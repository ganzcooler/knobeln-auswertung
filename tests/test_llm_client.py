from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from conftest import FAKE_RESPONSES

from knobeln.llm.cache import LLMCache
from knobeln.llm.client import DEFAULT_MAX_TOKENS, LLMError, OpenRouterClient


class FakeCompletions:
    def __init__(self, responses: list[str | tuple[str, str]]) -> None:
        self.responses = responses
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        item = self.responses.pop(0)
        if isinstance(item, tuple):
            content, finish_reason = item
        else:
            content, finish_reason = item, "stop"
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=content),
                    finish_reason=finish_reason,
                )
            ],
            usage=SimpleNamespace(
                prompt_tokens=100,
                completion_tokens=50,
                completion_tokens_details=SimpleNamespace(reasoning_tokens=40),
            ),
        )


class FakeOpenAI:
    def __init__(
        self,
        responses: list[str | tuple[str, str]],
        **kwargs,
    ) -> None:
        self.kwargs = kwargs
        self.completions = FakeCompletions(responses)
        self.chat = SimpleNamespace(completions=self.completions)


def _client(
    monkeypatch,
    tmp_path: Path,
    responses: list[str | tuple[str, str]],
    *,
    no_cache: bool = False,
) -> tuple[OpenRouterClient, FakeOpenAI]:
    created: list[FakeOpenAI] = []

    def factory(**kwargs):
        instance = FakeOpenAI(responses, **kwargs)
        created.append(instance)
        return instance

    monkeypatch.setattr("knobeln.llm.client.OpenAI", factory)
    client = OpenRouterClient(
        api_key="dummy",
        model="deepseek/deepseek-v4.1-flash",
        reasoning="max",
        cache=LLMCache(tmp_path / "cache"),
        no_cache=no_cache,
    )
    return client, created[0]


def test_request_und_cache(monkeypatch, tmp_path: Path):
    payload = json.dumps(FAKE_RESPONSES["img1.jpg"])
    client, api = _client(monkeypatch, tmp_path, [payload])

    result = client.extract_bogen(
        bogen_id="b-p1",
        quelle="img1.jpg",
        image_bytes=b"fake-image",
        mime_type="image/jpeg",
    )
    assert result.bogen.spieler[0].spieler_nr == "41"
    assert result.prompt_tokens == 100
    assert result.completion_tokens == 50
    assert result.reasoning_tokens == 40
    assert result.cost_usd > 0

    call = api.completions.calls[0]
    assert call["model"] == "deepseek/deepseek-v4.1-flash"
    assert call["temperature"] == 0
    assert call["response_format"]["type"] == "json_schema"
    assert call["extra_body"]["reasoning"]["effort"] == "max"
    assert call["extra_body"]["reasoning"]["exclude"] is True
    assert "data:image/jpeg;base64," in call["messages"][1]["content"][1]["image_url"]["url"]

    # Cache-Hit: neuer Client, gleicher Cache, kein zweiter API-Aufruf.
    client2, api2 = _client(monkeypatch, tmp_path, [])
    result2 = client2.extract_bogen(
        bogen_id="b-p1",
        quelle="img1.jpg",
        image_bytes=b"fake-image",
        mime_type="image/jpeg",
    )
    assert result2.cached is True
    assert api2.completions.calls == []


def test_length_retry(monkeypatch, tmp_path: Path):
    valid = json.dumps(FAKE_RESPONSES["img1.jpg"])
    client, api = _client(monkeypatch, tmp_path, [("", "length"), valid])

    result = client.extract_bogen(
        bogen_id="b-p1",
        quelle="img1.jpg",
        image_bytes=b"fake-image",
        mime_type="image/jpeg",
    )
    assert result.bogen.spieler[0].spieler_nr == "41"
    assert len(api.completions.calls) == 2
    assert api.completions.calls[0]["max_tokens"] == DEFAULT_MAX_TOKENS
    assert api.completions.calls[1]["max_tokens"] == DEFAULT_MAX_TOKENS * 2
    assert result.prompt_tokens == 200
    assert result.completion_tokens == 100


def test_length_retry_bei_abgeschnittenem_json(monkeypatch, tmp_path: Path):
    valid = json.dumps(FAKE_RESPONSES["img1.jpg"])
    client, api = _client(
        monkeypatch,
        tmp_path,
        [('{"bogen_unklar": false', "length"), valid],
    )

    result = client.extract_bogen(
        bogen_id="b-p1",
        quelle="img1.jpg",
        image_bytes=b"fake-image",
        mime_type="image/jpeg",
    )
    assert result.bogen.spieler[0].spieler_nr == "41"
    assert len(api.completions.calls) == 2
    assert api.completions.calls[1]["max_tokens"] == DEFAULT_MAX_TOKENS * 2


def test_reparatur_retry(monkeypatch, tmp_path: Path):
    valid = json.dumps(FAKE_RESPONSES["img1.jpg"])
    client, api = _client(monkeypatch, tmp_path, ["kein json", valid])

    result = client.extract_bogen(
        bogen_id="b-p1",
        quelle="img1.jpg",
        image_bytes=b"fake-image",
        mime_type="image/jpeg",
    )
    assert result.bogen.spieler[0].spieler_nr == "41"
    assert len(api.completions.calls) == 2
    repair_messages = api.completions.calls[1]["messages"]
    assert repair_messages[-2]["role"] == "assistant"
    assert "kein json" in repair_messages[-2]["content"]
    assert repair_messages[-1]["role"] == "user"


def test_ungueltiges_json_nach_reparatur(monkeypatch, tmp_path: Path):
    client, _ = _client(monkeypatch, tmp_path, ["kein json", "immer noch kein json"])
    with pytest.raises(LLMError):
        client.extract_bogen(
            bogen_id="b-p1",
            quelle="img1.jpg",
            image_bytes=b"fake-image",
            mime_type="image/jpeg",
        )


def test_no_cache(monkeypatch, tmp_path: Path):
    payload = json.dumps(FAKE_RESPONSES["img1.jpg"])
    client, api = _client(monkeypatch, tmp_path, [payload, payload], no_cache=True)
    for _ in range(2):
        client.extract_bogen(
            bogen_id="b-p1",
            quelle="img1.jpg",
            image_bytes=b"fake-image",
            mime_type="image/jpeg",
        )
    assert len(api.completions.calls) == 2
