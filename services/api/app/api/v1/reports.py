import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select

from app.core.config import settings
from app.core.deps import DbSession, get_current_user, get_optional_user
from app.core.errors import NotFound
from app.models.base import AuditLog, HazardReport
from app.schemas.report import CreateReportRequest

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))

ANONYMOUS_USER_ID = "00000000-0000-0000-0000-000000000000"


def _fuzz_location(location_geojson: dict) -> dict:
    """Fuzzy location to ~100m resolution for public reports.
    Precise location should only be stored separately for verification/rescue."""
    if location_geojson.get("type") == "Point" and "coordinates" in location_geojson:
        coords = location_geojson["coordinates"]
        # 3 decimal places ≈ 111m precision
        fuzzed = [round(coords[0], 3), round(coords[1], 3)]
        return {**location_geojson, "coordinates": fuzzed, "precision": "approximate"}
    return location_geojson


def _report_to_public_dict(report: HazardReport) -> dict:
    """Convert a HazardReport to a public API dict (fuzzed location)."""
    return {
        "id": str(report.id),
        "reportType": report.report_type,
        "severity": report.severity,
        "description": report.description,
        "photoUrl": report.photo_url,
        "location": report.location_fuzzed_geojson,
        "status": report.status,
        "createdAt": report.created_at.isoformat(),
    }


@router.post("")
async def create_report(
    body: CreateReportRequest,
    request: Request,
    session: DbSession,
    user: dict[str, Any] | None = Depends(get_optional_user),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)
    report_id = uuid.uuid4()

    location_geojson = None
    location_fuzzed_geojson = None
    if body.location:
        raw_location = body.location.model_dump()
        location_geojson = raw_location
        location_fuzzed_geojson = _fuzz_location(raw_location)

    reporter_id = uuid.UUID(user["id"]) if user else None
    audit_actor_id = reporter_id if reporter_id else uuid.UUID(ANONYMOUS_USER_ID)

    try:
        report = HazardReport(
            id=report_id,
            reporter_id=reporter_id,
            report_type=body.report_type,
            severity=body.severity,
            description=body.description,
            photo_url=body.photo_url,
            location_geojson=location_geojson,
            location_fuzzed_geojson=location_fuzzed_geojson,
            status="pending_review",
        )
        session.add(report)

        audit = AuditLog(
            actor_id=audit_actor_id,
            action="submit_report",
            resource_type="hazard_report",
            resource_id=report_id,
            details={"report_type": body.report_type, "severity": body.severity},
        )
        session.add(audit)

        await session.commit()
        await session.refresh(report)

        return {
            "requestId": request_id,
            "dataStatus": "normal",
            "timestamp": now.isoformat(),
            "data": _report_to_public_dict(report),
        }
    except Exception:
        if settings.MOCK_MODE:
            return {
                "requestId": request_id,
                "dataStatus": "normal",
                "timestamp": now.isoformat(),
                "data": {
                    "id": str(report_id),
                    "reportType": body.report_type,
                    "severity": body.severity,
                    "description": body.description,
                    "photoUrl": body.photo_url,
                    "location": location_fuzzed_geojson,
                    "status": "pending_review",
                    "createdAt": now.isoformat(),
                },
            }
        raise


@router.get("/mine")
async def list_my_reports(
    request: Request,
    session: DbSession,
    user: dict[str, Any] = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    try:
        user_id = uuid.UUID(user["id"])
        stmt = (
            select(HazardReport)
            .where(HazardReport.reporter_id == user_id)
            .order_by(HazardReport.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        reports = result.scalars().all()

        count_stmt = (
            select(func.count())
            .select_from(HazardReport)
            .where(HazardReport.reporter_id == user_id)
        )
        total = (await session.execute(count_stmt)).scalar() or 0

        return {
            "requestId": request_id,
            "dataStatus": "normal",
            "timestamp": now.isoformat(),
            "data": {
                "items": [_report_to_public_dict(r) for r in reports],
                "total": total,
                "limit": limit,
                "offset": offset,
                "hasNext": offset + limit < total,
            },
        }
    except Exception:
        if settings.MOCK_MODE:
            return {
                "requestId": request_id,
                "dataStatus": "normal",
                "timestamp": now.isoformat(),
                "data": {
                    "items": [],
                    "total": 0,
                    "limit": limit,
                    "offset": offset,
                    "hasNext": False,
                },
            }
        raise


@router.get("/{report_id}")
async def get_report(report_id: str, request: Request, session: DbSession):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    # Validate UUID format
    try:
        rid = uuid.UUID(report_id)
    except ValueError:
        raise NotFound(f"Report {report_id} not found", request_id=request_id)

    try:
        result = await session.execute(select(HazardReport).where(HazardReport.id == rid))
        report = result.scalar_one_or_none()
        if report:
            return {
                "requestId": request_id,
                "dataStatus": "normal",
                "timestamp": now.isoformat(),
                "data": _report_to_public_dict(report),
            }
    except Exception:
        if not settings.MOCK_MODE:
            raise

    # MOCK_MODE fallback: if not found in DB, return fixture
    if settings.MOCK_MODE:
        return {
            "requestId": request_id,
            "dataStatus": "normal",
            "timestamp": now.isoformat(),
            "data": {
                "id": report_id,
                "reportType": "flood",
                "severity": "high",
                "description": "Water level rising rapidly near the bridge.",
                "photoUrl": None,
                "location": {"type": "Point", "coordinates": [121.47, 31.23], "precision": "approximate"},
                "status": "pending_review",
                "createdAt": (now - timedelta(minutes=30)).isoformat(),
            },
        }

    raise NotFound(f"Report {report_id} not found", request_id=request_id)
