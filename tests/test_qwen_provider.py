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
