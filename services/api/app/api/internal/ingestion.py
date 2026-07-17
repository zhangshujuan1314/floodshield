import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.deps import DbSession
from app.models.base import OfficialAlert, Observation, RoadEvent

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
async def ingest_warnings(
    source_id: str,
    body: WarningBatch,
    request: Request,
    session: DbSession,
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    accepted = []
    for w in body.warnings:
        # Upsert: look for existing alert by source + external_id
        stmt = select(OfficialAlert).where(
            OfficialAlert.source == source_id,
            OfficialAlert.external_id == w.external_id,
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing record
            existing.alert_type = w.alert_type
            existing.severity = w.severity
            existing.title = w.title
            existing.description = w.description
            existing.area_geojson = w.area_geojson
            existing.effective_at = w.effective_at
            existing.expires_at = w.expires_at
            internal_id = str(existing.id)
            status = "updated"
        else:
            # Create new record
            alert = OfficialAlert(
                source=source_id,
                external_id=w.external_id,
                alert_type=w.alert_type,
                severity=w.severity,
                title=w.title,
                description=w.description,
                area_geojson=w.area_geojson,
                effective_at=w.effective_at,
                expires_at=w.expires_at,
                is_active=True,
            )
            session.add(alert)
            await session.flush()
            internal_id = str(alert.id)
            status = "created"

        accepted.append({
            "externalId": w.external_id,
            "internalId": internal_id,
            "status": status,
        })

    await session.commit()

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
async def ingest_rainfall(
    source_id: str,
    body: RainfallBatch,
    request: Request,
    session: DbSession,
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    accepted = []
    for r in body.readings:
        obs = Observation(
            source=source_id,
            station_id=r.station_id,
            obs_type="rainfall",
            value=r.value,
            unit=r.unit,
            observed_at=r.observed_at,
            quality_flag=r.quality_flag,
        )
        session.add(obs)
        await session.flush()
        accepted.append({
            "stationId": r.station_id,
            "internalId": str(obs.id),
            "status": "created",
        })

    await session.commit()

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
async def ingest_road_events(
    source_id: str,
    body: RoadEventBatch,
    request: Request,
    session: DbSession,
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    accepted = []
    for e in body.events:
        event = RoadEvent(
            event_type=e.event_type,
            severity=e.severity,
            road_name=e.road_name,
            description=e.description,
            location_geojson=e.location_geojson,
            effective_at=e.effective_at,
            expires_at=e.expires_at,
            source=source_id,
        )
        session.add(event)
        await session.flush()
        accepted.append({
            "roadName": e.road_name,
            "internalId": str(event.id),
            "status": "created",
        })

    await session.commit()

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
