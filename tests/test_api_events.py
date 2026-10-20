import json
import re

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def build_client(tmp_path):
    settings = Settings(
        app_env="test",
        hmac_secret="test-secret",
        event_log_path=tmp_path / "events.jsonl",
    )
    return TestClient(create_app(settings)), settings


def test_event_endpoint_writes_allowlisted_event(tmp_path):
    client, settings = build_client(tmp_path)
    response = client.post(
        "/api/event",
        json={
            "name": "help_clicked",
            "properties": {"difficulty": "explorer", "stars": 1},
        },
    )
    assert response.status_code == 200
    record = json.loads(settings.event_log_path.read_text(encoding="utf-8").strip())
    assert record["event"] == "help_clicked"
    assert record["difficulty"] == "explorer"


def test_event_endpoint_rejects_private_property(tmp_path):
    client, _ = build_client(tmp_path)
    response = client.post(
        "/api/event",
        json={
            "name": "technical_error",
            "properties": {"text": "private"},
        },
    )
    assert response.status_code == 422


def test_event_endpoint_rejects_unknown_event(tmp_path):
    client, _ = build_client(tmp_path)
    response = client.post(
        "/api/event",
        json={"name": "unknown_event", "properties": {}},
    )
    assert response.status_code == 422


def test_event_record_request_id_matches_response_header(tmp_path):
    client, settings = build_client(tmp_path)
    response = client.post(
        "/api/event",
        json={"name": "practice_started", "properties": {}},
    )
    assert response.status_code == 200
    request_id = response.headers["x-request-id"]
    record = json.loads(settings.event_log_path.read_text(encoding="utf-8").strip())
    assert record["request_id"] == request_id


def test_event_record_ignores_client_request_id(tmp_path):
    client, settings = build_client(tmp_path)
    client_supplied = "attacker-secret-transcript"
    response = client.post(
        "/api/event",
        json={"name": "practice_started", "properties": {}},
        headers={"X-Request-ID": client_supplied},
    )
    assert response.status_code == 200
    request_id = response.headers["x-request-id"]
    assert re.fullmatch(r"[0-9a-f]{32}", request_id)
    log_text = settings.event_log_path.read_text(encoding="utf-8")
    assert client_supplied not in log_text
    record = json.loads(log_text.strip())
    assert record["request_id"] == request_id


def test_continued_after_help_event_is_allowed(tmp_path):
    client, settings = build_client(tmp_path)
    response = client.post(
        "/api/event",
        json={
            "name": "continued_after_help",
            "properties": {
                "continued_after_help": True,
                "difficulty": "explorer",
            },
        },
    )
    assert response.status_code == 200
    record = json.loads(
        settings.event_log_path.read_text(encoding="utf-8").strip()
    )
    assert record["event"] == "continued_after_help"
    assert record["continued_after_help"] is True
