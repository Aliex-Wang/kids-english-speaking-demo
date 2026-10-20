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
from app.scene_generator import SceneGenerator
from app.scene_validator import SceneValidator
from app.schemas import Difficulty, ThemeId
from app.theme_selector import ThemeSelector


async def generate_samples(
    settings: Settings,
    rounds: int = 2,
) -> list[dict]:
    catalog = load_theme_catalog()
    safety_validator = SceneValidator()
    fallback = FallbackSceneFactory()
    _, llm, _ = build_providers(settings, fallback)
    samples: list[dict] = []
    for _ in range(rounds):
        for theme in ThemeId:
            for difficulty in Difficulty:
                generator = SceneGenerator(
                    llm=llm,
                    catalog=catalog,
                    validator=safety_validator,
                    fallback=fallback,
                    selector=ThemeSelector([theme]),
                    timeout_seconds=settings.scene_timeout_seconds,
                )
                generated = await generator.generate(difficulty, [])
                samples.append(
                    {
                        "theme": theme.value,
                        "difficulty": difficulty.value,
                        "fallback_used": generated.fallback_used,
                        "scene": generated.scene.model_dump(mode="json"),
                    }
                )
    return samples


def write_samples(samples: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for sample in samples:
            handle.write(json.dumps(sample, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/scene_samples.jsonl"),
    )
    parser.add_argument("--rounds", type=int, default=2)
    args = parser.parse_args()
    settings = Settings()
    samples = asyncio.run(generate_samples(settings, args.rounds))
    write_samples(samples, args.output)
    print(f"wrote {len(samples)} samples to {args.output}")


if __name__ == "__main__":
    main()
