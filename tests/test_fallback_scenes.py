import pytest
from app.fallback_scenes import FallbackSceneFactory
from app.scene_validator import SceneValidator
from app.schemas import Difficulty, ThemeId


@pytest.mark.parametrize("difficulty", list(Difficulty))
@pytest.mark.parametrize("theme", list(ThemeId))
def test_all_eighteen_fallbacks_validate(theme, difficulty):
    scene = FallbackSceneFactory().build(theme, difficulty)
    SceneValidator().validate(scene)
    assert scene.theme is theme
    assert scene.difficulty is difficulty


def test_fallback_step_chain_is_fixed():
    scene = FallbackSceneFactory().build(ThemeId.family, Difficulty.explorer)
    assert scene.steps[0].step_id == "step_1"
    assert scene.steps[0].next_step == "step_2"
    assert scene.steps[-1].next_step is None
