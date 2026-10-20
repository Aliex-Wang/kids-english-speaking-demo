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


def test_dockerignore_excludes_local_sensitive_files():
    content = read(".dockerignore")
    for entry in [".env", ".env.*", ".venv", "deploy/certs", "logs", ".git", ".superpowers"]:
        assert entry in content


def test_nginx_requires_https_and_allows_audio_upload():
    content = read("deploy/nginx.conf")
    assert "listen 443 ssl" in content
    assert "ssl_certificate" in content
    assert "ssl_certificate_key" in content
    assert "return 301" in content
    assert "client_max_body_size 6m" in content
    assert "proxy_pass http://app:8000" in content


def test_compose_defines_app_and_nginx():
    content = read("docker-compose.yml")
    for entry in ["env_file", "app:", "nginx:", "depends_on"]:
        assert entry in content


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
    assert "HMAC_SECRET=dev-only-change-me" in content
    assert "replace-with-a-32-byte-random-secret" not in content


def test_gitignore_excludes_secrets_logs_and_certificates():
    content = read(".gitignore")
    for entry in [".env", "deploy/certs/*.pem", "logs/*.jsonl"]:
        assert entry in content


def test_readme_contains_local_and_docker_commands():
    content = read("README.md")
    assert "playwright install chromium" in content
    assert "uvicorn app.main:app --app-dir backend --reload" in content
    assert "docker compose up" in content
    assert "pytest -q -m \"not slow\"" in content


def test_readme_documents_allowlisted_event_fields():
    content = read("README.md")
    assert "request_id" in content
    assert "continued_after_help" in content
