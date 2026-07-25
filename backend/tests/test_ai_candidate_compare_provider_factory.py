import builtins
import sys
from types import SimpleNamespace

import pytest

from app.integrations import ai_candidate_compare as factory_module


_OPENAI_PROVIDER_MODULE = "app.integrations.openai_ai_candidate_compare"


def test_factory_returns_mock_without_api_key_or_openai_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_import = builtins.__import__

    def guarded_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "openai" or name.startswith("openai.") or name == _OPENAI_PROVIDER_MODULE:
            raise AssertionError(f"{name} must not be imported in mock mode")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(factory_module.settings, "llm_provider", "mock")
    monkeypatch.setattr(factory_module.settings, "llm_api_key", "")
    monkeypatch.delitem(sys.modules, "openai", raising=False)
    monkeypatch.delitem(sys.modules, _OPENAI_PROVIDER_MODULE, raising=False)
    monkeypatch.setattr(builtins, "__import__", guarded_import)

    provider = factory_module.get_ai_candidate_compare_provider()

    from app.integrations.mock_ai_candidate_compare import MockAiCandidateCompareProvider

    assert isinstance(provider, MockAiCandidateCompareProvider)
    assert "openai" not in sys.modules
    assert _OPENAI_PROVIDER_MODULE not in sys.modules
    assert factory_module.generation_mode_for_provider() == "mock"


def test_factory_returns_openai_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    client = SimpleNamespace()
    monkeypatch.setattr(factory_module.settings, "llm_provider", "openai")
    monkeypatch.setattr(factory_module.settings, "llm_api_key", "test-key")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=lambda **_kwargs: client))

    provider = factory_module.get_ai_candidate_compare_provider()

    from app.integrations.openai_ai_candidate_compare import OpenAIAiCandidateCompareProvider

    assert isinstance(provider, OpenAIAiCandidateCompareProvider)
    assert factory_module.generation_mode_for_provider() == "live"


def test_factory_rejects_unknown_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory_module.settings, "llm_provider", "unknown")

    with pytest.raises(
        factory_module.AiCandidateCompareProviderConfigurationError,
        match="Unsupported AI Candidate Compare provider: 'unknown'",
    ):
        factory_module.get_ai_candidate_compare_provider()
