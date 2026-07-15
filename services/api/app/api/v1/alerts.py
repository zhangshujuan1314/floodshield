import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query, Request

from app.core.errors import NotFound

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))

# In-memory fixture alerts
_FIXTURE_ALERTS: list[dict] = []


def _build_fixtures() -> list[dict]:
    now = datetime.now(TZ_SHANGHAI)
    return [
        {
            "id": "a0000000-0000-0000-0000-000000000001",
            "source": "CMA",
            "alertType": "flood",
            "severity": "high",
            "title": "Flood Warning: Yangtze River Middle Reaches",
            "description": "Water levels expected to exceed warning level by 0.5m in the next 12 hours.",
            "areaGeojson": {"type": "Polygon", "coordinates": [[[113.5, 30.2], [114.5, 30.2], [114.5, 31.0], [113.5, 31.0], [113.5, 30.2]]]},
            "effectiveAt": now.isoformat(),
            "expiresAt": (now + timedelta(hours=24)).isoformat(),
            "isActive": True,
            "createdAt": (now - timedelta(hours=2)).isoformat(),
        },
        {
            "id": "a0000000-0000-0000-0000-000000000002",
            "source": "CMA",
            "alertType": "rainfall",
            "severity": "extreme",
            "title": "Extreme Rainfall Alert: Wuhan Metropolitan Area",
            "description": "Cumulative rainfall of 200mm+ expected over the next 6 hours.",
            "areaGeojson": {"type": "Polygon", "coordinates": [[[114.0, 30.4], [114.6, 30.4], [114.6, 30.8], [114.0, 30.8], [114.0, 30.4]]]},
            "effectiveAt": now.isoformat(),
            "expiresAt": (now + timedelta(hours=12)).isoformat(),
            "isActive": True,
            "createdAt": (now - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "a0000000-0000-0000-0000-000000000003",
            "source": "LOCAL",
            "alertType": "water_level",
            "severity": "medium",
            "title": "Elevated Water Level: East Lake",
            "description": "East Lake water level at 22.3m, approaching warning threshold of 23.0m.",
            "areaGeojson": {"type": "Point", "coordinates": [114.4, 30.55]},
            "effectiveAt": (now - timedelta(hours=3)).isoformat(),
            "expiresAt": (now + timedelta(hours=48)).isoformat(),
            "isActive": True,
            "createdAt": (now - timedelta(hours=3)).isoformat(),
        },
    ]


@router.get("")
async def list_alerts(
    request: Request,
    severity: str | None = Query(default=None, max_length=32),
    alert_type: str | None = Query(default=None, alias="alertType", max_length=32),
    active_only: bool = Query(default=True, alias="activeOnly"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)
    alerts = _build_fixtures()

    if active_only:
        alerts = [a for a in alerts if a["isActive"]]
    if severity:
        alerts = [a for a in alerts if a["severity"] == severity]
    if alert_type:
        alerts = [a for a in alerts if a["alertType"] == alert_type]

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": alerts,
    }


@router.get("/{alert_id}")
async def get_alert(alert_id: str, request: Request):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)
    alerts = _build_fixtures()

    for alert in alerts:
        if alert["id"] == alert_id:
            return {
                "requestId": request_id,
                "dataStatus": "normal",
                "timestamp": now.isoformat(),
                "data": alert,
            }

    raise NotFound(f"Alert {alert_id} not found", request_id=request_id)
