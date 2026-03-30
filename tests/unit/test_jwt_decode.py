"""Unit tests for JWT decode with issuer validation (SEC-C4)."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import jwt as pyjwt
import pytest
from fastapi import HTTPException

from cherry_evals.config import Settings


def _make_token(secret: str, issuer: str | None = None, audience: str = "authenticated") -> str:
    """Build a minimal HS256 JWT for testing."""
    payload: dict = {
        "sub": "user-abc",
        "email": "user@example.com",
        "aud": audience,
        "exp": datetime.now(UTC) + timedelta(hours=1),
        "iat": datetime.now(UTC),
    }
    if issuer is not None:
        payload["iss"] = issuer
    return pyjwt.encode(payload, secret, algorithm="HS256")


def _settings_with(supabase_url: str = "", supabase_jwt_secret: str = "secret") -> Settings:
    return Settings(
        auth_enabled=True,
        supabase_jwt_secret=supabase_jwt_secret,
        supabase_url=supabase_url,
    )


class TestJWTDecodeIssuerValidation:
    """SEC-C4: JWT decode must validate issuer when supabase_url is configured."""

    def test_valid_token_without_supabase_url_passes(self):
        """When supabase_url is empty, issuer is not checked — token passes."""
        from api.deps import _decode_supabase_jwt

        settings = _settings_with(supabase_url="", supabase_jwt_secret="secret")
        token = _make_token("secret")  # no issuer in token

        with patch("api.deps.settings", settings):
            payload = _decode_supabase_jwt(token)

        assert payload["sub"] == "user-abc"

    def test_valid_token_with_correct_issuer_passes(self):
        """When supabase_url is set, token with matching issuer passes."""
        from api.deps import _decode_supabase_jwt

        supabase_url = "https://abc123.supabase.co"
        expected_issuer = supabase_url + "/auth/v1"
        settings = _settings_with(supabase_url=supabase_url, supabase_jwt_secret="secret")
        token = _make_token("secret", issuer=expected_issuer)

        with patch("api.deps.settings", settings):
            payload = _decode_supabase_jwt(token)

        assert payload["sub"] == "user-abc"

    def test_token_with_wrong_issuer_rejected(self):
        """When supabase_url is set, token with wrong issuer raises 401."""
        from api.deps import _decode_supabase_jwt

        supabase_url = "https://abc123.supabase.co"
        settings = _settings_with(supabase_url=supabase_url, supabase_jwt_secret="secret")
        token = _make_token("secret", issuer="https://evil.example.com/auth/v1")

        with patch("api.deps.settings", settings):
            with pytest.raises(HTTPException) as exc_info:
                _decode_supabase_jwt(token)

        assert exc_info.value.status_code == 401

    def test_token_missing_issuer_rejected_when_supabase_url_set(self):
        """When supabase_url is set, token with no iss claim is rejected."""
        from api.deps import _decode_supabase_jwt

        supabase_url = "https://abc123.supabase.co"
        settings = _settings_with(supabase_url=supabase_url, supabase_jwt_secret="secret")
        token = _make_token("secret", issuer=None)  # no iss field

        with patch("api.deps.settings", settings):
            with pytest.raises(HTTPException) as exc_info:
                _decode_supabase_jwt(token)

        assert exc_info.value.status_code == 401

    def test_supabase_url_trailing_slash_normalised(self):
        """Trailing slash on supabase_url should not cause issuer mismatch."""
        from api.deps import _decode_supabase_jwt

        supabase_url = "https://abc123.supabase.co/"
        expected_issuer = "https://abc123.supabase.co/auth/v1"
        settings = _settings_with(supabase_url=supabase_url, supabase_jwt_secret="secret")
        token = _make_token("secret", issuer=expected_issuer)

        with patch("api.deps.settings", settings):
            payload = _decode_supabase_jwt(token)

        assert payload["sub"] == "user-abc"

    def test_expired_token_rejected(self):
        """Expired tokens must raise 401 regardless of issuer config."""
        from api.deps import _decode_supabase_jwt

        settings = _settings_with(supabase_jwt_secret="secret")
        expired_payload = {
            "sub": "user-abc",
            "aud": "authenticated",
            "exp": datetime.now(UTC) - timedelta(hours=1),
            "iat": datetime.now(UTC) - timedelta(hours=2),
        }
        token = pyjwt.encode(expired_payload, "secret", algorithm="HS256")

        with patch("api.deps.settings", settings):
            with pytest.raises(HTTPException) as exc_info:
                _decode_supabase_jwt(token)

        assert exc_info.value.status_code == 401

    def test_bad_signature_rejected(self):
        """Tokens signed with wrong key must raise 401."""
        from api.deps import _decode_supabase_jwt

        settings = _settings_with(supabase_jwt_secret="correct-secret")
        token = _make_token("wrong-secret")

        with patch("api.deps.settings", settings):
            with pytest.raises(HTTPException) as exc_info:
                _decode_supabase_jwt(token)

        assert exc_info.value.status_code == 401
