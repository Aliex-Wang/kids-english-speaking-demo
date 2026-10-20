from app.content import ThemeId
from app.fallback_scenes import FallbackSceneFactory
from app.config import Settings
from app.providers.aliyun_nls import (
    AliyunNLSASRProvider,
    AliyunNLSTTSProvider,
)
from app.providers.base import ASRProvider, LLMProvider, TTSProvider
from app.providers.fake import (
    FakeASRProvider,
    FakeLLMProvider,
    FakeTTSProvider,
)
from app.providers.qwen import QwenProvider
from app.schemas import Difficulty


def build_providers(
    settings: Settings,
    fallback_factory: FallbackSceneFactory,
) -> tuple[ASRProvider, LLMProvider, TTSProvider]:
    if settings.asr_provider == "fake":
        asr: ASRProvider = FakeASRProvider(
            texts=[
                "Yes, I am ready.",
                "I want milk.",
                "I like blue.",
                "Goodbye!",
            ]
        )
    elif settings.asr_provider == "aliyun":
        asr = AliyunNLSASRProvider(settings)
    else:
        raise ValueError(f"unknown ASR provider: {settings.asr_provider}")

    if settings.llm_provider == "fake":
        def scene_factory(theme: ThemeId, difficulty: Difficulty) -> dict:
            return fallback_factory.build(theme, difficulty).model_dump(
                mode="json"
            )

        llm: LLMProvider = FakeLLMProvider(scene_factory=scene_factory)
    elif settings.llm_provider == "qwen":
        llm = QwenProvider(settings)
    else:
        raise ValueError(f"unknown LLM provider: {settings.llm_provider}")

    if settings.tts_provider == "fake":
        tts: TTSProvider = FakeTTSProvider()
    elif settings.tts_provider == "aliyun":
        tts = AliyunNLSTTSProvider(settings)
    else:
        raise ValueError(f"unknown TTS provider: {settings.tts_provider}")

    return asr, llm, tts
