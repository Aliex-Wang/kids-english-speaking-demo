from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from app.schemas import Difficulty, ThemeId

CONTENT_DIR = Path(__file__).resolve().parent / "content"


class DifficultyProfile(BaseModel):
    id: Difficulty
    label: str
    target_age: str
    target_answer: str
    max_recording_seconds: int
    speech_rate: float
    max_reply_sentences: int
    max_target_words: int
    max_attempts: int
    min_steps: int
    max_steps: int
    free_expression_turns: int
    show_hint_zh: bool
    show_first_word: bool


PROFILES: dict[Difficulty, DifficultyProfile] = {
    Difficulty.sprout: DifficultyProfile(
        id=Difficulty.sprout,
        label="Sprout",
        target_age="4–6 岁",
        target_answer="单词或 1–3 个词",
        max_recording_seconds=10,
        speech_rate=0.8,
        max_reply_sentences=1,
        max_target_words=3,
        max_attempts=3,
        min_steps=4,
        max_steps=5,
        free_expression_turns=1,
        show_hint_zh=True,
        show_first_word=True,
    ),
    Difficulty.explorer: DifficultyProfile(
        id=Difficulty.explorer,
        label="Explorer",
        target_age="7–9 岁",
        target_answer="简单短句",
        max_recording_seconds=15,
        speech_rate=0.9,
        max_reply_sentences=2,
        max_target_words=8,
        max_attempts=2,
        min_steps=5,
        max_steps=6,
        free_expression_turns=2,
        show_hint_zh=False,
        show_first_word=True,
    ),
    Difficulty.star: DifficultyProfile(
        id=Difficulty.star,
        label="Star",
        target_age="10–12 岁",
        target_answer="完整句子",
        max_recording_seconds=15,
        speech_rate=1.0,
        max_reply_sentences=2,
        max_target_words=14,
        max_attempts=2,
        min_steps=6,
        max_steps=7,
        free_expression_turns=2,
        show_hint_zh=False,
        show_first_word=False,
    ),
}


class ThemeDefinition(BaseModel):
    id: ThemeId
    name_en: str
    name_zh: str
    icon: str
    color: str
    subthemes: list[str] = Field(min_length=3, max_length=3)
    setting: str
    role: str
    goal: str
    target_examples: dict[Difficulty, list[str]]


class ThemeCatalog(BaseModel):
    themes: list[ThemeDefinition] = Field(min_length=6, max_length=6)

    def by_id(self, theme_id: ThemeId) -> ThemeDefinition:
        for theme in self.themes:
            if theme.id is theme_id:
                return theme
        raise KeyError(theme_id)

    def ids(self) -> list[ThemeId]:
        return [theme.id for theme in self.themes]


@lru_cache(maxsize=1)
def load_theme_catalog(path: Path | None = None) -> ThemeCatalog:
    source = path or CONTENT_DIR / "life_themes.yaml"
    with source.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    return ThemeCatalog.model_validate(payload)
