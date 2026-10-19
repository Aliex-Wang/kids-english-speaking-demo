# Kids English Speaking Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable Python-first web/PWA demo in which a child completes a dynamically generated, 4–7 turn English speaking task with a cartoon role, browser recording, Aliyun ASR/TTS, Qwen dialogue, and a local-only progress record.

**Architecture:** FastAPI serves Jinja2 pages and JSON APIs. The backend generates a validated `SceneSpec`, signs a time-limited `SceneEnvelope`, and remains stateless; the browser stores only the signed envelope and non-text progress in `localStorage`. ASR, LLM, and TTS sit behind small provider interfaces so tests and local development use deterministic fake providers.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, pydantic-settings, Jinja2, vanilla HTML/CSS/JavaScript, MediaRecorder, Aliyun NLS ASR/TTS, DashScope Qwen, pytest, Playwright, Docker, Nginx.

**Spec:** `docs/superpowers/specs/2026-10-19-kids-english-speaking-demo-design.md`

## Global Constraints

- Target users are children aged 4–12; the main experience is used at home on a tablet or computer browser.
- The demo is an online, turn-based voice conversation; full-duplex real-time audio is out of scope.
- A practice session lasts 5–8 minutes and contains 4–7 dialogue steps, with at least one free-expression step.
- Each generated scene uses one of six life themes: family, school, shopping, food, transport, friends.
- The three difficulties are `sprout` (4–6), `explorer` (7–9), and `star` (10–12).
- Sprout recording limit is 10 seconds; Explorer and Star recording limit is 15 seconds.
- The system avoids the two most recently used themes when selecting a new scene.
- No login, parent dashboard, teacher dashboard, content CMS, payment, or full curriculum in the demo.
- No pronunciation scoring in the demo; define a `PronunciationProvider` interface for V1.1.
- Backend: Python 3.12 + FastAPI + Pydantic. Frontend: Jinja2 + native HTML/CSS/JavaScript. Do not add React, Next.js, or a Node build step.
- Voice collection uses browser `MediaRecorder`; ASR uses Aliyun; dialogue uses Qwen; TTS uses Aliyun.
- Deploy with Docker + Uvicorn + Nginx. HTTPS is required for browser recording; localhost is allowed for local development.
- Demo storage is `localStorage`; do not introduce a database.
- Do not save raw recordings or complete child transcripts on the server or in `localStorage`.
- Logs contain request ID, latency, event counts, and error type only; never audio or complete dialogue text.
- API keys stay on the server and never appear in browser code.
- Every generated scene and every model response must be validated by the backend before use.
- Scene generation gets at most two attempts; after that, use a reviewed theme-specific fallback scene.
- All model output must use structured JSON; invalid JSON or failed safety checks use a deterministic safe response.
- The normal-network target for one dialogue turn is at most 5 seconds; implement explicit timeouts and recoverable fallbacks.
- Automated tests use pytest for backend and Playwright for browser flows. Real Aliyun/Qwen calls are manual smoke tests, not CI tests.
- Acceptance requires at least six themes × three difficulties, recoverable microphone/ASR/LLM/TTS/network failures, and basic support for iPad Safari, Android Chrome, and desktop Chrome.

## File Structure

```text
D:\projects\English_learn\
├─ backend/
│  ├─ app/
│  │  ├─ __init__.py
│  │  ├─ main.py                 # FastAPI app factory, static/template wiring
│  │  ├─ config.py               # environment settings and production checks
│  │  ├─ schemas.py              # Pydantic API and domain models
│  │  ├─ content.py              # difficulty profiles and theme catalog loader
│  │  ├─ safety.py               # child-safety content checks
│  │  ├─ signature.py            # HMAC scene envelope signing/verification
│  │  ├─ scene_validator.py      # structure, difficulty, and safety validation
│  │  ├─ fallback_scenes.py      # reviewed fallback catalog and factory
│  │  ├─ theme_selector.py       # avoid recent themes
│  │  ├─ scene_generator.py      # LLM generation, retry, fallback
│  │  ├─ matching.py             # phrase/keyword matching
│  │  ├─ dialogue.py             # turn orchestration and state transitions
│  │  ├─ audio.py                # ffmpeg conversion to 16 kHz mono WAV
│  │  ├─ events.py               # allowlisted anonymous JSONL events
│  │  ├─ services.py             # dependency container for routes
│  │  ├─ prompts.py              # Qwen scene and turn prompts
│  │  ├─ api/
│  │  │  ├─ __init__.py
│  │  │  └─ routes.py            # pages and JSON APIs
│  │  ├─ providers/
│  │  │  ├─ __init__.py
│  │  │  ├─ base.py              # ASR/LLM/TTS protocols and result types
│  │  │  ├─ fake.py              # deterministic local/test providers
│  │  │  ├─ qwen.py              # DashScope OpenAI-compatible Qwen adapter
│  │  │  ├─ aliyun_nls.py        # Aliyun NLS ASR/TTS adapters and token cache
│  │  │  └─ factory.py           # provider selection from settings
│  │  ├─ content/
│  │  │  ├─ life_themes.yaml
│  │  │  └─ fallback_scenes.yaml
│  │  ├─ templates/
│  │  │  ├─ base.html
│  │  │  ├─ index.html
│  │  │  └─ practice.html
│  │  └─ static/
│  │     ├─ css/app.css
│  │     └─ js/
│  │        ├─ api.js
│  │        ├─ storage.js
│  │        ├─ recorder.js
│  │        ├─ index.js
│  │        └─ practice.js
│  ├─ requirements.txt
│  └─ requirements-dev.txt
├─ tests/
│  ├─ conftest.py
│  ├─ factories.py
│  ├─ test_*.py
│  └─ test_e2e_*.py
├─ scripts/
│  ├─ generate_scene_samples.py
│  └─ smoke_aliyun.py
├─ deploy/
│  ├─ nginx.conf
│  └─ certs/.gitkeep
├─ Dockerfile
├─ docker-compose.yml
├─ .env.example
├─ pytest.ini
└─ README.md
```

Theme visuals are six reviewed icon + color pairs in `life_themes.yaml` (for example `🏠` + `#f4a261`). This satisfies the six generic life-theme illustrations without generating an image per scene.

---

### Task 1: Project Scaffold, Settings, and Health Endpoint

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/main.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/routes.py`
- Create: `backend/requirements.txt`
- Create: `backend/requirements-dev.txt`
- Create: `pytest.ini`
- Create: `tests/conftest.py`
- Test: `tests/test_config.py`
- Test: `tests/test_health.py`

**Interfaces:**
- Consumes: no earlier tasks.
- Produces: `Settings`, `get_settings() -> Settings`, `create_app(settings: Settings | None = None) -> FastAPI`, and `GET /api/health`.

- [ ] **Step 1: Write the failing configuration and health tests**

Create `tests/test_config.py`:

```python
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
```

Create `tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_health_endpoint():
    app = create_app(Settings(app_env="test", hmac_secret="test-secret"))
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_config.py tests/test_health.py -v`

Expected: FAIL because `app.config` and `app.main` do not exist.

- [ ] **Step 3: Add the minimal project scaffold**

Create `backend/app/__init__.py` with:

```python
"""Kids English speaking demo backend."""
```

Create `backend/app/config.py`:

```python
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
```

Create `backend/app/api/__init__.py` with:

```python
"""HTTP routes for the demo."""
```

Create `backend/app/api/routes.py`:

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

Create `backend/app/main.py`:

```python
from fastapi import FastAPI

from app.api.routes import router
from app.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Kids English Speaking Demo")
    app.state.settings = settings
    app.include_router(router)
    return app


app = create_app()
```

Create `backend/requirements.txt`:

```text
fastapi>=0.115,<1
uvicorn[standard]>=0.34,<1
jinja2>=3.1,<4
python-multipart>=0.0.20,<1
pydantic>=2.10,<3
pydantic-settings>=2.7,<3
httpx>=0.28,<1
pyyaml>=6.0,<7
aliyun-python-sdk-core>=2.16,<3
```

Create `backend/requirements-dev.txt`:

```text
-r requirements.txt
pytest>=8.3,<9
pytest-asyncio>=0.25,<1
httpx2>=2,<3
playwright>=1.49,<2
ruff>=0.8,<1
```

Create `pytest.ini`:

```ini
[pytest]
pythonpath = backend
testpaths = tests
asyncio_mode = auto
```

Create `tests/conftest.py`:

```python
import pytest

from app.config import Settings


@pytest.fixture
def test_settings() -> Settings:
    return Settings(app_env="test", hmac_secret="test-secret")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_config.py tests/test_health.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/__init__.py backend/app/config.py backend/app/main.py backend/app/api/__init__.py backend/app/api/routes.py backend/requirements.txt backend/requirements-dev.txt pytest.ini tests/conftest.py tests/test_config.py tests/test_health.py
git commit -m "feat: scaffold FastAPI app and settings"
```

---

### Task 2: Domain Schemas, Difficulty Profiles, and Theme Catalog

**Files:**
- Create: `backend/app/schemas.py`
- Create: `backend/app/content.py`
- Create: `backend/app/content/life_themes.yaml`
- Create: `tests/factories.py`
- Test: `tests/test_schemas.py`
- Test: `tests/test_content.py`

**Interfaces:**
- Consumes: `Settings` from Task 1.
- Produces: `Difficulty`, `ThemeId`, `StepKind`, `SceneStep`, `SceneSpec`, `SceneEnvelope`, `SceneRequest`, `SceneResponse`, `TurnSummary`, `TurnResponse`, `EventName`, `EventRequest`, `DifficultyProfile`, `PROFILES`, `ThemeDefinition`, `ThemeCatalog`, `load_theme_catalog()`.

- [ ] **Step 1: Write the failing schema and content tests**

Create `tests/test_schemas.py`:

```python
import pytest
from pydantic import ValidationError

from app.schemas import Difficulty, SceneSpec, StepKind, ThemeId
from tests.factories import make_scene


def test_scene_requires_four_to_seven_steps():
    scene = make_scene()
    assert 4 <= len(scene.steps) <= 7
    with pytest.raises(ValidationError):
        SceneSpec(**{**scene.model_dump(), "steps": scene.steps[:3]})


def test_scene_has_one_free_expression_step():
    scene = make_scene()
    assert any(step.kind is StepKind.free_expression for step in scene.steps)


def test_scene_round_trips_through_json():
    scene = make_scene(theme=ThemeId.food, difficulty=Difficulty.star)
    restored = SceneSpec.model_validate_json(scene.model_dump_json())
    assert restored == scene
```

Create `tests/test_content.py`:

```python
from app.content import PROFILES, load_theme_catalog
from app.schemas import Difficulty, ThemeId


def test_catalog_contains_six_themes():
    catalog = load_theme_catalog()
    assert set(catalog.ids()) == {
        ThemeId.family,
        ThemeId.school,
        ThemeId.shopping,
        ThemeId.food,
        ThemeId.transport,
        ThemeId.friends,
    }


def test_every_theme_has_three_subthemes_and_three_difficulties():
    catalog = load_theme_catalog()
    for theme in catalog.themes:
        assert len(theme.subthemes) == 3
        assert set(theme.target_examples) == set(Difficulty)


def test_difficulty_profiles_match_the_spec():
    assert PROFILES[Difficulty.sprout].max_recording_seconds == 10
    assert PROFILES[Difficulty.explorer].max_recording_seconds == 15
    assert PROFILES[Difficulty.star].max_recording_seconds == 15
    assert PROFILES[Difficulty.sprout].min_steps == 4
    assert PROFILES[Difficulty.star].max_steps == 7
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_schemas.py tests/test_content.py -v`

Expected: FAIL because `app.schemas`, `app.content`, and `tests.factories` do not exist.

- [ ] **Step 3: Implement the schemas, profiles, catalog, and test factory**

Create `backend/app/schemas.py`:

```python
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Difficulty(str, Enum):
    sprout = "sprout"
    explorer = "explorer"
    star = "star"


class ThemeId(str, Enum):
    family = "family"
    school = "school"
    shopping = "shopping"
    food = "food"
    transport = "transport"
    friends = "friends"


class StepKind(str, Enum):
    greeting = "greeting"
    task = "task"
    free_expression = "free_expression"
    goodbye = "goodbye"


class SceneStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(pattern=r"^step_[1-9][0-9]*$")
    kind: StepKind
    goal: str = Field(min_length=1, max_length=200)
    role_prompt: str = Field(min_length=1, max_length=300)
    target_phrases: list[str] = Field(min_length=1, max_length=5)
    accepted_keywords: list[str] = Field(min_length=1, max_length=8)
    hint_en: str = Field(min_length=1, max_length=300)
    hint_zh: str = Field(min_length=1, max_length=300)
    retry_prompt: str = Field(min_length=1, max_length=200)
    max_attempts: int = Field(ge=1, le=3)
    next_step: str | None = None
    allow_skip: bool = True


class SceneSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scene_id: str = Field(min_length=1, max_length=64)
    theme: ThemeId
    difficulty: Difficulty
    title: str = Field(min_length=1, max_length=100)
    setting: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=80)
    goal: str = Field(min_length=1, max_length=200)
    steps: list[SceneStep] = Field(min_length=4, max_length=7)
    target_expressions: list[str] = Field(min_length=1, max_length=5)
    safety_notes: list[str] = Field(min_length=1, max_length=10)


class SceneEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scene: SceneSpec
    issued_at: datetime
    expires_at: datetime

    @model_validator(mode="after")
    def expiry_after_issue(self) -> "SceneEnvelope":
        if self.expires_at <= self.issued_at:
            raise ValueError("expires_at must be after issued_at")
        return self


class SceneRequest(BaseModel):
    difficulty: Difficulty
    recent_themes: list[ThemeId] = Field(default_factory=list, max_length=2)


class SceneResponse(BaseModel):
    envelope: SceneEnvelope
    signature: str
    opening_text: str
    opening_audio_base64: str | None = None
    opening_media_type: str | None = None
    fallback_used: bool = False


class TurnSummary(BaseModel):
    step_id: str
    accepted: bool
    attempts: int
    help_used: bool = False


class TurnResponse(BaseModel):
    recognized_text: str
    accepted: bool
    feedback: str
    reply: str
    hint: str
    next_step: str | None
    stars_earned: int
    safety: Literal["ok", "redirect"]
    attempts: int
    completed: bool
    audio_base64: str | None = None
    media_type: str | None = None


class EventName(str, Enum):
    practice_started = "practice_started"
    help_clicked = "help_clicked"
    practice_completed = "practice_completed"
    practice_restarted = "practice_restarted"
    technical_error = "technical_error"


class EventRequest(BaseModel):
    name: EventName
    properties: dict[str, str | int | bool] = Field(default_factory=dict)
```

Create `backend/app/content.py`:

```python
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from app.schemas import Difficulty, ThemeId

CONTENT_DIR = Path(__file__).resolve().parent / "content"


class DifficultyProfile(BaseModel):
    id: Difficulty
    label: str
    target_age: str
    target_answer: str
    max_recording_seconds: int
    speech_rate: float
    max_reply_sentences: int
    max_target_words: int
    max_attempts: int
    min_steps: int
    max_steps: int
    free_expression_turns: int
    show_hint_zh: bool
    show_first_word: bool


PROFILES: dict[Difficulty, DifficultyProfile] = {
    Difficulty.sprout: DifficultyProfile(
        id=Difficulty.sprout,
        label="Sprout",
        target_age="4–6 岁",
        target_answer="单词或 1–3 个词",
        max_recording_seconds=10,
        speech_rate=0.8,
        max_reply_sentences=1,
        max_target_words=3,
        max_attempts=3,
        min_steps=4,
        max_steps=5,
        free_expression_turns=1,
        show_hint_zh=True,
        show_first_word=True,
    ),
    Difficulty.explorer: DifficultyProfile(
        id=Difficulty.explorer,
        label="Explorer",
        target_age="7–9 岁",
        target_answer="简单短句",
        max_recording_seconds=15,
        speech_rate=0.9,
        max_reply_sentences=2,
        max_target_words=8,
        max_attempts=2,
        min_steps=5,
        max_steps=6,
        free_expression_turns=2,
        show_hint_zh=False,
        show_first_word=True,
    ),
    Difficulty.star: DifficultyProfile(
        id=Difficulty.star,
        label="Star",
        target_age="10–12 岁",
        target_answer="完整句子",
        max_recording_seconds=15,
        speech_rate=1.0,
        max_reply_sentences=2,
        max_target_words=14,
        max_attempts=2,
        min_steps=6,
        max_steps=7,
        free_expression_turns=2,
        show_hint_zh=False,
        show_first_word=False,
    ),
}


class ThemeDefinition(BaseModel):
    id: ThemeId
    name_en: str
    name_zh: str
    icon: str
    color: str
    subthemes: list[str] = Field(min_length=3, max_length=3)
    setting: str
    role: str
    goal: str
    target_examples: dict[Difficulty, list[str]]


class ThemeCatalog(BaseModel):
    themes: list[ThemeDefinition] = Field(min_length=6, max_length=6)

    def by_id(self, theme_id: ThemeId) -> ThemeDefinition:
        for theme in self.themes:
            if theme.id is theme_id:
                return theme
        raise KeyError(theme_id)

    def ids(self) -> list[ThemeId]:
        return [theme.id for theme in self.themes]


@lru_cache(maxsize=1)
def load_theme_catalog(path: Path | None = None) -> ThemeCatalog:
    source = path or CONTENT_DIR / "life_themes.yaml"
    with source.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    return ThemeCatalog.model_validate(payload)
```

- [ ] **Step 4: Add the six-theme catalog**

Create `backend/app/content/life_themes.yaml`:

```yaml
themes:
  - id: family
    name_en: Family Life
    name_zh: 家庭日常
    icon: "🏠"
    color: "#f4a261"
    subthemes: [breakfast, packing_schoolbag, bedtime]
    setting: at home
    role: Mom or Dad
    goal: talk about a daily family task
    target_examples:
      sprout: [milk, bag, bed]
      explorer: ["I want milk.", "My bag is here.", "I am ready for bed."]
      star:
        - "I would like some milk for breakfast, please."
        - "I put my book in my schoolbag."
        - "I am ready to go to bed."

  - id: school
    name_en: School Life
    name_zh: 学校生活
    icon: "🏫"
    color: "#457b9d"
    subthemes: [classroom, playground, library]
    setting: at school
    role: Teacher or classmate
    goal: complete a simple school task
    target_examples:
      sprout: [book, play, quiet]
      explorer: ["This is my book.", "Let's play together.", "Please be quiet."]
      star:
        - "May I borrow your book, please?"
        - "Would you like to play with me?"
        - "We should be quiet in the library."

  - id: shopping
    name_en: Shopping
    name_zh: 购物
    icon: "🛒"
    color: "#2a9d8f"
    subthemes: [supermarket, bakery, pet_shop]
    setting: at a shop
    role: Shop assistant
    goal: choose an item and complete a simple purchase
    target_examples:
      sprout: [apple, bread, please]
      explorer: ["I want an apple.", "How much is it?", "Here you are."]
      star:
        - "I would like to buy an apple, please."
        - "Could you tell me how much it is?"
        - "Here is the money. Thank you."

  - id: food
    name_en: Food
    name_zh: 饮食
    icon: "🍎"
    color: "#e76f51"
    subthemes: [restaurant, fruit_shop, snack_time]
    setting: at a restaurant or food shop
    role: Waiter or shopkeeper
    goal: order food and say a preference
    target_examples:
      sprout: [rice, juice, yummy]
      explorer: ["I want rice.", "I like juice.", "It is yummy."]
      star:
        - "I would like some rice and juice, please."
        - "I prefer apple juice to orange juice."
        - "The food is delicious. Thank you."

  - id: transport
    name_en: Transport
    name_zh: 出行
    icon: "🚌"
    color: "#264653"
    subthemes: [bus, park, zoo]
    setting: on the way or outdoors
    role: Driver, parent, or guide
    goal: talk about a place and how to get there
    target_examples:
      sprout: [bus, park, zoo]
      explorer: ["Let's take the bus.", "I want to go to the park.", "I like the zoo."]
      star:
        - "Shall we take the bus to the park?"
        - "I would like to see the animals at the zoo."
        - "How long does it take to get there?"

  - id: friends
    name_en: Friends and Social
    name_zh: 朋友与社交
    icon: "👋"
    color: "#e9c46a"
    subthemes: [meet_new_friend, birthday_party, play_together]
    setting: at a party or playground
    role: A friendly child
    goal: greet a friend, share an interest, and invite play
    target_examples:
      sprout: [hello, play, blue]
      explorer: ["Hello, I am happy.", "I like blue.", "Let's play together."]
      star:
        - "Hello, it is nice to meet you."
        - "I like drawing and playing football."
        - "Would you like to play with me?"
```

- [ ] **Step 5: Add the shared scene factory for tests**

Create `tests/factories.py`:

```python
from app.schemas import Difficulty, SceneSpec, SceneStep, StepKind, ThemeId


def make_scene(
    difficulty: Difficulty = Difficulty.explorer,
    theme: ThemeId = ThemeId.family,
    steps: list[SceneStep] | None = None,
) -> SceneSpec:
    if steps is None:
        steps = [
            SceneStep(
                step_id="step_1",
                kind=StepKind.greeting,
                goal="greet the child",
                role_prompt="Hello, are you ready?",
                target_phrases=["yes"],
                accepted_keywords=["yes", "ready"],
                hint_en="Say: yes",
                hint_zh="说：yes",
                retry_prompt="Try saying yes.",
                max_attempts=2,
                next_step="step_2",
                allow_skip=True,
            ),
            SceneStep(
                step_id="step_2",
                kind=StepKind.task,
                goal="ask for food",
                role_prompt="What would you like?",
                target_phrases=["I want milk."],
                accepted_keywords=["milk", "bread"],
                hint_en="Say: I want milk.",
                hint_zh="说：I want milk.",
                retry_prompt="Try saying what you want.",
                max_attempts=2,
                next_step="step_3",
                allow_skip=True,
            ),
            SceneStep(
                step_id="step_3",
                kind=StepKind.free_expression,
                goal="say a preference",
                role_prompt="What do you like?",
                target_phrases=["I like blue."],
                accepted_keywords=["blue", "red"],
                hint_en="Say: I like blue.",
                hint_zh="说：I like blue.",
                retry_prompt="Try saying what you like.",
                max_attempts=2,
                next_step="step_4",
                allow_skip=True,
            ),
            SceneStep(
                step_id="step_4",
                kind=StepKind.goodbye,
                goal="say goodbye",
                role_prompt="Goodbye, have a nice day!",
                target_phrases=["goodbye"],
                accepted_keywords=["goodbye", "bye"],
                hint_en="Say: goodbye",
                hint_zh="说：goodbye",
                retry_prompt="Try saying goodbye.",
                max_attempts=2,
                next_step=None,
                allow_skip=True,
            ),
        ]
    return SceneSpec(
        scene_id="scene_test",
        theme=theme,
        difficulty=difficulty,
        title="Test Scene",
        setting="at home",
        role="Mom",
        goal="practice a daily task",
        steps=steps,
        target_expressions=["I want milk.", "I like blue."],
        safety_notes=["Reviewed for children."],
    )
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python -m pytest tests/test_schemas.py tests/test_content.py -v`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas.py backend/app/content.py backend/app/content/life_themes.yaml tests/factories.py tests/test_schemas.py tests/test_content.py
git commit -m "feat: add domain schemas and life theme catalog"
```

