from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Annotated, Any

import jwt
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.core.errors import Forbidden, Unauthorized

TZ_SHANGHAI = timezone(timedelta(hours=8))

MOCK_USER_ID = "00000000-0000-0000-0000-000000000001"
MOCK_ORG_ID = "00000000-0000-0000-0000-000000000002"

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


def create_access_token(user_id: str, role: str, org_id: str) -> str:
    """Create a signed JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "role": role,
        "org_id": org_id,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token. Raises Unauthorized on failure."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise Unauthorized("Token has expired.")
    except jwt.InvalidTokenError:
        raise Unauthorized("Invalid token.")


async def get_current_user(request: Request) -> dict[str, Any]:
    """Authenticate request via JWT Bearer token.

    In MOCK_MODE, if no token is provided, returns a mock admin user for
    backward compatibility.  A valid token is still respected in MOCK_MODE.
    """
    auth_header: str | None = request.headers.get("Authorization")

    if auth_header:
        parts = auth_header.split(None, 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
            payload = verify_token(token)
            return {
                "id": payload.get("sub", ""),
                "username": payload.get("username", ""),
                "role": payload.get("role", "viewer"),
                "organization_id": payload.get("org_id", ""),
            }
        raise Unauthorized("Invalid Authorization header format. Expected 'Bearer <token>'.")

    # No Authorization header — MOCK_MODE fallback
    if settings.MOCK_MODE:
        return {
            "id": MOCK_USER_ID,
            "username": "admin",
            "role": "admin",
            "organization_id": MOCK_ORG_ID,
        }

    raise Unauthorized("Missing Authorization header.")


def require_role(*roles: str):
    """Decorator/factory that checks the user has one of the required roles."""

    def dependency(user: Annotated[dict[str, Any], Depends(get_current_user)]) -> dict[str, Any]:
        if user.get("role") not in roles:
            raise Forbidden(f"Role '{user.get('role')}' is not authorized. Required: {roles}")
        return user

    return Depends(dependency)
