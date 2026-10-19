import io
import wave
from collections.abc import Callable

from app.providers.base import ASRResult, TTSResult
from app.schemas import Difficulty, ThemeId


def make_silence_wav(seconds: float = 0.25, sample_rate: int = 16000) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * int(seconds * sample_rate))
    return buffer.getvalue()


class FakeASRProvider:
    def __init__(
        self,
        texts: list[str] | None = None,
        default_text: str = "I want milk.",
    ):
        self.texts = texts or [default_text]
        self.index = 0

    async def transcribe(self, audio_wav: bytes) -> ASRResult:
        if not audio_wav:
            return ASRResult(text="", confidence=None)
        text = self.texts[self.index % len(self.texts)]
        self.index += 1
        return ASRResult(text=text, confidence=0.95)


class FakeLLMProvider:
    def __init__(
        self,
        scene_factory: Callable[[ThemeId, Difficulty], dict],
        turn_response: dict | None = None,
    ):
        self.scene_factory = scene_factory
        self.turn_response = turn_response

    async def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        if system_prompt.startswith("SCENE_GENERATION"):
            theme = ThemeId(_line_value(user_prompt, "THEME"))
            difficulty = Difficulty(_line_value(user_prompt, "DIFFICULTY"))
            return self.scene_factory(theme, difficulty)
        next_prompt = _line_value(user_prompt, "NEXT_ROLE_PROMPT")
        return self.turn_response or {
            "accepted": True,
            "feedback": "Great job!",
            "reply": (
                next_prompt
                if next_prompt != "NONE"
                else "Great job! See you next time."
            ),
            "hint": "",
            "next_step": None,
            "stars": 1,
            "safety": "ok",
        }


class FakeTTSProvider:
    async def synthesize(self, text: str, voice: str, speed: float) -> TTSResult:
        return TTSResult(audio=make_silence_wav(0.25), media_type="audio/wav")


class FakePronunciationProvider:
    async def score(self, audio_wav: bytes, reference_text: str) -> dict:
        return {
            "overall": 80,
            "accuracy": 80,
            "fluency": 80,
            "completeness": 100,
            "errors": [],
        }


def _line_value(prompt: str, key: str) -> str:
    prefix = f"{key}:"
    for line in prompt.splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    raise ValueError(f"missing prompt line: {key}")
