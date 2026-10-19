import pytest
from app.scene_validator import SceneValidationError, SceneValidator
from app.schemas import Difficulty, StepKind

from tests.factories import make_scene


def test_valid_scene_passes():
    SceneValidator().validate(make_scene(difficulty=Difficulty.sprout))


def test_scene_must_start_with_greeting():
    scene = make_scene(difficulty=Difficulty.sprout)
    scene.steps[0] = scene.steps[0].model_copy(update={"kind": StepKind.task})
    with pytest.raises(SceneValidationError, match="first step must be greeting"):
        SceneValidator().validate(scene)


def test_scene_must_end_with_goodbye():
    scene = make_scene(difficulty=Difficulty.sprout)
    scene.steps[-1] = scene.steps[-1].model_copy(update={"kind": StepKind.task})
    with pytest.raises(SceneValidationError, match="last step must be goodbye"):
        SceneValidator().validate(scene)


def test_scene_must_have_a_free_expression_step():
    scene = make_scene(difficulty=Difficulty.sprout)
    for index, step in enumerate(scene.steps):
        scene.steps[index] = step.model_copy(update={"kind": StepKind.task})
    scene.steps[-1] = scene.steps[-1].model_copy(update={"kind": StepKind.goodbye})
    with pytest.raises(
        SceneValidationError,
        match="scene must contain at least 1 free_expression steps",
    ):
        SceneValidator().validate(scene)


def test_sprout_target_phrase_cannot_exceed_three_words():
    scene = make_scene(difficulty=Difficulty.sprout)
    scene.steps[1] = scene.steps[1].model_copy(
        update={"target_phrases": ["I would like some milk please"]}
    )
    with pytest.raises(SceneValidationError, match="target phrase is too long"):
        SceneValidator().validate(scene)


def test_broken_next_step_chain_is_rejected():
    scene = make_scene(difficulty=Difficulty.sprout)
    scene.steps[1] = scene.steps[1].model_copy(update={"next_step": "step_4"})
    with pytest.raises(
        SceneValidationError,
        match="step_2 next_step must be step_3",
    ):
        SceneValidator().validate(scene)


def test_rejects_unsafe_step_content():
    scene = make_scene(difficulty=Difficulty.sprout)
    scene.steps[1] = scene.steps[1].model_copy(
        update={"goal": "Ask the child about a knife."}
    )
    with pytest.raises(
        SceneValidationError,
        match="step_2 contains unsafe content",
    ):
        SceneValidator().validate(scene)


def test_rejects_unsafe_accepted_keywords():
    scene = make_scene(difficulty=Difficulty.sprout)
    scene.steps[1] = scene.steps[1].model_copy(update={"accepted_keywords": ["gun"]})
    with pytest.raises(
        SceneValidationError,
        match="step_2 contains unsafe content",
    ):
        SceneValidator().validate(scene)


def test_rejects_unsafe_scene_metadata():
    scene = make_scene(difficulty=Difficulty.sprout)
    scene = scene.model_copy(update={"title": "A horror night"})
    with pytest.raises(
        SceneValidationError,
        match="scene metadata contains unsafe content",
    ):
        SceneValidator().validate(scene)