---

### Task 3: HMAC Scene Envelopes

**Files:**
- Create: `backend/app/signature.py`
- Test: `tests/test_signature.py`

**Interfaces:**
- Consumes: `SceneSpec`, `SceneEnvelope` from Task 2.
- Produces: `make_envelope(scene: SceneSpec, ttl_seconds: int, now: datetime | None = None) -> SceneEnvelope`, `sign_envelope(envelope: SceneEnvelope, secret: str) -> str`, `verify_envelope(envelope: SceneEnvelope, signature: str, secret: str, now: datetime | None = None) -> None`, and `SceneSignatureError`.

- [ ] **Step 1: Write the failing signature tests**

Create `tests/test_signature.py`:

```python
from datetime import UTC, datetime, timedelta

import pytest

from app.signature import (
    SceneSignatureError,
    make_envelope,
    sign_envelope,
    verify_envelope,
)
from tests.factories import make_scene


def test_valid_signature_round_trip():
    now = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)
    envelope = make_envelope(make_scene(), ttl_seconds=3600, now=now)
    signature = sign_envelope(envelope, "secret")
    verify_envelope(envelope, signature, "secret", now=now)


def test_tampered_scene_is_rejected():
    now = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)
    envelope = make_envelope(make_scene(), ttl_seconds=3600, now=now)
    signature = sign_envelope(envelope, "secret")
    tampered = envelope.model_copy(
        update={"scene": envelope.scene.model_copy(update={"title": "Changed"})}
    )
    with pytest.raises(SceneSignatureError):
        verify_envelope(tampered, signature, "secret", now=now)


def test_expired_envelope_is_rejected():
    issued = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)
    envelope = make_envelope(make_scene(), ttl_seconds=60, now=issued)
    signature = sign_envelope(envelope, "secret")
    with pytest.raises(SceneSignatureError):
        verify_envelope(
            envelope,
            signature,
            "secret",
            now=issued + timedelta(seconds=61),
        )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_signature.py -v`

Expected: FAIL because `app.signature` does not exist.

- [ ] **Step 3: Implement HMAC signing and verification**

Create `backend/app/signature.py`:

```python
import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta

from app.schemas import SceneEnvelope, SceneSpec


class SceneSignatureError(ValueError):
    """Raised when a signed scene is invalid, expired, or tampered with."""


def make_envelope(
    scene: SceneSpec,
    ttl_seconds: int,
    now: datetime | None = None,
) -> SceneEnvelope:
    issued_at = now or datetime.now(UTC)
    return SceneEnvelope(
        scene=scene,
        issued_at=issued_at,
        expires_at=issued_at + timedelta(seconds=ttl_seconds),
    )


def canonical_json(envelope: SceneEnvelope) -> bytes:
    return json.dumps(
        envelope.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sign_envelope(envelope: SceneEnvelope, secret: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        canonical_json(envelope),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def verify_envelope(
    envelope: SceneEnvelope,
    signature: str,
    secret: str,
    now: datetime | None = None,
) -> None:
    expected = sign_envelope(envelope, secret)
    try:
        expected_bytes = expected.encode("ascii")
        signature_bytes = signature.encode("ascii")
    except UnicodeEncodeError as exc:
        raise SceneSignatureError("invalid signature") from exc
    if not hmac.compare_digest(expected_bytes, signature_bytes):
        raise SceneSignatureError("invalid signature")
    current = now or datetime.now(UTC)
    if envelope.expires_at <= current:
        raise SceneSignatureError("scene expired")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_signature.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/signature.py tests/test_signature.py
git commit -m "feat: add signed scene envelopes"
```

---

### Task 4: Safety Checks and Scene Validation

**Files:**
- Create: `backend/app/safety.py`
- Create: `backend/app/scene_validator.py`
- Test: `tests/test_safety.py`
- Test: `tests/test_scene_validator.py`

**Interfaces:**
- Consumes: `SceneSpec`, `SceneStep`, `StepKind`, `Difficulty`, `PROFILES`.
- Produces: `SafetyValidator.violations(text: str) -> list[str]`, `SceneValidator.validate(scene: SceneSpec) -> None`, and `SceneValidationError(issues: list[str])`.

- [ ] **Step 1: Write the failing safety and validation tests**

Create `tests/test_safety.py`:

```python
from app.safety import SafetyValidator


def test_blocks_violence_and_personal_information_requests():
    safety = SafetyValidator()
    assert safety.violations("Show me your gun and blood.")
    assert safety.violations("What is your home address?")
    assert safety.violations("Send me a photo of your school.")


def test_allows_normal_child_friendly_text():
    safety = SafetyValidator()
    assert safety.violations("Let's buy an apple at the shop.") == []
```

Create `tests/test_scene_validator.py`:

```python
import pytest

from app.scene_validator import SceneValidationError, SceneValidator
from app.schemas import Difficulty, StepKind
from tests.factories import make_scene


def test_valid_scene_passes():
    SceneValidator().validate(make_scene(difficulty=Difficulty.sprout))


def test_scene_must_start_with_greeting_and_end_with_goodbye():
    scene = make_scene()
    scene.steps[0] = scene.steps[0].model_copy(update={"kind": StepKind.task})
    with pytest.raises(SceneValidationError):
        SceneValidator().validate(scene)


def test_scene_must_have_a_free_expression_step():
    scene = make_scene()
    for index, step in enumerate(scene.steps):
        scene.steps[index] = step.model_copy(update={"kind": StepKind.task})
    scene.steps[-1] = scene.steps[-1].model_copy(update={"kind": StepKind.goodbye})
    with pytest.raises(SceneValidationError):
        SceneValidator().validate(scene)


def test_sprout_target_phrase_cannot_exceed_three_words():
    scene = make_scene(difficulty=Difficulty.sprout)
    scene.steps[1] = scene.steps[1].model_copy(
        update={"target_phrases": ["I would like some milk please"]}
    )
    with pytest.raises(SceneValidationError):
        SceneValidator().validate(scene)


def test_broken_next_step_chain_is_rejected():
    scene = make_scene()
    scene.steps[1] = scene.steps[1].model_copy(update={"next_step": "step_4"})
    with pytest.raises(SceneValidationError):
        SceneValidator().validate(scene)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_safety.py tests/test_scene_validator.py -v`

Expected: FAIL because `app.safety` and `app.scene_validator` do not exist.

- [ ] **Step 3: Implement safety and validation**

Create `backend/app/safety.py`:

```python
import re
from typing import ClassVar


class SafetyValidator:
    VIOLENCE_HORROR_PATTERNS: ClassVar[tuple[str, ...]] = (
        r"\b(kill|killing|killed|murder|fight|fighting|attack|attacking|gun|guns|knife|knives|weapon|weapons|blood|bloody|horror|nightmare|nightmares)\b",
    )
    ADULT_PATTERNS: ClassVar[tuple[str, ...]] = (
        r"\b(beer|wine|alcohol|drunk|smoke|smoking|cigarette|cigarettes|naked|sex|sexual|adult|adults)\b",
    )
    DISCRIMINATION_PATTERNS: ClassVar[tuple[str, ...]] = (
        r"\b(racist|racism|sexist|sexism|discrimination|discriminate)\b",
        r"\b(inferior|superior race)\b",
        r"\b(boys|girls)\s+(are|is)\s+(better|worse)\b",
        r"\b(boys|girls)\s+(cannot|can't|cant)\b",
        r"\bhate\s+(boys|girls|people|women|men|children)\b",
    )
    BRAND_PROMOTION_PATTERNS: ClassVar[tuple[str, ...]] = (
        r"\b(buy now|discount|subscribe|sponsored|brand|best brand)\b",
        r"\b(coca[- ]?cola|pepsi|mcdonald(?:'s|s)?|nike|adidas|disney)\b",
    )
    PERSONAL_INFORMATION_PATTERNS: ClassVar[tuple[str, ...]] = (
        r"\b(your (full|real) name|your name|your school|your (home )?address|your phone( number)?|your email( address)?|your birthday)\b",
        r"\b(what(?:'s| is) your (full |real |home )?(name|address|phone( number)?|email( address)?|birthday))\b",
        r"\b(send (me )?a (photo|picture))\b",
        r"\b(where do you live)\b",
        r"\b((what|which) school do you (go to|attend)|what(?:'s| is) your school('s name)?)\b",
    )
    BANNED_PATTERNS: ClassVar[tuple[str, ...]] = (
        *VIOLENCE_HORROR_PATTERNS,
        *ADULT_PATTERNS,
        *DISCRIMINATION_PATTERNS,
        *BRAND_PROMOTION_PATTERNS,
        *PERSONAL_INFORMATION_PATTERNS,
    )

    def violations(self, text: str) -> list[str]:
        normalized = text.lower()
        return [
            pattern
            for pattern in self.BANNED_PATTERNS
            if re.search(pattern, normalized, flags=re.IGNORECASE)
        ]
```

Create `backend/app/scene_validator.py`:

```python
import re

from app.content import PROFILES
from app.safety import SafetyValidator
from app.schemas import SceneSpec, StepKind


class SceneValidationError(ValueError):
    def __init__(self, issues: list[str]):
        super().__init__("; ".join(issues))
        self.issues = issues


def count_sentences(text: str) -> int:
    return max(1, len(re.findall(r"[.!?]+", text)))


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", text))


class SceneValidator:
    def __init__(self, safety: SafetyValidator | None = None):
        self.safety = safety or SafetyValidator()

    def validate(self, scene: SceneSpec) -> None:
        issues: list[str] = []
        profile = PROFILES[scene.difficulty]

        if not (profile.min_steps <= len(scene.steps) <= profile.max_steps):
            issues.append(
                f"step count must be {profile.min_steps}-{profile.max_steps}, "
                f"got {len(scene.steps)}"
            )
        if scene.steps[0].kind is not StepKind.greeting:
            issues.append("first step must be greeting")
        if scene.steps[-1].kind is not StepKind.goodbye:
            issues.append("last step must be goodbye")
        free_count = sum(
            step.kind is StepKind.free_expression for step in scene.steps
        )
        if free_count < profile.free_expression_turns:
            issues.append(
                "scene must contain at least "
                f"{profile.free_expression_turns} free_expression steps"
            )

        ids = [step.step_id for step in scene.steps]
        if len(ids) != len(set(ids)):
            issues.append("step ids must be unique")
        for index, step in enumerate(scene.steps):
            if step.step_id != f"step_{index + 1}":
                issues.append("step ids must be step_1, step_2, ... in order")
            expected_next = f"step_{index + 2}" if index + 1 < len(scene.steps) else None
            if step.next_step != expected_next:
                issues.append(f"{step.step_id} next_step must be {expected_next}")
            for phrase in step.target_phrases:
                if word_count(phrase) > profile.max_target_words:
                    issues.append(
                        f"{step.step_id} target phrase is too long for "
                        f"{scene.difficulty.value}"
                    )
            if count_sentences(step.role_prompt) > profile.max_reply_sentences:
                issues.append(
                    f"{step.step_id} role_prompt is too long for "
                    f"{scene.difficulty.value}"
                )
            for value in [
                step.goal,
                step.role_prompt,
                step.hint_en,
                step.hint_zh,
                step.retry_prompt,
                *step.target_phrases,
                *step.accepted_keywords,
            ]:
                if self.safety.violations(value):
                    issues.append(f"{step.step_id} contains unsafe content")

        for value in [
            scene.title,
            scene.setting,
            scene.role,
            scene.goal,
            *scene.target_expressions,
            *scene.safety_notes,
        ]:
            if self.safety.violations(value):
                issues.append("scene metadata contains unsafe content")

        if issues:
            raise SceneValidationError(issues)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_safety.py tests/test_scene_validator.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/safety.py backend/app/scene_validator.py tests/test_safety.py tests/test_scene_validator.py
git commit -m "feat: validate scene structure and child safety"
```

---

### Task 5: Fallback Scenes and Theme Selection

**Files:**
- Create: `backend/app/content/fallback_scenes.yaml`
- Create: `backend/app/fallback_scenes.py`
- Create: `backend/app/theme_selector.py`
- Test: `tests/test_fallback_scenes.py`
- Test: `tests/test_theme_selector.py`

**Interfaces:**
- Consumes: `Difficulty`, `ThemeId`, `SceneSpec`, `SceneStep`, `StepKind`, `PROFILES`, `ThemeCatalog`.
- Produces: `FallbackSceneFactory.build(theme_id: ThemeId, difficulty: Difficulty) -> SceneSpec` and `ThemeSelector.select(recent_themes: list[ThemeId]) -> ThemeId`.

- [ ] **Step 1: Write the failing fallback and selector tests**

Create `tests/test_fallback_scenes.py`:

```python
import pytest

from app.fallback_scenes import FallbackSceneFactory
from app.scene_validator import SceneValidator
from app.schemas import Difficulty, ThemeId


@pytest.mark.parametrize("difficulty", list(Difficulty))
@pytest.mark.parametrize("theme", list(ThemeId))
def test_all_eighteen_fallbacks_validate(theme, difficulty):
    scene = FallbackSceneFactory().build(theme, difficulty)
    SceneValidator().validate(scene)
    assert scene.theme is theme
    assert scene.difficulty is difficulty


def test_fallback_step_chain_is_fixed():
    scene = FallbackSceneFactory().build(ThemeId.family, Difficulty.explorer)
    assert scene.steps[0].step_id == "step_1"
    assert scene.steps[0].next_step == "step_2"
    assert scene.steps[-1].next_step is None
```

Create `tests/test_theme_selector.py`:

```python
import random

from app.schemas import ThemeId
from app.theme_selector import ThemeSelector


def test_selector_avoids_recent_themes():
    selector = ThemeSelector(theme_ids=list(ThemeId), rng=random.Random(7))
    recent = [ThemeId.family, ThemeId.school]
    for _ in range(20):
        assert selector.select(recent) not in recent


def test_selector_falls_back_when_all_themes_are_recent():
    selector = ThemeSelector(theme_ids=[ThemeId.family], rng=random.Random(1))
    assert selector.select([ThemeId.family]) is ThemeId.family
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_fallback_scenes.py tests/test_theme_selector.py -v`

Expected: FAIL because the fallback factory and selector do not exist.

- [ ] **Step 3: Implement the fallback factory and theme selector**

Create `backend/app/fallback_scenes.py`:

```python
from pathlib import Path
from uuid import uuid4

import yaml
from pydantic import BaseModel, Field

from app.content import PROFILES
from app.schemas import Difficulty, SceneSpec, SceneStep, StepKind, ThemeId

CONTENT_DIR = Path(__file__).resolve().parent / "content"


class FallbackStepTemplate(BaseModel):
    kind: StepKind
    goal: str
    role_prompt: str
    targets: dict[Difficulty, list[str]]
    keywords: list[str]
    hints: dict[Difficulty, str]
    hints_zh: dict[Difficulty, str]
    retry_prompt: str


class FallbackSceneTemplate(BaseModel):
    theme: ThemeId
    title: str
    setting: str
    role: str
    goal: str
    expressions: dict[Difficulty, list[str]]
    steps: list[FallbackStepTemplate] = Field(min_length=4, max_length=7)


class FallbackCatalog(BaseModel):
    templates: list[FallbackSceneTemplate] = Field(min_length=6, max_length=6)


class FallbackSceneFactory:
    def __init__(self, path: Path | None = None):
        source = path or CONTENT_DIR / "fallback_scenes.yaml"
        with source.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle)
        self.catalog = FallbackCatalog.model_validate(payload)

    def build(self, theme_id: ThemeId, difficulty: Difficulty) -> SceneSpec:
        template = next(
            item for item in self.catalog.templates if item.theme is theme_id
        )
        profile = PROFILES[difficulty]
        raw_steps = list(template.steps)
        free_template = next(
            step for step in template.steps
            if step.kind is StepKind.free_expression
        )
        free_count = sum(
            step.kind is StepKind.free_expression for step in raw_steps
        )
        while (
            free_count < profile.free_expression_turns
            or len(raw_steps) < profile.min_steps
        ):
            padding = free_template.model_copy(
                update={
                    "goal": "practice free expression once more",
                    "role_prompt": "Can you tell me one more thing?",
                }
            )
            raw_steps.insert(len(raw_steps) - 1, padding)
            free_count += 1

        steps: list[SceneStep] = []
        for index, raw in enumerate(raw_steps, start=1):
            next_step = f"step_{index + 1}" if index < len(raw_steps) else None
            steps.append(
                SceneStep(
                    step_id=f"step_{index}",
                    kind=raw.kind,
                    goal=raw.goal,
                    role_prompt=raw.role_prompt,
                    target_phrases=raw.targets[difficulty],
                    accepted_keywords=raw.keywords,
                    hint_en=raw.hints[difficulty],
                    hint_zh=raw.hints_zh[difficulty],
                    retry_prompt=raw.retry_prompt,
                    max_attempts=profile.max_attempts,
                    next_step=next_step,
                    allow_skip=True,
                )
            )
        return SceneSpec(
            scene_id=f"fallback_{theme_id.value}_{difficulty.value}_{uuid4().hex[:8]}",
            theme=theme_id,
            difficulty=difficulty,
            title=template.title,
            setting=template.setting,
            role=template.role,
            goal=template.goal,
            steps=steps,
            target_expressions=template.expressions[difficulty],
            safety_notes=["Reviewed fallback scene for children."],
        )
```

Create `backend/app/theme_selector.py`:

```python
import random

from app.schemas import ThemeId


class ThemeSelector:
    def __init__(self, theme_ids: list[ThemeId], rng: random.Random | None = None):
        if not theme_ids:
            raise ValueError("theme_ids must not be empty")
        self.theme_ids = list(theme_ids)
        self.rng = rng or random.Random()

    def select(self, recent_themes: list[ThemeId]) -> ThemeId:
        recent = recent_themes[-2:]
        candidates = [theme for theme in self.theme_ids if theme not in recent]
        if not candidates:
            candidates = self.theme_ids
        return self.rng.choice(candidates)
```

- [ ] **Step 4: Add the six reviewed fallback templates**

Create `backend/app/content/fallback_scenes.yaml` with the following content. The file contains exactly six `templates`, one per theme, and every template has four steps: greeting, task, free_expression, goodbye.

```yaml
templates:
  - theme: family
    title: Morning Helpers
    setting: in the kitchen
    role: Mom
    goal: ask for breakfast and get ready for school
    expressions:
      sprout: [milk, bag]
      explorer: ["I want milk.", "My bag is here."]
      star: ["I would like some milk, please.", "I put my book in my schoolbag."]
    steps:
      - kind: greeting
        goal: greet the child
        role_prompt: Good morning, are you ready for breakfast?
        targets:
          sprout: ["yes"]
          explorer: ["Yes, I am ready."]
          star: ["Yes, I am ready for breakfast."]
        keywords: ["yes", "ready"]
        hints:
          sprout: "Say: yes"
          explorer: "Say: Yes, I am ready."
          star: "Say: Yes, I am ready for breakfast."
        hints_zh:
          sprout: "说：yes"
          explorer: "说：Yes, I am ready."
          star: "说：Yes, I am ready for breakfast."
        retry_prompt: Try saying yes.
      - kind: task
        goal: ask for breakfast
        role_prompt: What would you like for breakfast?
        targets:
          sprout: [milk]
          explorer: ["I want milk."]
          star: ["I would like some milk, please."]
        keywords: [milk, bread, egg]
        hints:
          sprout: "Say: milk"
          explorer: "Say: I want milk."
          star: "Say: I would like some milk, please."
        hints_zh:
          sprout: "说：milk"
          explorer: "说：I want milk."
          star: "说：I would like some milk, please."
        retry_prompt: Try saying what you want.
      - kind: free_expression
        goal: say one more thing about the morning
        role_prompt: What do you like to eat with milk?
        targets:
          sprout: [bread]
          explorer: ["I like bread."]
          star: ["I like bread with milk."]
        keywords: [bread, cake, egg]
        hints:
          sprout: "Say: bread"
          explorer: "Say: I like bread."
          star: "Say: I like bread with milk."
        hints_zh:
          sprout: "说：bread"
          explorer: "说：I like bread."
          star: "说：I like bread with milk."
        retry_prompt: Try saying what you like.
      - kind: goodbye
        goal: say goodbye
        role_prompt: Have a good day at school!
        targets:
          sprout: [bye]
          explorer: ["Goodbye!"]
          star: ["Goodbye! Have a nice day!"]
        keywords: [bye, goodbye]
        hints:
          sprout: "Say: bye"
          explorer: "Say: Goodbye!"
          star: "Say: Goodbye! Have a nice day!"
        hints_zh:
          sprout: "说：bye"
          explorer: "说：Goodbye!"
          star: "说：Goodbye! Have a nice day!"
        retry_prompt: Try saying goodbye.

  - theme: school
    title: Library Helper
    setting: in the school library
    role: Teacher
    goal: borrow a book and speak quietly
    expressions:
      sprout: [book, quiet]
      explorer: ["This is my book.", "I will be quiet."]
      star: ["May I borrow this book, please?", "I will keep quiet in the library."]
    steps:
      - kind: greeting
        goal: greet the teacher
        role_prompt: Hello, welcome to the library!
        targets:
          sprout: [hello]
          explorer: ["Hello!"]
          star: ["Hello, thank you for welcoming me."]
        keywords: [hello, hi]
        hints:
          sprout: "Say: hello"
          explorer: "Say: Hello!"
          star: "Say: Hello, thank you for welcoming me."
        hints_zh:
          sprout: "说：hello"
          explorer: "说：Hello!"
          star: "说：Hello, thank you for welcoming me."
        retry_prompt: Try saying hello.
      - kind: task
        goal: ask to borrow a book
        role_prompt: Which book would you like to borrow?
        targets:
          sprout: [book]
          explorer: ["I want this book."]
          star: ["May I borrow this book, please?"]
        keywords: [book, story, animal]
        hints:
          sprout: "Say: book"
          explorer: "Say: I want this book."
          star: "Say: May I borrow this book, please?"
        hints_zh:
          sprout: "说：book"
          explorer: "说：I want this book."
          star: "说：May I borrow this book, please?"
        retry_prompt: Try saying which book you want.
      - kind: free_expression
        goal: say how to behave in the library
        role_prompt: How should we behave in the library?
        targets:
          sprout: [quiet]
          explorer: ["We are quiet."]
          star: ["We should be quiet in the library."]
        keywords: [quiet, whisper, read]
        hints:
          sprout: "Say: quiet"
          explorer: "Say: We are quiet."
          star: "Say: We should be quiet in the library."
        hints_zh:
          sprout: "说：quiet"
          explorer: "说：We are quiet."
          star: "说：We should be quiet in the library."
        retry_prompt: Try saying how to behave.
      - kind: goodbye
        goal: say goodbye
        role_prompt: Enjoy your book!
        targets:
          sprout: [thanks]
          explorer: ["Thank you!"]
          star: ["Thank you, I will enjoy it."]
        keywords: [thanks, thank]
        hints:
          sprout: "Say: thanks"
          explorer: "Say: Thank you!"
          star: "Say: Thank you, I will enjoy it."
        hints_zh:
          sprout: "说：thanks"
          explorer: "说：Thank you!"
          star: "说：Thank you, I will enjoy it."
        retry_prompt: Try saying thank you.

  - theme: shopping
    title: Bakery Visit
    setting: in a bakery
    role: Baker
    goal: buy bread and ask about the price
    expressions:
      sprout: [bread, apple]
      explorer: ["I want bread.", "How much is it?"]
      star: ["I would like to buy some bread, please.", "Could you tell me how much it is?"]
    steps:
      - kind: greeting
        goal: greet the baker
        role_prompt: Hello, welcome to the bakery!
        targets:
          sprout: [hello]
          explorer: ["Hello!"]
          star: ["Hello, the bakery smells wonderful."]
        keywords: [hello, hi]
        hints:
          sprout: "Say: hello"
          explorer: "Say: Hello!"
          star: "Say: Hello, the bakery smells wonderful."
        hints_zh:
          sprout: "说：hello"
          explorer: "说：Hello!"
          star: "说：Hello, the bakery smells wonderful."
        retry_prompt: Try saying hello.
      - kind: task
        goal: ask for bread
        role_prompt: What would you like to buy?
        targets:
          sprout: [bread]
          explorer: ["I want bread."]
          star: ["I would like to buy some bread, please."]
        keywords: [bread, cake, cookie]
        hints:
          sprout: "Say: bread"
          explorer: "Say: I want bread."
          star: "Say: I would like to buy some bread, please."
        hints_zh:
          sprout: "说：bread"
          explorer: "说：I want bread."
          star: "说：I would like to buy some bread, please."
        retry_prompt: Try saying what you want.
      - kind: free_expression
        goal: ask about the price
        role_prompt: Would you like to know the price?
        targets:
          sprout: [how much]
          explorer: ["How much is it?"]
          star: ["Could you tell me how much it is?"]
        keywords: [much, price, cost]
        hints:
          sprout: "Say: how much"
          explorer: "Say: How much is it?"
          star: "Say: Could you tell me how much it is?"
        hints_zh:
          sprout: "说：how much"
          explorer: "说：How much is it?"
          star: "说：Could you tell me how much it is?"
        retry_prompt: Try asking about the price.
      - kind: goodbye
        goal: say thank you
        role_prompt: Here you are!
        targets:
          sprout: [thanks]
          explorer: ["Thank you!"]
          star: ["Thank you very much. Goodbye!"]
        keywords: [thanks, thank]
        hints:
          sprout: "Say: thanks"
          explorer: "Say: Thank you!"
          star: "Say: Thank you very much. Goodbye!"
        hints_zh:
          sprout: "说：thanks"
          explorer: "说：Thank you!"
          star: "说：Thank you very much. Goodbye!"
        retry_prompt: Try saying thank you.
```

