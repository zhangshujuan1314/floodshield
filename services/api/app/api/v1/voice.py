import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import DbSession, get_current_user
from app.models.base import OfficialAlert, RiskSnapshot
from app.providers import factory as provider_factory

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class VoiceAnnouncementRequest(BaseModel):
    area_id: str = Field(alias="areaId", min_length=1, max_length=64)
    risk_level: str = Field(
        alias="riskLevel",
        default="attention",
        pattern="^(normal|attention|high|critical)$",
    )
    language: str = Field(default="zh", pattern="^(zh|en)$")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _query_area_data(
    db: AsyncSession, area_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (alerts, risk_snapshots) for the given area."""
    now = datetime.now(TZ_SHANGHAI)

    # Recent active alerts (last 24h)
    alert_stmt = (
        select(OfficialAlert)
        .where(OfficialAlert.is_active == True)  # noqa: E712
        .where(OfficialAlert.expires_at > now)
        .order_by(OfficialAlert.created_at.desc())
        .limit(10)
    )
    alert_result = await db.execute(alert_stmt)
    alerts = []
    for row in alert_result.scalars().all():
        alerts.append({
            "id": str(row.id),
            "source": row.source,
            "alertType": row.alert_type,
            "severity": row.severity,
            "title": row.title,
            "effectiveAt": row.effective_at.isoformat() if row.effective_at else None,
        })

    # Latest risk snapshot for area
    risk_stmt = (
        select(RiskSnapshot)
        .where(RiskSnapshot.area_id == area_id)
        .order_by(RiskSnapshot.computed_at.desc())
        .limit(1)
    )
    risk_result = await db.execute(risk_stmt)
    risks = []
    for row in risk_result.scalars().all():
        risks.append({
            "id": str(row.id),
            "areaId": row.area_id,
            "riskLevel": row.risk_level,
            "riskScore": row.risk_score,
            "confidence": row.confidence,
            "computedAt": row.computed_at.isoformat() if row.computed_at else None,
        })

    return alerts, risks


def _build_mock_voice_data(area_id: str, risk_level: str, language: str) -> dict:
    """Return fixture alerts and risk data for MOCK_MODE."""
    now = datetime.now(TZ_SHANGHAI)
    alerts = [
        {
            "id": "a0000000-0000-0000-0000-000000000001",
            "source": "CMA",
            "alertType": "flood",
            "severity": "high",
            "title": "Flood Warning" if language == "en" else "洪水预警",
            "effectiveAt": now.isoformat(),
        },
    ]
    risks = [
        {
            "id": "r0000000-0000-0000-0000-000000000001",
            "areaId": area_id,
            "riskLevel": risk_level,
            "riskScore": 0.7,
            "confidence": 0.85,
            "computedAt": now.isoformat(),
        },
    ]
    return alerts, risks


def _build_template_script(
    area_id: str, risk_level: str, language: str, alerts: list[dict], risks: list[dict]
) -> str:
    """Build a voice script from template when AI is unavailable.

    Follows ai-safety.md section 2.6 (voice script format):
    - Short sentences
    - Include time, source, and actions
    - No jargon
    """
    now = datetime.now(TZ_SHANGHAI)
    time_str = f"{now.hour}点{now.minute}分" if language == "zh" else f"{now.hour}:{now.minute:02d}"

    alert_titles = [a["title"] for a in alerts[:3]]
    alert_text = "、".join(alert_titles) if alert_titles else ("暂无预警信息" if language == "zh" else "No active alerts")

    if language == "zh":
        if risk_level in ("high", "critical"):
            return (
                f"现在是{time_str}。"
                f"您所在的{area_id}当前风险等级为{risk_level}。"
                f"当前活跃预警：{alert_text}。"
                f"请立即撤离至最近的避难所，避免经过积水路段。"
                f"如遇紧急情况请拨打119求助。"
            )
        return (
            f"现在是{time_str}。"
            f"您所在的{area_id}当前风险等级为{risk_level}。"
            f"当前活跃预警：{alert_text}。"
            f"请关注水位变化，做好防洪准备。"
        )

    # English
    if risk_level in ("high", "critical"):
        return (
            f"It is {time_str}. "
            f"Flood risk in {area_id} is {risk_level}. "
            f"Active alerts: {alert_text}. "
            f"Evacuate to the nearest shelter immediately. Avoid flooded roads. "
            f"Call emergency services if in danger."
        )
    return (
        f"It is {time_str}. "
        f"Flood risk in {area_id} is {risk_level}. "
        f"Active alerts: {alert_text}. "
        f"Monitor water levels and prepare for possible evacuation."
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/announcement")
async def create_voice_announcement(
    body: VoiceAnnouncementRequest,
    request: Request,
    db: DbSession,
    user: dict | None = None,
):
    """Generate a voice announcement script for a given area.

    Queries recent alerts and risk data, then calls the AI provider to
    generate a voice script.  Falls back to a template script when the
    AI provider fails or in MOCK_MODE.
    """
    # Try to get current user; allow anonymous access
    try:
        user = await get_current_user(request)
    except Exception:
        user = None

    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)
    announcement_id = uuid.uuid4()

    # Query area data from DB (or mock fixtures)
    try:
        alerts, risks = await _query_area_data(db, body.area_id)
    except Exception as e:
        logger.warning("DB query failed for voice announcement: %s", e)
        alerts, risks = [], []

    if not alerts and not risks and settings.MOCK_MODE:
        alerts, risks = _build_mock_voice_data(body.area_id, body.risk_level, body.language)

    # Determine effective risk level from latest snapshot
    effective_risk = body.risk_level
    data_freshness = now.isoformat()
    if risks:
        effective_risk = risks[0].get("riskLevel", body.risk_level)
        data_freshness = risks[0].get("computedAt", now.isoformat())

    # Generate script via AI provider, with fallback
    script = None
    data_status = "normal"
    try:
        ai_provider = provider_factory("ai", settings.AI_PROVIDER)
        script = await ai_provider.generate_voice_script({
            "area_id": body.area_id,
            "area_name": body.area_id,
            "risk_level": effective_risk,
            "language": "zh-CN" if body.language == "zh" else "en",
        })
    except Exception as e:
        logger.warning("AI provider failed, using template: %s", e)
        data_status = "degraded"

    # Always fall back to template if AI returned nothing
    if not script:
        script = _build_template_script(
            body.area_id, effective_risk, body.language, alerts, risks
        )
        data_status = "degraded"

    # Build data source references
    source_ids = [a["id"] for a in alerts]

    return {
        "requestId": request_id,
        "dataStatus": data_status,
        "timestamp": now.isoformat(),
        "data": {
            "id": str(announcement_id),
            "status": "generated",
            "generatedScript": script,
            "areaId": body.area_id,
            "language": body.language,
            "riskLevel": effective_risk,
            "sourceIds": source_ids,
            "dataFreshness": data_freshness,
            "needsHumanReview": True,
            "generatedAt": now.isoformat(),
            "expiresAt": (now + timedelta(hours=1)).isoformat(),
        },
    }
