from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ShelterItem(BaseModel):
    id: UUID
    name: str
    address: str
    capacity: int
    current_occupancy: int = Field(alias="currentOccupancy")
    status: str
    contact_phone: str | None = Field(default=None, alias="contactPhone")
    facilities: dict[str, Any] | None = None
    location_geojson: dict[str, Any] | None = Field(default=None, alias="location")

    model_config = {"from_attributes": True, "populate_by_name": True}


class ShelterListResponse(BaseModel):
    request_id: str = Field(alias="requestId")
    data_status: str = Field(default="normal", alias="dataStatus")
    timestamp: datetime
    data: list[ShelterItem]

    model_config = {"populate_by_name": True}