The file continues with the food, transport, and friends templates in the next edit.

Append this fragment to the same `fallback_scenes.yaml` file:

```yaml
  - theme: food
    title: Snack Time
    setting: at a snack shop
    role: Shopkeeper
    goal: order a snack and a drink
    expressions:
      sprout: [juice, rice]
      explorer: ["I want juice.", "I like rice."]
      star: ["I would like some juice and rice, please.", "I prefer apple juice."]
    steps:
      - kind: greeting
        goal: greet the shopkeeper
        role_prompt: Hello, what would you like today?
        targets:
          sprout: [hello]
          explorer: ["Hello!"]
          star: ["Hello, I would like something to eat."]
        keywords: [hello, hi]
        hints:
          sprout: "Say: hello"
          explorer: "Say: Hello!"
          star: "Say: Hello, I would like something to eat."
        hints_zh:
          sprout: "说：hello"
          explorer: "说：Hello!"
          star: "说：Hello, I would like something to eat."
        retry_prompt: Try saying hello.
      - kind: task
        goal: order a drink
        role_prompt: What would you like to drink?
        targets:
          sprout: [juice]
          explorer: ["I want juice."]
          star: ["I would like some apple juice, please."]
        keywords: [juice, milk, water]
        hints:
          sprout: "Say: juice"
          explorer: "Say: I want juice."
          star: "Say: I would like some apple juice, please."
        hints_zh:
          sprout: "说：juice"
          explorer: "说：I want juice."
          star: "说：I would like some apple juice, please."
        retry_prompt: Try saying what you want to drink.
      - kind: free_expression
        goal: say what food you like
        role_prompt: What would you like to eat?
        targets:
          sprout: [rice]
          explorer: ["I like rice."]
          star: ["I would like some rice with vegetables."]
        keywords: [rice, noodles, fruit]
        hints:
          sprout: "Say: rice"
          explorer: "Say: I like rice."
          star: "Say: I would like some rice with vegetables."
        hints_zh:
          sprout: "说：rice"
          explorer: "说：I like rice."
          star: "说：I would like some rice with vegetables."
        retry_prompt: Try saying what you like to eat.
      - kind: goodbye
        goal: say thank you
        role_prompt: Here is your food!
        targets:
          sprout: [thanks]
          explorer: ["Thank you!"]
          star: ["Thank you, it looks delicious!"]
        keywords: [thanks, thank]
        hints:
          sprout: "Say: thanks"
          explorer: "Say: Thank you!"
          star: "Say: Thank you, it looks delicious!"
        hints_zh:
          sprout: "说：thanks"
          explorer: "说：Thank you!"
          star: "说：Thank you, it looks delicious!"
        retry_prompt: Try saying thank you.

  - theme: transport
    title: Bus to the Park
    setting: at a bus stop
    role: Parent
    goal: talk about going to the park by bus
    expressions:
      sprout: [bus, park]
      explorer: ["Let's take the bus.", "I want to go to the park."]
      star: ["Shall we take the bus to the park?", "How long does it take to get there?"]
    steps:
      - kind: greeting
        goal: greet the parent
        role_prompt: Are you ready to go to the park?
        targets:
          sprout: ["yes"]
          explorer: ["Yes, I am ready."]
          star: ["Yes, I am ready to go to the park."]
        keywords: ["yes", "ready"]
        hints:
          sprout: "Say: yes"
          explorer: "Say: Yes, I am ready."
          star: "Say: Yes, I am ready to go to the park."
        hints_zh:
          sprout: "说：yes"
          explorer: "说：Yes, I am ready."
          star: "说：Yes, I am ready to go to the park."
        retry_prompt: Try saying yes.
      - kind: task
        goal: choose the bus
        role_prompt: How shall we go to the park?
        targets:
          sprout: [bus]
          explorer: ["Let's take the bus."]
          star: ["Shall we take the bus to the park?"]
        keywords: [bus, walk, bike]
        hints:
          sprout: "Say: bus"
          explorer: "Say: Let's take the bus."
          star: "Say: Shall we take the bus to the park?"
        hints_zh:
          sprout: "说：bus"
          explorer: "说：Let's take the bus."
          star: "说：Shall we take the bus to the park?"
        retry_prompt: Try saying how to go.
      - kind: free_expression
        goal: say what to do at the park
        role_prompt: What would you like to do at the park?
        targets:
          sprout: [play]
          explorer: ["I want to play."]
          star: ["I would like to play on the swing."]
        keywords: [play, swing, slide]
        hints:
          sprout: "Say: play"
          explorer: "Say: I want to play."
          star: "Say: I would like to play on the swing."
        hints_zh:
          sprout: "说：play"
          explorer: "说：I want to play."
          star: "说：I would like to play on the swing."
        retry_prompt: Try saying what you want to do.
      - kind: goodbye
        goal: respond to the bus arriving
        role_prompt: The bus is coming!
        targets:
          sprout: [ok]
          explorer: ["Okay, let's go!"]
          star: ["Great, let's get on the bus!"]
        keywords: [ok, okay, go]
        hints:
          sprout: "Say: ok"
          explorer: "Say: Okay, let's go!"
          star: "Say: Great, let's get on the bus!"
        hints_zh:
          sprout: "说：ok"
          explorer: "说：Okay, let's go!"
          star: "说：Great, let's get on the bus!"
        retry_prompt: Try saying okay.
```

Append this final fragment to the same `fallback_scenes.yaml` file:

```yaml
  - theme: friends
    title: Meet a New Friend
    setting: at the playground
    role: A friendly child
    goal: greet a new friend and invite them to play
    expressions:
      sprout: [hello, play]
      explorer: ["Hello, I am happy.", "Let's play together."]
      star: ["Hello, it is nice to meet you.", "Would you like to play with me?"]
    steps:
      - kind: greeting
        goal: greet the new friend
        role_prompt: Hi, I am new here!
        targets:
          sprout: [hello]
          explorer: ["Hello!"]
          star: ["Hello, it is nice to meet you."]
        keywords: [hello, hi]
        hints:
          sprout: "Say: hello"
          explorer: "Say: Hello!"
          star: "Say: Hello, it is nice to meet you."
        hints_zh:
          sprout: "说：hello"
          explorer: "说：Hello!"
          star: "说：Hello, it is nice to meet you."
        retry_prompt: Try saying hello.
      - kind: task
        goal: share an interest
        role_prompt: What do you like to do?
        targets:
          sprout: [play]
          explorer: ["I like to play."]
          star: ["I like drawing and playing football."]
        keywords: [play, draw, football]
        hints:
          sprout: "Say: play"
          explorer: "Say: I like to play."
          star: "Say: I like drawing and playing football."
        hints_zh:
          sprout: "说：play"
          explorer: "说：I like to play."
          star: "说：I like drawing and playing football."
        retry_prompt: Try saying what you like.
      - kind: free_expression
        goal: invite the friend to play
        role_prompt: Would you like to play with me?
        targets:
          sprout: ["yes"]
          explorer: ["Yes, let's play!"]
          star: ["Yes, I would love to play with you."]
        keywords: [yes, play]
        hints:
          sprout: "Say: yes"
          explorer: "Say: Yes, let's play!"
          star: "Say: Yes, I would love to play with you."
        hints_zh:
          sprout: "说：yes"
          explorer: "说：Yes, let's play!"
          star: "说：Yes, I would love to play with you."
        retry_prompt: Try saying yes.
      - kind: goodbye
        goal: say goodbye
        role_prompt: See you later!
        targets:
          sprout: [bye]
          explorer: ["See you!"]
          star: ["See you later, it was fun!"]
        keywords: [bye, see]
        hints:
          sprout: "Say: bye"
          explorer: "Say: See you!"
          star: "Say: See you later, it was fun!"
        hints_zh:
          sprout: "说：bye"
          explorer: "说：See you!"
          star: "说：See you later, it was fun!"
        retry_prompt: Try saying goodbye.
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest tests/test_fallback_scenes.py tests/test_theme_selector.py -v`

Expected: PASS for all 18 fallback combinations and both selector tests.

- [ ] **Step 6: Commit**

```bash
git add backend/app/content/fallback_scenes.yaml backend/app/fallback_scenes.py backend/app/theme_selector.py tests/test_fallback_scenes.py tests/test_theme_selector.py
git commit -m "feat: add reviewed fallback scenes and theme selection"
```

---

### Task 6: Provider Interfaces, Fake Providers, and Prompts

**Files:**
- Create: `backend/app/providers/__init__.py`
- Create: `backend/app/providers/base.py`
- Create: `backend/app/providers/fake.py`
- Create: `backend/app/prompts.py`
- Test: `tests/test_providers_fake.py`

**Interfaces:**
- Consumes: `SceneSpec`, `SceneStep`, `TurnSummary`, `Difficulty`, `ThemeId`, `ThemeDefinition`, `DifficultyProfile`.
- Produces: `ASRResult`, `TTSResult`, `ProviderError`, `ASRProvider`, `LLMProvider`, `TTSProvider`, `PronunciationProvider`, `FakeASRProvider`, `FakeLLMProvider`, `FakeTTSProvider`, `FakePronunciationProvider`, `make_silence_wav`, `SCENE_SYSTEM_PROMPT`, `build_scene_prompt`, `TURN_SYSTEM_PROMPT`, `build_turn_prompt`.

- [ ] **Step 1: Write the failing fake-provider tests**

Create `tests/test_providers_fake.py`:

```python
import io
import wave

from app.content import PROFILES, load_theme_catalog
from app.prompts import SCENE_SYSTEM_PROMPT, TURN_SYSTEM_PROMPT, build_scene_prompt
from app.providers.fake import (
    FakeASRProvider,
    FakeLLMProvider,
    FakePronunciationProvider,
    FakeTTSProvider,
    make_silence_wav,
)
from app.schemas import Difficulty, ThemeId
from tests.factories import make_scene


async def test_fake_asr_cycles_configured_texts():
    provider = FakeASRProvider(texts=["one", "two"])
    assert (await provider.transcribe(b"audio")).text == "one"
    assert (await provider.transcribe(b"audio")).text == "two"
    assert (await provider.transcribe(b"audio")).text == "one"
    assert (await provider.transcribe(b"")).text == ""


async def test_fake_llm_returns_a_scene_payload():
    catalog = load_theme_catalog()
    provider = FakeLLMProvider(
        scene_factory=lambda theme, difficulty: make_scene(
            theme=theme, difficulty=difficulty
        ).model_dump(mode="json")
    )
    prompt = build_scene_prompt(
        catalog.by_id(ThemeId.family),
        Difficulty.explorer,
        PROFILES[Difficulty.explorer],
    )
    payload = await provider.complete_json(SCENE_SYSTEM_PROMPT, prompt)
    assert payload["theme"] == "family"
    assert payload["difficulty"] == "explorer"


async def test_fake_llm_uses_next_role_prompt_for_turn_reply():
    provider = FakeLLMProvider(scene_factory=lambda theme, difficulty: {})
    payload = await provider.complete_json(
        TURN_SYSTEM_PROMPT,
        "NEXT_ROLE_PROMPT: What would you like?\nCHILD_TEXT: milk",
    )
    assert payload["accepted"] is True
    assert payload["reply"] == "What would you like?"


async def test_fake_tts_returns_a_valid_wav():
    result = await FakeTTSProvider().synthesize("Hello", voice="test", speed=1.0)
    with wave.open(io.BytesIO(result.audio), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getframerate() == 16000
    assert result.media_type == "audio/wav"


async def test_fake_pronunciation_provider_is_available_for_v11():
    result = await FakePronunciationProvider().score(b"wav", "I like blue.")
    assert result["overall"] == 80
    assert result["errors"] == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_providers_fake.py -v`

Expected: FAIL because the provider modules and prompt constants do not exist.

- [ ] **Step 3: Implement provider protocols, fakes, and prompts**

Create `backend/app/providers/__init__.py` with:

```python
"""External service adapters and deterministic local fakes."""
```

Create `backend/app/providers/base.py`:

```python
from dataclasses import dataclass
from typing import Protocol


class ProviderError(RuntimeError):
    """Raised when an external provider fails or returns an invalid response."""


@dataclass(frozen=True)
class ASRResult:
    text: str
    confidence: float | None = None


@dataclass(frozen=True)
class TTSResult:
    audio: bytes
    media_type: str


class ASRProvider(Protocol):
    async def transcribe(self, audio_wav: bytes) -> ASRResult:
        ...


class LLMProvider(Protocol):
    async def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        ...


class TTSProvider(Protocol):
    async def synthesize(self, text: str, voice: str, speed: float) -> TTSResult:
        ...


class PronunciationProvider(Protocol):
    async def score(self, audio_wav: bytes, reference_text: str) -> dict:
        ...
```

Create `backend/app/providers/fake.py`:

```python
import io
import wave
from collections.abc import Callable

from app.providers.base import ASRResult, TTSResult
from app.schemas import Difficulty, ThemeId


def make_silence_wav(seconds: float = 0.25, sample_rate: int = 16000) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * int(seconds * sample_rate))
    return buffer.getvalue()


class FakeASRProvider:
    def __init__(
        self,
        texts: list[str] | None = None,
        default_text: str = "I want milk.",
    ):
        self.texts = texts or [default_text]
        self.index = 0

    async def transcribe(self, audio_wav: bytes) -> ASRResult:
        if not audio_wav:
            return ASRResult(text="", confidence=None)
        text = self.texts[self.index % len(self.texts)]
        self.index += 1
        return ASRResult(text=text, confidence=0.95)


class FakeLLMProvider:
    def __init__(
        self,
        scene_factory: Callable[[ThemeId, Difficulty], dict],
        turn_response: dict | None = None,
    ):
        self.scene_factory = scene_factory
        self.turn_response = turn_response

    async def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        if system_prompt.startswith("SCENE_GENERATION"):
            theme = ThemeId(_line_value(user_prompt, "THEME"))
            difficulty = Difficulty(_line_value(user_prompt, "DIFFICULTY"))
            return self.scene_factory(theme, difficulty)
        next_prompt = _line_value(user_prompt, "NEXT_ROLE_PROMPT")
        return self.turn_response or {
            "accepted": True,
            "feedback": "Great job!",
            "reply": (
                next_prompt
                if next_prompt != "NONE"
                else "Great job! See you next time."
            ),
            "hint": "",
            "next_step": None,
            "stars": 1,
            "safety": "ok",
        }


class FakeTTSProvider:
    async def synthesize(self, text: str, voice: str, speed: float) -> TTSResult:
        return TTSResult(audio=make_silence_wav(0.25), media_type="audio/wav")


class FakePronunciationProvider:
    async def score(self, audio_wav: bytes, reference_text: str) -> dict:
        return {
            "overall": 80,
            "accuracy": 80,
            "fluency": 80,
            "completeness": 100,
            "errors": [],
        }


def _line_value(prompt: str, key: str) -> str:
    prefix = f"{key}:"
    for line in prompt.splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    raise ValueError(f"missing prompt line: {key}")
```

Create `backend/app/prompts.py`:

```python
import json

from app.content import DifficultyProfile, ThemeDefinition
from app.schemas import Difficulty, SceneSpec, SceneStep, TurnSummary


SCENE_SYSTEM_PROMPT = """SCENE_GENERATION
You design safe English speaking tasks for children aged 4-12.
Return ONLY a JSON object. Do not use Markdown or code fences.
The JSON object must match this shape:
{
  "scene_id": "string",
  "theme": "family|school|shopping|food|transport|friends",
  "difficulty": "sprout|explorer|star",
  "title": "string",
  "setting": "string",
  "role": "string",
  "goal": "string",
  "steps": [
    {
      "step_id": "step_1",
      "kind": "greeting|task|free_expression|goodbye",
      "goal": "string",
      "role_prompt": "string",
      "target_phrases": ["string"],
      "accepted_keywords": ["string"],
      "hint_en": "string",
      "hint_zh": "string",
      "retry_prompt": "string",
      "max_attempts": 2,
      "next_step": "step_2",
      "allow_skip": true
    }
  ],
  "target_expressions": ["string"],
  "safety_notes": ["string"]
}
Rules:
- First step kind is greeting. Last step kind is goodbye.
- Include at least one free_expression step.
- Step IDs are step_1, step_2, ... in order.
- Last step next_step is null. Every other next_step points to the next step.
- The scene must be a familiar daily-life task.
- No violence, horror, adult content, discrimination, brand promotion, or requests for personal information.
- The character must never ask for a real name, school, address, phone number, or photo.
"""

TURN_SYSTEM_PROMPT = """TURN_JUDGEMENT
You are a friendly English conversation partner for a child.
Return ONLY a JSON object with exactly these fields:
{
  "accepted": true,
  "feedback": "short positive feedback",
  "reply": "one or two short English sentences",
  "hint": "optional short hint",
  "next_step": "step_2",
  "stars": 1,
  "safety": "ok"
}
Rules:
- Accept an answer if it completes the current step's communicative goal.
- If NEXT_ROLE_PROMPT is not NONE, your reply must naturally include that question or a close paraphrase.
- If the child is off-topic, gently redirect.
- Never ask for a real name, school, address, phone number, or photo.
- Never mention violence, horror, adult content, brands, or personal information.
- Keep feedback positive. Do not use red-error language.
- Reply in English only.
"""


def build_scene_prompt(
    theme: ThemeDefinition,
    difficulty: Difficulty,
    profile: DifficultyProfile,
) -> str:
    return "\n".join(
        [
            f"THEME: {theme.id.value}",
            f"DIFFICULTY: {difficulty.value}",
            f"TARGET_AGE: {profile.target_age}",
            f"TARGET_ANSWER: {profile.target_answer}",
            f"STEP_COUNT: {profile.min_steps} to {profile.max_steps}",
            f"FREE_EXPRESSION_STEPS: at least {profile.free_expression_turns}",
            f"SUBTHEMES: {', '.join(theme.subthemes)}",
            f"SETTING: {theme.setting}",
            f"ROLE: {theme.role}",
            f"GOAL: {theme.goal}",
            "TARGET_EXAMPLES: "
            + json.dumps(theme.target_examples[difficulty], ensure_ascii=False),
            "Create one complete scene now. Use only the theme and difficulty above.",
        ]
    )


def build_turn_prompt(
    scene: SceneSpec,
    step: SceneStep,
    transcript: str,
    attempts: int,
    history: list[TurnSummary],
    next_step: SceneStep | None,
) -> str:
    next_prompt = next_step.role_prompt if next_step else "NONE"
    return "\n".join(
        [
            f"SCENE_TITLE: {scene.title}",
            f"ROLE: {scene.role}",
            f"GOAL: {scene.goal}",
            f"DIFFICULTY: {scene.difficulty.value}",
            f"CURRENT_STEP: {step.step_id}",
            f"STEP_GOAL: {step.goal}",
            f"ROLE_PROMPT: {step.role_prompt}",
            f"TARGET_PHRASES: {json.dumps(step.target_phrases, ensure_ascii=False)}",
            f"ACCEPTED_KEYWORDS: {json.dumps(step.accepted_keywords, ensure_ascii=False)}",
            f"HINT_EN: {step.hint_en}",
            f"ATTEMPTS: {attempts}",
            "HISTORY: "
            + json.dumps([item.model_dump() for item in history], ensure_ascii=False),
            f"NEXT_STEP: {next_step.step_id if next_step else 'NONE'}",
            f"NEXT_ROLE_PROMPT: {next_prompt}",
            f"CHILD_TEXT: {transcript}",
            "Return the JSON object now.",
        ]
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_providers_fake.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/providers/__init__.py backend/app/providers/base.py backend/app/providers/fake.py backend/app/prompts.py tests/test_providers_fake.py
git commit -m "feat: add provider interfaces and deterministic fakes"
```

