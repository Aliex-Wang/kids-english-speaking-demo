import pytest
from pydantic import ValidationError

from app.schemas import Difficulty, SceneSpec, StepKind, ThemeId
from tests.factories import make_scene


def test_scene_requires_four_to_seven_steps():
    scene = make_scene()
    assert 4 <= len(scene.steps) <= 7
    with pytest.raises(ValidationError):
        SceneSpec(**{**scene.model_dump(), "steps": scene.steps[:3]})


def test_scene_has_one_free_expression_step():
    scene = make_scene()
    assert any(step.kind is StepKind.free_expression for step in scene.steps)


def test_scene_round_trips_through_json():
    scene = make_scene(theme=ThemeId.food, difficulty=Difficulty.star)
    restored = SceneSpec.model_validate_json(scene.model_dump_json())
    assert restored == scene
