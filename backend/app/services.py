from dataclasses import dataclass

from fastapi.templating import Jinja2Templates

from app.config import Settings
from app.content import PROFILES, ThemeCatalog, load_theme_catalog
from app.dialogue import DialogueOrchestrator
from app.events import EventLogger
from app.fallback_scenes import FallbackSceneFactory
from app.providers.base import ASRProvider, TTSProvider
from app.providers.factory import build_providers
from app.scene_generator import SceneGenerator
from app.scene_validator import SceneValidator
from app.safety import SafetyValidator
from app.schemas import Difficulty
from app.theme_selector import ThemeSelector


@dataclass
class Services:
    settings: Settings
    catalog: ThemeCatalog
    scene_generator: SceneGenerator
    dialogue: DialogueOrchestrator
    asr: ASRProvider
    tts: TTSProvider
    events: EventLogger
    templates: Jinja2Templates
    app_config: dict


def build_services(
    settings: Settings,
    templates: Jinja2Templates,
) -> Services:
    catalog = load_theme_catalog()
    safety = SafetyValidator()
    validator = SceneValidator(safety)
    fallback = FallbackSceneFactory()
    asr, llm, tts = build_providers(settings, fallback)
    selector = ThemeSelector(catalog.ids())
    scene_generator = SceneGenerator(
        llm=llm,
        catalog=catalog,
        validator=validator,
        fallback=fallback,
        selector=selector,
        timeout_seconds=settings.scene_timeout_seconds,
    )
    dialogue = DialogueOrchestrator(
        llm=llm,
        safety=safety,
        tts=tts,
        timeout_seconds=settings.turn_timeout_seconds,
        voice=settings.tts_voice,
    )
    events = EventLogger(settings.event_log_path)
    app_config = {
        "difficulties": [
            PROFILES[difficulty].model_dump(mode="json")
            for difficulty in Difficulty
        ],
        "themes": {
            theme.id.value: {
                "name_en": theme.name_en,
                "name_zh": theme.name_zh,
                "icon": theme.icon,
                "color": theme.color,
            }
            for theme in catalog.themes
        },
        "avatars": ["🐻", "🐰", "🦊", "🐼"],
    }
    return Services(
        settings=settings,
        catalog=catalog,
        scene_generator=scene_generator,
        dialogue=dialogue,
        asr=asr,
        tts=tts,
        events=events,
        templates=templates,
        app_config=app_config,
    )
