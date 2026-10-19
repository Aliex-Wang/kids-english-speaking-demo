from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.providers.base import ASRResult
from app.providers.fake import make_silence_wav
from app.signature import make_envelope, sign_envelope
from tests.factories import make_scene


def build_client(tmp_path, max_audio_bytes=5_000_000):
    settings = Settings(
        app_env="test",
        hmac_secret="test-secret",
        max_audio_bytes=max_audio_bytes,
        event_log_path=tmp_path / "events.jsonl",
        scene_timeout_seconds=0.05,
        turn_timeout_seconds=0.05,
    )
    return TestClient(create_app(settings)), settings


def signed_envelope(settings):
    envelope = make_envelope(make_scene(), 3600)
    return envelope, sign_envelope(envelope, settings.hmac_secret)


def form_data(envelope, signature, **overrides):
    data = {
        "envelope_json": envelope.model_dump_json(),
        "signature": signature,
        "current_step_id": "step_1",
        "attempts": "0",
        "history_json": "[]",
        "help_used": "false",
    }
    data.update(overrides)
    return data


def test_turn_accepts_audio_and_returns_next_step(tmp_path):
    client, settings = build_client(tmp_path)
    envelope, signature = signed_envelope(settings)
    response = client.post(
        "/api/turn",
        data=form_data(envelope, signature),
        files={
            "audio": (
                "turn.wav",
                make_silence_wav(0.2),
                "audio/wav",
            )
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["next_step"] == "step_2"
    assert payload["accepted"] is True
    assert payload["stars_earned"] == 2


def test_turn_accepts_text_fallback(tmp_path):
    client, settings = build_client(tmp_path)
    envelope, signature = signed_envelope(settings)
    response = client.post(
        "/api/turn",
        data=form_data(envelope, signature, text_input="yes"),
    )
    assert response.status_code == 200
    assert response.json()["accepted"] is True


def test_turn_rejects_invalid_signature(tmp_path):
    client, settings = build_client(tmp_path)
    envelope, _ = signed_envelope(settings)
    response = client.post(
        "/api/turn",
        data=form_data(envelope, "wrong"),
        files={"audio": ("turn.wav", make_silence_wav(0.2), "audio/wav")},
    )
    assert response.status_code == 400


def test_turn_rejects_oversized_audio(tmp_path):
    client, settings = build_client(tmp_path, max_audio_bytes=100_000)
    envelope, signature = signed_envelope(settings)
    response = client.post(
        "/api/turn",
        data=form_data(envelope, signature),
        files={"audio": ("turn.wav", b"x" * 100_001, "audio/wav")},
    )
    assert response.status_code == 413


def test_turn_rejects_empty_audio(tmp_path):
    client, settings = build_client(tmp_path)
    envelope, signature = signed_envelope(settings)
    response = client.post(
        "/api/turn",
        data=form_data(envelope, signature),
        files={"audio": ("turn.wav", b"", "audio/wav")},
    )
    assert response.status_code == 422


def test_turn_rejects_unknown_step(tmp_path):
    client, settings = build_client(tmp_path)
    envelope, signature = signed_envelope(settings)
    response = client.post(
        "/api/turn",
        data=form_data(envelope, signature, current_step_id="step_9"),
        files={"audio": ("turn.wav", make_silence_wav(0.2), "audio/wav")},
    )
    assert response.status_code == 400


def test_turn_rejects_attempts_over_cap(tmp_path):
    client, settings = build_client(tmp_path)
    envelope, signature = signed_envelope(settings)
    response = client.post(
        "/api/turn",
        data=form_data(envelope, signature, attempts="4"),
        files={"audio": ("turn.wav", make_silence_wav(0.2), "audio/wav")},
    )
    assert response.status_code == 422


def test_low_confidence_asr_returns_retry(tmp_path):
    class LowConfidenceASR:
        async def transcribe(self, audio_wav):
            return ASRResult(text="maybe", confidence=0.1)

    client, settings = build_client(tmp_path)
    client.app.state.services.asr = LowConfidenceASR()
    envelope, signature = signed_envelope(settings)
    response = client.post(
        "/api/turn",
        data=form_data(envelope, signature),
        files={"audio": ("turn.wav", make_silence_wav(0.2), "audio/wav")},
    )
    assert response.status_code == 200
    assert response.json()["recognized_text"] == ""
    assert response.json()["accepted"] is False


def test_tts_failure_returns_text_only(tmp_path):
    class FailingTTS:
        async def synthesize(self, text, voice, speed):
            raise RuntimeError("tts unavailable")

    client, settings = build_client(tmp_path)
    failing = FailingTTS()
    client.app.state.services.tts = failing
    client.app.state.services.dialogue.tts = failing
    envelope, signature = signed_envelope(settings)
    response = client.post(
        "/api/turn",
        data=form_data(envelope, signature),
        files={"audio": ("turn.wav", make_silence_wav(0.2), "audio/wav")},
    )
    assert response.status_code == 200
    assert response.json()["audio_base64"] is None
    assert response.json()["reply"]
