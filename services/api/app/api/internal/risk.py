from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.services.risk_engine import compute_risk, SignalInput

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))


class RecomputeRequest(BaseModel):
    area_ids: list[str] = Field(alias="areaIds", min_length=1, max_length=100)
    force: bool = False

    model_config = {"populate_by_name": True}


@router.post("/recompute")
async def recompute_risk(body: RecomputeRequest, request: Request):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    results = []
    for area_id in body.area_ids:
        # Use mock signals for recomputation
        signals = {
            "rainfall_mm": SignalInput(value=20.0, observed_at=now - timedelta(minutes=10), source="ingestion"),
            "water_level_m": SignalInput(value=2.0, observed_at=now - timedelta(minutes=5), source="ingestion"),
            "alert_severity": SignalInput(value=2.0, observed_at=now - timedelta(hours=1), source="ingestion"),
            "ground_saturation": SignalInput(value=0.5, observed_at=now - timedelta(hours=2), source="ingestion"),
            "drainage_capacity": SignalInput(value=0.6, observed_at=now - timedelta(hours=1), source="ingestion"),
        }
        risk = compute_risk(signals, now=now)

        results.append({
            "areaId": area_id,
            "riskLevel": risk.risk_level,
            "riskScore": risk.risk_score,
            "confidence": risk.confidence,
            "dataStatus": risk.data_status,
            "computedAt": risk.computed_at.isoformat(),
        })

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "recomputed": len(results),
            "results": results,
        },
    }
