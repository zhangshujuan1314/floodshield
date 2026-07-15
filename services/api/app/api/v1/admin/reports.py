import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from app.core.deps import require_role
from app.core.errors import NotFound

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))


class VerifyAction(BaseModel):
    notes: str | None = None


class RejectAction(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


@router.get("/reports")
async def list_reports(
    request: Request,
    status: str | None = Query(default=None, max_length=32),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    user: dict = require_role("admin", "analyst"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    reports = [
        {
            "id": "r0000000-0000-0000-0000-000000000001",
            "reportType": "flood",
            "severity": "high",
            "description": "Water overflowing onto main road near Hankou bridge.",
            "photoUrl": None,
            "location": {"type": "Point", "coordinates": [114.27, 30.58]},
            "status": "pending",
            "createdAt": (now - timedelta(hours=2)).isoformat(),
        },
        {
            "id": "r0000000-0000-0000-0000-000000000002",
            "reportType": "road_damage",
            "severity": "medium",
            "description": "Road surface collapsed after heavy rain, partial lane closure.",
            "photoUrl": "https://example.com/photo1.jpg",
            "location": {"type": "Point", "coordinates": [114.35, 30.55]},
            "status": "pending",
            "createdAt": (now - timedelta(hours=5)).isoformat(),
        },
        {
            "id": "r0000000-0000-0000-0000-000000000003",
            "reportType": "drainage",
            "severity": "low",
            "description": "Storm drain blocked by debris, slow drainage.",
            "photoUrl": None,
            "location": {"type": "Point", "coordinates": [114.22, 30.55]},
            "status": "verified",
            "createdAt": (now - timedelta(hours=8)).isoformat(),
        },
    ]

    if status:
        reports = [r for r in reports if r["status"] == status]

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "items": reports,
            "total": len(reports),
            "page": page,
            "pageSize": page_size,
            "hasNext": False,
        },
    }


@router.post("/reports/{report_id}/verify")
async def verify_report(
    report_id: str,
    body: VerifyAction,
    request: Request,
    user: dict = require_role("admin", "analyst"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    try:
        uuid.UUID(report_id)
    except ValueError:
        raise NotFound(f"Report {report_id} not found", request_id=request_id)

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "id": report_id,
            "status": "verified",
            "verifiedBy": user["id"],
            "verifiedAt": now.isoformat(),
            "notes": body.notes,
        },
    }


@router.post("/reports/{report_id}/reject")
async def reject_report(
    report_id: str,
    body: RejectAction,
    request: Request,
    user: dict = require_role("admin", "analyst"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    try:
        uuid.UUID(report_id)
    except ValueError:
        raise NotFound(f"Report {report_id} not found", request_id=request_id)

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "id": report_id,
            "status": "rejected",
            "rejectedBy": user["id"],
            "rejectedAt": now.isoformat(),
            "reason": body.reason,
        },
    }
