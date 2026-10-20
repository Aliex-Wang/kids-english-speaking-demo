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
