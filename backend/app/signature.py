import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

from app.schemas import SceneEnvelope, SceneSpec


class SceneSignatureError(ValueError):
    """Raised when a signed scene is invalid, expired, or tampered with."""


def make_envelope(
    scene: SceneSpec,
    ttl_seconds: int,
    now: datetime | None = None,
) -> SceneEnvelope:
    issued_at = now or datetime.now(timezone.utc)
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
    if not hmac.compare_digest(expected, signature):
        raise SceneSignatureError("invalid signature")
    current = now or datetime.now(timezone.utc)
    if envelope.expires_at <= current:
        raise SceneSignatureError("scene expired")