---

### Task 7: Scene Generator with Retry and Fallback

**Files:**
- Create: `backend/app/scene_generator.py`
- Test: `tests/test_scene_generator.py`

**Interfaces:**
- Consumes: `LLMProvider`, `ThemeCatalog`, `SceneValidator`, `FallbackSceneFactory`, `ThemeSelector`, `SCENE_SYSTEM_PROMPT`, `build_scene_prompt`, `PROFILES`.
- Produces: `GeneratedScene(scene: SceneSpec, fallback_used: bool)` and `SceneGenerator.generate(difficulty: Difficulty, recent_themes: list[ThemeId]) -> GeneratedScene`.

- [ ] **Step 1: Write the failing scene generator tests**

Create `tests/test_scene_generator.py`:

```python
import asyncio
import random

from app.content import PROFILES, load_theme_catalog
from app.fallback_scenes import FallbackSceneFactory
from app.prompts import build_scene_prompt
from app.providers.fake import FakeLLMProvider
from app.scene_generator import SceneGenerator
from app.scene_validator import SceneValidator
from app.schemas import Difficulty, ThemeId
from app.theme_selector import ThemeSelector
from tests.factories import make_scene


def build_generator(llm, recent_seed=7, timeout_seconds=1.0):
    catalog = load_theme_catalog()
    return SceneGenerator(
        llm=llm,
        catalog=catalog,
        validator=SceneValidator(),
        fallback=FallbackSceneFactory(),
        selector=ThemeSelector(list(ThemeId), random.Random(recent_seed)),
        timeout_seconds=timeout_seconds,
    )


async def test_generator_returns_llm_scene_when_valid():
    llm = FakeLLMProvider(
        scene_factory=lambda theme, difficulty: make_scene(
            theme=theme, difficulty=difficulty
        ).model_dump(mode="json")
    )
    generated = await build_generator(llm).generate(
        Difficulty.explorer, [ThemeId.family, ThemeId.school]
    )
    assert generated.fallback_used is False
    assert generated.scene.theme not in {ThemeId.family, ThemeId.school}


async def test_generator_uses_fallback_after_invalid_payloads():
    llm = FakeLLMProvider(scene_factory=lambda theme, difficulty: {"bad": "payload"})
    generated = await build_generator(llm).generate(
        Difficulty.star, [ThemeId.family, ThemeId.school]
    )
    assert generated.fallback_used is True
    SceneValidator().validate(generated.scene)


async def test_generator_uses_fallback_after_timeout():
    class SlowLLM:
        async def complete_json(self, system_prompt, user_prompt):
            await asyncio.sleep(0.05)
            return {}

    generated = await build_generator(SlowLLM(), timeout_seconds=0.001).generate(
        Difficulty.sprout, []
    )
    assert generated.fallback_used is True


async def test_generator_prompt_contains_difficulty_and_theme():
    captured = {}

    class CapturingLLM:
        async def complete_json(self, system_prompt, user_prompt):
            captured["prompt"] = user_prompt
            return make_scene().model_dump(mode="json")

    llm = CapturingLLM()
    generated = await build_generator(llm).generate(Difficulty.explorer, [])
    assert "DIFFICULTY: explorer" in captured["prompt"]
    assert f"THEME: {generated.scene.theme.value}" in captured["prompt"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_scene_generator.py -v`

Expected: FAIL because `app.scene_generator` does not exist.

- [ ] **Step 3: Implement the generator**

Create `backend/app/scene_generator.py`:

```python
import asyncio
from dataclasses import dataclass
from uuid import uuid4

from app.content import PROFILES, ThemeCatalog
from app.fallback_scenes import FallbackSceneFactory
from app.prompts import SCENE_SYSTEM_PROMPT, build_scene_prompt
from app.providers.base import LLMProvider
from app.scene_validator import SceneValidator
from app.schemas import Difficulty, SceneSpec, ThemeId
from app.theme_selector import ThemeSelector


@dataclass(frozen=True)
class GeneratedScene:
    scene: SceneSpec
    fallback_used: bool


class SceneGenerator:
    def __init__(
        self,
        llm: LLMProvider,
        catalog: ThemeCatalog,
        validator: SceneValidator,
        fallback: FallbackSceneFactory,
        selector: ThemeSelector,
        timeout_seconds: float = 8.0,
        max_attempts: int = 2,
    ):
        self.llm = llm
        self.catalog = catalog
        self.validator = validator
        self.fallback = fallback
        self.selector = selector
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts

    async def generate(
        self,
        difficulty: Difficulty,
        recent_themes: list[ThemeId],
    ) -> GeneratedScene:
        theme_id = self.selector.select(recent_themes)
        theme = self.catalog.by_id(theme_id)
        profile = PROFILES[difficulty]
        prompt = build_scene_prompt(theme, difficulty, profile)

        for _ in range(self.max_attempts):
            try:
                payload = await asyncio.wait_for(
                    self.llm.complete_json(SCENE_SYSTEM_PROMPT, prompt),
                    timeout=self.timeout_seconds,
                )
                scene = SceneSpec.model_validate(
                    {
                        **payload,
                        "scene_id": uuid4().hex,
                        "theme": theme_id.value,
                        "difficulty": difficulty.value,
                    }
                )
                self.validator.validate(scene)
                return GeneratedScene(scene=scene, fallback_used=False)
            except Exception:
                continue

        return GeneratedScene(
            scene=self.fallback.build(theme_id, difficulty),
            fallback_used=True,
        )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_scene_generator.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/scene_generator.py tests/test_scene_generator.py
git commit -m "feat: generate scenes with retry and fallback"
```

---

### Task 8: Rule Matching and Dialogue Orchestration

**Files:**
- Create: `backend/app/matching.py`
- Create: `backend/app/dialogue.py`
- Test: `tests/test_matching.py`
- Test: `tests/test_dialogue.py`

**Interfaces:**
- Consumes: `LLMProvider`, `TTSProvider`, `SafetyValidator`, `TurnSummary`, `TurnResponse`, `build_turn_prompt`, `PROFILES`.
- Produces: `normalize_text(text: str) -> str`, `phrase_in_text(phrase: str, text: str) -> bool`, `rule_match(text: str, step: SceneStep, difficulty: Difficulty) -> bool`, `TurnContext`, `DialogueOrchestrator.handle_turn(context: TurnContext) -> TurnResponse`.

- [ ] **Step 1: Write the failing matching and dialogue tests**

Create `tests/test_matching.py`:

```python
from app.matching import rule_match
from app.schemas import Difficulty
from tests.factories import make_scene


def test_exact_target_phrase_matches():
    scene = make_scene()
    assert rule_match("I want milk.", scene.steps[1], Difficulty.explorer)


def test_case_and_punctuation_are_ignored():
    scene = make_scene()
    assert rule_match("I WANT MILK!", scene.steps[1], Difficulty.explorer)


def test_sprout_keyword_matches():
    scene = make_scene(difficulty=Difficulty.sprout)
    assert rule_match("milk", scene.steps[1], Difficulty.sprout)


def test_explorer_keyword_does_not_auto_match():
    scene = make_scene()
    assert not rule_match("milk", scene.steps[1], Difficulty.explorer)
```

Create `tests/test_dialogue.py`:

```python
from app.dialogue import DialogueOrchestrator, TurnContext
from app.providers.fake import FakeLLMProvider, FakeTTSProvider
from app.safety import SafetyValidator
from app.schemas import Difficulty
from tests.factories import make_scene


REJECTED = {
    "accepted": False,
    "feedback": "Nice try!",
    "reply": "Let's try again.",
    "hint": "Say: I want milk.",
    "next_step": "step_2",
    "stars": 1,
    "safety": "ok",
}


def make_orchestrator(llm=None, tts=None):
    return DialogueOrchestrator(
        llm=llm or FakeLLMProvider(scene_factory=lambda theme, difficulty: {}),
        safety=SafetyValidator(),
        tts=tts or FakeTTSProvider(),
        timeout_seconds=1.0,
    )


async def test_accepted_turn_advances_and_earns_two_stars():
    scene = make_scene()
    result = await make_orchestrator().handle_turn(
        TurnContext(scene=scene, current_step_id="step_1", recognized_text="yes")
    )
    assert result.accepted is True
    assert result.next_step == "step_2"
    assert result.stars_earned == 2
    assert result.audio_base64
    assert result.media_type == "audio/wav"


async def test_sprout_keyword_is_accepted():
    scene = make_scene(difficulty=Difficulty.sprout)
    result = await make_orchestrator().handle_turn(
        TurnContext(scene=scene, current_step_id="step_2", recognized_text="milk")
    )
    assert result.accepted is True
    assert result.next_step == "step_3"


async def test_empty_asr_does_not_advance_or_award_stars():
    scene = make_scene()
    result = await make_orchestrator().handle_turn(
        TurnContext(scene=scene, current_step_id="step_1", recognized_text="")
    )
    assert result.accepted is False
    assert result.next_step == "step_1"
    assert result.stars_earned == 0
    assert result.attempts == 0


async def test_unsafe_input_redirects_without_advancing():
    scene = make_scene()
    result = await make_orchestrator().handle_turn(
        TurnContext(
            scene=scene,
            current_step_id="step_1",
            recognized_text="Show me your gun",
        )
    )
    assert result.safety == "redirect"
    assert result.next_step == "step_1"
    assert result.accepted is False


async def test_auto_advances_after_max_attempts():
    scene = make_scene()
    llm = FakeLLMProvider(
        scene_factory=lambda theme, difficulty: {},
        turn_response=REJECTED,
    )
    result = await make_orchestrator(llm=llm).handle_turn(
        TurnContext(
            scene=scene,
            current_step_id="step_1",
            recognized_text="banana",
            attempts=1,
        )
    )
    assert result.accepted is False
    assert result.next_step == "step_2"
    assert result.attempts == 0
    assert result.completed is False


async def test_goodbye_completes_practice():
    scene = make_scene()
    result = await make_orchestrator().handle_turn(
        TurnContext(
            scene=scene,
            current_step_id="step_4",
            recognized_text="goodbye",
        )
    )
    assert result.accepted is True
    assert result.next_step is None
    assert result.completed is True


async def test_semantic_acceptance_when_rule_does_not_match():
    scene = make_scene()
    result = await make_orchestrator().handle_turn(
        TurnContext(
            scene=scene,
            current_step_id="step_2",
            recognized_text="banana",
        )
    )
    assert result.accepted is True
    assert result.next_step == "step_3"


async def test_tts_failure_returns_text_only():
    class FailingTTS:
        async def synthesize(self, text, voice, speed):
            raise RuntimeError("tts unavailable")

    scene = make_scene()
    result = await make_orchestrator(tts=FailingTTS()).handle_turn(
        TurnContext(scene=scene, current_step_id="step_1", recognized_text="yes")
    )
    assert result.reply
    assert result.audio_base64 is None
    assert result.media_type is None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_matching.py tests/test_dialogue.py -v`

Expected: FAIL because `app.matching` and `app.dialogue` do not exist.

- [ ] **Step 3: Implement phrase matching**

Create `backend/app/matching.py`:

```python
import re

from app.schemas import Difficulty, SceneStep


def normalize_text(text: str) -> str:
    spaced = re.sub(r"[^a-z0-9' ]+", " ", text.lower())
    return re.sub(r"\s+", " ", spaced).strip()


def phrase_in_text(phrase: str, text: str) -> bool:
    normalized_phrase = normalize_text(phrase)
    normalized_text = normalize_text(text)
    if not normalized_phrase:
        return False
    pattern = rf"(?<!\w){re.escape(normalized_phrase)}(?!\w)"
    return re.search(pattern, normalized_text) is not None


def rule_match(text: str, step: SceneStep, difficulty: Difficulty) -> bool:
    if any(phrase_in_text(phrase, text) for phrase in step.target_phrases):
        return True
    if difficulty is Difficulty.sprout:
        return any(
            phrase_in_text(keyword, text)
            for keyword in step.accepted_keywords
        )
    return False
```

- [ ] **Step 4: Implement the dialogue orchestrator**

Create `backend/app/dialogue.py`:

```python
import asyncio
import base64
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

from app.content import PROFILES
from app.matching import rule_match
from app.prompts import TURN_SYSTEM_PROMPT, build_turn_prompt
from app.providers.base import LLMProvider, TTSProvider
from app.safety import SafetyValidator
from app.scene_validator import count_sentences
from app.schemas import (
    Difficulty,
    SceneSpec,
    SceneStep,
    TurnResponse,
    TurnSummary,
)


@dataclass(frozen=True)
class TurnContext:
    scene: SceneSpec
    current_step_id: str
    recognized_text: str
    attempts: int = 0
    history: list[TurnSummary] = field(default_factory=list)
    help_used: bool = False


class TurnJudgement(BaseModel):
    accepted: bool
    feedback: str = Field(min_length=1, max_length=160)
    reply: str = Field(min_length=1, max_length=300)
    hint: str = Field(default="", max_length=200)
    next_step: str | None = None
    stars: int = Field(default=1, ge=0, le=2)
    safety: Literal["ok", "redirect"] = "ok"


class DialogueOrchestrator:
    def __init__(
        self,
        llm: LLMProvider,
        safety: SafetyValidator,
        tts: TTSProvider,
        timeout_seconds: float = 12.0,
        voice: str = "xiaoyun",
    ):
        self.llm = llm
        self.safety = safety
        self.tts = tts
        self.timeout_seconds = timeout_seconds
        self.voice = voice

    async def handle_turn(self, context: TurnContext) -> TurnResponse:
        step = self._find_step(context.scene, context.current_step_id)
        text = context.recognized_text.strip()

        if not text:
            return self._retry(
                step,
                context,
                message="I didn't hear you. Let's try again.",
                stars=0,
                attempts=context.attempts,
            )
        if self.safety.violations(text):
            return self._safe_redirect(step, context)

        next_step = self._next_step(context.scene, step)
        judgement = await self._judge(context, step, next_step)
        if judgement and judgement.safety == "redirect":
            return self._safe_redirect(step, context)

        accepted = rule_match(text, step, context.scene.difficulty) or bool(
            judgement and judgement.accepted
        )
        if accepted:
            return await self._accepted(context, step, next_step, judgement)
        return await self._not_accepted(context, step, next_step, judgement)

    async def _judge(
        self,
        context: TurnContext,
        step: SceneStep,
        next_step: SceneStep | None,
    ) -> TurnJudgement | None:
        prompt = build_turn_prompt(
            context.scene,
            step,
            context.recognized_text,
            context.attempts,
            context.history,
            next_step,
        )
        try:
            payload = await asyncio.wait_for(
                self.llm.complete_json(TURN_SYSTEM_PROMPT, prompt),
                timeout=self.timeout_seconds,
            )
            judgement = TurnJudgement.model_validate(payload)
        except Exception:
            return None

        if self.safety.violations(
            " ".join([judgement.feedback, judgement.reply, judgement.hint])
        ):
            return None
        if next_step is not None:
            profile = PROFILES[context.scene.difficulty]
            if count_sentences(judgement.reply) > profile.max_reply_sentences:
                return None
        return judgement

    async def _accepted(
        self,
        context: TurnContext,
        step: SceneStep,
        next_step: SceneStep | None,
        judgement: TurnJudgement | None,
    ) -> TurnResponse:
        feedback = judgement.feedback if judgement else "Great job!"
        if next_step is None:
            reply = (
                judgement.reply
                if judgement
                else "Great job! See you next time."
            )
            next_step_id = None
            completed = True
        else:
            reply = judgement.reply if judgement else next_step.role_prompt
            next_step_id = next_step.step_id
            completed = False
        audio_base64, media_type = await self._tts(
            reply, context.scene.difficulty
        )
        return TurnResponse(
            recognized_text=context.recognized_text,
            accepted=True,
            feedback=feedback,
            reply=reply,
            hint="",
            next_step=next_step_id,
            stars_earned=2,
            safety="ok",
            attempts=0,
            completed=completed,
            audio_base64=audio_base64,
            media_type=media_type,
        )

    async def _not_accepted(
        self,
        context: TurnContext,
        step: SceneStep,
        next_step: SceneStep | None,
        judgement: TurnJudgement | None,
    ) -> TurnResponse:
        attempts = context.attempts + 1
        if attempts >= step.max_attempts and step.allow_skip:
            if next_step is None:
                reply = "Great job! See you next time."
                next_step_id = None
                completed = True
                feedback = "Nice try! Let's finish here."
            else:
                reply = next_step.role_prompt
                next_step_id = next_step.step_id
                completed = False
                feedback = "Nice try! Let's keep going."
            audio_base64, media_type = await self._tts(
                reply, context.scene.difficulty
            )
            return TurnResponse(
                recognized_text=context.recognized_text,
                accepted=False,
                feedback=feedback,
                reply=reply,
                hint="",
                next_step=next_step_id,
                stars_earned=1,
                safety="ok",
                attempts=0,
                completed=completed,
                audio_base64=audio_base64,
                media_type=media_type,
            )

        reply = step.retry_prompt
        audio_base64, media_type = await self._tts(
            reply, context.scene.difficulty
        )
        return TurnResponse(
            recognized_text=context.recognized_text,
            accepted=False,
            feedback=judgement.feedback if judgement else "Nice try!",
            reply=reply,
            hint=step.hint_en,
            next_step=step.step_id,
            stars_earned=1,
            safety="ok",
            attempts=attempts,
            completed=False,
            audio_base64=audio_base64,
            media_type=media_type,
        )

    def _retry(
        self,
        step: SceneStep,
        context: TurnContext,
        message: str,
        stars: int,
        attempts: int,
    ) -> TurnResponse:
        return TurnResponse(
            recognized_text="",
            accepted=False,
            feedback=message,
            reply=step.retry_prompt,
            hint=step.hint_en,
            next_step=step.step_id,
            stars_earned=stars,
            safety="ok",
            attempts=attempts,
            completed=False,
            audio_base64=None,
            media_type=None,
        )

    def _safe_redirect(
        self,
        step: SceneStep,
        context: TurnContext,
    ) -> TurnResponse:
        return TurnResponse(
            recognized_text=context.recognized_text,
            accepted=False,
            feedback="Let's keep playing our game.",
            reply=step.retry_prompt,
            hint=step.hint_en,
            next_step=step.step_id,
            stars_earned=1,
            safety="redirect",
            attempts=context.attempts,
            completed=False,
            audio_base64=None,
            media_type=None,
        )

    async def _tts(
        self,
        text: str,
        difficulty: Difficulty,
    ) -> tuple[str | None, str | None]:
        profile = PROFILES[difficulty]
        try:
            result = await asyncio.wait_for(
                self.tts.synthesize(
                    text,
                    voice=self.voice,
                    speed=profile.speech_rate,
                ),
                timeout=self.timeout_seconds,
            )
        except Exception:
            return None, None
        encoded = base64.b64encode(result.audio).decode("ascii")
        return encoded, result.media_type

    @staticmethod
    def _find_step(scene: SceneSpec, step_id: str) -> SceneStep:
        for step in scene.steps:
            if step.step_id == step_id:
                return step
        raise ValueError(f"unknown step: {step_id}")

    @classmethod
    def _next_step(
        cls,
        scene: SceneSpec,
        step: SceneStep,
    ) -> SceneStep | None:
        if step.next_step is None:
            return None
        return cls._find_step(scene, step.next_step)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest tests/test_matching.py tests/test_dialogue.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/matching.py backend/app/dialogue.py tests/test_matching.py tests/test_dialogue.py
git commit -m "feat: orchestrate dialogue turns and state transitions"
```

---

### Task 9: Audio Conversion to 16 kHz Mono WAV

**Files:**
- Create: `backend/app/audio.py`
- Test: `tests/test_audio.py`

**Interfaces:**
- Consumes: browser audio bytes and content type.
- Produces: `convert_to_wav_16k_mono(audio: bytes, content_type: str, timeout_seconds: float = 10.0) -> bytes` and `AudioConversionError`.

- [ ] **Step 1: Write the failing audio tests**

Create `tests/test_audio.py`:

```python
import io
import shutil
import subprocess
import wave

import pytest

from app.audio import AudioConversionError, convert_to_wav_16k_mono
from app.providers.fake import make_silence_wav


def test_empty_audio_is_rejected():
    with pytest.raises(AudioConversionError):
        convert_to_wav_16k_mono(b"", "audio/webm")


def test_ffmpeg_command_targets_16k_mono(monkeypatch):
    captured = {}

    def fake_run(command, capture_output, timeout):
        captured["command"] = command
        captured["timeout"] = timeout
        return subprocess.CompletedProcess(command, 0, stdout=b"RIFFok", stderr=b"")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = convert_to_wav_16k_mono(b"input", "audio/webm", timeout_seconds=3)
    assert result == b"RIFFok"
    assert "-ac" in captured["command"]
    assert captured["command"][captured["command"].index("-ac") + 1] == "1"
    assert "-ar" in captured["command"]
    assert captured["command"][captured["command"].index("-ar") + 1] == "16000"


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_real_conversion_returns_16k_mono_wav():
    source = make_silence_wav(0.2, sample_rate=44100)
    converted = convert_to_wav_16k_mono(source, "audio/wav")
    with wave.open(io.BytesIO(converted), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getframerate() == 16000
        assert wav.getsampwidth() == 2
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_audio.py -v`

Expected: FAIL because `app.audio` does not exist.

- [ ] **Step 3: Implement audio conversion**

Create `backend/app/audio.py`:

```python
import subprocess
import tempfile
from pathlib import Path


class AudioConversionError(ValueError):
    """Raised when uploaded audio cannot be converted for ASR."""


def convert_to_wav_16k_mono(
    audio: bytes,
    content_type: str,
    timeout_seconds: float = 10.0,
) -> bytes:
    if not audio:
        raise AudioConversionError("empty audio")

    with tempfile.TemporaryDirectory() as temp_dir:
        source = Path(temp_dir) / "input"
        source.write_bytes(audio)
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "wav",
            "pipe:1",
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise AudioConversionError("audio conversion timed out") from exc
        except OSError as exc:
            raise AudioConversionError(
                f"ffmpeg is not available for {content_type}"
            ) from exc

        if completed.returncode != 0 or not completed.stdout:
            stderr = completed.stderr.decode("utf-8", "ignore")[:300]
            raise AudioConversionError(f"ffmpeg failed: {stderr}")
        return completed.stdout
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_audio.py -v`

Expected: PASS. The real conversion test is skipped when ffmpeg is not installed; the Docker image installs it.

- [ ] **Step 5: Commit**

```bash
git add backend/app/audio.py tests/test_audio.py
git commit -m "feat: convert browser audio for ASR"
```

---

### Task 10: Allowlisted Anonymous Event Logger

**Files:**
- Create: `backend/app/events.py`
- Test: `tests/test_events.py`

