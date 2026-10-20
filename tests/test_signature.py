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
    now = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
    envelope = make_envelope(make_scene(), ttl_seconds=3600, now=now)
    signature = sign_envelope(envelope, "secret")
    verify_envelope(envelope, signature, "secret", now=now)


def test_tampered_scene_is_rejected():
    now = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
    envelope = make_envelope(make_scene(), ttl_seconds=3600, now=now)
    signature = sign_envelope(envelope, "secret")
    tampered = envelope.model_copy(
        update={"scene": envelope.scene.model_copy(update={"title": "Changed"})}
    )
    with pytest.raises(SceneSignatureError):
        verify_envelope(tampered, signature, "secret", now=now)


def test_expired_envelope_is_rejected():
    issued = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
    envelope = make_envelope(make_scene(), ttl_seconds=60, now=issued)
    signature = sign_envelope(envelope, "secret")
    with pytest.raises(SceneSignatureError):
        verify_envelope(
            envelope,
            signature,
            "secret",
            now=issued + timedelta(seconds=61),
        )


def test_non_ascii_signature_is_rejected():
    now = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
    envelope = make_envelope(make_scene(), ttl_seconds=3600, now=now)
    with pytest.raises(SceneSignatureError):
        verify_envelope(envelope, "invalid-\u00e9", "secret", now=now)


def test_incorrect_secret_is_rejected():
    now = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
    envelope = make_envelope(make_scene(), ttl_seconds=3600, now=now)
    signature = sign_envelope(envelope, "secret")
    with pytest.raises(SceneSignatureError):
        verify_envelope(envelope, signature, "wrong-secret", now=now)


def test_tampered_issued_at_is_rejected():
    issued = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
    envelope = make_envelope(make_scene(), ttl_seconds=3600, now=issued)
    signature = sign_envelope(envelope, "secret")
    tampered = envelope.model_copy(update={"issued_at": issued + timedelta(seconds=1)})
    with pytest.raises(SceneSignatureError):
        verify_envelope(tampered, signature, "secret", now=issued)


def test_tampered_expires_at_is_rejected():
    issued = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
    envelope = make_envelope(make_scene(), ttl_seconds=3600, now=issued)
    signature = sign_envelope(envelope, "secret")
    tampered = envelope.model_copy(
        update={"expires_at": issued + timedelta(seconds=3601)}
    )
    with pytest.raises(SceneSignatureError):
        verify_envelope(tampered, signature, "secret", now=issued)


def test_envelope_at_exact_expiry_boundary_is_rejected():
    issued = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
    envelope = make_envelope(make_scene(), ttl_seconds=60, now=issued)
    signature = sign_envelope(envelope, "secret")
    with pytest.raises(SceneSignatureError):
        verify_envelope(
            envelope,
            signature,
            "secret",
            now=issued + timedelta(seconds=60),
        )
