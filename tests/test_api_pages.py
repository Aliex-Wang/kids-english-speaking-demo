from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def build_client(tmp_path):
    settings = Settings(
        app_env="test",
        hmac_secret="test-secret",
        event_log_path=tmp_path / "events.jsonl",
    )
    return TestClient(create_app(settings))


def test_index_page_contains_difficulties_and_themes(tmp_path):
    client = build_client(tmp_path)
    response = client.get("/")
    assert response.status_code == 200
    for text in [
        "Sprout",
        "Explorer",
        "Star",
        "家庭日常",
        "学校生活",
        "购物",
        "饮食",
        "出行",
        "朋友与社交",
    ]:
        assert text in response.text


def test_practice_page_contains_mic_button(tmp_path):
    client = build_client(tmp_path)
    response = client.get("/practice")
    assert response.status_code == 200
    assert "mic-button" in response.text
    assert "text-input" in response.text