**Interfaces:**
- Consumes: an event name and a metadata dictionary.
- Produces: `ALLOWED_EVENT_PROPERTIES` and `EventLogger.log(name: str, properties: dict[str, str | int | bool] | None = None) -> None`.

- [ ] **Step 1: Write the failing event logger tests**

Create `tests/test_events.py`:

```python
import json

import pytest

from app.events import EventLogger


def test_logs_allowlisted_event(tmp_path):
    path = tmp_path / "logs" / "events.jsonl"
    logger = EventLogger(path)
    logger.log(
        "turn_completed",
        {"theme": "family", "difficulty": "explorer", "stars": 2},
    )
    record = json.loads(path.read_text(encoding="utf-8").strip())
    assert record["event"] == "turn_completed"
    assert record["theme"] == "family"
    assert record["difficulty"] == "explorer"
    assert record["stars"] == 2
    assert "ts" in record


@pytest.mark.parametrize("key", ["text", "audio", "transcript", "child_text"])
def test_rejects_private_content_keys(tmp_path, key):
    logger = EventLogger(tmp_path / "events.jsonl")
    with pytest.raises(ValueError):
        logger.log("technical_error", {key: "private content"})


def test_creates_parent_directory(tmp_path):
    path = tmp_path / "nested" / "events.jsonl"
    EventLogger(path).log("practice_started", {"difficulty": "sprout"})
    assert path.exists()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_events.py -v`

Expected: FAIL because `app.events` does not exist.

- [ ] **Step 3: Implement the allowlisted logger**

Create `backend/app/events.py`:

```python
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

ALLOWED_EVENT_PROPERTIES = {
    "theme",
    "difficulty",
    "success",
    "turns",
    "stars",
    "latency_ms",
    "error_type",
    "continued_after_help",
}


class EventLogger:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    def log(
        self,
        name: str,
        properties: dict[str, str | int | bool] | None = None,
    ) -> None:
        properties = properties or {}
        forbidden = set(properties) - ALLOWED_EVENT_PROPERTIES
        if forbidden:
            raise ValueError(
                f"event properties not allowed: {sorted(forbidden)}"
            )
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": name,
            **properties,
        }
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_events.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/events.py tests/test_events.py
git commit -m "feat: log anonymous allowlisted events"
```

---

### Task 11: Provider Factory and Aliyun/Qwen Adapters

**Files:**
- Create: `backend/app/providers/qwen.py`
- Create: `backend/app/providers/aliyun_nls.py`
- Create: `backend/app/providers/factory.py`
- Test: `tests/test_provider_factory.py`
- Test: `tests/test_qwen_provider.py`
- Test: `tests/test_aliyun_nls.py`

**Interfaces:**
- Consumes: `Settings`, `FallbackSceneFactory`, `FakeASRProvider`, `FakeLLMProvider`, `FakeTTSProvider`.
- Produces: `QwenProvider`, `AliyunNLSASRProvider`, `AliyunNLSTTSProvider`, `AliyunTokenCache`, and `build_providers(settings, fallback_factory) -> tuple[ASRProvider, LLMProvider, TTSProvider]`.

- [ ] **Step 1: Write the failing adapter and factory tests**

Create `tests/test_qwen_provider.py`:

```python
import httpx
import pytest

from app.config import Settings
from app.providers.base import ProviderError
from app.providers.qwen import QwenProvider


async def test_qwen_parses_json_content():
    def handler(request):
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": '{"accepted": true}'}}
                ]
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = QwenProvider(
        Settings(app_env="test", dashscope_api_key="test-key"),
        client=client,
    )
    payload = await provider.complete_json("system", "user")
    assert payload == {"accepted": True}


async def test_qwen_rejects_invalid_json():
    def handler(request):
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "not json"}}]},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = QwenProvider(
        Settings(app_env="test", dashscope_api_key="test-key"),
        client=client,
    )
    with pytest.raises(ProviderError):
        await provider.complete_json("system", "user")


async def test_qwen_requires_api_key():
    provider = QwenProvider(Settings(app_env="test"))
    with pytest.raises(ProviderError):
        await provider.complete_json("system", "user")
```

Create `tests/test_aliyun_nls.py`:

```python
import json
import time

import httpx
import pytest

from app.config import Settings
from app.providers.aliyun_nls import (
    AliyunNLSASRProvider,
    AliyunNLSTTSProvider,
    AliyunTokenCache,
)
from app.providers.base import ProviderError


class FakeTokenCache:
    def get_token(self) -> str:
        return "test-token"


def aliyun_settings() -> Settings:
    return Settings(
        app_env="test",
        aliyun_access_key_id="id",
        aliyun_access_key_secret="secret",
        aliyun_nls_app_key="app-key",
    )


async def test_asr_parses_successful_response():
    def handler(request):
        assert request.headers["X-NLS-Token"] == "test-token"
        assert request.url.params["appkey"] == "app-key"
        return httpx.Response(
            200,
            json={"status": 20000000, "result": "I want milk."},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = AliyunNLSASRProvider(
        aliyun_settings(),
        client=client,
        token_cache=FakeTokenCache(),
    )
    result = await provider.transcribe(b"wav")
    assert result.text == "I want milk."


async def test_asr_rejects_error_status():
    def handler(request):
        return httpx.Response(
            200,
            json={"status": 40000001, "message": "bad audio"},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = AliyunNLSASRProvider(
        aliyun_settings(),
        client=client,
        token_cache=FakeTokenCache(),
    )
    with pytest.raises(ProviderError):
        await provider.transcribe(b"wav")


async def test_tts_returns_audio_bytes():
    def handler(request):
        assert request.headers["X-NLS-Token"] == "test-token"
        return httpx.Response(
            200,
            content=b"ID3test",
            headers={"content-type": "audio/mpeg"},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = AliyunNLSTTSProvider(
        aliyun_settings(),
        client=client,
        token_cache=FakeTokenCache(),
    )
    result = await provider.synthesize("Hello", voice="xiaoyun", speed=0.9)
    assert result.audio == b"ID3test"
    assert result.media_type == "audio/mpeg"


async def test_tts_rejects_json_error_body():
    def handler(request):
        return httpx.Response(
            200,
            content=b'{"error":"bad"}',
            headers={"content-type": "application/json"},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = AliyunNLSTTSProvider(
        aliyun_settings(),
        client=client,
        token_cache=FakeTokenCache(),
    )
    with pytest.raises(ProviderError):
        await provider.synthesize("Hello", voice="xiaoyun", speed=1.0)


def test_token_cache_reuses_unexpired_token():
    class FakeClient:
        def __init__(self):
            self.calls = 0

        def do_action_with_exception(self, request):
            self.calls += 1
            return json.dumps(
                {
                    "Token": {
                        "Id": "abc",
                        "ExpireTime": int(time.time()) + 3600,
                    }
                }
            ).encode()

    client = FakeClient()
    cache = AliyunTokenCache("id", "secret", client=client)
    assert cache.get_token() == "abc"
    assert cache.get_token() == "abc"
    assert client.calls == 1
```

Create `tests/test_provider_factory.py`:

```python
import pytest

from app.config import Settings
from app.fallback_scenes import FallbackSceneFactory
from app.providers.factory import build_providers
from app.providers.fake import FakeASRProvider, FakeLLMProvider, FakeTTSProvider


def test_factory_builds_fakes_by_default():
    asr, llm, tts = build_providers(
        Settings(app_env="test"),
        FallbackSceneFactory(),
    )
    assert isinstance(asr, FakeASRProvider)
    assert isinstance(llm, FakeLLMProvider)
    assert isinstance(tts, FakeTTSProvider)


def test_factory_rejects_unknown_provider():
    with pytest.raises(ValueError):
        build_providers(
            Settings(app_env="test", asr_provider="unknown"),
            FallbackSceneFactory(),
        )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_qwen_provider.py tests/test_aliyun_nls.py tests/test_provider_factory.py -v`

Expected: FAIL because the adapter modules do not exist.

- [ ] **Step 3: Implement the Qwen adapter**

Create `backend/app/providers/qwen.py`:

```python
import json

import httpx

from app.config import Settings
from app.providers.base import ProviderError


class QwenProvider:
    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
    ):
        self.api_key = settings.dashscope_api_key
        self.model = settings.qwen_model
        self.client = client or httpx.AsyncClient(
            timeout=settings.scene_timeout_seconds
        )

    async def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        if not self.api_key:
            raise ProviderError("DASHSCOPE_API_KEY is not configured")
        response = await self.client.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.7,
            },
        )
        if response.status_code >= 400:
            raise ProviderError(f"qwen http error: {response.status_code}")
        try:
            content = response.json()["choices"][0]["message"]["content"]
            return json.loads(content)
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise ProviderError("invalid qwen response") from exc
```

- [ ] **Step 4: Implement the Aliyun NLS adapters and factory**

Create `backend/app/providers/aliyun_nls.py`:

```python
import json
import time

import httpx
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import RpcRequest

from app.config import Settings
from app.providers.base import ASRResult, ProviderError, TTSResult


class CreateTokenRequest(RpcRequest):
    def __init__(self):
        super().__init__("nls-meta", "2019-02-28", "CreateToken")
        self.set_method("POST")


class AliyunTokenCache:
    def __init__(
        self,
        access_key_id: str | None,
        access_key_secret: str | None,
        region_id: str = "cn-shanghai",
        client=None,
    ):
        self.client = client or AcsClient(
            access_key_id,
            access_key_secret,
            region_id,
        )
        self.token: str | None = None
        self.expires_at: float = 0.0

    def get_token(self) -> str:
        now = time.time()
        if self.token and now < self.expires_at - 60:
            return self.token
        request = CreateTokenRequest()
        raw = self.client.do_action_with_exception(request)
        payload = json.loads(raw)
        self.token = payload["Token"]["Id"]
        self.expires_at = float(payload["Token"]["ExpireTime"])
        return self.token


class AliyunNLSASRProvider:
    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
        token_cache=None,
    ):
        self.app_key = settings.aliyun_nls_app_key
        self.region = settings.aliyun_region
        self.client = client or httpx.AsyncClient(
            timeout=settings.turn_timeout_seconds
        )
        self.token_cache = token_cache or AliyunTokenCache(
            settings.aliyun_access_key_id,
            settings.aliyun_access_key_secret,
            settings.aliyun_region,
        )

    async def transcribe(self, audio_wav: bytes) -> ASRResult:
        if not self.app_key:
            raise ProviderError("ALIYUN_NLS_APP_KEY is not configured")
        response = await self.client.post(
            f"https://nls-gateway-{self.region}.aliyuncs.com/stream/v1/asr",
            params={
                "appkey": self.app_key,
                "format": "wav",
                "sample_rate": 16000,
                "enable_punctuation_prediction": "true",
                "enable_inverse_text_normalization": "true",
            },
            headers={"X-NLS-Token": self.token_cache.get_token()},
            content=audio_wav,
        )
        if response.status_code >= 400:
            raise ProviderError(f"aliyun asr http error: {response.status_code}")
        payload = response.json()
        if payload.get("status") != 20000000:
            raise ProviderError(
                f"aliyun asr error: {payload.get('message', 'unknown')}"
            )
        return ASRResult(text=payload.get("result", ""), confidence=None)


class AliyunNLSTTSProvider:
    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient | None = None,
        token_cache=None,
    ):
        self.app_key = settings.aliyun_nls_app_key
        self.region = settings.aliyun_region
        self.client = client or httpx.AsyncClient(
            timeout=settings.turn_timeout_seconds
        )
        self.token_cache = token_cache or AliyunTokenCache(
            settings.aliyun_access_key_id,
            settings.aliyun_access_key_secret,
            settings.aliyun_region,
        )

    async def synthesize(
        self,
        text: str,
        voice: str,
        speed: float,
    ) -> TTSResult:
        if not self.app_key:
            raise ProviderError("ALIYUN_NLS_APP_KEY is not configured")
        response = await self.client.post(
            f"https://nls-gateway-{self.region}.aliyuncs.com/stream/v1/tts",
            json={
                "appkey": self.app_key,
                "token": self.token_cache.get_token(),
                "text": text,
                "format": "mp3",
                "voice": voice,
                "sample_rate": 16000,
                "speech_rate": int((speed - 1.0) * 500),
                "volume": 50,
            },
        )
        if response.status_code >= 400:
            raise ProviderError(f"aliyun tts http error: {response.status_code}")
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            raise ProviderError(f"aliyun tts error: {response.text[:200]}")
        return TTSResult(audio=response.content, media_type="audio/mpeg")
```

Create `backend/app/providers/factory.py`:

```python
from app.content import ThemeId
from app.fallback_scenes import FallbackSceneFactory
from app.config import Settings
from app.providers.aliyun_nls import (
    AliyunNLSASRProvider,
    AliyunNLSTTSProvider,
)
from app.providers.base import ASRProvider, LLMProvider, TTSProvider
from app.providers.fake import (
    FakeASRProvider,
    FakeLLMProvider,
    FakeTTSProvider,
)
from app.providers.qwen import QwenProvider
from app.schemas import Difficulty


def build_providers(
    settings: Settings,
    fallback_factory: FallbackSceneFactory,
) -> tuple[ASRProvider, LLMProvider, TTSProvider]:
    if settings.asr_provider == "fake":
        asr: ASRProvider = FakeASRProvider(
            texts=[
                "Yes, I am ready.",
                "I want milk.",
                "I like blue.",
                "Goodbye!",
            ]
        )
    elif settings.asr_provider == "aliyun":
        asr = AliyunNLSASRProvider(settings)
    else:
        raise ValueError(f"unknown ASR provider: {settings.asr_provider}")

    if settings.llm_provider == "fake":
        def scene_factory(theme: ThemeId, difficulty: Difficulty) -> dict:
            return fallback_factory.build(theme, difficulty).model_dump(
                mode="json"
            )

        llm: LLMProvider = FakeLLMProvider(scene_factory=scene_factory)
    elif settings.llm_provider == "qwen":
        llm = QwenProvider(settings)
    else:
        raise ValueError(f"unknown LLM provider: {settings.llm_provider}")

    if settings.tts_provider == "fake":
        tts: TTSProvider = FakeTTSProvider()
    elif settings.tts_provider == "aliyun":
        tts = AliyunNLSTTSProvider(settings)
    else:
        raise ValueError(f"unknown TTS provider: {settings.tts_provider}")

    return asr, llm, tts
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest tests/test_qwen_provider.py tests/test_aliyun_nls.py tests/test_provider_factory.py -v`

Expected: PASS. These tests use mocked HTTP transports and do not call Aliyun or DashScope.

- [ ] **Step 6: Commit**

```bash
git add backend/app/providers/qwen.py backend/app/providers/aliyun_nls.py backend/app/providers/factory.py tests/test_qwen_provider.py tests/test_aliyun_nls.py tests/test_provider_factory.py
git commit -m "feat: add Aliyun and Qwen provider adapters"
```

---

### Task 12: Services, Pages, and JSON APIs

**Files:**
- Create: `backend/app/services.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/api/routes.py`
- Create: `backend/app/templates/base.html`
- Create: `backend/app/templates/index.html`
- Create: `backend/app/templates/practice.html`
- Test: `tests/test_api_scene.py`
- Test: `tests/test_api_turn.py`
- Test: `tests/test_api_events.py`
- Test: `tests/test_api_pages.py`

**Interfaces:**
- Consumes: all backend components from Tasks 1–11.
- Produces: `Services`, `build_services(settings, templates) -> Services`, `create_app(settings=None, services=None) -> FastAPI`, `GET /`, `GET /practice`, `POST /api/scene`, `POST /api/turn`, `POST /api/event`, `GET /api/health`.

- [ ] **Step 1: Write the failing API and page tests**

Create `tests/test_api_scene.py`:

```python
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.providers.fake import FakeLLMProvider
from app.schemas import SceneEnvelope
from app.signature import verify_envelope


def build_client(tmp_path):
    settings = Settings(
        app_env="test",
        hmac_secret="test-secret",
        event_log_path=tmp_path / "events.jsonl",
    )
    return TestClient(create_app(settings)), settings


def test_scene_endpoint_returns_signed_envelope(tmp_path):
    client, settings = build_client(tmp_path)
    response = client.post(
        "/api/scene",
        json={"difficulty": "explorer", "recent_themes": []},
    )
    assert response.status_code == 200
    payload = response.json()
    envelope = SceneEnvelope.model_validate(payload["envelope"])
    verify_envelope(envelope, payload["signature"], settings.hmac_secret)
    assert payload["opening_text"]
    assert payload["opening_audio_base64"]


def test_scene_endpoint_avoids_recent_themes(tmp_path):
    client, _ = build_client(tmp_path)
    response = client.post(
        "/api/scene",
        json={
            "difficulty": "star",
            "recent_themes": ["family", "school"],
        },
    )
    assert response.status_code == 200
    theme = response.json()["envelope"]["scene"]["theme"]
    assert theme not in {"family", "school"}


def test_scene_endpoint_returns_fallback_for_invalid_llm(tmp_path):
    client, _ = build_client(tmp_path)
    services = client.app.state.services
    services.scene_generator.llm = FakeLLMProvider(
        scene_factory=lambda theme, difficulty: {"bad": "payload"}
    )
    response = client.post(
        "/api/scene",
        json={"difficulty": "sprout", "recent_themes": []},
    )
    assert response.status_code == 200
    assert response.json()["fallback_used"] is True
```

Create `tests/test_api_turn.py`:

```python
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.providers.base import ASRResult
from app.providers.fake import make_silence_wav
from app.schemas import SceneEnvelope
from app.signature import make_envelope, sign_envelope
from tests.factories import make_scene


def build_client(tmp_path, max_audio_bytes=5_000_000):
    settings = Settings(
        app_env="test",
        hmac_secret="test-secret",
        max_audio_bytes=max_audio_bytes,
        event_log_path=tmp_path / "events.jsonl",
        scene_timeout_seconds=0.05,
        turn_timeout_seconds=0.05,
    )
    return TestClient(create_app(settings)), settings


def signed_envelope(settings):
    envelope = make_envelope(make_scene(), 3600)
    return envelope, sign_envelope(envelope, settings.hmac_secret)


def form_data(envelope, signature, **overrides):
    data = {
        "envelope_json": envelope.model_dump_json(),
        "signature": signature,
        "current_step_id": "step_1",
        "attempts": "0",
        "history_json": "[]",
        "help_used": "false",
    }
    data.update(overrides)
    return data


def test_turn_accepts_audio_and_returns_next_step(tmp_path):
    client, settings = build_client(tmp_path)
    envelope, signature = signed_envelope(settings)
    response = client.post(
        "/api/turn",
        data=form_data(envelope, signature),
        files={
            "audio": (
                "turn.wav",
                make_silence_wav(0.2),
                "audio/wav",
            )
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["next_step"] == "step_2"
    assert payload["accepted"] is True
    assert payload["stars_earned"] == 2


def test_turn_accepts_text_fallback(tmp_path):
    client, settings = build_client(tmp_path)
    envelope, signature = signed_envelope(settings)
    response = client.post(
        "/api/turn",
        data=form_data(envelope, signature, text_input="yes"),
    )
    assert response.status_code == 200
    assert response.json()["accepted"] is True


def test_turn_rejects_invalid_signature(tmp_path):
    client, settings = build_client(tmp_path)
    envelope, _ = signed_envelope(settings)
    response = client.post(
        "/api/turn",
        data=form_data(envelope, "wrong"),
        files={"audio": ("turn.wav", make_silence_wav(0.2), "audio/wav")},
    )
    assert response.status_code == 400


def test_turn_rejects_oversized_audio(tmp_path):
    client, settings = build_client(tmp_path, max_audio_bytes=100_000)
    envelope, signature = signed_envelope(settings)
    response = client.post(
        "/api/turn",
        data=form_data(envelope, signature),
        files={"audio": ("turn.wav", b"x" * 100_001, "audio/wav")},
    )
    assert response.status_code == 413


def test_turn_rejects_empty_audio(tmp_path):
    client, settings = build_client(tmp_path)
    envelope, signature = signed_envelope(settings)
    response = client.post(
        "/api/turn",
        data=form_data(envelope, signature),
        files={"audio": ("turn.wav", b"", "audio/wav")},
    )
    assert response.status_code == 422


def test_turn_rejects_unknown_step(tmp_path):
    client, settings = build_client(tmp_path)
    envelope, signature = signed_envelope(settings)
    response = client.post(
        "/api/turn",
        data=form_data(envelope, signature, current_step_id="step_9"),
        files={"audio": ("turn.wav", make_silence_wav(0.2), "audio/wav")},
    )
    assert response.status_code == 400


def test_low_confidence_asr_returns_retry(tmp_path):
    class LowConfidenceASR:
        async def transcribe(self, audio_wav):
            return ASRResult(text="maybe", confidence=0.1)

    client, settings = build_client(tmp_path)
    client.app.state.services.asr = LowConfidenceASR()
    envelope, signature = signed_envelope(settings)
    response = client.post(
        "/api/turn",
        data=form_data(envelope, signature),
        files={"audio": ("turn.wav", make_silence_wav(0.2), "audio/wav")},
    )
    assert response.status_code == 200
    assert response.json()["recognized_text"] == ""
    assert response.json()["accepted"] is False


def test_tts_failure_returns_text_only(tmp_path):
    class FailingTTS:
        async def synthesize(self, text, voice, speed):
            raise RuntimeError("tts unavailable")

    client, settings = build_client(tmp_path)
    failing = FailingTTS()
    client.app.state.services.tts = failing
    client.app.state.services.dialogue.tts = failing
    envelope, signature = signed_envelope(settings)
    response = client.post(
        "/api/turn",
        data=form_data(envelope, signature),
        files={"audio": ("turn.wav", make_silence_wav(0.2), "audio/wav")},
    )
    assert response.status_code == 200
    assert response.json()["audio_base64"] is None
    assert response.json()["reply"]
```

Create `tests/test_api_events.py`:

```python
import json

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
```

Create `tests/test_api_pages.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_api_scene.py tests/test_api_turn.py tests/test_api_events.py tests/test_api_pages.py -v`

Expected: FAIL because the services, routes, and templates do not exist.

- [ ] **Step 3: Implement the service container and app factory**

Create `backend/app/services.py`:

```python
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
```

Modify `backend/app/main.py`:

```python
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes import router
from app.config import Settings, get_settings
from app.services import Services, build_services

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def create_app(
    settings: Settings | None = None,
    services: Services | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Kids English Speaking Demo")
    if services is None:
        services = build_services(settings, templates)
    app.state.services = services
    app.state.settings = settings
    app.mount(
        "/static",
        StaticFiles(directory=BASE_DIR / "static", check_dir=False),
        name="static",
    )
    app.include_router(router)
    return app


app = create_app()
```

- [ ] **Step 4: Implement the page and JSON routes**

Replace `backend/app/api/routes.py` with:

