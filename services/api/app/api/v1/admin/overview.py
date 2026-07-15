from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request

from app.core.deps import require_role
from app.services.risk_engine import compute_risk, SignalInput

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))


@router.get("/risk/overview")
async def risk_overview(
    request: Request,
    user: dict = require_role("admin", "analyst"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    # Generate risk overview for multiple areas
    areas = [
        {"areaId": "wuhan-hankou", "name": "Hankou District", "lat": 30.58, "lon": 114.27},
        {"areaId": "wuhan-hanyang", "name": "Hanyang District", "lat": 30.55, "lon": 114.22},
        {"areaId": "wuhan-wuchang", "name": "Wuchang District", "lat": 30.55, "lon": 114.35},
    ]

    area_risks = []
    for area in areas:
        signals = {
            "rainfall_mm": SignalInput(value=30.0 + hash(area["areaId"]) % 50, observed_at=now - timedelta(minutes=20), source="mock"),
            "water_level_m": SignalInput(value=1.5 + (hash(area["areaId"]) % 30) / 10.0, observed_at=now - timedelta(minutes=10), source="mock"),
            "alert_severity": SignalInput(value=2.0, observed_at=now - timedelta(hours=1), source="mock"),
            "ground_saturation": SignalInput(value=0.5, observed_at=now - timedelta(hours=2), source="mock"),
            "drainage_capacity": SignalInput(value=0.6, observed_at=now - timedelta(hours=1), source="mock"),
        }
        risk = compute_risk(signals, now=now)
        area_risks.append({
            "areaId": area["areaId"],
            "name": area["name"],
            "riskLevel": risk.risk_level,
            "riskScore": risk.risk_score,
            "confidence": risk.confidence,
            "dataStatus": risk.data_status,
        })

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "areas": area_risks,
            "summary": {
                "totalAreas": len(area_risks),
                "highRiskAreas": sum(1 for a in area_risks if a["riskLevel"] in ("high", "extreme")),
                "activeAlerts": 3,
                "pendingReports": 12,
                "openTasks": 5,
            },
        },
    }
