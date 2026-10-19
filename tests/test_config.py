import pytest
from pydantic import ValidationError

from app.config import Settings


def test_development_defaults_are_safe():
    settings = Settings(app_env="test")
    assert settings.max_audio_bytes == 5_000_000
    assert settings.scene_timeout_seconds == 8.0
    assert settings.turn_timeout_seconds == 12.0


def test_production_rejects_default_hmac_secret():
    with pytest.raises(ValidationError):
        Settings(app_env="production", hmac_secret="dev-only-change-me")