import asyncio
import random

from app.content import PROFILES, load_theme_catalog
from app.fallback_scenes import FallbackSceneFactory
from app.prompts import build_scene_prompt
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
