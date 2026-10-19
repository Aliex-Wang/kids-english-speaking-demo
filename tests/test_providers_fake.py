import io
import wave

from app.content import PROFILES, load_theme_catalog
from app.prompts import SCENE_SYSTEM_PROMPT, TURN_SYSTEM_PROMPT, build_scene_prompt
from app.providers.fake import (
    FakeASRProvider,
    FakeLLMProvider,
    FakePronunciationProvider,
    FakeTTSProvider,
    make_silence_wav,
)
from app.schemas import Difficulty, ThemeId
from tests.factories import make_scene


async def test_fake_asr_cycles_configured_texts():
    provider = FakeASRProvider(texts=["one", "two"])
    assert (await provider.transcribe(b"audio")).text == "one"
    assert (await provider.transcribe(b"audio")).text == "two"
    assert (await provider.transcribe(b"audio")).text == "one"
    assert (await provider.transcribe(b"")).text == ""


async def test_fake_llm_returns_a_scene_payload():
    catalog = load_theme_catalog()
    provider = FakeLLMProvider(
        scene_factory=lambda theme, difficulty: make_scene(
            theme=theme, difficulty=difficulty
        ).model_dump(mode="json")
    )
    prompt = build_scene_prompt(
        catalog.by_id(ThemeId.family),
        Difficulty.explorer,
        PROFILES[Difficulty.explorer],
    )
    payload = await provider.complete_json(SCENE_SYSTEM_PROMPT, prompt)
    assert payload["theme"] == "family"
    assert payload["difficulty"] == "explorer"


async def test_fake_llm_uses_next_role_prompt_for_turn_reply():
    provider = FakeLLMProvider(scene_factory=lambda theme, difficulty: {})
    payload = await provider.complete_json(
        TURN_SYSTEM_PROMPT,
        "NEXT_ROLE_PROMPT: What would you like?\nCHILD_TEXT: milk",
    )
    assert payload["accepted"] is True
    assert payload["reply"] == "What would you like?"


async def test_fake_tts_returns_a_valid_wav():
    result = await FakeTTSProvider().synthesize("Hello", voice="test", speed=1.0)
    with wave.open(io.BytesIO(result.audio), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getframerate() == 16000
    assert result.media_type == "audio/wav"


async def test_fake_pronunciation_provider_is_available_for_v11():
    result = await FakePronunciationProvider().score(b"wav", "I like blue.")
    assert result["overall"] == 80
    assert result["errors"] == []
