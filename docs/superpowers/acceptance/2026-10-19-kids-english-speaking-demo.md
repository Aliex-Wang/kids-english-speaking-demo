# Kids English Speaking Demo Acceptance Record

- Date: 2026-10-20
- Fast suite: PASS
- Slow Playwright matrix: PASS
- Ruff: PASS
- Docker Compose config: PASS
- Content samples generated: 36 (fake providers)
- Content samples manually reviewed: N/A (fake-provider output; real Qwen content review NOT RUN)
- Real Aliyun/Qwen smoke test: NOT RUN
- iPad Safari: NOT RUN
- Android Chrome: NOT RUN
- Desktop Chrome: NOT RUN
- Privacy inspection: PASS

## Fast suite

Command (audio-capable ffmpeg prepended to `PATH`):

```powershell
$env:PATH = 'D:\Program Files\EVCapture;' + $env:PATH
.venv\Scripts\python.exe -m pytest -q -m "not slow"
```

Result:

```text
173 passed, 18 deselected in 48.14s
```

## Slow Playwright matrix

Command:

```powershell
$env:PATH = 'D:\Program Files\EVCapture;' + $env:PATH
.venv\Scripts\python.exe -m pytest -q -m slow
```

Result:

```text
18 passed, 173 deselected in 48.22s
```

All 18 theme/difficulty browser combinations pass.

## Ruff and lint policy

Command:

```text
.venv\Scripts\ruff.exe check backend tests scripts
```

Result:

```text
All checks passed!
```

Lint policy (recorded, not applied as behavior changes):

- Project `ruff.toml` sets `target-version = "py312"` and selects Ruff's default
  correctness gate `["E4", "E7", "E9", "F"]`.
- `E402` is waived only for `scripts/*.py` via `[lint.per-file-ignores]`, because
  the operational scripts must `sys.path.insert(0, .../backend)` before importing
  `app.*` to run standalone from the repository root.
- The intentional FastAPI `B008`, fallback `BLE001`, and style-only `I`/`UP`/`PLW`
  findings are outside this demo's lint policy and are left unchanged.

## Docker Compose config

Command (temporary ignored `.env` copied from `.env.example`, removed afterward):

```text
docker compose config
```

Result: valid Compose output for project `english_learn` with services `app` and
`nginx`. The temporary `.env` was removed after the check and is not committed.

## Content sampling (fake providers, script exercise only)

Command (fake providers forced via environment; real Qwen was not called):

```text
.venv\Scripts\python.exe scripts/generate_scene_samples.py --rounds 2 --output artifacts/scene_samples.jsonl
```

Result:

```text
wrote 36 samples to artifacts\scene_samples.jsonl
```

36 JSONL lines = 18 theme/difficulty combinations x 2 rounds. Structural check:
all 6 themes x 3 difficulties appear exactly twice; step counts are 4/5/6; every
scene contains at least one `free_expression` step. A keyword scan of all 36
samples found no violence, horror, adult, discrimination, brand-promotion, or
personal-information content.

Label: this is fake-provider output (deterministic fallback templates served by
`FakeLLMProvider`), used to exercise the sampling script. It is NOT Qwen content
review. The generated `artifacts/` directory is gitignored and not committed.

## Real Aliyun/Qwen smoke test

NOT RUN: cloud credentials unavailable. `DASHSCOPE_API_KEY`,
`ALIYUN_ACCESS_KEY_ID`, `ALIYUN_ACCESS_KEY_SECRET`, and `ALIYUN_NLS_APP_KEY` are
all unset in this environment.

The smoke script's ASR -> scene -> TTS path was instead exercised with fake
providers:

```text
.venv\Scripts\python.exe scripts/smoke_aliyun.py --output-dir artifacts/smoke
```

```text
{"asr_text": "Yes, I am ready.", "scene_title": "Morning Helpers",
 "fallback_used": false, "tts_path": "artifacts\\smoke\\smoke_tts.wav",
 "tts_media_type": "audio/wav"}
```

This is fake-provider script verification only; real cloud smoke remains NOT RUN.

## Device checks

- iPad Safari: NOT RUN - no physical iPad available in this environment.
- Android Chrome: NOT RUN - no physical Android device available in this environment.
- Desktop Chrome: NOT RUN - no interactive desktop browser session available in
  this environment (Playwright matrix runs headless Chromium with fake media
  streams, which is recorded under the slow matrix, not as a manual device check).
- HTTPS deployment: NOT RUN - no deployed HTTPS environment available; the Compose
  configuration (nginx + app) was validated with `docker compose config` only.

## Privacy inspection

PASS at code level (no physical device or live deployment was exercised):

- `logs/events.jsonl` contains only allowlisted event fields. The
  `EventLogger` raises `ValueError` for any property outside
  `ALLOWED_EVENT_PROPERTIES` (`tests/test_events.py` parametrized rejection of
  `text`, `audio`, `transcript`, `child_text`). The one observed log line is a
  `scene_generated` event with `theme`, `difficulty`, `success`, `latency_ms`,
  `error_type`, and `request_id` - no audio, transcript, or child text.
- `localStorage` contains no recognized transcript. `practice.js` pushes only
  `step_id`, `accepted`, `attempts`, `help_used` into `history`; the
  `TurnSummary` schema has no transcript field, and `test_e2e_practice.py`
  asserts `recognized_text` and `transcript` are absent from the persisted
  practice state.
- Browser network payloads contain no API keys. No key/secret/token literal
  appears in `backend/app/static/js/*.js` or `backend/app/templates/*.html`;
  credentials exist only server-side in `Settings`.
- `GET /api/health` returns `200 {"status":"ok"}` (verified live via
  `TestClient` and covered by `tests/test_health.py`).

## Notes

- Environment limitations:
  - ffmpeg is not on the default `PATH`; the E2E suites require
    `D:\Program Files\EVCapture` prepended. The Docker image installs ffmpeg.
  - Aliyun/Qwen cloud credentials are unavailable, so real-provider smoke and
    Qwen content review were not performed.
  - No iPad/Android/Desktop physical devices or deployed HTTPS environment are
    available for device checks.
- Content sampling used fake providers and produced deterministic fallback
  templates, not Qwen-generated content.
- `git` reports an `LF will be replaced by CRLF` warning for the newline cleanups
  because `core.autocrlf=true`; committed content is LF-normalized.
- Generated `artifacts/` and the temporary `.env` were not committed.

## Acceptance

This record documents honest verification results. Tests that could not be run
for lack of credentials or devices are recorded as NOT RUN with their reasons;
no NOT RUN item is claimed as PASS.
