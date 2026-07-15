from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.core.deps import get_current_user

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class LoginData(BaseModel):
    access_token: str = Field(alias="accessToken")
    token_type: str = Field(default="bearer", alias="tokenType")
    expires_in: int = Field(default=3600, alias="expiresIn")

    model_config = {"populate_by_name": True}


@router.post("/login")
async def login(body: LoginRequest, request: Request):
    """Mock login endpoint — always succeeds in MOCK_MODE."""
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    # In mock mode, always return a token
    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "accessToken": "mock-jwt-token-for-development",
            "tokenType": "bearer",
            "expiresIn": 3600,
            "user": {
                "id": "00000000-0000-0000-0000-000000000001",
                "username": body.username,
                "role": "admin",
            },
        },
    }


@router.get("/me")
async def me(request: Request):
    """Return current user info from mock auth."""
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)
    user = await get_current_user(request)

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": user,
    }
