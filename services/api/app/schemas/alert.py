from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AlertItem(BaseModel):
    id: UUID
    source: str
    alert_type: str = Field(alias="alertType")
    severity: str
    title: str
    description: str | None = None
    area_geojson: dict[str, Any] | None = Field(default=None, alias="areaGeojson")
    effective_at: datetime | None = Field(default=None, alias="effectiveAt")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")
    is_active: bool = Field(default=True, alias="isActive")
    created_at: datetime = Field(alias="createdAt")

    model_config = {"from_attributes": True, "populate_by_name": True}


class AlertListResponse(BaseModel):
    request_id: str = Field(alias="requestId")
    data_status: str = Field(default="normal", alias="dataStatus")
    timestamp: datetime
    data: list[AlertItem]

    model_config = {"populate_by_name": True}


class AlertDetailResponse(BaseModel):
    request_id: str = Field(alias="requestId")
    data_status: str = Field(default="normal", alias="dataStatus")
    timestamp: datetime
    data: AlertItem

    model_config = {"populate_by_name": True}
