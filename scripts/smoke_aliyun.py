import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import Settings
from app.content import load_theme_catalog
from app.fallback_scenes import FallbackSceneFactory
from app.providers.factory import build_providers
from app.providers.fake import make_silence_wav
from app.scene_generator import SceneGenerator
from app.scene_validator import SceneValidator
from app.schemas import Difficulty, ThemeId
from app.theme_selector import ThemeSelector


async def run_smoke(
    settings: Settings,
    audio_wav: bytes,
    output_dir: Path,
) -> dict:
    fallback = FallbackSceneFactory()
    asr, llm, tts = build_providers(settings, fallback)
    asr_result = await asr.transcribe(audio_wav)
    catalog = load_theme_catalog()
    generator = SceneGenerator(
        llm=llm,
        catalog=catalog,
        validator=SceneValidator(),
        fallback=fallback,
        selector=ThemeSelector([ThemeId.family]),
        timeout_seconds=settings.scene_timeout_seconds,
    )
    generated = await generator.generate(Difficulty.explorer, [])
    tts_result = await tts.synthesize(
        "Hello, let's practice English.",
        voice=settings.tts_voice,
        speed=0.9,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    extension = "mp3" if tts_result.media_type == "audio/mpeg" else "wav"
    tts_path = output_dir / f"smoke_tts.{extension}"
    tts_path.write_bytes(tts_result.audio)
    return {
        "asr_text": asr_result.text,
        "scene_title": generated.scene.title,
        "fallback_used": generated.fallback_used,
        "tts_path": str(tts_path),
        "tts_media_type": tts_result.media_type,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts"),
    )
    args = parser.parse_args()
    settings = Settings()
    if args.audio:
        audio = args.audio.read_bytes()
    else:
        audio = make_silence_wav(0.5)
        print("warning: using silence; pass --audio with a spoken WAV for a real ASR check")
    result = asyncio.run(run_smoke(settings, audio, args.output_dir))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