```python
import base64
import json
import time

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app.audio import AudioConversionError, convert_to_wav_16k_mono
from app.content import PROFILES
from app.dialogue import TurnContext
from app.schemas import (
    EventRequest,
    SceneEnvelope,
    SceneRequest,
    SceneResponse,
    TurnResponse,
    TurnSummary,
)
from app.services import Services
from app.signature import (
    SceneSignatureError,
    make_envelope,
    sign_envelope,
    verify_envelope,
)

router = APIRouter()


def get_services(request: Request) -> Services:
    return request.app.state.services


@router.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    services: Services = Depends(get_services),
):
    return services.templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_config": services.app_config,
            "app_config_json": json.dumps(
                services.app_config,
                ensure_ascii=False,
            ),
        },
    )


@router.get("/practice", response_class=HTMLResponse)
async def practice(
    request: Request,
    services: Services = Depends(get_services),
):
    return services.templates.TemplateResponse(
        request=request,
        name="practice.html",
        context={
            "app_config": services.app_config,
            "app_config_json": json.dumps(
                services.app_config,
                ensure_ascii=False,
            ),
        },
    )


@router.post("/api/scene", response_model=SceneResponse)
async def create_scene(
    payload: SceneRequest,
    services: Services = Depends(get_services),
):
    started = time.perf_counter()
    generated = await services.scene_generator.generate(
        payload.difficulty,
        payload.recent_themes,
    )
    envelope = make_envelope(
        generated.scene,
        services.settings.scene_ttl_seconds,
    )
    signature = sign_envelope(envelope, services.settings.hmac_secret)
    opening_text = generated.scene.steps[0].role_prompt
    opening_audio_base64 = None
    opening_media_type = None
    try:
        opening = await services.tts.synthesize(
            opening_text,
            voice=services.settings.tts_voice,
            speed=PROFILES[generated.scene.difficulty].speech_rate,
        )
        opening_audio_base64 = base64.b64encode(opening.audio).decode("ascii")
        opening_media_type = opening.media_type
    except Exception:
        services.events.log(
            "technical_error",
            {
                "difficulty": payload.difficulty.value,
                "error_type": "tts_opening",
            },
        )
    services.events.log(
        "scene_generated",
        {
            "theme": generated.scene.theme.value,
            "difficulty": payload.difficulty.value,
            "success": not generated.fallback_used,
            "latency_ms": round((time.perf_counter() - started) * 1000),
        },
    )
    return SceneResponse(
        envelope=envelope,
        signature=signature,
        opening_text=opening_text,
        opening_audio_base64=opening_audio_base64,
        opening_media_type=opening_media_type,
        fallback_used=generated.fallback_used,
    )


@router.post("/api/turn", response_model=TurnResponse)
async def submit_turn(
    envelope_json: str = Form(...),
    signature: str = Form(...),
    current_step_id: str = Form(...),
    attempts: int = Form(0),
    history_json: str = Form("[]"),
    help_used: bool = Form(False),
    audio: UploadFile | None = File(None),
    text_input: str | None = Form(None),
    services: Services = Depends(get_services),
):
    started = time.perf_counter()
    if not 0 <= attempts <= 10:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_attempts",
                "message": "attempts must be between 0 and 10",
            },
        )
    try:
        envelope = SceneEnvelope.model_validate_json(envelope_json)
        verify_envelope(
            envelope,
            signature,
            services.settings.hmac_secret,
        )
    except (ValidationError, SceneSignatureError) as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_scene", "message": str(exc)},
        ) from exc

    try:
        raw_history = json.loads(history_json)
        history = [TurnSummary.model_validate(item) for item in raw_history]
    except (json.JSONDecodeError, TypeError, ValidationError) as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_history",
                "message": "history must be a list of turn summaries",
            },
        ) from exc

    if text_input is not None and text_input.strip():
        transcript = text_input.strip()
    else:
        if audio is None:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "missing_audio",
                    "message": "audio or text_input is required",
                },
            )
        raw_audio = await audio.read()
        if len(raw_audio) > services.settings.max_audio_bytes:
            raise HTTPException(
                status_code=413,
                detail={
                    "code": "audio_too_large",
                    "message": "audio file is too large",
                },
            )
        try:
            wav = convert_to_wav_16k_mono(
                raw_audio,
                audio.content_type or "application/octet-stream",
            )
        except AudioConversionError as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": "invalid_audio", "message": str(exc)},
            ) from exc
        try:
            asr_result = await services.asr.transcribe(wav)
        except Exception as exc:
            services.events.log(
                "technical_error",
                {
                    "difficulty": envelope.scene.difficulty.value,
                    "error_type": "asr",
                },
            )
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "asr_unavailable",
                    "message": "Please try again.",
                },
            ) from exc
        transcript = asr_result.text
        if (
            asr_result.confidence is not None
            and asr_result.confidence < 0.5
        ):
            transcript = ""

    try:
        result = await services.dialogue.handle_turn(
            TurnContext(
                scene=envelope.scene,
                current_step_id=current_step_id,
                recognized_text=transcript,
                attempts=attempts,
                history=history,
                help_used=help_used,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_step", "message": str(exc)},
        ) from exc

    services.events.log(
        "turn_completed",
        {
            "theme": envelope.scene.theme.value,
            "difficulty": envelope.scene.difficulty.value,
            "success": result.accepted,
            "stars": result.stars_earned,
            "turns": len(history) + 1,
            "latency_ms": round((time.perf_counter() - started) * 1000),
        },
    )
    return result


@router.post("/api/event")
async def record_event(
    payload: EventRequest,
    services: Services = Depends(get_services),
):
    try:
        services.events.log(payload.name.value, payload.properties)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_event", "message": str(exc)},
        ) from exc
    return {"ok": True}
```

`time` is used to record allowlisted `latency_ms` values for scene generation and turns.

- [ ] **Step 5: Add the page templates**

Create `backend/app/templates/base.html`:

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{% block title %}English Play{% endblock %}</title>
  <link rel="stylesheet" href="/static/css/app.css">
</head>
<body>
  <main class="app-shell">
    {% block content %}{% endblock %}
  </main>
  <script>
    window.__APP_CONFIG__ = {{ app_config_json | safe }};
  </script>
  {% block scripts %}{% endblock %}
</body>
</html>
```

Create `backend/app/templates/index.html`:

```html
{% extends "base.html" %}
{% block title %}English Play{% endblock %}
{% block content %}
<header class="hero">
  <p class="eyebrow">Kids English Speaking</p>
  <h1>今天想和谁说英语？</h1>
  <p>选择一个难度和一个卡通小伙伴，系统会为你准备一个生活场景。</p>
</header>

<section class="panel" aria-labelledby="difficulty-heading">
  <h2 id="difficulty-heading">选择难度</h2>
  <div id="difficulty-grid" class="choice-grid">
    {% for difficulty in app_config.difficulties %}
    <button
      class="choice-card difficulty-card"
      type="button"
      data-testid="difficulty-{{ difficulty.id }}"
      data-difficulty="{{ difficulty.id }}"
    >
      <strong>{{ difficulty.label }}</strong>
      <span>{{ difficulty.target_age }}</span>
      <span>{{ difficulty.target_answer }}</span>
    </button>
    {% endfor %}
  </div>
</section>

<section class="panel" aria-labelledby="avatar-heading">
  <h2 id="avatar-heading">选择小伙伴</h2>
  <div id="avatar-grid" class="avatar-grid">
    {% for avatar in app_config.avatars %}
    <button
      class="avatar-button"
      type="button"
      data-testid="avatar-{{ loop.index0 }}"
      data-avatar="{{ avatar }}"
      aria-label="选择头像 {{ avatar }}"
    >{{ avatar }}</button>
    {% endfor %}
  </div>
</section>

<ul id="theme-name-list" class="sr-only" aria-hidden="true">
  {% for theme in app_config.themes.values() %}
  <li>{{ theme.name_zh }} {{ theme.name_en }}</li>
  {% endfor %}
</ul>

<button id="start-button" data-testid="start-button" class="primary-button" type="button" disabled>
  开始练习
</button>
<p id="start-status" data-testid="start-status" class="status" aria-live="polite"></p>
{% endblock %}
{% block scripts %}
<script type="module" src="/static/js/index.js"></script>
{% endblock %}
```

Create `backend/app/templates/practice.html`:

```html
{% extends "base.html" %}
{% block title %}Practice{% endblock %}
{% block content %}
<section id="task-intro" class="screen">
  <div id="theme-visual" class="theme-visual" aria-hidden="true"></div>
  <p class="eyebrow">任务介绍</p>
  <h1 id="scene-title"></h1>
  <p id="scene-goal"></p>
  <div id="opening-text" class="bubble" data-testid="opening-text"></div>
  <div class="button-row">
    <button id="replay-opening" data-testid="replay-opening" class="secondary-button" type="button">再听一次</button>
    <button id="begin-button" data-testid="begin-button" class="primary-button" type="button">开始对话</button>
  </div>
</section>

<section id="dialogue" class="screen hidden">
  <header class="practice-header">
    <div id="practice-theme-icon" class="theme-icon" aria-hidden="true"></div>
    <div>
      <p class="eyebrow" id="practice-theme-name"></p>
      <h1 id="practice-title"></h1>
      <p id="progress-label" data-testid="progress-label"></p>
    </div>
  </header>

  <div id="ai-bubble" data-testid="ai-bubble" class="bubble" aria-live="polite"></div>
  <div class="button-row">
    <button id="replay-reply" data-testid="replay-reply" class="secondary-button" type="button">再听一次</button>
    <button id="slow-reply" data-testid="slow-reply" class="secondary-button" type="button">慢速播放</button>
  </div>

  <p id="hint" data-testid="hint" class="hint hidden"></p>

  <button id="mic-button" data-testid="mic-button" class="mic-button" type="button">
    <span class="mic-icon" aria-hidden="true">🎤</span>
    <span id="mic-label">点击开始说话</span>
  </button>
  <button id="help-button" data-testid="help-button" class="secondary-button" type="button">帮帮我</button>

  <div id="text-fallback" class="text-fallback hidden">
    <label for="text-input">也可以输入你的回答</label>
    <input id="text-input" data-testid="text-input" type="text" autocomplete="off">
    <button id="text-submit" data-testid="text-submit" class="primary-button" type="button">提交回答</button>
  </div>

  <p id="status" data-testid="status" class="status" aria-live="polite"></p>
</section>

<section id="end-screen" data-testid="end-screen" class="screen hidden">
  <p class="eyebrow">练习完成</p>
  <h1>太棒了！</h1>
  <p id="stars" data-testid="stars" class="stars"></p>
  <h2>今天的目标表达</h2>
  <ul id="target-expressions" class="target-list"></ul>
  <div class="button-row">
    <button id="restart-button" data-testid="restart-button" class="primary-button" type="button">再练一次</button>
    <button id="change-difficulty" data-testid="change-difficulty" class="secondary-button" type="button">换难度</button>
  </div>
</section>
{% endblock %}
{% block scripts %}
<script type="module" src="/static/js/practice.js"></script>
{% endblock %}
```

- [ ] **Step 6: Run the API and page tests to verify they pass**

Run: `python -m pytest tests/test_api_scene.py tests/test_api_turn.py tests/test_api_events.py tests/test_api_pages.py -v`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/services.py backend/app/main.py backend/app/api/routes.py backend/app/templates/base.html backend/app/templates/index.html backend/app/templates/practice.html tests/test_api_scene.py tests/test_api_turn.py tests/test_api_events.py tests/test_api_pages.py
git commit -m "feat: expose scene, turn, event, and page APIs"
```

---

### Task 13: Start Page, Local Storage, and Scene Creation Flow

**Files:**
- Create: `backend/app/static/css/app.css`
- Create: `backend/app/static/js/api.js`
- Create: `backend/app/static/js/storage.js`
- Create: `backend/app/static/js/index.js`
- Modify: `tests/conftest.py`
- Test: `tests/test_e2e_start.py`

**Interfaces:**
- Consumes: `GET /`, `POST /api/scene`, `POST /api/event`.
- Produces: browser functions `createScene(difficulty, recentThemes)`, `logEvent(name, properties)`, `savePractice(state)`, `loadPractice()`, `clearPractice()`, `loadRecentThemes()`, `recordRecentTheme(theme)`.

- [ ] **Step 1: Write the failing start-flow test**

Create `tests/test_e2e_start.py`:

```python
def test_start_flow_saves_practice_and_navigates(live_server, browser_page):
    page = browser_page
    page.goto(live_server)
    page.get_by_test_id("difficulty-explorer").click()
    page.get_by_test_id("avatar-0").click()
    assert page.get_by_test_id("start-button").is_enabled()
    page.get_by_test_id("start-button").click()
    page.wait_for_url("**/practice")
    state = page.evaluate(
        "JSON.parse(localStorage.getItem('kidsEnglishPracticeV1'))"
    )
    assert state["difficulty"] == "explorer"
    assert state["signature"]
    assert state["envelope"]["scene"]["steps"]
    assert state["currentStepId"] == "step_1"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_e2e_start.py -v`

Expected: FAIL because the browser fixtures and frontend files do not exist.

- [ ] **Step 3: Add live-server and browser fixtures**

Replace `tests/conftest.py` with:

```python
import threading
import time

import pytest
import uvicorn
from playwright.sync_api import sync_playwright

from app.config import Settings
from app.main import create_app


@pytest.fixture
def test_settings() -> Settings:
    return Settings(app_env="test", hmac_secret="test-secret")


@pytest.fixture
def live_server(tmp_path):
    settings = Settings(
        app_env="test",
        hmac_secret="test-secret",
        event_log_path=tmp_path / "events.jsonl",
        asr_provider="fake",
        llm_provider="fake",
        tts_provider="fake",
    )
    app = create_app(settings)
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=0,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while not server.started and time.time() < deadline:
        time.sleep(0.05)
    if not server.started:
        raise RuntimeError("test server did not start")
    port = server.servers[0].sockets[0].getsockname()[1]
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture
def browser_page():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                "--use-fake-device-for-media-stream",
                "--use-fake-ui-for-media-stream",
            ],
        )
        context = browser.new_context(
            permissions=["microphone"],
            viewport={"width": 1024, "height": 768},
        )
        page = context.new_page()
        yield page
        browser.close()
```

- [ ] **Step 4: Implement the API, storage, and start-page scripts**

Create `backend/app/static/js/api.js`:

```javascript
export async function createScene(difficulty, recentThemes) {
  const response = await fetch('/api/scene', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      difficulty,
      recent_themes: recentThemes,
    }),
  });
  if (!response.ok) {
    throw new Error(`scene request failed: ${response.status}`);
  }
  return response.json();
}

export async function submitTurn({
  audio,
  textInput,
  envelope,
  signature,
  currentStepId,
  attempts,
  history,
  helpUsed,
}) {
  const form = new FormData();
  form.append('envelope_json', JSON.stringify(envelope));
  form.append('signature', signature);
  form.append('current_step_id', currentStepId);
  form.append('attempts', String(attempts));
  form.append('history_json', JSON.stringify(history));
  form.append('help_used', helpUsed ? 'true' : 'false');
  if (audio) {
    form.append('audio', audio, 'turn.webm');
  }
  if (textInput) {
    form.append('text_input', textInput);
  }
  const response = await fetch('/api/turn', {
    method: 'POST',
    body: form,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const message = payload.detail?.message
      || `turn request failed: ${response.status}`;
    throw new Error(message);
  }
  return response.json();
}

export async function logEvent(name, properties = {}) {
  try {
    await fetch('/api/event', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name, properties}),
      keepalive: true,
    });
  } catch {
    // Event logging must never block the learning flow.
  }
}
```

Create `backend/app/static/js/storage.js`:

```javascript
const PRACTICE_KEY = 'kidsEnglishPracticeV1';
const RECENT_KEY = 'kidsEnglishRecentThemesV1';

export function savePractice(state) {
  localStorage.setItem(
    PRACTICE_KEY,
    JSON.stringify({version: 1, ...state}),
  );
}

export function loadPractice() {
  try {
    const raw = localStorage.getItem(PRACTICE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    return data.version === 1 ? data : null;
  } catch {
    return null;
  }
}

export function clearPractice() {
  localStorage.removeItem(PRACTICE_KEY);
}

export function loadRecentThemes() {
  try {
    const raw = localStorage.getItem(RECENT_KEY);
    const data = raw ? JSON.parse(raw) : [];
    return Array.isArray(data) ? data.slice(-2) : [];
  } catch {
    return [];
  }
}

export function recordRecentTheme(theme) {
  const recent = loadRecentThemes().filter((item) => item !== theme);
  recent.push(theme);
  localStorage.setItem(RECENT_KEY, JSON.stringify(recent.slice(-2)));
}
```

Create `backend/app/static/js/index.js`:

```javascript
import {createScene, logEvent} from './api.js';
import {
  clearPractice,
  loadRecentThemes,
  recordRecentTheme,
  savePractice,
} from './storage.js';

const selection = {difficulty: null, avatar: null};
const difficultyButtons = [
  ...document.querySelectorAll('[data-difficulty]'),
];
const avatarButtons = [...document.querySelectorAll('[data-avatar]')];
const startButton = document.getElementById('start-button');
const status = document.getElementById('start-status');

function updateStartState() {
  startButton.disabled = !(selection.difficulty && selection.avatar);
}

difficultyButtons.forEach((button) => {
  button.addEventListener('click', () => {
    selection.difficulty = button.dataset.difficulty;
    difficultyButtons.forEach((item) => {
      item.classList.toggle('selected', item === button);
    });
    updateStartState();
  });
});

avatarButtons.forEach((button) => {
  button.addEventListener('click', () => {
    selection.avatar = button.dataset.avatar;
    avatarButtons.forEach((item) => {
      item.classList.toggle('selected', item === button);
    });
    updateStartState();
  });
});

startButton.addEventListener('click', async () => {
  if (!selection.difficulty || !selection.avatar) return;
  startButton.disabled = true;
  status.textContent = '正在准备你的场景...';
  try {
    const recentThemes = loadRecentThemes();
    const response = await createScene(selection.difficulty, recentThemes);
    const scene = response.envelope.scene;
    recordRecentTheme(scene.theme);
    clearPractice();
    savePractice({
      difficulty: selection.difficulty,
      avatar: selection.avatar,
      envelope: response.envelope,
      signature: response.signature,
      openingText: response.opening_text,
      openingAudioBase64: response.opening_audio_base64,
      openingMediaType: response.opening_media_type,
      currentStepId: scene.steps[0].step_id,
      attempts: 0,
      stars: 0,
      completedStepIds: [],
      targetExpressionsCompleted: [],
      history: [],
      helpUsed: false,
      hasStarted: false,
      completed: false,
      lastPracticeAt: new Date().toISOString(),
    });
    logEvent('practice_started', {
      difficulty: selection.difficulty,
      theme: scene.theme,
    });
    window.location.href = '/practice';
  } catch {
    status.textContent = '场景准备失败了，请再试一次。';
    startButton.disabled = false;
  }
});

updateStartState();
```

- [ ] **Step 5: Add the shared stylesheet**

Create `backend/app/static/css/app.css`:

```css
:root {
  --bg: #fff8ee;
  --ink: #22313f;
  --muted: #5c6b73;
  --card: #ffffff;
  --accent: #ff8a5b;
  --accent-strong: #e76f51;
  --blue: #457b9d;
  --green: #2a9d8f;
  --border: #eadfd0;
  --shadow: 0 12px 30px rgba(34, 49, 63, 0.12);
}

* {
  box-sizing: border-box;
}

html,
body {
  margin: 0;
  min-height: 100%;
}

body {
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  background:
    radial-gradient(circle at 12% 0%, #ffe2c8 0, transparent 34%),
    radial-gradient(circle at 92% 8%, #dceff0 0, transparent 32%),
    var(--bg);
  color: var(--ink);
}

.app-shell {
  width: min(960px, 100%);
  margin: 0 auto;
  padding: 24px 18px 48px;
}

.hero {
  padding: 24px 8px 12px;
}

.eyebrow {
  margin: 0 0 8px;
  color: var(--accent-strong);
  font-size: 0.82rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

h1 {
  margin: 0 0 12px;
  font-size: clamp(1.8rem, 4vw, 2.7rem);
  line-height: 1.12;
}

h2 {
  margin: 0 0 14px;
  font-size: 1.15rem;
}

p {
  line-height: 1.65;
}

.panel {
  margin: 16px 0;
  padding: 20px;
  border: 1px solid var(--border);
  border-radius: 24px;
  background: var(--card);
  box-shadow: var(--shadow);
}

.choice-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.choice-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px;
  border: 2px solid var(--border);
  border-radius: 18px;
  background: #fff;
  color: var(--ink);
  text-align: left;
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease;
}

.choice-card:hover,
.choice-card.selected {
  border-color: var(--accent);
  transform: translateY(-2px);
}

.choice-card strong {
  font-size: 1.2rem;
}

.choice-card span:last-child {
  color: var(--muted);
  font-size: 0.92rem;
}

.avatar-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.avatar-button {
  width: 72px;
  height: 72px;
  border: 2px solid var(--border);
  border-radius: 50%;
  background: #fff;
  font-size: 2rem;
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease;
}

.avatar-button:hover,
.avatar-button.selected {
  border-color: var(--accent);
  background: #fff0e8;
  transform: translateY(-2px);
}

.primary-button,
.secondary-button {
  border-radius: 999px;
  padding: 14px 22px;
  font: inherit;
  font-weight: 800;
  cursor: pointer;
}

.primary-button {
  border: 0;
  background: var(--accent-strong);
  color: #fff;
  box-shadow: 0 8px 18px rgba(231, 111, 81, 0.25);
}

.primary-button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  box-shadow: none;
}

.secondary-button {
  border: 1px solid var(--border);
  background: #fff;
  color: var(--ink);
}

.button-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.status {
  min-height: 1.5em;
  color: var(--muted);
}

.screen {
  animation: fade-in 0.25s ease;
}

.hidden {
  display: none !important;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.theme-visual {
  min-height: 160px;
  margin-bottom: 20px;
  border-radius: 24px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #ffe8d7, #dceff0);
  font-size: 4rem;
}

.theme-icon {
  width: 64px;
  height: 64px;
  flex: 0 0 auto;
  border-radius: 20px;
  display: grid;
  place-items: center;
  background: #fff0e8;
  font-size: 2rem;
}

.practice-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 18px;
}

.bubble {
  padding: 18px 20px;
  border: 1px solid var(--border);
  border-radius: 22px;
  background: #fff;
  box-shadow: var(--shadow);
  font-size: 1.15rem;
}

.hint {
  padding: 12px 16px;
  border: 1px solid #cfe8e0;
  border-radius: 16px;
  background: #eef7f4;
  color: #245c50;
}

.mic-button {
  width: 100%;
  min-height: 120px;
  margin: 18px 0 12px;
  border: 0;
  border-radius: 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  background: linear-gradient(135deg, #ff8a5b, #e76f51);
  color: #fff;
  font: inherit;
  font-size: 1.1rem;
  font-weight: 800;
  cursor: pointer;
  box-shadow: 0 16px 30px rgba(231, 111, 81, 0.3);
}

.mic-button.recording {
  background: linear-gradient(135deg, #2a9d8f, #1f776d);
  animation: pulse 1s infinite;
}

.mic-icon {
  font-size: 2.4rem;
}

.text-fallback {
  margin-top: 16px;
  padding: 16px;
  border-radius: 18px;
  background: #f7f4ee;
}

.text-fallback input {
  width: 100%;
  margin: 8px 0;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  font: inherit;
}

.stars {
  font-size: 2rem;
  letter-spacing: 4px;
}

.target-list {
  display: grid;
  gap: 8px;
  padding-left: 0;
  list-style: none;
}

.target-list li {
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: #fff;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.02);
  }
}

@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 700px) {
  .app-shell {
    padding: 16px 12px 36px;
  }

  .choice-grid {
    grid-template-columns: 1fr;
  }

  .panel {
    padding: 16px;
    border-radius: 20px;
  }

  .mic-button {
    min-height: 104px;
  }
}
```

