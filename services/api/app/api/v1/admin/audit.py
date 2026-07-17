import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import DbSession, require_role
from app.models.base import AuditLog

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))


async def create_audit_log(
    session: AsyncSession,
    actor_id: str,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    details: dict | None = None,
) -> AuditLog:
    """Create an audit log entry. Importable by other modules."""
    log = AuditLog(
        actor_id=uuid.UUID(actor_id),
        action=action,
        resource_type=resource_type,
        resource_id=uuid.UUID(resource_id) if resource_id else None,
        details=details,
    )
    session.add(log)
    return log


def _fixture_logs(now: datetime) -> list[dict]:
    """Generate fixture audit logs for MOCK_MODE fallback."""
    return [
        {
            "id": str(uuid.uuid4()),
            "actorId": "00000000-0000-0000-0000-000000000001",
            "action": "verify_report",
            "resourceType": "hazard_report",
            "resourceId": "00000000-0000-0000-0000-000000000011",
            "details": {"notes": "Verified by on-site inspection"},
            "createdAt": (now - timedelta(hours=1)).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "actorId": "00000000-0000-0000-0000-000000000001",
            "action": "create_road_event",
            "resourceType": "road_event",
            "resourceId": "00000000-0000-0000-0000-000000000012",
            "details": {"roadName": "Zhongshan Rd", "eventType": "closure"},
            "createdAt": (now - timedelta(hours=2)).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "actorId": "00000000-0000-0000-0000-000000000002",
            "action": "dispatch_notification",
            "resourceType": "notification",
            "resourceId": str(uuid.uuid4()),
            "details": {"channel": "sms", "recipientCount": 1500},
            "createdAt": (now - timedelta(hours=3)).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "actorId": "00000000-0000-0000-0000-000000000001",
            "action": "update_shelter",
            "resourceType": "shelter",
            "resourceId": "00000000-0000-0000-0000-000000000013",
            "details": {"field": "currentOccupancy", "oldValue": 300, "newValue": 350},
            "createdAt": (now - timedelta(hours=4)).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "actorId": "00000000-0000-0000-0000-000000000001",
            "action": "reject_report",
            "resourceType": "hazard_report",
            "resourceId": "00000000-0000-0000-0000-000000000015",
            "details": {"reason": "Duplicate report"},
            "createdAt": (now - timedelta(hours=5)).isoformat(),
        },
    ]


def _serialize_log(log: AuditLog) -> dict:
    """Serialize an AuditLog model to API response dict."""
    return {
        "id": str(log.id),
        "actorId": str(log.actor_id),
        "action": log.action,
        "resourceType": log.resource_type,
        "resourceId": str(log.resource_id) if log.resource_id else None,
        "details": log.details,
        "createdAt": log.created_at.isoformat() if log.created_at else None,
    }


@router.get("/audit-logs")
async def list_audit_logs(
    request: Request,
    session: DbSession,
    action: str | None = Query(default=None, max_length=64),
    resource_type: str | None = Query(default=None, alias="resourceType", max_length=64),
    actor_id: str | None = Query(default=None, alias="actorId"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: dict = require_role("admin"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    # Build query with optional filters
    query = select(AuditLog)
    count_query = select(func.count()).select_from(AuditLog)

    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
        count_query = count_query.where(AuditLog.resource_type == resource_type)
    if actor_id:
        query = query.where(AuditLog.actor_id == uuid.UUID(actor_id))
        count_query = count_query.where(AuditLog.actor_id == uuid.UUID(actor_id))

    # Get total count
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # MOCK_MODE fallback: if DB is empty, return fixtures
    if total == 0 and settings.MOCK_MODE:
        fixture_logs = _fixture_logs(now)
        filtered = fixture_logs
        if action:
            filtered = [l for l in filtered if l["action"] == action]
        if resource_type:
            filtered = [l for l in filtered if l["resourceType"] == resource_type]
        if actor_id:
            filtered = [l for l in filtered if l["actorId"] == actor_id]

        return {
            "requestId": request_id,
            "dataStatus": "normal",
            "timestamp": now.isoformat(),
            "data": {
                "logs": filtered[offset: offset + limit],
                "total": len(filtered),
                "limit": limit,
                "offset": offset,
            },
        }

    # Query with pagination and ordering
    query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    logs = [_serialize_log(row) for row in result.scalars().all()]

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "logs": logs,
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    }
