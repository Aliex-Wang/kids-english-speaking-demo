import json

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.providers.fake import FakeLLMProvider
from app.schemas import SceneEnvelope
from app.signature import verify_envelope


def build_client(tmp_path):
    settings = Settings(
        app_env="test",
        hmac_secret="test-secret",
        event_log_path=tmp_path / "events.jsonl",
    )
    return TestClient(create_app(settings)), settings


def test_scene_endpoint_returns_signed_envelope(tmp_path):
    client, settings = build_client(tmp_path)
    response = client.post(
        "/api/scene",
        json={"difficulty": "explorer", "recent_themes": []},
    )
    assert response.status_code == 200
    payload = response.json()
    envelope = SceneEnvelope.model_validate(payload["envelope"])
    verify_envelope(envelope, payload["signature"], settings.hmac_secret)
    assert payload["opening_text"]
    assert payload["opening_audio_base64"]


def test_scene_endpoint_avoids_recent_themes(tmp_path):
    client, _ = build_client(tmp_path)
    response = client.post(
        "/api/scene",
        json={
            "difficulty": "star",
            "recent_themes": ["family", "school"],
        },
    )
    assert response.status_code == 200
    theme = response.json()["envelope"]["scene"]["theme"]
    assert theme not in {"family", "school"}


def test_scene_endpoint_returns_fallback_for_invalid_llm(tmp_path):
    client, _ = build_client(tmp_path)
    services = client.app.state.services
    services.scene_generator.llm = FakeLLMProvider(
        scene_factory=lambda theme, difficulty: {"bad": "payload"}
    )
    response = client.post(
        "/api/scene",
        json={"difficulty": "sprout", "recent_themes": []},
    )
    assert response.status_code == 200
    assert response.json()["fallback_used"] is True


def test_scene_opening_tts_failure_returns_text_only(tmp_path):
    class FailingTTS:
        async def synthesize(self, text, voice, speed):
            raise RuntimeError("tts unavailable")

    client, settings = build_client(tmp_path)
    client.app.state.services.tts = FailingTTS()
    response = client.post(
        "/api/scene",
        json={"difficulty": "explorer", "recent_themes": []},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["opening_text"]
    assert payload["opening_audio_base64"] is None
    request_id = response.headers["x-request-id"]
    records = [
        json.loads(line)
        for line in settings.event_log_path.read_text(
            encoding="utf-8"
        ).strip().splitlines()
    ]
    technical = [
        record for record in records if record["event"] == "technical_error"
    ]
    assert len(technical) == 1
    assert technical[0]["error_type"] == "RuntimeError"
    assert technical[0]["request_id"] == request_id
