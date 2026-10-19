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
