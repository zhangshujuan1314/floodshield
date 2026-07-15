import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query, Request

from app.core.deps import require_role

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))


@router.get("/audit-logs")
async def list_audit_logs(
    request: Request,
    action: str | None = Query(default=None, max_length=64),
    resource_type: str | None = Query(default=None, alias="resourceType", max_length=64),
    actor_id: str | None = Query(default=None, alias="actorId"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200, alias="pageSize"),
    user: dict = require_role("admin"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    logs = [
        {
            "id": str(uuid.uuid4()),
            "actorId": "00000000-0000-0000-0000-000000000001",
            "actorName": "admin",
            "action": "verify_report",
            "resourceType": "hazard_report",
            "resourceId": "r0000000-0000-0000-0000-000000000001",
            "details": {"notes": "Verified by on-site inspection"},
            "createdAt": (now - timedelta(hours=1)).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "actorId": "00000000-0000-0000-0000-000000000001",
            "actorName": "admin",
            "action": "create_road_event",
            "resourceType": "road_event",
            "resourceId": "e0000000-0000-0000-0000-000000000001",
            "details": {"roadName": "Zhongshan Rd", "eventType": "closure"},
            "createdAt": (now - timedelta(hours=2)).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "actorId": "00000000-0000-0000-0000-000000000002",
            "actorName": "operator-01",
            "action": "dispatch_notification",
            "resourceType": "notification",
            "resourceId": str(uuid.uuid4()),
            "details": {"channel": "sms", "recipientCount": 1500},
            "createdAt": (now - timedelta(hours=3)).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "actorId": "00000000-0000-0000-0000-000000000001",
            "actorName": "admin",
            "action": "update_shelter",
            "resourceType": "shelter",
            "resourceId": "s0000000-0000-0000-0000-000000000001",
            "details": {"field": "currentOccupancy", "oldValue": 300, "newValue": 350},
            "createdAt": (now - timedelta(hours=4)).isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "actorId": "00000000-0000-0000-0000-000000000001",
            "actorName": "admin",
            "action": "reject_report",
            "resourceType": "hazard_report",
            "resourceId": "r0000000-0000-0000-0000-000000000005",
            "details": {"reason": "Duplicate report"},
            "createdAt": (now - timedelta(hours=5)).isoformat(),
        },
    ]

    if action:
        logs = [l for l in logs if l["action"] == action]
    if resource_type:
        logs = [l for l in logs if l["resourceType"] == resource_type]

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "items": logs,
            "total": len(logs),
            "page": page,
            "pageSize": page_size,
            "hasNext": False,
        },
    }
