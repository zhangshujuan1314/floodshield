import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.v1.admin.audit import create_audit_log
from app.core.config import settings
from app.core.deps import DbSession, require_role
from app.core.errors import BadRequest, NotFound
from app.models.base import Shelter

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))


class UpdateShelterRequest(BaseModel):
    name: str | None = None
    address: str | None = None
    capacity: int | None = Field(default=None, ge=0)
    status: str | None = None
    contact_phone: str | None = Field(default=None, alias="contactPhone")
    facilities: dict | None = None

    model_config = {"populate_by_name": True}


FIXTURE_SHELTER = {
    "id": "00000000-0000-0000-0000-000000000021",
    "name": "Wuhan Sports Center Shelter",
    "address": "No. 1 Jianghan Rd, Wuhan",
    "capacity": 2000,
    "currentOccupancy": 350,
    "status": "open",
    "contactPhone": "027-88888888",
    "facilities": {"medical": True, "food": True, "water": True, "power": True},
    "location": {"type": "Point", "coordinates": [114.30, 30.58]},
}


def _serialize_shelter(shelter: Shelter) -> dict:
    """Serialize a Shelter model to API response dict."""
    return {
        "id": str(shelter.id),
        "name": shelter.name,
        "address": shelter.address,
        "capacity": shelter.capacity,
        "currentOccupancy": shelter.current_occupancy,
        "status": shelter.status,
        "contactPhone": shelter.contact_phone,
        "facilities": shelter.facilities,
        "location": shelter.location_geojson,
        "createdAt": shelter.created_at.isoformat() if shelter.created_at else None,
        "updatedAt": shelter.updated_at.isoformat() if shelter.updated_at else None,
    }


@router.get("/shelters")
async def list_shelters(
    request: Request,
    session: DbSession,
    status: str | None = Query(default=None, max_length=32),
    user: dict = require_role("admin", "operator"),
):
    """List all shelters with optional status filter."""
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    query = select(Shelter).order_by(Shelter.name)
    if status:
        query = query.where(Shelter.status == status)

    result = await session.execute(query)
    shelters = [_serialize_shelter(row) for row in result.scalars().all()]

    # MOCK_MODE fallback: if DB is empty, return fixture
    if not shelters and settings.MOCK_MODE:
        fixture = {**FIXTURE_SHELTER, "createdAt": now.isoformat(), "updatedAt": now.isoformat()}
        shelters = [fixture]

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": shelters,
    }


@router.patch("/shelters/{shelter_id}")
async def update_shelter(
    shelter_id: str,
    body: UpdateShelterRequest,
    request: Request,
    session: DbSession,
    user: dict = require_role("admin", "operator"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    try:
        sid = uuid.UUID(shelter_id)
    except ValueError:
        raise NotFound(f"Shelter {shelter_id} not found", request_id=request_id)

    # Query real Shelter record
    result = await session.execute(select(Shelter).where(Shelter.id == sid))
    shelter = result.scalar_one_or_none()

    if shelter is None:
        # MOCK_MODE fallback: return fixture if not in DB
        if settings.MOCK_MODE:
            updated = {**FIXTURE_SHELTER, "id": shelter_id}
            if body.name is not None:
                updated["name"] = body.name
            if body.address is not None:
                updated["address"] = body.address
            if body.capacity is not None:
                updated["capacity"] = body.capacity
            if body.status is not None:
                updated["status"] = body.status
            if body.contact_phone is not None:
                updated["contactPhone"] = body.contact_phone
            if body.facilities is not None:
                updated["facilities"] = body.facilities
            updated["updatedAt"] = now.isoformat()
            return {
                "requestId": request_id,
                "dataStatus": "normal",
                "timestamp": now.isoformat(),
                "data": updated,
            }
        raise NotFound(f"Shelter {shelter_id} not found", request_id=request_id)

    # Validate capacity >= current_occupancy when reducing capacity
    if body.capacity is not None and body.capacity < shelter.current_occupancy:
        raise BadRequest(
            f"Capacity ({body.capacity}) cannot be less than current occupancy ({shelter.current_occupancy})",
            request_id=request_id,
        )

    # Track changes for audit log
    changes = {}
    if body.name is not None and body.name != shelter.name:
        changes["name"] = {"old": shelter.name, "new": body.name}
        shelter.name = body.name
    if body.address is not None and body.address != shelter.address:
        changes["address"] = {"old": shelter.address, "new": body.address}
        shelter.address = body.address
    if body.capacity is not None and body.capacity != shelter.capacity:
        changes["capacity"] = {"old": shelter.capacity, "new": body.capacity}
        shelter.capacity = body.capacity
    if body.status is not None and body.status != shelter.status:
        changes["status"] = {"old": shelter.status, "new": body.status}
        shelter.status = body.status
    if body.contact_phone is not None and body.contact_phone != shelter.contact_phone:
        changes["contact_phone"] = {"old": shelter.contact_phone, "new": body.contact_phone}
        shelter.contact_phone = body.contact_phone
    if body.facilities is not None and body.facilities != shelter.facilities:
        changes["facilities"] = {"old": shelter.facilities, "new": body.facilities}
        shelter.facilities = body.facilities

    # Create audit log if there were changes
    if changes:
        await create_audit_log(
            session=session,
            actor_id=user["id"],
            action="update_shelter",
            resource_type="shelter",
            resource_id=str(shelter.id),
            details=changes,
        )
        await session.commit()
        await session.refresh(shelter)

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": _serialize_shelter(shelter),
    }
