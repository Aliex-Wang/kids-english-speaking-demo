from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient


def test_health_endpoint():
    app = create_app(Settings(app_env="test", hmac_secret="test-secret"))
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
