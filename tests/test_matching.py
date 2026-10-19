from app.matching import rule_match
from app.schemas import Difficulty
from tests.factories import make_scene


def test_exact_target_phrase_matches():
    scene = make_scene()
    assert rule_match("I want milk.", scene.steps[1], Difficulty.explorer)


def test_case_and_punctuation_are_ignored():
    scene = make_scene()
    assert rule_match("I WANT MILK!", scene.steps[1], Difficulty.explorer)


def test_sprout_keyword_matches():
    scene = make_scene(difficulty=Difficulty.sprout)
    assert rule_match("milk", scene.steps[1], Difficulty.sprout)


def test_explorer_keyword_does_not_auto_match():
    scene = make_scene()
    assert not rule_match("milk", scene.steps[1], Difficulty.explorer)
