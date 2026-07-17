import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import TZ_SHANGHAI
from app.core.deps import DbSession, require_role
from app.core.errors import BadRequest, NotFound
from app.models.base import AuditLog, HazardReport

router = APIRouter()


class VerifyAction(BaseModel):
    notes: str | None = None


class RejectAction(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


def _report_to_dict(report: HazardReport) -> dict:
    """Convert a HazardReport ORM instance to an API response dict."""
    return {
        "id": str(report.id),
        "reportType": report.report_type,
        "severity": report.severity,
        "description": report.description,
        "photoUrl": report.photo_url,
        "location": report.location_geojson,
        "status": report.status,
        "verifiedBy": str(report.verified_by) if report.verified_by else None,
        "verifiedAt": report.verified_at.isoformat() if report.verified_at else None,
        "createdAt": report.created_at.isoformat(),
    }


def _fixture_reports(now: datetime) -> list[dict]:
    """Return hardcoded fixture reports for MOCK_MODE fallback."""
    return [
        {
            "id": "r0000000-0000-0000-0000-000000000001",
            "reportType": "flood",
            "severity": "high",
            "description": "Water overflowing onto main road near Hankou bridge.",
            "photoUrl": None,
            "location": {"type": "Point", "coordinates": [114.27, 30.58]},
            "status": "pending_review",
            "verifiedBy": None,
            "verifiedAt": None,
            "createdAt": (now - timedelta(hours=2)).isoformat(),
        },
        {
            "id": "r0000000-0000-0000-0000-000000000002",
            "reportType": "road_damage",
            "severity": "medium",
            "description": "Road surface collapsed after heavy rain, partial lane closure.",
            "photoUrl": "https://example.com/photo1.jpg",
            "location": {"type": "Point", "coordinates": [114.35, 30.55]},
            "status": "pending_review",
            "verifiedBy": None,
            "verifiedAt": None,
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
            "verifiedBy": None,
            "verifiedAt": None,
            "createdAt": (now - timedelta(hours=8)).isoformat(),
        },
    ]


@router.get("/reports")
async def list_reports(
    request: Request,
    db: DbSession,
    status: str | None = Query(default=None, max_length=32),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = require_role("admin", "analyst"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    stmt = select(HazardReport)
    count_stmt = select(func.count()).select_from(HazardReport)

    if status:
        stmt = stmt.where(HazardReport.status == status)
        count_stmt = count_stmt.where(HazardReport.status == status)

    stmt = stmt.order_by(HazardReport.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(stmt)
    reports = result.scalars().all()
    total = (await db.execute(count_stmt)).scalar() or 0

    # MOCK_MODE fallback: if DB is empty, return fixtures
    if settings.MOCK_MODE and total == 0:
        items = _fixture_reports(now)
        if status:
            items = [r for r in items if r["status"] == status]
        return {
            "requestId": request_id,
            "dataStatus": "normal",
            "timestamp": now.isoformat(),
            "data": {
                "items": items,
                "total": len(items),
                "limit": limit,
                "offset": offset,
                "hasNext": False,
            },
        }

    items = [_report_to_dict(r) for r in reports]
    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "hasNext": offset + limit < total,
        },
    }


@router.post("/reports/{report_id}/verify")
async def verify_report(
    report_id: str,
    body: VerifyAction,
    request: Request,
    db: DbSession,
    user: dict = require_role("admin", "community"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    try:
        rid = uuid.UUID(report_id)
    except ValueError:
        raise NotFound(f"Report {report_id} not found", request_id=request_id)

    result = await db.execute(select(HazardReport).where(HazardReport.id == rid))
    report = result.scalar_one_or_none()
    if not report:
        raise NotFound(f"Report {report_id} not found", request_id=request_id)

    if report.status != "pending_review":
        raise BadRequest("Report is not pending review", request_id=request_id)

    report.status = "verified"
    report.verified_by = uuid.UUID(user["id"])
    report.verified_at = now

    audit = AuditLog(
        actor_id=uuid.UUID(user["id"]),
        action="verify_report",
        resource_type="hazard_report",
        resource_id=rid,
        details={"notes": body.notes},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(report)

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": _report_to_dict(report),
    }


@router.post("/reports/{report_id}/reject")
async def reject_report(
    report_id: str,
    body: RejectAction,
    request: Request,
    db: DbSession,
    user: dict = require_role("admin", "community"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    try:
        rid = uuid.UUID(report_id)
    except ValueError:
        raise NotFound(f"Report {report_id} not found", request_id=request_id)

    result = await db.execute(select(HazardReport).where(HazardReport.id == rid))
    report = result.scalar_one_or_none()
    if not report:
        raise NotFound(f"Report {report_id} not found", request_id=request_id)

    if report.status != "pending_review":
        raise BadRequest("Report is not pending review", request_id=request_id)

    report.status = "rejected"

    audit = AuditLog(
        actor_id=uuid.UUID(user["id"]),
        action="reject_report",
        resource_type="hazard_report",
        resource_id=rid,
        details={"reason": body.reason},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(report)

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": _report_to_dict(report),
    }
