from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

TZ_SHANGHAI = timezone(timedelta(hours=8))

T = TypeVar("T")


def shanghai_now() -> datetime:
    return datetime.now(TZ_SHANGHAI)


class ResponseMeta(BaseModel):
    request_id: str = Field(alias="requestId")
    data_status: str = Field(default="normal", alias="dataStatus")
    timestamp: datetime = Field(default_factory=shanghai_now)


class PaginationResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = 1
    page_size: int = Field(default=20, alias="pageSize")
    has_next: bool = Field(default=False, alias="hasNext")


class Envelope(BaseModel):
    """Unified response wrapper with requestId and dataStatus."""
    request_id: str = Field(alias="requestId")
    data_status: str = Field(default="normal", alias="dataStatus")
    timestamp: datetime = Field(default_factory=shanghai_now)
    data: Any = None

    model_config = {"populate_by_name": True}
