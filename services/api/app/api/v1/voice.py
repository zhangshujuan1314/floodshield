import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request

from app.core.config import settings
from app.providers import factory as provider_factory
from app.schemas.voice import VoiceAnnouncementRequest

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))


@router.post("/announcement")
async def create_voice_announcement(body: VoiceAnnouncementRequest, request: Request):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)
    announcement_id = uuid.uuid4()

    # Graceful AI failure: return template script if AI provider fails
    script = None
    data_status = "normal"
    try:
        ai_provider = provider_factory("ai", settings.AI_PROVIDER)
        script = await ai_provider.generate_voice_script({
            "area_id": body.area_id,
            "risk_level": body.urgency,
            "language": body.language,
            "area_name": body.area_id,
        })
    except Exception:
        # AI failure must NOT break core functionality
        data_status = "degraded"
        script = f"当前区域{body.area_id}，请关注官方预警信息，注意安全。"

    return {
        "requestId": request_id,
        "dataStatus": data_status,
        "timestamp": now.isoformat(),
        "data": {
            "id": str(announcement_id),
            "status": "generated",
            "audioUrl": None,
            "message": body.message,
            "generatedScript": script,
            "areaId": body.area_id,
            "language": body.language,
            "urgency": body.urgency,
            "sourceIds": [],
            "needsHumanReview": True,
            "generatedAt": now.isoformat(),
            "expiresAt": (now + timedelta(hours=1)).isoformat(),
        },
    }
