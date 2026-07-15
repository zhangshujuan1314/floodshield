import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.core.deps import require_role
from app.core.errors import NotFound

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))


class UpdateShelterRequest(BaseModel):
    name: str | None = None
    capacity: int | None = Field(default=None, ge=0)
    current_occupancy: int | None = Field(default=None, alias="currentOccupancy", ge=0)
    status: str | None = None
    contact_phone: str | None = Field(default=None, alias="contactPhone")
    facilities: dict | None = None

    model_config = {"populate_by_name": True}


@router.patch("/shelters/{shelter_id}")
async def update_shelter(
    shelter_id: str,
    body: UpdateShelterRequest,
    request: Request,
    user: dict = require_role("admin", "operator"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    try:
        uuid.UUID(shelter_id)
    except ValueError:
        raise NotFound(f"Shelter {shelter_id} not found", request_id=request_id)

    # Mock update — return the merged result
    updated = {
        "id": shelter_id,
        "name": body.name or "Wuhan Sports Center Shelter",
        "address": "No. 1 Jianghan Rd, Wuhan",
        "capacity": body.capacity or 2000,
        "currentOccupancy": body.current_occupancy if body.current_occupancy is not None else 350,
        "status": body.status or "open",
        "contactPhone": body.contact_phone or "027-88888888",
        "facilities": body.facilities or {"medical": True, "food": True, "water": True, "power": True},
        "location": {"type": "Point", "coordinates": [114.30, 30.58]},
        "updatedAt": now.isoformat(),
    }

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": updated,
    }
