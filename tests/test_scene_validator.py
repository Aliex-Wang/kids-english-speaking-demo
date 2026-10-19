import pytest

from app.scene_validator import SceneValidationError, SceneValidator
from app.schemas import Difficulty, StepKind
from tests.factories import make_scene


def test_valid_scene_passes():
    SceneValidator().validate(make_scene(difficulty=Difficulty.sprout))


def test_scene_must_start_with_greeting_and_end_with_goodbye():
    scene = make_scene()
    scene.steps[0] = scene.steps[0].model_copy(update={"kind": StepKind.task})
    with pytest.raises(SceneValidationError):
        SceneValidator().validate(scene)


def test_scene_must_have_a_free_expression_step():
    scene = make_scene()
    for index, step in enumerate(scene.steps):
        scene.steps[index] = step.model_copy(update={"kind": StepKind.task})
    scene.steps[-1] = scene.steps[-1].model_copy(update={"kind": StepKind.goodbye})
    with pytest.raises(SceneValidationError):
        SceneValidator().validate(scene)


def test_sprout_target_phrase_cannot_exceed_three_words():
    scene = make_scene(difficulty=Difficulty.sprout)
    scene.steps[1] = scene.steps[1].model_copy(
        update={"target_phrases": ["I would like some milk please"]}
    )
    with pytest.raises(SceneValidationError):
        SceneValidator().validate(scene)


def test_broken_next_step_chain_is_rejected():
    scene = make_scene()
    scene.steps[1] = scene.steps[1].model_copy(update={"next_step": "step_4"})
    with pytest.raises(SceneValidationError):
        SceneValidator().validate(scene)
