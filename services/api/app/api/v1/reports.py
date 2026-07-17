import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request

from app.core.errors import NotFound
from app.schemas.report import CreateReportRequest

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))


def _fuzz_location(location_geojson: dict) -> dict:
    """Fuzzy location to ~100m resolution for public reports.
    Precise location should only be stored separately for verification/rescue."""
    if location_geojson.get("type") == "Point" and "coordinates" in location_geojson:
        coords = location_geojson["coordinates"]
        # 3 decimal places ≈ 111m precision
        fuzzed = [round(coords[0], 3), round(coords[1], 3)]
        return {**location_geojson, "coordinates": fuzzed, "precision": "approximate"}
    return location_geojson


@router.post("")
async def create_report(body: CreateReportRequest, request: Request):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)
    report_id = uuid.uuid4()

    location_geojson = None
    if body.location:
        raw_location = body.location.model_dump()
        # Always fuzz location for storage — precise coords only for verification
        location_geojson = _fuzz_location(raw_location)

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "id": str(report_id),
            "reportType": body.report_type,
            "severity": body.severity,
            "description": body.description,
            "photoUrl": body.photo_url,
            "location": location_geojson,
            "status": "pending_review",
            "createdAt": now.isoformat(),
        },
    }


@router.get("/{report_id}")
async def get_report(report_id: str, request: Request):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    # Validate UUID format
    try:
        uuid.UUID(report_id)
    except ValueError:
        raise NotFound(f"Report {report_id} not found", request_id=request_id)

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "id": report_id,
            "reportType": "flood",
            "severity": "high",
            "description": "Water level rising rapidly near the bridge.",
            "photoUrl": None,
            "location": {"type": "Point", "coordinates": [121.47, 31.23]},
            "status": "pending_review",
            "createdAt": (now - timedelta(minutes=30)).isoformat(),
        },
    }
