from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))


@router.get("/issues")
async def list_data_quality_issues(request: Request):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    issues = [
        {
            "id": "dq-001",
            "severity": "high",
            "type": "stale_data",
            "source": "weather_station",
            "stationId": "WS-042",
            "signal": "water_level_m",
            "description": "Water level data from station WS-042 is 3 hours old. Last received at "
            + (now - timedelta(hours=3)).isoformat(),
            "detectedAt": (now - timedelta(minutes=30)).isoformat(),
            "affectedAreas": ["wuhan-hankou"],
        },
        {
            "id": "dq-002",
            "severity": "medium",
            "type": "missing_data",
            "source": "rainfall_gauge",
            "stationId": "RG-017",
            "signal": "rainfall_mm",
            "description": "No rainfall data received from gauge RG-017 for the past 2 hours.",
            "detectedAt": (now - timedelta(hours=1)).isoformat(),
            "affectedAreas": ["wuhan-hanyang"],
        },
        {
            "id": "dq-003",
            "severity": "low",
            "type": "out_of_range",
            "source": "weather_station",
            "stationId": "WS-008",
            "signal": "rainfall_mm",
            "description": "Rainfall reading of 600mm exceeds physical plausible range (0-500mm).",
            "detectedAt": (now - timedelta(minutes=15)).isoformat(),
            "affectedAreas": ["wuhan-wuchang"],
        },
        {
            "id": "dq-004",
            "severity": "medium",
            "type": "conflicting",
            "source": "multi_source",
            "stationId": None,
            "signal": "rainfall_mm vs water_level_m",
            "description": "High rainfall reported but water level remains low. Possible upstream data lag.",
            "detectedAt": (now - timedelta(minutes=45)).isoformat(),
            "affectedAreas": ["wuhan-hankou", "wuhan-hanyang"],
        },
    ]

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "items": issues,
            "total": len(issues),
            "summary": {
                "high": sum(1 for i in issues if i["severity"] == "high"),
                "medium": sum(1 for i in issues if i["severity"] == "medium"),
                "low": sum(1 for i in issues if i["severity"] == "low"),
            },
        },
    }
