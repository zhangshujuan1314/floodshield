from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query, Request

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))


@router.get("/nearby")
async def nearby_shelters(
    request: Request,
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    radius_m: int = Query(default=5000, ge=100, le=50000, alias="radiusM"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    shelters = [
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

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": shelters,
    }