- [ ] **Step 6: Run the start-flow test to verify it passes**

Run: `python -m pytest tests/test_e2e_start.py -v`

Expected: PASS. If Chromium is missing, run `python -m playwright install chromium` first.

- [ ] **Step 7: Commit**

```bash
git add backend/app/static/css/app.css backend/app/static/js/api.js backend/app/static/js/storage.js backend/app/static/js/index.js tests/conftest.py tests/test_e2e_start.py
git commit -m "feat: add start page and scene creation flow"
```

---

### Task 14: Practice Page, Recorder, and Turn Loop

**Files:**
- Create: `backend/app/static/js/recorder.js`
- Create: `backend/app/static/js/practice.js`
- Test: `tests/test_e2e_practice.py`

**Interfaces:**
- Consumes: `submitTurn`, `logEvent`, `loadPractice`, `savePractice`, `window.__APP_CONFIG__`.
- Produces: `MicRecorder.start()`, `MicRecorder.stop()`, `MicRecorder.isRecording()`, and the practice page dialogue loop.

- [ ] **Step 1: Write the failing practice-flow test**

Create `tests/test_e2e_practice.py`:

```python
def start_practice(page, live_server, difficulty="explorer"):
    page.goto(live_server)
    page.get_by_test_id(f"difficulty-{difficulty}").click()
    page.get_by_test_id("avatar-0").click()
    page.get_by_test_id("start-button").click()
    page.wait_for_url("**/practice")
    page.get_by_test_id("begin-button").click()
    page.wait_for_selector("#dialogue:not(.hidden)")


def record_one_turn(page):
    page.get_by_test_id("mic-button").click()
    page.wait_for_timeout(350)
    page.get_by_test_id("mic-button").click()


def test_practice_records_a_turn_and_restores_progress(
    live_server,
    browser_page,
):
    page = browser_page
    start_practice(page, live_server)
    assert page.get_by_test_id("progress-label").inner_text() == "1 / 5"
    record_one_turn(page)
    page.wait_for_function(
        "document.querySelector('[data-testid=progress-label]').textContent === '2 / 5'",
        timeout=15000,
    )
    assert page.get_by_test_id("ai-bubble").inner_text()
    page.reload()
    page.wait_for_selector("#dialogue:not(.hidden)")
    assert page.get_by_test_id("progress-label").inner_text() == "2 / 5"
    state = page.evaluate(
        "JSON.parse(localStorage.getItem('kidsEnglishPracticeV1'))"
    )
    assert state["currentStepId"] == "step_2"
    assert "recognized_text" not in state
    assert "transcript" not in str(state).lower()


def test_help_button_shows_hint_without_advancing(
    live_server,
    browser_page,
):
    page = browser_page
    start_practice(page, live_server)
    page.get_by_test_id("help-button").click()
    hint = page.get_by_test_id("hint")
    assert hint.is_visible()
    assert hint.inner_text()
    assert page.get_by_test_id("progress-label").inner_text() == "1 / 5"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_e2e_practice.py -v`

Expected: FAIL because the practice scripts do not exist.

- [ ] **Step 3: Implement the microphone recorder**

Create `backend/app/static/js/recorder.js`:

```javascript
export class MicRecorder {
  constructor({maxSeconds, onComplete, onError}) {
    this.maxSeconds = maxSeconds;
    this.onComplete = onComplete;
    this.onError = onError;
    this.mediaRecorder = null;
    this.stream = null;
    this.chunks = [];
    this.timer = null;
  }

  isRecording() {
    return this.mediaRecorder?.state === 'recording';
  }

  async start() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
    } catch (error) {
      this.onError(error);
      return false;
    }
    const mimeType = this.pickMimeType();
    const options = mimeType ? {mimeType} : undefined;
    this.mediaRecorder = new MediaRecorder(this.stream, options);
    this.chunks = [];
    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        this.chunks.push(event.data);
      }
    };
    this.mediaRecorder.onstop = () => {
      const type = this.mediaRecorder.mimeType || 'audio/webm';
      const blob = new Blob(this.chunks, {type});
      this.stopTracks();
      this.onComplete(blob);
    };
    this.mediaRecorder.start();
    this.timer = window.setTimeout(
      () => this.stop(),
      this.maxSeconds * 1000,
    );
    return true;
  }

  stop() {
    if (this.isRecording()) {
      window.clearTimeout(this.timer);
      this.mediaRecorder.stop();
    }
  }

  stopTracks() {
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = null;
  }

  pickMimeType() {
    const options = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/mp4',
      'audio/ogg;codecs=opus',
    ];
    return options.find(
      (type) => MediaRecorder.isTypeSupported(type),
    ) || '';
  }
}
```

- [ ] **Step 4: Implement the practice page controller**

Create `backend/app/static/js/practice.js`:

```javascript
import {logEvent, submitTurn} from './api.js';
import {MicRecorder} from './recorder.js';
import {loadPractice, savePractice} from './storage.js';

const config = window.__APP_CONFIG__;
const state = loadPractice();

if (!state) {
  window.location.replace('/');
  throw new Error('practice state missing');
}

const scene = state.envelope.scene;
const profile = config.difficulties.find(
  (item) => item.id === state.difficulty,
) || {
  max_recording_seconds: 15,
  speech_rate: 1,
  show_hint_zh: false,
};
const theme = config.themes[scene.theme] || {
  name_en: 'English',
  name_zh: '英语',
  icon: '💬',
  color: '#ff8a5b',
};

const elements = {
  taskIntro: document.getElementById('task-intro'),
  dialogue: document.getElementById('dialogue'),
  endScreen: document.getElementById('end-screen'),
  themeVisual: document.getElementById('theme-visual'),
  sceneTitle: document.getElementById('scene-title'),
  sceneGoal: document.getElementById('scene-goal'),
  openingText: document.getElementById('opening-text'),
  replayOpening: document.getElementById('replay-opening'),
  beginButton: document.getElementById('begin-button'),
  practiceThemeIcon: document.getElementById('practice-theme-icon'),
  practiceThemeName: document.getElementById('practice-theme-name'),
  practiceTitle: document.getElementById('practice-title'),
  progressLabel: document.getElementById('progress-label'),
  aiBubble: document.getElementById('ai-bubble'),
  replayReply: document.getElementById('replay-reply'),
  slowReply: document.getElementById('slow-reply'),
  hint: document.getElementById('hint'),
  micButton: document.getElementById('mic-button'),
  micLabel: document.getElementById('mic-label'),
  helpButton: document.getElementById('help-button'),
  textFallback: document.getElementById('text-fallback'),
  textInput: document.getElementById('text-input'),
  textSubmit: document.getElementById('text-submit'),
  status: document.getElementById('status'),
  stars: document.getElementById('stars'),
  targetExpressions: document.getElementById('target-expressions'),
  restartButton: document.getElementById('restart-button'),
  changeDifficulty: document.getElementById('change-difficulty'),
};

let lastReplyText = '';
let lastReplyAudio = null;
let lastReplyMediaType = null;
let recorder = null;

function currentStep() {
  return scene.steps.find(
    (step) => step.step_id === state.currentStepId,
  ) || null;
}

function save() {
  savePractice(state);
}

function setStatus(message) {
  elements.status.textContent = message;
}

function speak(text, rate = profile.speech_rate) {
  if (!('speechSynthesis' in window) || !text) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'en-US';
  utterance.rate = rate;
  window.speechSynthesis.speak(utterance);
}

function playAudio(base64, mediaType, rate = 1) {
  if (!base64) return false;
  const audio = new Audio(
    `data:${mediaType || 'audio/mpeg'};base64,${base64}`,
  );
  audio.playbackRate = rate;
  audio.play().catch(() => {});
  return true;
}

function playOpening() {
  if (!playAudio(state.openingAudioBase64, state.openingMediaType)) {
    speak(state.openingText, profile.speech_rate);
  }
}

function setThemeVisuals() {
  elements.themeVisual.textContent = theme.icon;
  elements.themeVisual.style.background =
    `linear-gradient(135deg, ${theme.color}33, #e9f4f4)`;
  elements.practiceThemeIcon.textContent = theme.icon;
  elements.practiceThemeIcon.style.background = `${theme.color}22`;
  elements.practiceThemeName.textContent =
    theme.name_zh || theme.name_en;
  elements.practiceTitle.textContent = scene.title;
}

function renderIntro() {
  elements.sceneTitle.textContent = scene.title;
  elements.sceneGoal.textContent = `${scene.role} · ${scene.goal}`;
  elements.openingText.textContent = state.openingText;
  setThemeVisuals();
}

function renderStep() {
  const step = currentStep();
  if (!step) {
    showEnd();
    return;
  }
  const index = scene.steps.findIndex(
    (item) => item.step_id === step.step_id,
  );
  elements.progressLabel.textContent =
    `${index + 1} / ${scene.steps.length}`;
  elements.aiBubble.textContent = step.role_prompt;
  elements.hint.classList.add('hidden');
  elements.hint.textContent = '';
  elements.micLabel.textContent = '点击开始说话';
  elements.micButton.classList.remove('recording');
  lastReplyText = step.role_prompt;
  lastReplyAudio = null;
  lastReplyMediaType = null;
}

function showDialogue() {
  elements.taskIntro.classList.add('hidden');
  elements.endScreen.classList.add('hidden');
  elements.dialogue.classList.remove('hidden');
}

function showEnd() {
  elements.taskIntro.classList.add('hidden');
  elements.dialogue.classList.add('hidden');
  elements.endScreen.classList.remove('hidden');
  elements.stars.textContent = '⭐'.repeat(state.stars);
  elements.targetExpressions.innerHTML = '';
  scene.target_expressions.forEach((text) => {
    const item = document.createElement('li');
    item.textContent = text;
    elements.targetExpressions.appendChild(item);
  });
}

async function sendTurn({audio, textInput}) {
  setStatus('识别中...');
  elements.micButton.disabled = true;
  try {
    const response = await submitTurn({
      audio,
      textInput,
      envelope: state.envelope,
      signature: state.signature,
      currentStepId: state.currentStepId,
      attempts: state.attempts,
      history: state.history,
      helpUsed: state.helpUsed,
    });
    handleResponse(response);
  } catch {
    setStatus('没有听清，请再试一次。');
    logEvent('technical_error', {
      difficulty: state.difficulty,
      error_type: 'turn',
    });
  } finally {
    elements.micButton.disabled = false;
  }
}

function handleResponse(response) {
  const step = currentStep();
  if (!step) return;
  state.history.push({
    step_id: step.step_id,
    accepted: response.accepted,
    attempts: response.attempts,
    help_used: state.helpUsed,
  });
  state.stars += response.stars_earned;
  state.attempts = response.attempts;
  if (state.helpUsed && response.accepted) {
    logEvent('continued_after_help', {
      difficulty: state.difficulty,
      theme: scene.theme,
      continued_after_help: true,
    });
  }
  state.helpUsed = false;
  if (response.accepted) {
    if (!state.completedStepIds.includes(step.step_id)) {
      state.completedStepIds.push(step.step_id);
    }
    step.target_phrases.forEach((phrase) => {
      if (!state.targetExpressionsCompleted.includes(phrase)) {
        state.targetExpressionsCompleted.push(phrase);
      }
    });
  }
  setStatus(response.feedback);
  if (response.completed) {
    state.completed = true;
    state.currentStepId = null;
    save();
    logEvent('practice_completed', {
      difficulty: state.difficulty,
      theme: scene.theme,
      stars: state.stars,
      turns: state.history.length,
    });
    showEnd();
    return;
  }
  state.currentStepId = response.next_step;
  save();
  renderStep();
  if (response.hint) {
    elements.hint.textContent = response.hint;
    elements.hint.classList.remove('hidden');
  }
  lastReplyText = response.reply;
  lastReplyAudio = response.audio_base64;
  lastReplyMediaType = response.media_type;
  if (!playAudio(lastReplyAudio, lastReplyMediaType)) {
    speak(lastReplyText, profile.speech_rate);
  }
}

function createRecorder() {
  return new MicRecorder({
    maxSeconds: profile.max_recording_seconds,
    onComplete: (blob) => {
      elements.micButton.classList.remove('recording');
      elements.micLabel.textContent = '识别中...';
      sendTurn({audio: blob});
    },
    onError: (error) => {
      elements.micButton.classList.remove('recording');
      if (error?.name === 'NotAllowedError') {
        elements.textFallback.classList.remove('hidden');
        setStatus('请允许麦克风权限，或者输入你的回答。');
      } else {
        setStatus('麦克风暂时不可用，请再试一次。');
      }
    },
  });
}

function handleMicClick() {
  if (!recorder.isRecording()) {
    recorder.start().then((started) => {
      if (started) {
        elements.micButton.classList.add('recording');
        elements.micLabel.textContent = '点击结束录音';
        setStatus('录音中... 点击麦克风结束');
      }
    });
  } else {
    recorder.stop();
  }
}

function showHelp() {
  const step = currentStep();
  if (!step) return;
  const hint = profile.show_hint_zh
    ? `${step.hint_en} ${step.hint_zh}`
    : step.hint_en;
  elements.hint.textContent = hint;
  elements.hint.classList.remove('hidden');
  speak(step.hint_en, 0.75);
  state.helpUsed = true;
  save();
  logEvent('help_clicked', {
    difficulty: state.difficulty,
    theme: scene.theme,
  });
}

function initialize() {
  renderIntro();
  if (state.completed) {
    showEnd();
    return;
  }
  if (state.hasStarted) {
    showDialogue();
    renderStep();
  }
}

elements.beginButton.addEventListener('click', () => {
  state.hasStarted = true;
  save();
  showDialogue();
  renderStep();
  playOpening();
});
elements.replayOpening.addEventListener('click', playOpening);
elements.replayReply.addEventListener('click', () => {
  if (!playAudio(lastReplyAudio, lastReplyMediaType)) {
    speak(lastReplyText, profile.speech_rate);
  }
});
elements.slowReply.addEventListener('click', () => {
  if (!playAudio(lastReplyAudio, lastReplyMediaType, 0.7)) {
    speak(lastReplyText, 0.7);
  }
});
elements.helpButton.addEventListener('click', showHelp);
elements.micButton.addEventListener('click', handleMicClick);
elements.textSubmit.addEventListener('click', () => {
  const text = elements.textInput.value.trim();
  if (!text) return;
  elements.textInput.value = '';
  sendTurn({textInput: text});
});
elements.textInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    event.preventDefault();
    elements.textSubmit.click();
  }
});
elements.changeDifficulty.addEventListener('click', () => {
  window.location.href = '/';
});
elements.restartButton.addEventListener('click', () => {
  window.location.reload();
});

recorder = createRecorder();
initialize();
```

- [ ] **Step 5: Run the practice-flow tests to verify they pass**

Run: `python -m pytest tests/test_e2e_practice.py -v`

Expected: PASS for the microphone turn and help-button tests.

- [ ] **Step 6: Commit**

```bash
git add backend/app/static/js/recorder.js backend/app/static/js/practice.js tests/test_e2e_practice.py
git commit -m "feat: add recorder-driven practice loop"
```

---

### Task 15: Error Recovery, Text Fallback, and Help Continuation Events

**Files:**
- Modify: `backend/app/schemas.py`
- Modify: `backend/app/static/js/practice.js` only if the tests expose a missing recovery path
- Test: `tests/test_api_events.py`
- Test: `tests/test_e2e_errors.py`

**Interfaces:**
- Consumes: practice page controls, `/api/turn`, `/api/event`.
- Produces: recoverable microphone denial, recoverable network failure, and the `continued_after_help` anonymous event.

- [ ] **Step 1: Write the failing event and browser recovery tests**

Add this test to `tests/test_api_events.py`:

```python
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
```

Create `tests/test_e2e_errors.py`:

```python
import json


def start_practice(page, live_server):
    page.goto(live_server)
    page.get_by_test_id("difficulty-explorer").click()
    page.get_by_test_id("avatar-0").click()
    page.get_by_test_id("start-button").click()
    page.wait_for_url("**/practice")
    page.get_by_test_id("begin-button").click()
    page.wait_for_selector("#dialogue:not(.hidden)")


def test_microphone_denial_exposes_text_fallback(live_server, browser_page):
    page = browser_page
    start_practice(page, live_server)
    page.evaluate(
        """() => {
          navigator.mediaDevices.getUserMedia = () =>
            Promise.reject(new DOMException('denied', 'NotAllowedError'));
        }"""
    )
    page.get_by_test_id("mic-button").click()
    page.wait_for_selector("#text-fallback:not(.hidden)")
    page.get_by_test_id("text-input").fill("yes")
    page.get_by_test_id("text-submit").click()
    page.wait_for_function(
        "document.querySelector('[data-testid=progress-label]').textContent === '2 / 5'",
        timeout=15000,
    )


def test_network_failure_is_recoverable(live_server, browser_page):
    page = browser_page
    start_practice(page, live_server)
    page.route("**/api/turn", lambda route: route.abort())
    page.get_by_test_id("mic-button").click()
    page.wait_for_timeout(350)
    page.get_by_test_id("mic-button").click()
    page.wait_for_function(
        "document.querySelector('[data-testid=status]').textContent.includes('没有听清')",
        timeout=15000,
    )
    assert page.get_by_test_id("progress-label").inner_text() == "1 / 5"
    page.unroute("**/api/turn")
    page.get_by_test_id("mic-button").click()
    page.wait_for_timeout(350)
    page.get_by_test_id("mic-button").click()
    page.wait_for_function(
        "document.querySelector('[data-testid=progress-label]').textContent === '2 / 5'",
        timeout=15000,
    )


def test_help_then_answer_logs_continued_after_help(
    live_server,
    browser_page,
):
    page = browser_page
    events = []

    def capture(request):
        if request.url.endswith("/api/event"):
            try:
                events.append(json.loads(request.post_data))
            except (TypeError, json.JSONDecodeError):
                pass

    page.on("request", capture)
    start_practice(page, live_server)
    page.get_by_test_id("help-button").click()
    page.get_by_test_id("mic-button").click()
    page.wait_for_timeout(350)
    page.get_by_test_id("mic-button").click()
    page.wait_for_function(
        "document.querySelector('[data-testid=progress-label]').textContent === '2 / 5'",
        timeout=15000,
    )
    page.wait_for_timeout(500)
    assert any(
        event.get("name") == "continued_after_help"
        for event in events
    )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_api_events.py::test_continued_after_help_event_is_allowed tests/test_e2e_errors.py -v`

Expected: FAIL because `continued_after_help` is not an allowed `EventName`; the browser tests may also expose timing issues in the recovery path.

- [ ] **Step 3: Add the continuation event name**

In `backend/app/schemas.py`, add this member to `EventName`:

```python
    continued_after_help = "continued_after_help"
```

The complete enum becomes:

```python
class EventName(str, Enum):
    practice_started = "practice_started"
    help_clicked = "help_clicked"
    practice_completed = "practice_completed"
    practice_restarted = "practice_restarted"
    continued_after_help = "continued_after_help"
    technical_error = "technical_error"
```

- [ ] **Step 4: Confirm the browser recovery paths**

The existing `practice.js` already implements these paths:

- `MicRecorder` returns `NotAllowedError` to `onError`, which removes the hidden class from `#text-fallback`.
- `sendTurn` catches a failed request, writes “没有听清，请再试一次。” to `#status`, and leaves `state.currentStepId` unchanged.
- `handleResponse` logs `continued_after_help` when the previous help action was followed by an accepted turn.
- `playAudio` returns false when no audio is available; `handleResponse` calls `speak` as the fallback.

If a browser test fails, fix only the failing path in `backend/app/static/js/practice.js`. Do not change the backend state machine or the generated scene during this task.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest tests/test_api_events.py tests/test_e2e_errors.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas.py backend/app/static/js/practice.js tests/test_api_events.py tests/test_e2e_errors.py
git commit -m "feat: recover from microphone and network failures"
```

---

### Task 16: Completion Screen, Restart, Recent Themes, and Mobile Layout

**Files:**
- Modify: `backend/app/static/js/practice.js`
- Test: `tests/test_e2e_completion.py`

**Interfaces:**
- Consumes: `createScene`, `loadRecentThemes`, `recordRecentTheme`, `clearPractice`, `savePractice`.
- Produces: a completed practice screen, same-difficulty restart with a new scene, recent-theme rotation, and a no-overflow mobile layout.

- [ ] **Step 1: Write the failing completion and mobile tests**

Create `tests/test_e2e_completion.py`:

```python
def start_practice(page, live_server):
    page.goto(live_server)
    page.get_by_test_id("difficulty-explorer").click()
    page.get_by_test_id("avatar-0").click()
    page.get_by_test_id("start-button").click()
    page.wait_for_url("**/practice")
    page.get_by_test_id("begin-button").click()
    page.wait_for_selector("#dialogue:not(.hidden)")


def answer_until_complete(page, max_turns=8):
    for _ in range(max_turns):
        if page.get_by_test_id("end-screen").is_visible():
            return
        page.get_by_test_id("mic-button").click()
        page.wait_for_timeout(350)
        page.get_by_test_id("mic-button").click()
        page.wait_for_timeout(1200)


def test_complete_practice_and_restart_with_new_theme(
    live_server,
    browser_page,
):
    page = browser_page
    start_practice(page, live_server)
    previous_theme = page.evaluate(
        "JSON.parse(localStorage.getItem('kidsEnglishPracticeV1')).envelope.scene.theme"
    )
    answer_until_complete(page)
    page.wait_for_selector(
        "[data-testid=end-screen]:not(.hidden)",
        timeout=15000,
    )
    assert page.get_by_test_id("stars").inner_text()
    assert page.get_by_test_id("target-expressions").locator("li").count() >= 1
    page.get_by_test_id("restart-button").click()
    page.wait_for_selector("#task-intro:not(.hidden)", timeout=15000)
    state = page.evaluate(
        "JSON.parse(localStorage.getItem('kidsEnglishPracticeV1'))"
    )
    assert state["hasStarted"] is False
    assert state["stars"] == 0
    assert state["envelope"]["scene"]["theme"] != previous_theme


