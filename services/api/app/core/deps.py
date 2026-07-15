from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from functools import wraps
from typing import Annotated, Any

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.errors import Forbidden

TZ_SHANGHAI = timezone(timedelta(hours=8))

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


async def get_current_user(request: Request) -> dict[str, Any]:
    """Mock authentication: returns an admin user for development."""
    return {
        "id": str(uuid.uuid4()),
        "username": "admin",
        "role": "admin",
        "organization_id": str(uuid.uuid4()),
    }


def require_role(*roles: str):
    """Decorator/factory that checks the user has one of the required roles."""

    def dependency(user: Annotated[dict[str, Any], Depends(get_current_user)]) -> dict[str, Any]:
        if user.get("role") not in roles:
            raise Forbidden(f"Role '{user.get('role')}' is not authorized. Required: {roles}")
        return user

    return Depends(dependency)
