from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RiskSummary(BaseModel):
    area_id: str = Field(alias="areaId")
    risk_level: str = Field(alias="riskLevel")
    risk_score: float = Field(alias="riskScore")
    confidence: float
    data_status: str = Field(default="normal", alias="dataStatus")
    evidence: list[dict[str, Any]] = []
    updated_at: datetime = Field(alias="updatedAt")

    model_config = {"populate_by_name": True}


class NearbySummaryData(BaseModel):
    risk: RiskSummary
    active_alerts: int = Field(default=0, alias="activeAlerts")
    nearby_shelters: int = Field(default=0, alias="nearbyShelters")
    road_closures: int = Field(default=0, alias="roadClosures")

    model_config = {"populate_by_name": True}


class NearbySummaryResponse(BaseModel):
    request_id: str = Field(alias="requestId")
    data_status: str = Field(default="normal", alias="dataStatus")
    timestamp: datetime
    data: NearbySummaryData

    model_config = {"populate_by_name": True}
