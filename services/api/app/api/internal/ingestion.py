import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))


class WarningItem(BaseModel):
    external_id: str = Field(alias="externalId", min_length=1)
    alert_type: str = Field(alias="alertType", min_length=1, max_length=32)
    severity: str = Field(min_length=1, max_length=32)
    title: str = Field(min_length=1, max_length=512)
    description: str | None = None
    area_geojson: dict | None = Field(default=None, alias="areaGeojson")
    effective_at: datetime | None = Field(default=None, alias="effectiveAt")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")

    model_config = {"populate_by_name": True}


class WarningBatch(BaseModel):
    source: str = Field(min_length=1, max_length=64)
    warnings: list[WarningItem]


class RainfallItem(BaseModel):
    station_id: str = Field(alias="stationId", min_length=1)
    value: float
    unit: str = Field(default="mm", max_length=16)
    observed_at: datetime = Field(alias="observedAt")
    quality_flag: str = Field(default="normal", alias="qualityFlag")

    model_config = {"populate_by_name": True}


class RainfallBatch(BaseModel):
    source: str = Field(min_length=1, max_length=64)
    readings: list[RainfallItem]


class RoadEventItem(BaseModel):
    event_type: str = Field(alias="eventType", min_length=1, max_length=32)
    severity: str = Field(min_length=1, max_length=32)
    road_name: str = Field(alias="roadName", min_length=1, max_length=256)
    description: str | None = None
    location_geojson: dict | None = Field(default=None, alias="locationGeojson")
    effective_at: datetime | None = Field(default=None, alias="effectiveAt")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")

    model_config = {"populate_by_name": True}


class RoadEventBatch(BaseModel):
    source: str = Field(min_length=1, max_length=64)
    events: list[RoadEventItem]


@router.post("/{source_id}/warnings")
async def ingest_warnings(source_id: str, body: WarningBatch, request: Request):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    accepted = []
    for i, w in enumerate(body.warnings):
        accepted.append({
            "externalId": w.external_id,
            "internalId": str(uuid.uuid4()),
            "status": "accepted",
        })

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "sourceId": source_id,
            "accepted": len(accepted),
            "rejected": 0,
            "items": accepted,
        },
    }


@router.post("/{source_id}/rainfall")
async def ingest_rainfall(source_id: str, body: RainfallBatch, request: Request):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    accepted = []
    for r in body.readings:
        accepted.append({
            "stationId": r.station_id,
            "internalId": str(uuid.uuid4()),
            "status": "accepted",
        })

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "sourceId": source_id,
            "accepted": len(accepted),
            "rejected": 0,
            "items": accepted,
        },
    }


@router.post("/{source_id}/road-events")
async def ingest_road_events(source_id: str, body: RoadEventBatch, request: Request):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    accepted = []
    for e in body.events:
        accepted.append({
            "roadName": e.road_name,
            "internalId": str(uuid.uuid4()),
            "status": "accepted",
        })

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "sourceId": source_id,
            "accepted": len(accepted),
            "rejected": 0,
            "items": accepted,
        },
    }
