from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.core.deps import MOCK_ORG_ID, create_access_token, get_current_user
from app.core.errors import Unauthorized

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))

# ---------------------------------------------------------------------------
# Password helpers — pbkdf2_hmac based, no bcrypt dependency
# ---------------------------------------------------------------------------

# Stored format: "pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>"
_ALGO = "sha256"
_ITERATIONS = 260_000  # OWASP 2023 recommendation for PBKDF2-SHA256


def get_password_hash(password: str) -> str:
    """Hash a password with PBKDF2-SHA256 and return a storable string."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac(_ALGO, password.encode(), salt, _ITERATIONS)
    return f"pbkdf2_{_ALGO}${_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a stored PBKDF2 hash."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4:
            return False
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        stored_hash = bytes.fromhex(parts[3])
        computed = hashlib.pbkdf2_hmac(_ALGO, plain_password.encode(), salt, iterations)
        return hmac.compare_digest(computed, stored_hash)
    except (ValueError, IndexError):
        return False


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class LoginData(BaseModel):
    access_token: str = Field(alias="accessToken")
    token_type: str = Field(default="bearer", alias="tokenType")
    expires_in: int = Field(alias="expiresIn")
    user: dict

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/login")
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db_session)):
    """Authenticate user and return a real JWT token."""
    from app.models.base import User  # local import to avoid circular deps at module level

    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    # Look up user in database
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()

    if user is None:
        # In MOCK_MODE, accept any credentials and create a mock user on the fly
        if settings.MOCK_MODE:
            mock_user_id = "00000000-0000-0000-0000-000000000001"
            token = create_access_token(user_id=mock_user_id, role="admin", org_id=MOCK_ORG_ID)
            return {
                "requestId": request_id,
                "dataStatus": "normal",
                "timestamp": now.isoformat(),
                "data": {
                    "accessToken": token,
                    "tokenType": "bearer",
                    "expiresIn": settings.JWT_EXPIRE_MINUTES * 60,
                    "user": {
                        "id": mock_user_id,
                        "username": body.username,
                        "role": "admin",
                    },
                },
            }
        # Dummy hash to prevent timing-based username enumeration
        hashlib.pbkdf2_hmac("sha256", b"dummy-password", os.urandom(16), 260000)
        raise Unauthorized("Invalid username or password.")

    # Always verify password first (constant-time: 1 PBKDF2 for all paths)
    if not verify_password(body.password, user.hashed_password):
        raise Unauthorized("Invalid username or password.")

    # Check is_active AFTER password verification to prevent timing side-channel
    if not user.is_active:
        raise Unauthorized("Account is deactivated.")

    token = create_access_token(
        user_id=str(user.id),
        role=user.role,
        org_id=str(user.organization_id) if user.organization_id else "",
    )

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "accessToken": token,
            "tokenType": "bearer",
            "expiresIn": settings.JWT_EXPIRE_MINUTES * 60,
            "user": {
                "id": str(user.id),
                "username": user.username,
                "role": user.role,
            },
        },
    }


@router.get("/me")
async def me(request: Request):
    """Return current user info from JWT auth."""
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)
    user = await get_current_user(request)

    # Never expose hashed_password in the response
    safe_user = {k: v for k, v in user.items() if k != "hashed_password"}

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": safe_user,
    }
