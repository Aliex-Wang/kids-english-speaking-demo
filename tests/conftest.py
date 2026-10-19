import pytest
from app.config import Settings


@pytest.fixture
def test_settings() -> Settings:
    return Settings(app_env="test", hmac_secret="test-secret")
