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
