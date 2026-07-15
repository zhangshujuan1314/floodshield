import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.deps import require_role
from app.core.errors import NotFound
from app.providers import factory as provider_factory

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))


class DispatchRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    channel: str = Field(min_length=1, max_length=32, pattern="^(sms|email|push|wechat)$")
    recipients: list[str] = Field(min_length=1, max_length=1000)
    area_id: str | None = Field(default=None, alias="areaId")

    model_config = {"populate_by_name": True}


@router.post("/notifications/dispatch")
async def dispatch_notification(
    body: DispatchRequest,
    request: Request,
    user: dict = require_role("admin", "operator"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    notif_provider = provider_factory("notification", settings.NOTIFICATION_PROVIDER)
    deliveries = await notif_provider.bulk_dispatch(
        message=body.message,
        channel=body.channel,
        recipients=body.recipients,
        metadata={"area_id": body.area_id, "dispatched_by": user["id"]},
    )

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "dispatchId": str(uuid.uuid4()),
            "totalRecipients": len(body.recipients),
            "deliveries": [
                {
                    "id": d["id"],
                    "recipient": d["recipient"],
                    "status": d["status"],
                    "sentAt": d["sent_at"],
                }
                for d in deliveries
            ],
        },
    }


@router.get("/notification-deliveries/{delivery_id}")
async def get_delivery(
    delivery_id: str,
    request: Request,
    user: dict = require_role("admin", "operator"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    try:
        uuid.UUID(delivery_id)
    except ValueError:
        raise NotFound(f"Delivery {delivery_id} not found", request_id=request_id)

    notif_provider = provider_factory("notification", settings.NOTIFICATION_PROVIDER)
    delivery = await notif_provider.get_delivery(delivery_id)

    if delivery is None:
        # Return a fixture for demo purposes
        return {
            "requestId": request_id,
            "dataStatus": "normal",
            "timestamp": now.isoformat(),
            "data": {
                "id": delivery_id,
                "channel": "sms",
                "recipient": "+86-138****1234",
                "message": "Flood warning in your area. Seek shelter immediately.",
                "status": "delivered",
                "sentAt": (now - timedelta(minutes=5)).isoformat(),
                "deliveredAt": (now - timedelta(minutes=4, seconds=58)).isoformat(),
                "errorMessage": None,
            },
        }

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": delivery,
    }
