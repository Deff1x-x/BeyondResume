import sys
from types import SimpleNamespace

import pytest

from app.integrations import openai_hiring_intelligence as provider_module


def test_openai_provider_returns_json_content(monkeypatch: pytest.MonkeyPatch) -> None:
    parsed = SimpleNamespace(model_dump_json=lambda: '{"verdict":{}}')
    completion = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(parsed=parsed, refusal=None))])
    calls: list[dict[str, object]] = []
    client = SimpleNamespace(
        beta=SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(parse=lambda **kwargs: calls.append(kwargs) or completion)
            )
        )
    )
    monkeypatch.setattr(provider_module.settings, "openai_api_key", "test-key")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=lambda **_kwargs: client))

    assert provider_module.OpenAIHiringIntelligenceProvider().generate("prompt") == '{"verdict":{}}'
    assert calls[0]["response_format"] is provider_module.AiHiringIntelligenceResponse


@pytest.mark.parametrize("key", ["", None])
def test_openai_provider_rejects_missing_key(monkeypatch: pytest.MonkeyPatch, key: str | None) -> None:
    monkeypatch.setattr(provider_module.settings, "openai_api_key", key)
    with pytest.raises(provider_module.OpenAIHiringIntelligenceProviderError):
        provider_module.OpenAIHiringIntelligenceProvider()


def test_openai_provider_wraps_sdk_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    client = SimpleNamespace(
        beta=SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(parse=lambda **_kwargs: (_ for _ in ()).throw(TimeoutError()))
            )
        )
    )
    monkeypatch.setattr(provider_module.settings, "openai_api_key", "test-key")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=lambda **_kwargs: client))
    with pytest.raises(
        provider_module.OpenAIHiringIntelligenceProviderError,
        match=r"OpenAI request failed \(TimeoutError\)",
    ):
        provider_module.OpenAIHiringIntelligenceProvider().generate("prompt")
