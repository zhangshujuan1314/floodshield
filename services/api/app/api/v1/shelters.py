import math
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Query, Request
from sqlalchemy import select

from app.core.deps import DbSession
from app.models.base import Shelter

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))

# Hardcoded fixtures for MOCK_MODE fallback when DB is empty
_FIXTURE_SHELTERS = [
    {
        "id": "s0000000-0000-0000-0000-000000000001",
        "name": "Wuhan Sports Center Shelter",
        "address": "No. 1 Jianghan Rd, Wuhan",
        "capacity": 2000,
        "currentOccupancy": 350,
        "status": "open",
        "contactPhone": "027-88888888",
        "facilities": {"medical": True, "food": True, "water": True, "power": True, "wifi": True},
        "location": {"type": "Point", "coordinates": [114.30, 30.58]},
        "distanceM": 1200,
    },
    {
        "id": "s0000000-0000-0000-0000-000000000002",
        "name": "Hongshan Gymnasium Emergency Shelter",
        "address": "No. 100 Luoyu Rd, Wuhan",
        "capacity": 1500,
        "currentOccupancy": 120,
        "status": "open",
        "contactPhone": "027-77777777",
        "facilities": {"medical": True, "food": True, "water": True, "power": True, "wifi": False},
        "location": {"type": "Point", "coordinates": [114.36, 30.52]},
        "distanceM": 2800,
    },
    {
        "id": "s0000000-0000-0000-0000-000000000003",
        "name": "Jianghan Community Center",
        "address": "No. 50 Minzu St, Wuhan",
        "capacity": 500,
        "currentOccupancy": 480,
        "status": "nearly_full",
        "contactPhone": "027-66666666",
        "facilities": {"medical": False, "food": True, "water": True, "power": True, "wifi": False},
        "location": {"type": "Point", "coordinates": [114.27, 30.60]},
        "distanceM": 4500,
    },
]


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in meters between two lat/lon points."""
    R = 6_371_000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _shelter_to_response(shelter: Shelter, distance_m: float) -> dict[str, Any]:
    return {
        "id": str(shelter.id),
        "name": shelter.name,
        "address": shelter.address,
        "distanceM": round(distance_m),
        "capacity": shelter.capacity,
        "currentOccupancy": shelter.current_occupancy,
        "status": shelter.status,
        "contactPhone": shelter.contact_phone,
        "facilities": shelter.facilities or {},
        "location": shelter.location_geojson or {},
    }


@router.get("/nearby")
async def nearby_shelters(
    request: Request,
    db: DbSession,
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    radius_m: int = Query(default=5000, ge=100, le=50000, alias="radiusM"),
    accessibility: str | None = Query(default=None, description="Comma-separated facility keys required"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    # Parse required accessibility features
    required_features: set[str] = set()
    if accessibility:
        required_features = {f.strip().lower() for f in accessibility.split(",") if f.strip()}

    # Query all non-closed shelters
    stmt = select(Shelter).where(Shelter.status != "closed")
    result = await db.execute(stmt)
    db_shelters = list(result.scalars().all())

    # If DB has data, use it; otherwise fall back to fixtures
    if db_shelters:
        shelters: list[dict[str, Any]] = []
        for s in db_shelters:
            # Compute distance
            loc = s.location_geojson or {}
            coords = (loc.get("coordinates") or []) if isinstance(loc, dict) else []
            if len(coords) >= 2:
                dist = _haversine_m(lat, lon, coords[1], coords[0])
            else:
                dist = 0.0

            # Filter by radius
            if dist > radius_m:
                continue

            # Filter by accessibility
            if required_features:
                facilities = s.facilities or {}
                if not all(facilities.get(f, False) for f in required_features):
                    continue

            shelters.append(_shelter_to_response(s, dist))

        shelters.sort(key=lambda x: x["distanceM"])
    else:
        # MOCK_MODE fallback: use fixtures, apply accessibility filter
        shelters = list(_FIXTURE_SHELTERS)
        if required_features:
            shelters = [
                s for s in shelters
                if all(s.get("facilities", {}).get(f, False) for f in required_features)
            ]

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": shelters,
    }
