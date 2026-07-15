import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))


class SubscriptionRequest(BaseModel):
    channel: str = Field(min_length=1, max_length=32, pattern="^(sms|email|push|wechat)$")
    recipient: str = Field(min_length=1, max_length=256)
    areas: list[str] = Field(default_factory=list)
    alert_types: list[str] = Field(default_factory=lambda: ["flood", "rainfall"], alias="alertTypes")

    model_config = {"populate_by_name": True}


@router.post("/subscriptions")
async def create_subscription(body: SubscriptionRequest, request: Request):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)
    sub_id = uuid.uuid4()

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": {
            "id": str(sub_id),
            "channel": body.channel,
            "recipient": body.recipient,
            "areas": body.areas,
            "alertTypes": body.alert_types,
            "isActive": True,
            "createdAt": now.isoformat(),
        },
    }
