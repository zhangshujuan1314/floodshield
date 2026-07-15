import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request

from app.core.config import settings
from app.core.errors import NotFound, ServiceUnavailable
from app.providers import factory as provider_factory
from app.schemas.route import EvacuationRouteRequest

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))


@router.post("/evacuation")
async def compute_evacuation_route(body: EvacuationRouteRequest, request: Request):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)
    start_ms = datetime.now().timestamp() * 1000

    map_provider = provider_factory("map", settings.MAP_PROVIDER)
    result = await map_provider.compute_route(
        origin=body.origin.coordinates,
        destination=body.destination.coordinates,
        transport_mode=body.transport_mode,
        avoid_hazards=body.avoid_hazards,
    )

    calc_ms = int(datetime.now().timestamp() * 1000 - start_ms)

    if not result["is_viable"]:
        return {
            "requestId": request_id,
            "dataStatus": "normal",
            "timestamp": now.isoformat(),
            "data": {
                "id": result["id"],
                "routeGeojson": None,
                "distanceM": 0,
                "durationS": 0,
                "safetyScore": 0.0,
                "warnings": result["warnings"],
                "isViable": False,
                "evidence": result.get("evidence", []),
                "dataTime": now.isoformat(),
                "expiresAt": (now + timedelta(minutes=15)).isoformat(),
                "calculationTimeMs": calc_ms,
            },
        }

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "id": result["id"],
            "routeGeojson": result["route_geojson"],
            "distanceM": result["distance_m"],
            "durationS": result["duration_s"],
            "safetyScore": result["safety_score"],
            "warnings": result["warnings"],
            "isViable": True,
            "evidence": result.get("evidence", []),
            "dataTime": now.isoformat(),
            "expiresAt": (now + timedelta(minutes=15)).isoformat(),
            "calculationTimeMs": calc_ms,
        },
    }


@router.get("/{route_id}")
async def get_route(route_id: str, request: Request):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    try:
        uuid.UUID(route_id)
    except ValueError:
        raise NotFound(f"Route {route_id} not found", request_id=request_id)

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "id": route_id,
            "routeGeojson": {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [114.30, 30.58],
                        [114.31, 30.57],
                        [114.33, 30.55],
                    ],
                },
            },
            "distanceM": 2500.0,
            "durationS": 1800.0,
            "safetyScore": 0.92,
            "warnings": [],
            "isViable": True,
        },
    }
