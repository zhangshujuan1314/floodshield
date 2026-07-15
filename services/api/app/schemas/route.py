from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class WaypointGeojson(BaseModel):
    type: str = "Point"
    coordinates: list[float]


class EvacuationRouteRequest(BaseModel):
    origin: WaypointGeojson
    destination: WaypointGeojson
    transport_mode: str = Field(default="walking", alias="transportMode")
    avoid_hazards: bool = Field(default=True, alias="avoidHazards")

    model_config = {"populate_by_name": True}


class RouteResultData(BaseModel):
    id: UUID
    route_geojson: dict[str, Any] = Field(alias="routeGeojson")
    distance_m: float = Field(alias="distanceM")
    duration_s: float = Field(alias="durationS")
    safety_score: float = Field(alias="safetyScore")
    warnings: list[str] = []
    is_viable: bool = Field(default=True, alias="isViable")

    model_config = {"from_attributes": True, "populate_by_name": True}


class EvacuationRouteResponse(BaseModel):
    request_id: str = Field(alias="requestId")
    data_status: str = Field(default="normal", alias="dataStatus")
    timestamp: datetime
    data: RouteResultData

    model_config = {"populate_by_name": True}


class RouteDetailResponse(BaseModel):
    request_id: str = Field(alias="requestId")
    data_status: str = Field(default="normal", alias="dataStatus")
    timestamp: datetime
    data: RouteResultData

    model_config = {"populate_by_name": True}
