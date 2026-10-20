from contextlib import contextmanager
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


@contextmanager
def _live_server_context(tmp_path):
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
    try:
        deadline = time.time() + 10
        while not server.started and time.time() < deadline:
            time.sleep(0.05)
        if not server.started:
            raise RuntimeError("test server did not start")
        port = server.servers[0].sockets[0].getsockname()[1]
        yield f"http://127.0.0.1:{port}", app
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        if thread.is_alive():
            raise RuntimeError("test server thread did not stop within 5 seconds")


@pytest.fixture
def live_server(tmp_path):
    with _live_server_context(tmp_path) as (url, _app):
        yield url


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


@pytest.fixture
def live_server_app(tmp_path):
    with _live_server_context(tmp_path) as server:
        yield server
