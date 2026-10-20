from app.content import PROFILES, load_theme_catalog
from app.schemas import Difficulty, ThemeId


def test_catalog_contains_six_themes():
    catalog = load_theme_catalog()
    assert set(catalog.ids()) == {
        ThemeId.family,
        ThemeId.school,
        ThemeId.shopping,
        ThemeId.food,
        ThemeId.transport,
        ThemeId.friends,
    }


def test_every_theme_has_three_subthemes_and_three_difficulties():
    catalog = load_theme_catalog()
    for theme in catalog.themes:
        assert len(theme.subthemes) == 3
        assert set(theme.target_examples) == set(Difficulty)


def test_difficulty_profiles_match_the_spec():
    assert PROFILES[Difficulty.sprout].max_recording_seconds == 10
    assert PROFILES[Difficulty.explorer].max_recording_seconds == 15
    assert PROFILES[Difficulty.star].max_recording_seconds == 15
    assert PROFILES[Difficulty.sprout].min_steps == 4
    assert PROFILES[Difficulty.star].max_steps == 7
