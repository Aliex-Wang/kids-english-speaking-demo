import asyncio
from pathlib import Path

from app.config import Settings
from app.providers.fake import make_silence_wav

from scripts.generate_scene_samples import generate_samples
from scripts.smoke_aliyun import run_smoke


def fake_settings() -> Settings:
    return Settings(
        app_env="test",
        asr_provider="fake",
        llm_provider="fake",
        tts_provider="fake",
    )


def test_generate_samples_covers_all_combinations_once():
    samples = asyncio.run(generate_samples(fake_settings(), rounds=1))
    assert len(samples) == 18
    assert all("scene" in item for item in samples)
    assert {item["theme"] for item in samples} == {
        "family",
        "school",
        "shopping",
        "food",
        "transport",
        "friends",
    }
    assert {item["difficulty"] for item in samples} == {
        "sprout",
        "explorer",
        "star",
    }


def test_smoke_script_runs_with_fake_providers(tmp_path):
    result = asyncio.run(
        run_smoke(
            fake_settings(),
            make_silence_wav(0.2),
            tmp_path,
        )
    )
    assert result["asr_text"] == "Yes, I am ready."
    assert result["scene_title"]
    assert Path(result["tts_path"]).exists()