def test_mobile_layout_has_no_horizontal_overflow(
    live_server,
    browser_page,
):
    page = browser_page
    page.set_viewport_size({"width": 390, "height": 844})
    start_practice(page, live_server)
    assert page.get_by_test_id("mic-button").is_visible()
    overflow = page.evaluate(
        "document.documentElement.scrollWidth - window.innerWidth"
    )
    assert overflow <= 1
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_e2e_completion.py -v`

Expected: FAIL because restart currently reloads the completed practice instead of creating a new scene.

- [ ] **Step 3: Update imports in `practice.js`**

Change the import block to:

```javascript
import {createScene, logEvent, submitTurn} from './api.js';
import {MicRecorder} from './recorder.js';
import {
  clearPractice,
  loadPractice,
  loadRecentThemes,
  recordRecentTheme,
  savePractice,
} from './storage.js';
```

- [ ] **Step 4: Add the restart function**

Add this function before `initialize()`:

```javascript
async function restartPractice() {
  elements.restartButton.disabled = true;
  setStatus('正在准备新的场景...');
  try {
    const response = await createScene(
      state.difficulty,
      loadRecentThemes(),
    );
    const nextScene = response.envelope.scene;
    recordRecentTheme(nextScene.theme);
    clearPractice();
    savePractice({
      difficulty: state.difficulty,
      avatar: state.avatar,
      envelope: response.envelope,
      signature: response.signature,
      openingText: response.opening_text,
      openingAudioBase64: response.opening_audio_base64,
      openingMediaType: response.opening_media_type,
      currentStepId: nextScene.steps[0].step_id,
      attempts: 0,
      stars: 0,
      completedStepIds: [],
      targetExpressionsCompleted: [],
      history: [],
      helpUsed: false,
      hasStarted: false,
      completed: false,
      lastPracticeAt: new Date().toISOString(),
    });
    logEvent('practice_restarted', {
      difficulty: state.difficulty,
      theme: nextScene.theme,
    });
    window.location.reload();
  } catch {
    setStatus('新场景准备失败，请再试一次。');
    elements.restartButton.disabled = false;
  }
}
```

Replace the restart listener with:

```javascript
elements.restartButton.addEventListener('click', restartPractice);
```

- [ ] **Step 5: Run the completion and mobile tests to verify they pass**

Run: `python -m pytest tests/test_e2e_completion.py -v`

Expected: PASS. The restart creates a new signed scene with the same difficulty and avatar, resets stars and progress, and avoids the previous theme through `loadRecentThemes()`.

- [ ] **Step 6: Commit**

```bash
git add backend/app/static/js/practice.js tests/test_e2e_completion.py
git commit -m "feat: complete practice and restart with a new theme"
```

---

### Task 17: Full Six-Theme by Three-Difficulty Playwright Matrix

**Files:**
- Modify: `tests/conftest.py`
- Modify: `pytest.ini`
- Test: `tests/test_e2e_matrix.py`

**Interfaces:**
- Consumes: `create_app`, `ThemeSelector`, `ThemeId`, `Difficulty`, the start page, the practice page, and `/api/turn`.
- Produces: a slow Playwright matrix that completes all 18 theme/difficulty combinations through the text fallback.

- [ ] **Step 1: Write the failing matrix test**

Create `tests/test_e2e_matrix.py`:

```python
import pytest

from app.schemas import Difficulty, ThemeId
from app.theme_selector import ThemeSelector

STEP_COUNTS = {
    Difficulty.sprout: 4,
    Difficulty.explorer: 5,
    Difficulty.star: 6,
}


@pytest.mark.slow
@pytest.mark.parametrize("difficulty", list(Difficulty))
@pytest.mark.parametrize("theme", list(ThemeId))
def test_all_theme_difficulty_combinations_complete(
    live_server_app,
    browser_page,
    theme,
    difficulty,
):
    url, app = live_server_app
    app.state.services.scene_generator.selector = ThemeSelector([theme])
    page = browser_page
    page.goto(url)
    page.evaluate("localStorage.clear()")
    page.get_by_test_id(f"difficulty-{difficulty.value}").click()
    page.get_by_test_id("avatar-0").click()
    page.get_by_test_id("start-button").click()
    page.wait_for_url("**/practice")
    page.get_by_test_id("begin-button").click()
    page.wait_for_selector("#dialogue:not(.hidden)")
    page.evaluate(
        """() => {
          navigator.mediaDevices.getUserMedia = () =>
            Promise.reject(new DOMException('denied', 'NotAllowedError'));
        }"""
    )
    page.get_by_test_id("mic-button").click()
    page.wait_for_selector("#text-fallback:not(.hidden)")
    total = STEP_COUNTS[difficulty]
    for index in range(total):
        page.get_by_test_id("text-input").fill("yes")
        page.get_by_test_id("text-submit").click()
        if index < total - 1:
            expected = f"{index + 2} / {total}"
            page.wait_for_function(
                "document.querySelector('[data-testid=progress-label]').textContent === "
                f"'{expected}'",
                timeout=15000,
            )
        else:
            page.wait_for_selector(
                "[data-testid=end-screen]:not(.hidden)",
                timeout=15000,
            )
    assert page.get_by_test_id("end-screen").is_visible()
    state = page.evaluate(
        "JSON.parse(localStorage.getItem('kidsEnglishPracticeV1'))"
    )
    assert state["completed"] is True
    assert state["envelope"]["scene"]["theme"] == theme.value
    assert state["envelope"]["scene"]["difficulty"] == difficulty.value
```

- [ ] **Step 2: Run the matrix test to verify it fails**

Run: `python -m pytest tests/test_e2e_matrix.py -v -m slow`

Expected: FAIL until `live_server_app`, the slow marker, and the fallback step padding are in place.

- [ ] **Step 3: Add the app-aware live-server fixture**

Append this fixture to `tests/conftest.py`:

```python
@pytest.fixture
def live_server_app(tmp_path):
    settings = Settings(
        app_env="test",
        hmac_secret="test-secret",
        event_log_path=tmp_path / "events.jsonl",
        asr_provider="fake",
        llm_provider="fake",
        tts_provider="fake",
    )
    app = create_app(settings)
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=0,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while not server.started and time.time() < deadline:
        time.sleep(0.05)
    if not server.started:
        raise RuntimeError("test server did not start")
    port = server.servers[0].sockets[0].getsockname()[1]
    yield f"http://127.0.0.1:{port}", app
    server.should_exit = True
    thread.join(timeout=5)
```

- [ ] **Step 4: Register the slow marker**

Update `pytest.ini` to:

```ini
[pytest]
pythonpath = backend
testpaths = tests
asyncio_mode = auto
markers =
    slow: full six-theme by three-difficulty Playwright matrix
```

- [ ] **Step 5: Pad fallback templates to the difficulty minimum**

The fallback factory must add free-expression steps until both the difficulty's minimum step count and minimum free-expression count are met. The Task 5 `build` method already contains this padding block; if the repository implementation does not, replace its `build` method with the code below:

```python
    def build(self, theme_id: ThemeId, difficulty: Difficulty) -> SceneSpec:
        template = next(
            item for item in self.catalog.templates if item.theme is theme_id
        )
        profile = PROFILES[difficulty]
        raw_steps = list(template.steps)
        free_template = next(
            step for step in template.steps
            if step.kind is StepKind.free_expression
        )
        free_count = sum(
            step.kind is StepKind.free_expression for step in raw_steps
        )
        while (
            free_count < profile.free_expression_turns
            or len(raw_steps) < profile.min_steps
        ):
            padding = free_template.model_copy(
                update={
                    "goal": "practice free expression once more",
                    "role_prompt": "Can you tell me one more thing?",
                }
            )
            raw_steps.insert(len(raw_steps) - 1, padding)
            free_count += 1

        steps: list[SceneStep] = []
        for index, raw in enumerate(raw_steps, start=1):
            next_step = f"step_{index + 1}" if index < len(raw_steps) else None
            steps.append(
                SceneStep(
                    step_id=f"step_{index}",
                    kind=raw.kind,
                    goal=raw.goal,
                    role_prompt=raw.role_prompt,
                    target_phrases=raw.targets[difficulty],
                    accepted_keywords=raw.keywords,
                    hint_en=raw.hints[difficulty],
                    hint_zh=raw.hints_zh[difficulty],
                    retry_prompt=raw.retry_prompt,
                    max_attempts=profile.max_attempts,
                    next_step=next_step,
                    allow_skip=True,
                )
            )
        return SceneSpec(
            scene_id=f"fallback_{theme_id.value}_{difficulty.value}_{uuid4().hex[:8]}",
            theme=theme_id,
            difficulty=difficulty,
            title=template.title,
            setting=template.setting,
            role=template.role,
            goal=template.goal,
            steps=steps,
            target_expressions=template.expressions[difficulty],
            safety_notes=["Reviewed fallback scene for children."],
        )
```

- [ ] **Step 6: Run the fallback and matrix tests**

Run: `python -m pytest tests/test_fallback_scenes.py -v`

Expected: PASS for all 18 fallback combinations with 4/5/6 steps.

Run: `python -m pytest tests/test_e2e_matrix.py -v -m slow`

Expected: PASS for all 18 browser combinations. This test is intentionally slow; the normal suite can exclude it with `-m "not slow"`.

- [ ] **Step 7: Commit**

```bash
git add tests/conftest.py pytest.ini tests/test_e2e_matrix.py backend/app/fallback_scenes.py
git commit -m "test: cover every theme and difficulty in the browser"
```

---

### Task 18: Docker, Nginx, Environment Example, and README

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `deploy/nginx.conf`
- Create: `deploy/certs/.gitkeep`
- Create: `logs/.gitkeep`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `README.md`
- Test: `tests/test_deployment_files.py`

**Interfaces:**
- Consumes: the complete application.
- Produces: a reproducible local run, a Docker deployment with HTTPS termination, and operator documentation.

- [ ] **Step 1: Write the failing deployment-file tests**

Create `tests/test_deployment_files.py`:

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_dockerfile_installs_ffmpeg_and_runs_uvicorn():
    content = read("Dockerfile")
    assert "python:3.12-slim" in content
    assert "ffmpeg" in content
    assert "uvicorn" in content
    assert "app.main:app" in content


def test_nginx_requires_https_and_allows_audio_upload():
    content = read("deploy/nginx.conf")
    assert "listen 443 ssl" in content
    assert "ssl_certificate" in content
    assert "client_max_body_size 6m" in content
    assert "proxy_pass http://app:8000" in content


def test_env_example_lists_required_settings():
    content = read(".env.example")
    for key in [
        "HMAC_SECRET",
        "ASR_PROVIDER",
        "LLM_PROVIDER",
        "TTS_PROVIDER",
        "DASHSCOPE_API_KEY",
        "ALIYUN_ACCESS_KEY_ID",
        "ALIYUN_ACCESS_KEY_SECRET",
        "ALIYUN_NLS_APP_KEY",
    ]:
        assert key in content


def test_readme_contains_local_and_docker_commands():
    content = read("README.md")
    assert "playwright install chromium" in content
    assert "uvicorn app.main:app --app-dir backend --reload" in content
    assert "docker compose up" in content
    assert "pytest -q -m \"not slow\"" in content
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_deployment_files.py -v`

Expected: FAIL because the deployment files do not exist.

- [ ] **Step 3: Add the Docker image and Compose stack**

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
RUN mkdir -p /app/logs \
    && useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-compose.yml`:

```yaml
services:
  app:
    build: .
    env_file: .env
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  nginx:
    image: nginx:1.27-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deploy/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./deploy/certs:/etc/nginx/certs:ro
    depends_on:
      - app
    restart: unless-stopped
```

Create `deploy/certs/.gitkeep` and `logs/.gitkeep` as empty files.

- [ ] **Step 4: Add Nginx HTTPS configuration**

Create `deploy/nginx.conf`:

```nginx
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name _;

    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    client_max_body_size 6m;

    location /static/ {
        proxy_pass http://app:8000;
        expires 7d;
    }

    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 30s;
    }
}
```

- [ ] **Step 5: Add environment and ignore files**

Create `.env.example`:

```dotenv
APP_ENV=production
HMAC_SECRET=replace-with-a-32-byte-random-secret
ASR_PROVIDER=aliyun
LLM_PROVIDER=qwen
TTS_PROVIDER=aliyun
DASHSCOPE_API_KEY=
ALIYUN_ACCESS_KEY_ID=
ALIYUN_ACCESS_KEY_SECRET=
ALIYUN_NLS_APP_KEY=
ALIYUN_REGION=cn-shanghai
QWEN_MODEL=qwen-plus
TTS_VOICE=xiaoyun
EVENT_LOG_PATH=logs/events.jsonl
MAX_AUDIO_BYTES=5000000
SCENE_TTL_SECONDS=7200
SCENE_TIMEOUT_SECONDS=8
TURN_TIMEOUT_SECONDS=12
```

Create `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
test-results/
playwright-report/
logs/*.jsonl
deploy/certs/*.pem
```

- [ ] **Step 6: Add the operator README**

Create `README.md` with this content:

```markdown
# Kids English Speaking Demo

A Python-first web demo for children aged 4–12 to practice English speaking through a short, turn-based conversation with a cartoon role. The demo generates one life scene, uses browser recording, Aliyun ASR/TTS, and Qwen dialogue, and stores progress locally.

## Local development

Requirements: Python 3.12 and ffmpeg.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements-dev.txt
python -m playwright install chromium
uvicorn app.main:app --app-dir backend --reload
```

Open http://localhost:8000. The default providers are deterministic fakes, so no cloud credentials are required.

## Tests

```powershell
python -m pytest -q -m "not slow"
python -m pytest -q -m slow
ruff check backend tests scripts
```

The slow suite runs all six themes × three difficulties in Playwright.

## Real Aliyun and Qwen configuration

Copy `.env.example` to `.env`, replace the placeholders, and keep the real file out of Git. The application refuses to start in production with the default HMAC secret or missing provider credentials.

- `ALIYUN_NLS_APP_KEY`: Aliyun Intelligent Speech Interaction project appkey.
- `ALIYUN_ACCESS_KEY_ID` and `ALIYUN_ACCESS_KEY_SECRET`: used to create the short-lived NLS token.
- `DASHSCOPE_API_KEY`: used by the Qwen OpenAI-compatible endpoint.

For content review, run `python scripts/generate_scene_samples.py` with `LLM_PROVIDER=qwen` and real credentials. The JSONL records `fallback_used` so reviewers can separate generated scenes from reviewed fallbacks.

## Docker deployment

```powershell
docker compose build
docker compose up -d
```

Place the HTTPS certificate at `deploy/certs/fullchain.pem` and the private key at `deploy/certs/privkey.pem`. Nginx redirects HTTP to HTTPS and proxies `/` and `/static/` to the FastAPI container. The audio upload limit is 6 MB; the application enforces the 5 MB application limit. On Linux, run `sudo chown -R 10001:10001 logs` before starting Compose so the non-root app user can write event logs.

## Privacy behavior

- Raw recordings are converted only for the current ASR request and are not persisted.
- Child speech transcripts are not stored in `localStorage` or in event logs.
- `localStorage` stores the signed scene, current step, stars, completed step IDs, target-expression completion, recent themes, and setup choices.
- Event logs contain allowlisted metadata only: theme, difficulty, success, turns, stars, latency, and error type.
- API keys never appear in browser code.
```

- [ ] **Step 7: Run the deployment tests**

Run: `python -m pytest tests/test_deployment_files.py -v`

Expected: PASS.

Run: `docker compose config`

Expected: valid Compose configuration. If Docker is not installed locally, record that in the final verification notes instead of blocking the source tests.

- [ ] **Step 8: Commit**

```bash
git add Dockerfile docker-compose.yml deploy/nginx.conf deploy/certs/.gitkeep logs/.gitkeep .env.example .gitignore README.md tests/test_deployment_files.py
git commit -m "chore: add Docker, HTTPS proxy, and operator docs"
```

---

### Task 19: Content Sampling and Real-Service Smoke Scripts

**Files:**
- Create: `scripts/__init__.py`
- Create: `scripts/generate_scene_samples.py`
- Create: `scripts/smoke_aliyun.py`
- Test: `tests/test_sample_and_smoke_scripts.py`

**Interfaces:**
- Consumes: `Settings`, `build_providers`, `FallbackSceneFactory`, `SceneGenerator`, `ThemeSelector`, `SceneValidator`.
- Produces: `generate_samples(settings, rounds=2) -> list[dict]` and `run_smoke(settings, audio_wav, output_dir) -> dict`.

- [ ] **Step 1: Write the failing script tests**

Create `tests/test_sample_and_smoke_scripts.py`:

```python
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
    assert result["asr_text"] == "I want milk."
    assert result["scene_title"]
    assert Path(result["tts_path"]).exists()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_sample_and_smoke_scripts.py -v`

Expected: FAIL because the scripts do not exist.

- [ ] **Step 3: Implement the scene-sampling script**

Create `scripts/__init__.py` with:

```python
"""Operational helper scripts."""
```

Create `scripts/generate_scene_samples.py`:

```python
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
```

- [ ] **Step 4: Implement the real-service smoke script**

Create `scripts/smoke_aliyun.py`:

```python
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
```

- [ ] **Step 5: Run the script tests**

Run: `python -m pytest tests/test_sample_and_smoke_scripts.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/__init__.py scripts/generate_scene_samples.py scripts/smoke_aliyun.py tests/test_sample_and_smoke_scripts.py
git commit -m "chore: add content sampling and provider smoke scripts"
```

---

### Task 20: Final Verification and Acceptance Record

**Files:**
- Create: `docs/superpowers/acceptance/2026-10-19-kids-english-speaking-demo.md`
- No application code changes in this task.

**Interfaces:**
- Consumes: every earlier task.
- Produces: a recorded verification result and a manual acceptance checklist.

- [ ] **Step 1: Run the fast automated suite**

Run: `python -m pytest -q -m "not slow"`

Expected: all fast tests pass.

- [ ] **Step 2: Run the slow browser matrix**

Run: `python -m pytest -q -m slow`

Expected: all 18 theme/difficulty browser combinations pass.

- [ ] **Step 3: Run lint and configuration checks**

Run: `ruff check backend tests scripts scripts`

Expected: no lint errors.

Run: `docker compose config`

Expected: valid Compose output. If Docker is unavailable on the workstation, record “not run: Docker unavailable” in the acceptance file.

- [ ] **Step 4: Run content sampling**

Set `LLM_PROVIDER=qwen` and real credentials before this step. Run: `python scripts/generate_scene_samples.py --rounds 2 --output artifacts/scene_samples.jsonl`

Expected: 36 samples (18 combinations × 2 rounds). If the provider falls back for any sample, record the reason in the acceptance notes. Manually inspect at least 30 samples for:

- A familiar daily-life task.
- A clear role and communicative goal.
- 4–7 steps and at least one free-expression step.
- Difficulty-appropriate target phrases and hints.
- No violence, horror, adult content, discrimination, brand promotion, or personal-information requests.
- No child name, school, address, phone, or photo request.

- [ ] **Step 5: Run real-provider smoke tests when credentials are available**

Run:

```bash
python scripts/smoke_aliyun.py --audio path/to/spoken-sample.wav
```

Expected:

- ASR returns a non-empty English transcript for the spoken sample.
- Qwen generates a scene that passes validation, or the reported `fallback_used` is `true`.
- TTS writes `artifacts/smoke_tts.mp3`.

If credentials are unavailable, record “not run: cloud credentials unavailable” in the acceptance file.

- [ ] **Step 6: Run device checks**

Record the result of these checks in the acceptance file:

- iPad Safari: microphone permission, recording, playback, responsive layout.
- Android Chrome: microphone permission, recording, playback, responsive layout.
- Desktop Chrome: full practice, refresh restore, restart.
- HTTPS deployment: no mixed-content or microphone-permission errors.

- [ ] **Step 7: Inspect privacy behavior**

Confirm:

- `logs/events.jsonl` contains no audio, transcript, or child text.
- `localStorage` contains no recognized transcript.
- Browser network payloads do not contain API keys.
- `GET /api/health` returns `{"status":"ok"}`.

- [ ] **Step 8: Write the acceptance record**

Create `docs/superpowers/acceptance/2026-10-19-kids-english-speaking-demo.md`:

```markdown
# Kids English Speaking Demo Acceptance Record

- Date: 2026-10-19
- Fast suite: PASS / FAIL
- Slow Playwright matrix: PASS / FAIL
- Ruff: PASS / FAIL
- Docker Compose config: PASS / FAIL / NOT RUN
- Content samples generated: 36
- Content samples manually reviewed: 30+
- Real Aliyun/Qwen smoke test: PASS / FAIL / NOT RUN
- iPad Safari: PASS / FAIL / NOT RUN
- Android Chrome: PASS / FAIL / NOT RUN
- Desktop Chrome: PASS / FAIL / NOT RUN
- Privacy inspection: PASS / FAIL

## Notes

Write the exact observed results, failures, fixes, and any provider or device limitations in this section before committing.
```

Replace the placeholder status words with the actual results before committing. Do not commit a record that claims a test passed without its command output.

- [ ] **Step 9: Commit the acceptance record**

```bash
git add docs/superpowers/acceptance/2026-10-19-kids-english-speaking-demo.md
git commit -m "docs: record demo acceptance results"
```

---

## Plan Self-Review

- **Spec coverage:** Tasks 1–12 cover the domain model, dynamic scene generation, validation, signing, fallback scenes, providers, audio conversion, privacy-safe events, and APIs. Tasks 13–17 cover the start page, practice loop, recording, help, errors, completion, restart, localStorage, and the six-theme × three-difficulty browser matrix. Tasks 18–20 cover Docker/Nginx deployment, content sampling, real-service smoke testing, and acceptance evidence.
- **No placeholders:** Every implementation step includes exact file paths, code, commands, and expected results. The acceptance record contains explicit PASS / FAIL / NOT RUN result fields and a Notes section; those fields must be filled from real command and device output before commit.
- **Type consistency:** `SceneSpec`, `SceneStep`, `SceneEnvelope`, `TurnResponse`, `TurnContext`, `ASRResult`, `TTSResult`, and provider method names are used consistently across tasks. `Difficulty` and `ThemeId` are enum values throughout; API JSON uses their `.value` strings.
- **Intentional implementation notes:** Fallback scenes are padded with free-expression steps until both the difficulty step minimum and free-expression minimum are met (Sprout 4 steps / 1 free turn, Explorer 5 / 2, Star 6 / at least 2). The LLM’s `next_step` is never trusted directly; the backend computes the next step from the validated scene chain. Event names are allowlisted at the API boundary, while server-side scene and turn events use the same allowlisted property set.
