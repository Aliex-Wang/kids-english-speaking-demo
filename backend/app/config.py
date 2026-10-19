from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"
    hmac_secret: str = "dev-only-change-me"
    scene_ttl_seconds: int = Field(default=7200, ge=60)
    max_audio_bytes: int = Field(default=5_000_000, ge=100_000)
    scene_timeout_seconds: float = Field(default=8.0, gt=0)
    turn_timeout_seconds: float = Field(default=12.0, gt=0)
    event_log_path: Path = Path("logs/events.jsonl")

    asr_provider: str = "fake"
    llm_provider: str = "fake"
    tts_provider: str = "fake"

    dashscope_api_key: str | None = None
    aliyun_access_key_id: str | None = None
    aliyun_access_key_secret: str | None = None
    aliyun_nls_app_key: str | None = None
    aliyun_region: str = "cn-shanghai"
    qwen_model: str = "qwen-plus"
    tts_voice: str = "xiaoyun"

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.app_env == "production":
            if self.hmac_secret == "dev-only-change-me":
                raise ValueError("HMAC_SECRET must be changed in production")
            if self.asr_provider == "aliyun" or self.tts_provider == "aliyun":
                if not self.aliyun_nls_app_key:
                    raise ValueError(
                        "ALIYUN_NLS_APP_KEY is required for Aliyun ASR/TTS"
                    )
                if (
                    not self.aliyun_access_key_id
                    or not self.aliyun_access_key_secret
                ):
                    raise ValueError(
                        "ALIYUN_ACCESS_KEY_ID and "
                        "ALIYUN_ACCESS_KEY_SECRET are required"
                    )
            if self.llm_provider == "qwen" and not self.dashscope_api_key:
                raise ValueError("DASHSCOPE_API_KEY is required for Qwen")
        return self


def get_settings() -> Settings:
    return Settings()
