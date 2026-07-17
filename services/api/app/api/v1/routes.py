import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Request
from sqlalchemy import select

from app.core.config import settings
from app.core.deps import DbSession
from app.core.errors import NotFound
from app.models.base import RouteRequest, RouteResult
from app.providers import factory as provider_factory
from app.schemas.route import EvacuationRouteRequest

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))

# Hardcoded fixture for MOCK_MODE fallback when route not in DB
_FIXTURE_ROUTE = {
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
}


def _route_result_to_data(route_result: RouteResult, route_request: RouteRequest | None = None) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": str(route_result.id),
        "routeGeojson": route_result.route_geojson,
        "distanceM": route_result.distance_m,
        "durationS": route_result.duration_s,
        "safetyScore": route_result.safety_score,
        "warnings": route_result.warnings or [],
        "isViable": route_result.is_viable,
    }
    if route_request:
        data["evidence"] = []
    return data


@router.post("/evacuation")
async def compute_evacuation_route(body: EvacuationRouteRequest, request: Request, db: DbSession):
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

    # Persist request and result to DB
    route_req = RouteRequest(
        origin_geojson={"type": "Point", "coordinates": body.origin.coordinates},
        destination_geojson={"type": "Point", "coordinates": body.destination.coordinates},
        transport_mode=body.transport_mode,
        avoid_hazards=body.avoid_hazards,
    )
    db.add(route_req)
    await db.flush()  # assign route_req.id

    route_res = RouteResult(
        request_id=route_req.id,
        route_geojson=result.get("route_geojson") or {},
        distance_m=result.get("distance_m", 0),
        duration_s=result.get("duration_s", 0),
        safety_score=result.get("safety_score", 0),
        warnings=result.get("warnings", []),
        provider=result.get("provider", "unknown"),
        is_viable=result.get("is_viable", False),
    )
    db.add(route_res)
    await db.commit()

    if not result["is_viable"]:
        return {
            "requestId": request_id,
            "dataStatus": "normal",
            "timestamp": now.isoformat(),
            "data": {
                "id": str(route_res.id),
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
            "id": str(route_res.id),
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
async def get_route(route_id: str, request: Request, db: DbSession):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    try:
        route_uuid = uuid.UUID(route_id)
    except ValueError:
        raise NotFound(f"Route {route_id} not found", request_id=request_id)

    # Query RouteResult by id
    result = await db.execute(select(RouteResult).where(RouteResult.id == route_uuid))
    route_result = result.scalar_one_or_none()

    if route_result is not None:
        # Load the associated request
        req_stmt = select(RouteRequest).where(RouteRequest.id == route_result.request_id)
        req_result = await db.execute(req_stmt)
        route_request = req_result.scalar_one_or_none()

        data = _route_result_to_data(route_result, route_request)
        return {
            "requestId": request_id,
            "dataStatus": "normal",
            "timestamp": now.isoformat(),
            "data": data,
        }

    # MOCK_MODE fallback: if not in DB, return fixture
    if settings.MOCK_MODE:
        data = {"id": route_id, **_FIXTURE_ROUTE}
        return {
            "requestId": request_id,
            "dataStatus": "normal",
            "timestamp": now.isoformat(),
            "data": data,
        }

    raise NotFound(f"Route {route_id} not found", request_id=request_id)
