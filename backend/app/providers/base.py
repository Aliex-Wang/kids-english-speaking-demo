from dataclasses import dataclass
from typing import Protocol


class ProviderError(RuntimeError):
    """Raised when an external provider fails or returns an invalid response."""


@dataclass(frozen=True)
class ASRResult:
    text: str
    confidence: float | None = None


@dataclass(frozen=True)
class TTSResult:
    audio: bytes
    media_type: str


class ASRProvider(Protocol):
    async def transcribe(self, audio_wav: bytes) -> ASRResult:
        ...


class LLMProvider(Protocol):
    async def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        ...


class TTSProvider(Protocol):
    async def synthesize(self, text: str, voice: str, speed: float) -> TTSResult:
        ...


class PronunciationProvider(Protocol):
    async def score(self, audio_wav: bytes, reference_text: str) -> dict:
        ...
