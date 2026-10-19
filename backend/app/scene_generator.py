import asyncio
from dataclasses import dataclass
from uuid import uuid4

from app.content import PROFILES, ThemeCatalog
from app.fallback_scenes import FallbackSceneFactory
from app.prompts import SCENE_SYSTEM_PROMPT, build_scene_prompt
from app.providers.base import LLMProvider
from app.scene_validator import SceneValidator
from app.schemas import Difficulty, SceneSpec, ThemeId
from app.theme_selector import ThemeSelector


@dataclass(frozen=True)
class GeneratedScene:
    scene: SceneSpec
    fallback_used: bool


class SceneGenerator:
    def __init__(
        self,
        llm: LLMProvider,
        catalog: ThemeCatalog,
        validator: SceneValidator,
        fallback: FallbackSceneFactory,
        selector: ThemeSelector,
        timeout_seconds: float = 8.0,
        max_attempts: int = 2,
    ):
        self.llm = llm
        self.catalog = catalog
        self.validator = validator
        self.fallback = fallback
        self.selector = selector
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts

    async def generate(
        self,
        difficulty: Difficulty,
        recent_themes: list[ThemeId],
    ) -> GeneratedScene:
        theme_id = self.selector.select(recent_themes)
        theme = self.catalog.by_id(theme_id)
        profile = PROFILES[difficulty]
        prompt = build_scene_prompt(theme, difficulty, profile)

        for _ in range(self.max_attempts):
            try:
                payload = await asyncio.wait_for(
                    self.llm.complete_json(SCENE_SYSTEM_PROMPT, prompt),
                    timeout=self.timeout_seconds,
                )
                scene = SceneSpec.model_validate(
                    {
                        **payload,
                        "scene_id": uuid4().hex,
                        "theme": theme_id.value,
                        "difficulty": difficulty.value,
                    }
                )
                self.validator.validate(scene)
                return GeneratedScene(scene=scene, fallback_used=False)
            except Exception:
                continue

        return GeneratedScene(
            scene=self.fallback.build(theme_id, difficulty),
            fallback_used=True,
        )
