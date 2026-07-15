from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class LocationGeojson(BaseModel):
    type: str = "Point"
    coordinates: list[float]


class CreateReportRequest(BaseModel):
    report_type: str = Field(alias="reportType", min_length=1, max_length=32)
    severity: str = Field(min_length=1, max_length=32)
    description: str = Field(min_length=1, max_length=2000)
    photo_url: str | None = Field(default=None, alias="photoUrl", max_length=1024)
    location: LocationGeojson | None = None

    model_config = {"populate_by_name": True}


class ReportItem(BaseModel):
    id: UUID
    report_type: str = Field(alias="reportType")
    severity: str
    description: str
    photo_url: str | None = Field(default=None, alias="photoUrl")
    location_geojson: dict[str, Any] | None = Field(default=None, alias="location")
    status: str
    created_at: datetime = Field(alias="createdAt")

    model_config = {"from_attributes": True, "populate_by_name": True}


class CreateReportResponse(BaseModel):
    request_id: str = Field(alias="requestId")
    data_status: str = Field(default="normal", alias="dataStatus")
    timestamp: datetime
    data: ReportItem

    model_config = {"populate_by_name": True}


class ReportDetailResponse(BaseModel):
    request_id: str = Field(alias="requestId")
    data_status: str = Field(default="normal", alias="dataStatus")
    timestamp: datetime
    data: ReportItem

    model_config = {"populate_by_name": True}
