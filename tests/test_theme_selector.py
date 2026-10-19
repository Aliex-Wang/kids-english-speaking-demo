import random

from app.schemas import ThemeId
from app.theme_selector import ThemeSelector


def test_selector_avoids_recent_themes():
    selector = ThemeSelector(theme_ids=list(ThemeId), rng=random.Random(7))
    recent = [ThemeId.family, ThemeId.school]
    for _ in range(20):
        assert selector.select(recent) not in recent


def test_selector_falls_back_when_all_themes_are_recent():
    selector = ThemeSelector(theme_ids=[ThemeId.family], rng=random.Random(1))
    assert selector.select([ThemeId.family]) is ThemeId.family
