import pytest

from app.config import Settings
from app.fallback_scenes import FallbackSceneFactory
from app.providers.factory import build_providers
from app.providers.fake import FakeASRProvider, FakeLLMProvider, FakeTTSProvider


def test_factory_builds_fakes_by_default():
    asr, llm, tts = build_providers(
        Settings(app_env="test"),
        FallbackSceneFactory(),
    )
    assert isinstance(asr, FakeASRProvider)
    assert isinstance(llm, FakeLLMProvider)
    assert isinstance(tts, FakeTTSProvider)


def test_factory_rejects_unknown_provider():
    with pytest.raises(ValueError):
        build_providers(
            Settings(app_env="test", asr_provider="unknown"),
            FallbackSceneFactory(),
        )
