from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query, Request

from app.services.risk_engine import compute_risk, SignalInput

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))


@router.get("/summary")
async def nearby_summary(
    request: Request,
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    radius_m: int = Query(default=5000, ge=100, le=50000, alias="radiusM"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    # Use risk engine with mock data
    signals = {
        "rainfall_mm": SignalInput(value=25.4, observed_at=now - timedelta(minutes=15), source="mock"),
        "water_level_m": SignalInput(value=2.1, observed_at=now - timedelta(minutes=10), source="mock"),
        "alert_severity": SignalInput(value=2.0, observed_at=now - timedelta(hours=1), source="mock"),
        "ground_saturation": SignalInput(value=0.55, observed_at=now - timedelta(hours=2), source="mock"),
        "drainage_capacity": SignalInput(value=0.6, observed_at=now - timedelta(hours=1), source="mock"),
    }

    risk = compute_risk(signals, now=now)

    return {
        "requestId": request_id,
        "dataStatus": risk.data_status,
        "timestamp": now.isoformat(),
        "data": {
            "risk": {
                "areaId": f"area-{lat:.2f}-{lon:.2f}",
                "riskLevel": risk.risk_level,
                "riskScore": risk.risk_score,
                "confidence": risk.confidence,
                "dataStatus": risk.data_status,
                "evidence": [
                    {
                        "signal": s.signal,
                        "value": s.value,
                        "subScore": s.sub_score,
                        "status": s.data_status,
                        "message": s.message,
                    }
                    for s in risk.signals
                ],
                "updatedAt": risk.computed_at.isoformat(),
            },
            "activeAlerts": 2,
            "nearbyShelters": 3,
            "roadClosures": 1,
        },
    }
