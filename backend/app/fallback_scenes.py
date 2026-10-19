from pathlib import Path
from uuid import uuid4

import yaml
from pydantic import BaseModel, Field

from app.content import PROFILES
from app.schemas import Difficulty, SceneSpec, SceneStep, StepKind, ThemeId

CONTENT_DIR = Path(__file__).resolve().parent / "content"


class FallbackStepTemplate(BaseModel):
    kind: StepKind
    goal: str
    role_prompt: str
    targets: dict[Difficulty, list[str]]
    keywords: list[str]
    hints: dict[Difficulty, str]
    hints_zh: dict[Difficulty, str]
    retry_prompt: str


class FallbackSceneTemplate(BaseModel):
    theme: ThemeId
    title: str
    setting: str
    role: str
    goal: str
    expressions: dict[Difficulty, list[str]]
    steps: list[FallbackStepTemplate] = Field(min_length=4, max_length=7)


class FallbackCatalog(BaseModel):
    templates: list[FallbackSceneTemplate] = Field(min_length=6, max_length=6)


class FallbackSceneFactory:
    def __init__(self, path: Path | None = None):
        source = path or CONTENT_DIR / "fallback_scenes.yaml"
        with source.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle)
        self.catalog = FallbackCatalog.model_validate(payload)

    def build(self, theme_id: ThemeId, difficulty: Difficulty) -> SceneSpec:
        template = next(
            item for item in self.catalog.templates if item.theme is theme_id
        )
        profile = PROFILES[difficulty]
        raw_steps = list(template.steps)
        free_template = next(
            step for step in template.steps
            if step.kind is StepKind.free_expression
        )
        free_count = sum(
            step.kind is StepKind.free_expression for step in raw_steps
        )
        while (
            free_count < profile.free_expression_turns
            or len(raw_steps) < profile.min_steps
        ):
            padding = free_template.model_copy(
                update={
                    "goal": "practice free expression once more",
                    "role_prompt": "Can you tell me one more thing?",
                }
            )
            raw_steps.insert(len(raw_steps) - 1, padding)
            free_count += 1

        steps: list[SceneStep] = []
        for index, raw in enumerate(raw_steps, start=1):
            next_step = f"step_{index + 1}" if index < len(raw_steps) else None
            steps.append(
                SceneStep(
                    step_id=f"step_{index}",
                    kind=raw.kind,
                    goal=raw.goal,
                    role_prompt=raw.role_prompt,
                    target_phrases=raw.targets[difficulty],
                    accepted_keywords=raw.keywords,
                    hint_en=raw.hints[difficulty],
                    hint_zh=raw.hints_zh[difficulty],
                    retry_prompt=raw.retry_prompt,
                    max_attempts=profile.max_attempts,
                    next_step=next_step,
                    allow_skip=True,
                )
            )
        return SceneSpec(
            scene_id=f"fallback_{theme_id.value}_{difficulty.value}_{uuid4().hex[:8]}",
            theme=theme_id,
            difficulty=difficulty,
            title=template.title,
            setting=template.setting,
            role=template.role,
            goal=template.goal,
            steps=steps,
            target_expressions=template.expressions[difficulty],
            safety_notes=["Reviewed fallback scene for children."],
        )
