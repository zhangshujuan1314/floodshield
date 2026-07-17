"""Tests for JWT authentication system."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import jwt
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.deps import create_access_token, get_current_user, require_role, verify_token
from app.core.errors import AppError, Forbidden, Unauthorized, app_error_handler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_token(user_id: str = "u1", role: str = "admin", org_id: str = "o1", **extra_claims) -> str:
    """Helper to build a token with sensible defaults."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "org_id": org_id,
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
        **extra_claims,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _make_expired_token(user_id: str = "u1", role: str = "admin", org_id: str = "o1") -> str:
    """Create a token that is already expired."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "org_id": org_id,
        "iat": now - timedelta(hours=2),
        "exp": now - timedelta(hours=1),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# ---------------------------------------------------------------------------
# Unit tests for create_access_token / verify_token
# ---------------------------------------------------------------------------

class TestCreateAccessToken:
    def test_returns_valid_jwt_string(self):
        token = create_access_token("user-1", "admin", "org-1")
        assert isinstance(token, str)
        # Should be three dot-separated base64 segments
        assert token.count(".") == 2

    def test_payload_contains_expected_claims(self):
        token = create_access_token("user-1", "viewer", "org-2")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == "user-1"
        assert payload["role"] == "viewer"
        assert payload["org_id"] == "org-2"
        assert "iat" in payload
        assert "exp" in payload


class TestVerifyToken:
    def test_decodes_valid_token(self):
        token = create_access_token("u1", "admin", "o1")
        payload = verify_token(token)
        assert payload["sub"] == "u1"
        assert payload["role"] == "admin"
        assert payload["org_id"] == "o1"

    def test_raises_unauthorized_on_expired_token(self):
        token = _make_expired_token()
        with pytest.raises(Unauthorized):
            verify_token(token)

    def test_raises_unauthorized_on_garbage(self):
        with pytest.raises(Unauthorized):
            verify_token("not-a-jwt-at-all")

    def test_raises_unauthorized_on_tampered_token(self):
        token = create_access_token("u1", "admin", "o1")
        # Tamper with the signature by flipping last char
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        with pytest.raises(Unauthorized):
            verify_token(tampered)


# ---------------------------------------------------------------------------
# Integration-style tests using a minimal FastAPI app
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_app():
    """Build a minimal FastAPI app exercising get_current_user and require_role."""
    app = FastAPI()
    app.add_exception_handler(AppError, app_error_handler)

    @app.get("/protected")
    async def protected(user=Depends(get_current_user)):
        return user

    @app.get("/admin-only")
    async def admin_only(user=require_role("admin")):
        return user

    @app.get("/viewer-or-admin")
    async def viewer_or_admin(user=require_role("admin", "viewer")):
        return user

    return app


class TestGetCurrentUser:
    """Tests for the get_current_user dependency."""

    def test_valid_token_returns_user(self, auth_app):
        token = _make_token(user_id="user-42", role="viewer", org_id="org-99")
        client = TestClient(auth_app)
        resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "user-42"
        assert data["role"] == "viewer"
        assert data["organization_id"] == "org-99"

    def test_expired_token_returns_401(self, auth_app):
        token = _make_expired_token()
        client = TestClient(auth_app)
        resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_no_token_mock_mode_returns_admin(self, auth_app):
        """In MOCK_MODE, missing Authorization header falls back to mock admin."""
        with patch.object(settings, "MOCK_MODE", True):
            client = TestClient(auth_app)
            resp = client.get("/protected")
        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "admin"
        assert data["username"] == "admin"

    def test_no_token_non_mock_mode_returns_401(self, auth_app):
        """In non-MOCK_MODE, missing Authorization header is a 401."""
        with patch.object(settings, "MOCK_MODE", False):
            client = TestClient(auth_app)
            resp = client.get("/protected")
        assert resp.status_code == 401

    def test_malformed_auth_header_returns_401(self, auth_app):
        client = TestClient(auth_app)
        resp = client.get("/protected", headers={"Authorization": "Basic foobar"})
        assert resp.status_code == 401

    def test_bearer_prefix_without_token_returns_401(self, auth_app):
        client = TestClient(auth_app)
        resp = client.get("/protected", headers={"Authorization": "Bearer"})
        # "Bearer" alone splits into 1 part, not 2 -> 401
        assert resp.status_code == 401


class TestRequireRole:
    """Tests for the require_role dependency."""

    def test_correct_role_passes(self, auth_app):
        token = _make_token(role="admin")
        client = TestClient(auth_app)
        resp = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["role"] == "admin"

    def test_wrong_role_blocked(self, auth_app):
        token = _make_token(role="viewer")
        client = TestClient(auth_app)
        resp = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_multi_role_passes(self, auth_app):
        token = _make_token(role="viewer")
        client = TestClient(auth_app)
        resp = client.get("/viewer-or-admin", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["role"] == "viewer"

    def test_multi_role_blocks_unlisted(self, auth_app):
        token = _make_token(role="editor")
        client = TestClient(auth_app)
        resp = client.get("/viewer-or-admin", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
