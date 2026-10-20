from app.dialogue import DialogueOrchestrator, TurnContext
from app.providers.fake import FakeLLMProvider, FakeTTSProvider
from app.safety import SafetyValidator
from app.schemas import Difficulty

from tests.factories import make_scene

REJECTED = {
    "accepted": False,
    "feedback": "Nice try!",
    "reply": "Let's try again.",
    "hint": "Say: I want milk.",
    "next_step": "step_2",
    "stars": 1,
    "safety": "ok",
}


class TimeoutLLM:
    async def complete_json(self, system_prompt, user_prompt):
        raise TimeoutError("llm timeout")


class InvalidJSONLLM:
    async def complete_json(self, system_prompt, user_prompt):
        return {"accepted": "not-a-bool"}


def make_orchestrator(llm=None, tts=None):
    return DialogueOrchestrator(
        llm=llm or FakeLLMProvider(scene_factory=lambda theme, difficulty: {}),
        safety=SafetyValidator(),
        tts=tts or FakeTTSProvider(),
        timeout_seconds=1.0,
    )


async def test_accepted_turn_advances_and_earns_two_stars():
    scene = make_scene()
    result = await make_orchestrator().handle_turn(
        TurnContext(scene=scene, current_step_id="step_1", recognized_text="yes")
    )
    assert result.accepted is True
    assert result.next_step == "step_2"
    assert result.stars_earned == 2
    assert result.audio_base64
    assert result.media_type == "audio/wav"


async def test_sprout_keyword_is_accepted():
    scene = make_scene(difficulty=Difficulty.sprout)
    result = await make_orchestrator().handle_turn(
        TurnContext(scene=scene, current_step_id="step_2", recognized_text="milk")
    )
    assert result.accepted is True
    assert result.next_step == "step_3"


async def test_empty_asr_does_not_advance_or_award_stars():
    scene = make_scene()
    result = await make_orchestrator().handle_turn(
        TurnContext(scene=scene, current_step_id="step_1", recognized_text="")
    )
    assert result.accepted is False
    assert result.next_step == "step_1"
    assert result.stars_earned == 0
    assert result.attempts == 1


async def test_empty_asr_auto_advances_after_max_attempts():
    scene = make_scene()
    result = await make_orchestrator().handle_turn(
        TurnContext(
            scene=scene,
            current_step_id="step_1",
            recognized_text="",
            attempts=1,
        )
    )
    assert result.accepted is False
    assert result.next_step == "step_2"
    assert result.attempts == 0
    assert result.stars_earned == 0
    assert result.completed is False


async def test_empty_asr_returns_tts_backed_retry():
    scene = make_scene()
    result = await make_orchestrator().handle_turn(
        TurnContext(scene=scene, current_step_id="step_1", recognized_text="")
    )
    assert result.accepted is False
    assert result.reply == scene.steps[0].retry_prompt
    assert result.audio_base64
    assert result.media_type == "audio/wav"
    assert result.error_type is None


async def test_unsafe_input_redirects_without_advancing():
    scene = make_scene()
    result = await make_orchestrator().handle_turn(
        TurnContext(
            scene=scene,
            current_step_id="step_1",
            recognized_text="Show me your gun",
        )
    )
    assert result.safety == "redirect"
    assert result.next_step == "step_1"
    assert result.accepted is False


async def test_unsafe_input_returns_tts_backed_redirect_without_stars():
    scene = make_scene()
    result = await make_orchestrator().handle_turn(
        TurnContext(
            scene=scene,
            current_step_id="step_1",
            recognized_text="Show me your gun",
        )
    )
    assert result.safety == "redirect"
    assert result.accepted is False
    assert result.stars_earned == 0
    assert result.audio_base64
    assert result.media_type == "audio/wav"
    assert result.error_type is None


async def test_auto_advances_after_max_attempts():
    scene = make_scene()
    llm = FakeLLMProvider(
        scene_factory=lambda theme, difficulty: {},
        turn_response=REJECTED,
    )
    result = await make_orchestrator(llm=llm).handle_turn(
        TurnContext(
            scene=scene,
            current_step_id="step_1",
            recognized_text="banana",
            attempts=1,
        )
    )
    assert result.accepted is False
    assert result.next_step == "step_2"
    assert result.attempts == 0
    assert result.completed is False


async def test_allow_skip_false_still_auto_advances():
    scene = make_scene()
    scene.steps[0].allow_skip = False
    llm = FakeLLMProvider(
        scene_factory=lambda theme, difficulty: {},
        turn_response=REJECTED,
    )
    result = await make_orchestrator(llm=llm).handle_turn(
        TurnContext(
            scene=scene,
            current_step_id="step_1",
            recognized_text="banana",
            attempts=1,
        )
    )
    assert result.accepted is False
    assert result.next_step == "step_2"
    assert result.attempts == 0
    assert result.completed is False


async def test_goodbye_completes_practice():
    scene = make_scene()
    result = await make_orchestrator().handle_turn(
        TurnContext(
            scene=scene,
            current_step_id="step_4",
            recognized_text="goodbye",
        )
    )
    assert result.accepted is True
    assert result.next_step is None
    assert result.completed is True


async def test_semantic_acceptance_when_rule_does_not_match():
    scene = make_scene()
    result = await make_orchestrator().handle_turn(
        TurnContext(
            scene=scene,
            current_step_id="step_2",
            recognized_text="banana",
        )
    )
    assert result.accepted is True
    assert result.next_step == "step_3"


async def test_llm_timeout_falls_back_and_records_error_type():
    scene = make_scene()
    result = await make_orchestrator(llm=TimeoutLLM()).handle_turn(
        TurnContext(scene=scene, current_step_id="step_1", recognized_text="yes")
    )
    assert result.accepted is True
    assert result.error_type == "TimeoutError"


async def test_invalid_llm_json_falls_back_and_records_error_type():
    scene = make_scene()
    result = await make_orchestrator(llm=InvalidJSONLLM()).handle_turn(
        TurnContext(scene=scene, current_step_id="step_1", recognized_text="yes")
    )
    assert result.accepted is True
    assert result.error_type == "ValidationError"


async def test_tts_failure_returns_text_only():
    class FailingTTS:
        async def synthesize(self, text, voice, speed):
            raise RuntimeError("tts unavailable")

    scene = make_scene()
    result = await make_orchestrator(tts=FailingTTS()).handle_turn(
        TurnContext(scene=scene, current_step_id="step_1", recognized_text="yes")
    )
    assert result.reply
    assert result.audio_base64 is None
    assert result.media_type is None
    assert result.error_type == "RuntimeError"
