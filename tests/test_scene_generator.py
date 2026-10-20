import asyncio
import random

from app.content import load_theme_catalog
from app.fallback_scenes import FallbackSceneFactory
from app.providers.fake import FakeLLMProvider
from app.scene_generator import SceneGenerator
from app.scene_validator import SceneValidator
from app.schemas import Difficulty, ThemeId
from app.theme_selector import ThemeSelector

from tests.factories import make_scene


def build_generator(llm, recent_seed=7, timeout_seconds=1.0):
    catalog = load_theme_catalog()
    return SceneGenerator(
        llm=llm,
        catalog=catalog,
        validator=SceneValidator(),
        fallback=FallbackSceneFactory(),
        selector=ThemeSelector(list(ThemeId), random.Random(recent_seed)),
        timeout_seconds=timeout_seconds,
    )


async def test_generator_returns_llm_scene_when_valid():
    llm = FakeLLMProvider(
        scene_factory=lambda theme, difficulty: make_scene(
            theme=theme, difficulty=difficulty
        ).model_dump(mode="json")
    )
    generated = await build_generator(llm).generate(
        Difficulty.sprout, [ThemeId.family, ThemeId.school]
    )
    assert generated.fallback_used is False
    assert generated.scene.theme not in {ThemeId.family, ThemeId.school}


async def test_generator_reports_single_attempt_on_success():
    llm = FakeLLMProvider(
        scene_factory=lambda theme, difficulty: make_scene(
            theme=theme, difficulty=difficulty
        ).model_dump(mode="json")
    )
    generated = await build_generator(llm).generate(Difficulty.sprout, [])
    assert generated.attempts == 1
    assert generated.error_type is None


async def test_generator_retries_exactly_twice_before_fallback():
    calls = 0

    class CountingInvalidLLM:
        async def complete_json(self, system_prompt, user_prompt):
            nonlocal calls
            calls += 1
            return {"bad": "payload"}

    generated = await build_generator(CountingInvalidLLM()).generate(
        Difficulty.sprout, []
    )
    assert calls == 2
    assert generated.fallback_used is True
    assert generated.attempts == 2
    assert generated.error_type == "ValidationError"
    SceneValidator().validate(generated.scene)


async def test_generator_overrides_conflicting_llm_scene_fields():
    conflicting = make_scene(
        difficulty=Difficulty.sprout, theme=ThemeId.family
    ).model_dump(mode="json")
    conflicting.update(
        scene_id="llm_scene",
        theme=ThemeId.family.value,
        difficulty=Difficulty.explorer.value,
    )
    llm = FakeLLMProvider(scene_factory=lambda theme, difficulty: conflicting)

    generated = await build_generator(llm).generate(
        Difficulty.sprout, [ThemeId.family, ThemeId.school]
    )

    assert generated.fallback_used is False
    assert generated.scene.scene_id != "llm_scene"
    assert len(generated.scene.scene_id) == 32
    assert generated.scene.theme not in {ThemeId.family, ThemeId.school}
    assert generated.scene.difficulty is Difficulty.sprout


async def test_generator_uses_fallback_after_invalid_payloads():
    llm = FakeLLMProvider(scene_factory=lambda theme, difficulty: {"bad": "payload"})
    generated = await build_generator(llm).generate(
        Difficulty.star, [ThemeId.family, ThemeId.school]
    )
    assert generated.fallback_used is True
    SceneValidator().validate(generated.scene)


async def test_generator_uses_fallback_after_timeout():
    class SlowLLM:
        async def complete_json(self, system_prompt, user_prompt):
            await asyncio.sleep(0.05)
            return {}

    generated = await build_generator(SlowLLM(), timeout_seconds=0.001).generate(
        Difficulty.sprout, []
    )
    assert generated.fallback_used is True


async def test_generator_prompt_contains_difficulty_and_theme():
    captured = {}

    class CapturingLLM:
        async def complete_json(self, system_prompt, user_prompt):
            captured["prompt"] = user_prompt
            return make_scene().model_dump(mode="json")

    llm = CapturingLLM()
    generated = await build_generator(llm).generate(Difficulty.sprout, [])
    assert "DIFFICULTY: sprout" in captured["prompt"]
    assert f"THEME: {generated.scene.theme.value}" in captured["prompt"]
