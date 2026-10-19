import random

from app.schemas import ThemeId


class ThemeSelector:
    def __init__(self, theme_ids: list[ThemeId], rng: random.Random | None = None):
        if not theme_ids:
            raise ValueError("theme_ids must not be empty")
        self.theme_ids = list(theme_ids)
        self.rng = rng or random.Random()

    def select(self, recent_themes: list[ThemeId]) -> ThemeId:
        recent = recent_themes[-2:]
        candidates = [theme for theme in self.theme_ids if theme not in recent]
        if not candidates:
            candidates = self.theme_ids
        return self.rng.choice(candidates)
