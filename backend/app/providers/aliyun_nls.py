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
        token = self.token_cache.get_token()
        response = await self.client.post(
            f"https://nls-gateway-{self.region}.aliyuncs.com/stream/v1/tts",
            headers={"X-NLS-Token": token},
            json={
                "appkey": self.app_key,
                "token": token,
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
