import logging
import uuid as _uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.config import settings
from app.core.deps import DbSession, get_current_user
from app.core.errors import Conflict, Forbidden, NotFound
from app.models.base import AuditLog, NotificationSubscription

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class SubscriptionCreate(BaseModel):
    area_id: str = Field(alias="areaId", min_length=1, max_length=64)
    channel: str = Field(min_length=1, max_length=32, pattern="^(push|sms|email)$")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sub_to_dict(sub: NotificationSubscription) -> dict[str, Any]:
    return {
        "id": str(sub.id),
        "userId": str(sub.user_id),
        "areaId": sub.area_id,
        "channel": sub.channel,
        "isActive": sub.is_active,
        "createdAt": sub.created_at.isoformat() if sub.created_at else None,
    }


# ---------------------------------------------------------------------------
# POST /subscriptions
# ---------------------------------------------------------------------------

@router.post("/subscriptions")
async def create_subscription(
    body: SubscriptionCreate,
    request: Request,
    db: DbSession,
    user: dict[str, Any] = Depends(get_current_user),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)
    user_id = _uuid.UUID(user["id"])

    # Check for duplicate subscription (same user + area + channel)
    dup_stmt = select(NotificationSubscription).where(
        NotificationSubscription.user_id == user_id,
        NotificationSubscription.area_id == body.area_id,
        NotificationSubscription.channel == body.channel,
        NotificationSubscription.is_active == True,  # noqa: E712
    )
    dup_result = await db.execute(dup_stmt)
    existing = dup_result.scalar_one_or_none()
    if existing is not None:
        raise Conflict(
            f"Subscription already exists for user {user['id']}, "
            f"area {body.area_id}, channel {body.channel}",
            request_id=request_id,
        )

    # Create subscription
    sub = NotificationSubscription(
        user_id=user_id,
        area_id=body.area_id,
        channel=body.channel,
        is_active=True,
    )
    db.add(sub)

    # Create audit log
    audit = AuditLog(
        actor_id=user_id,
        action="subscription.created",
        resource_type="notification_subscription",
        resource_id=sub.id,
        details={"area_id": body.area_id, "channel": body.channel},
    )
    db.add(audit)

    await db.commit()
    await db.refresh(sub)

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": _sub_to_dict(sub),
    }


# ---------------------------------------------------------------------------
# GET /subscriptions
# ---------------------------------------------------------------------------

@router.get("/subscriptions")
async def list_subscriptions(
    request: Request,
    db: DbSession,
    user: dict[str, Any] = Depends(get_current_user),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)
    user_id = _uuid.UUID(user["id"])

    stmt = (
        select(NotificationSubscription)
        .where(NotificationSubscription.user_id == user_id)
        .where(NotificationSubscription.is_active == True)  # noqa: E712
        .order_by(NotificationSubscription.created_at.desc())
    )
    result = await db.execute(stmt)
    subs = [_sub_to_dict(row) for row in result.scalars().all()]

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": subs,
    }


# ---------------------------------------------------------------------------
# DELETE /subscriptions/{id}
# ---------------------------------------------------------------------------

@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: str,
    request: Request,
    db: DbSession,
    user: dict[str, Any] = Depends(get_current_user),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)
    user_id = _uuid.UUID(user["id"])

    # Parse UUID
    try:
        sub_uuid = _uuid.UUID(subscription_id)
    except ValueError:
        raise NotFound(f"Subscription {subscription_id} not found", request_id=request_id)

    # Fetch subscription
    result = await db.execute(
        select(NotificationSubscription).where(NotificationSubscription.id == sub_uuid)
    )
    sub = result.scalar_one_or_none()

    if sub is None:
        raise NotFound(f"Subscription {subscription_id} not found", request_id=request_id)

    # Verify ownership
    if sub.user_id != user_id:
        raise Forbidden("You do not own this subscription", request_id=request_id)

    # Soft delete
    sub.is_active = False

    # Audit log
    audit = AuditLog(
        actor_id=user_id,
        action="subscription.deleted",
        resource_type="notification_subscription",
        resource_id=sub.id,
        details={"area_id": sub.area_id, "channel": sub.channel},
    )
    db.add(audit)

    await db.commit()

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {"id": subscription_id, "deleted": True},
    }
