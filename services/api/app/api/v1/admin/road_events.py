import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.core.deps import require_role

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))


class CreateRoadEventRequest(BaseModel):
    event_type: str = Field(alias="eventType", min_length=1, max_length=32)
    severity: str = Field(min_length=1, max_length=32)
    description: str | None = None
    road_name: str = Field(alias="roadName", min_length=1, max_length=256)
    location: dict | None = None
    effective_at: datetime | None = Field(default=None, alias="effectiveAt")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")

    model_config = {"populate_by_name": True}


@router.post("/road-events")
async def create_road_event(
    body: CreateRoadEventRequest,
    request: Request,
    user: dict = require_role("admin", "operator"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)
    event_id = uuid.uuid4()

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "id": str(event_id),
            "eventType": body.event_type,
            "severity": body.severity,
            "description": body.description,
            "roadName": body.road_name,
            "location": body.location,
            "isActive": True,
            "effectiveAt": (body.effective_at or now).isoformat(),
            "expiresAt": body.expires_at.isoformat() if body.expires_at else None,
            "source": "manual",
            "createdAt": now.isoformat(),
        },
    }
