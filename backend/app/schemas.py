from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Difficulty(str, Enum):
    sprout = "sprout"
    explorer = "explorer"
    star = "star"


class ThemeId(str, Enum):
    family = "family"
    school = "school"
    shopping = "shopping"
    food = "food"
    transport = "transport"
    friends = "friends"


class StepKind(str, Enum):
    greeting = "greeting"
    task = "task"
    free_expression = "free_expression"
    goodbye = "goodbye"


class SceneStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(pattern=r"^step_[1-9][0-9]*$")
    kind: StepKind
    goal: str = Field(min_length=1, max_length=200)
    role_prompt: str = Field(min_length=1, max_length=300)
    target_phrases: list[str] = Field(min_length=1, max_length=5)
    accepted_keywords: list[str] = Field(min_length=1, max_length=8)
    hint_en: str = Field(min_length=1, max_length=300)
    hint_zh: str = Field(min_length=1, max_length=300)
    retry_prompt: str = Field(min_length=1, max_length=200)
    max_attempts: int = Field(ge=1, le=3)
    next_step: str | None = None
    allow_skip: bool = True


class SceneSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scene_id: str = Field(min_length=1, max_length=64)
    theme: ThemeId
    difficulty: Difficulty
    title: str = Field(min_length=1, max_length=100)
    setting: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=80)
    goal: str = Field(min_length=1, max_length=200)
    steps: list[SceneStep] = Field(min_length=4, max_length=7)
    target_expressions: list[str] = Field(min_length=1, max_length=5)
    safety_notes: list[str] = Field(min_length=1, max_length=10)


class SceneEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scene: SceneSpec
    issued_at: datetime
    expires_at: datetime

    @model_validator(mode="after")
    def expiry_after_issue(self) -> "SceneEnvelope":
        if self.expires_at <= self.issued_at:
            raise ValueError("expires_at must be after issued_at")
        return self


class SceneRequest(BaseModel):
    difficulty: Difficulty
    recent_themes: list[ThemeId] = Field(default_factory=list, max_length=2)


class SceneResponse(BaseModel):
    envelope: SceneEnvelope
    signature: str
    opening_text: str
    opening_audio_base64: str | None = None
    opening_media_type: str | None = None
    fallback_used: bool = False


class TurnSummary(BaseModel):
    step_id: str
    accepted: bool
    attempts: int
    help_used: bool = False


class TurnResponse(BaseModel):
    recognized_text: str
    accepted: bool
    feedback: str
    reply: str
    hint: str
    next_step: str | None
    stars_earned: int
    safety: Literal["ok", "redirect"]
    attempts: int
    completed: bool
    audio_base64: str | None = None
    media_type: str | None = None
    error_type: str | None = None


class EventName(str, Enum):
    practice_started = "practice_started"
    help_clicked = "help_clicked"
    practice_completed = "practice_completed"
    practice_restarted = "practice_restarted"
    continued_after_help = "continued_after_help"
    technical_error = "technical_error"


class EventRequest(BaseModel):
    name: EventName
    properties: dict[str, str | int | bool] = Field(default_factory=dict)

