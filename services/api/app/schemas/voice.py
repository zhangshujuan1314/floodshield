from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class VoiceAnnouncementRequest(BaseModel):
    area_id: str = Field(alias="areaId", min_length=1)
    message: str = Field(min_length=1, max_length=2000)
    language: str = Field(default="zh-CN", max_length=16)
    urgency: str = Field(default="normal", pattern="^(low|normal|high|critical)$")

    model_config = {"populate_by_name": True}


class VoiceAnnouncementData(BaseModel):
    id: UUID
    status: str
    audio_url: str | None = Field(default=None, alias="audioUrl")
    message: str
    area_id: str = Field(alias="areaId")

    model_config = {"populate_by_name": True}


class VoiceAnnouncementResponse(BaseModel):
    request_id: str = Field(alias="requestId")
    data_status: str = Field(default="normal", alias="dataStatus")
    timestamp: datetime
    data: VoiceAnnouncementData

    model_config = {"populate_by_name": True}
