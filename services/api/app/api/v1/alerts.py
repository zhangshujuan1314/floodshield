import logging
import uuid as _uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query, Request
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError, InterfaceError, OperationalError

from app.core.config import settings
from app.core.database import async_session_factory
from app.core.errors import NotFound
from app.models.base import OfficialAlert

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _alert_to_dict(alert: OfficialAlert) -> dict:
    """Convert an OfficialAlert ORM instance to the camelCase dict expected
    by the public API response schema."""
    return {
        "id": str(alert.id),
        "source": alert.source,
        "alertType": alert.alert_type,
        "severity": alert.severity,
        "title": alert.title,
        "description": alert.description,
        "areaGeojson": alert.area_geojson,
        "effectiveAt": alert.effective_at.isoformat() if alert.effective_at else None,
        "expiresAt": alert.expires_at.isoformat() if alert.expires_at else None,
        "isActive": alert.is_active,
        "createdAt": alert.created_at.isoformat() if alert.created_at else None,
    }


def _build_fixtures() -> list[dict]:
    """Return hardcoded fixture alerts for MOCK_MODE fallback."""
    now = datetime.now(TZ_SHANGHAI)
    return [
        {
            "id": "a0000000-0000-0000-0000-000000000001",
            "source": "CMA",
            "alertType": "flood",
            "severity": "high",
            "title": "Flood Warning: Yangtze River Middle Reaches",
            "description": "Water levels expected to exceed warning level by 0.5m in the next 12 hours.",
            "areaGeojson": {"type": "Polygon", "coordinates": [[[113.5, 30.2], [114.5, 30.2], [114.5, 31.0], [113.5, 31.0], [113.5, 30.2]]]},
            "effectiveAt": now.isoformat(),
            "expiresAt": (now + timedelta(hours=24)).isoformat(),
            "isActive": True,
            "createdAt": (now - timedelta(hours=2)).isoformat(),
        },
        {
            "id": "a0000000-0000-0000-0000-000000000002",
            "source": "CMA",
            "alertType": "rainfall",
            "severity": "critical",
            "title": "Extreme Rainfall Alert: Wuhan Metropolitan Area",
            "description": "Cumulative rainfall of 200mm+ expected over the next 6 hours.",
            "areaGeojson": {"type": "Polygon", "coordinates": [[[114.0, 30.4], [114.6, 30.4], [114.6, 30.8], [114.0, 30.8], [114.0, 30.4]]]},
            "effectiveAt": now.isoformat(),
            "expiresAt": (now + timedelta(hours=12)).isoformat(),
            "isActive": True,
            "createdAt": (now - timedelta(hours=1)).isoformat(),
        },
        {
            "id": "a0000000-0000-0000-0000-000000000003",
            "source": "LOCAL",
            "alertType": "water_level",
            "severity": "attention",
            "title": "Elevated Water Level: East Lake",
            "description": "East Lake water level at 22.3m, approaching warning threshold of 23.0m.",
            "areaGeojson": {"type": "Point", "coordinates": [114.4, 30.55]},
            "effectiveAt": (now - timedelta(hours=3)).isoformat(),
            "expiresAt": (now + timedelta(hours=48)).isoformat(),
            "isActive": True,
            "createdAt": (now - timedelta(hours=3)).isoformat(),
        },
    ]


def _filter_fixtures(
    alerts: list[dict],
    *,
    active_only: bool = True,
    severity: str | None = None,
    alert_type: str | None = None,
) -> list[dict]:
    """Apply query filters to fixture data."""
    if active_only:
        alerts = [a for a in alerts if a["isActive"]]
    if severity:
        alerts = [a for a in alerts if a["severity"] == severity]
    if alert_type:
        alerts = [a for a in alerts if a["alertType"] == alert_type]
    return alerts


async def _try_query_alerts(
    *,
    active_only: bool,
    severity: str | None,
    alert_type: str | None,
) -> list[dict] | None:
    """Attempt to query alerts from the database.

    Returns a list of alert dicts on success, or None if the DB is
    unavailable (connection error).
    """
    try:
        async with async_session_factory() as session:
            stmt = select(OfficialAlert)
            now = datetime.now(TZ_SHANGHAI)

            if active_only:
                stmt = stmt.where(
                    OfficialAlert.is_active == True,  # noqa: E712
                    OfficialAlert.expires_at > now,
                )
            if severity:
                stmt = stmt.where(OfficialAlert.severity == severity)
            if alert_type:
                stmt = stmt.where(OfficialAlert.alert_type == alert_type)

            stmt = stmt.order_by(OfficialAlert.created_at.desc())

            result = await session.execute(stmt)
            rows = result.scalars().all()
            return [_alert_to_dict(row) for row in rows]
    except (OperationalError, InterfaceError, DBAPIError) as e:
        logger.warning("Database query failed, falling back: %s", e)
        return None


async def _try_get_alert(alert_uuid: _uuid.UUID) -> dict | None:
    """Attempt to fetch a single alert from the database.

    Returns the alert dict on success, or None if not found or DB
    unavailable.
    """
    try:
        async with async_session_factory() as session:
            result = await session.execute(
                select(OfficialAlert).where(OfficialAlert.id == alert_uuid)
            )
            alert = result.scalar_one_or_none()
            if alert is None:
                return None
            return _alert_to_dict(alert)
    except (OperationalError, InterfaceError, DBAPIError) as e:
        logger.warning("Database query failed, falling back: %s", e)
        return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("")
async def list_alerts(
    request: Request,
    severity: str | None = Query(default=None, max_length=32),
    alert_type: str | None = Query(default=None, alias="alertType", max_length=32),
    active_only: bool = Query(default=True, alias="activeOnly"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    alerts = await _try_query_alerts(
        active_only=active_only,
        severity=severity,
        alert_type=alert_type,
    )

    # DB unavailable (returned None) or empty results in MOCK_MODE => fixtures
    if alerts is None:
        if settings.MOCK_MODE:
            alerts = _filter_fixtures(
                _build_fixtures(),
                active_only=active_only,
                severity=severity,
                alert_type=alert_type,
            )
        else:
            alerts = []
    elif not alerts and settings.MOCK_MODE:
        alerts = _filter_fixtures(
            _build_fixtures(),
            active_only=active_only,
            severity=severity,
            alert_type=alert_type,
        )

    return {
        "requestId": request_id,
        "dataStatus": "normal",
        "timestamp": now.isoformat(),
        "data": alerts,
    }


@router.get("/{alert_id}")
async def get_alert(alert_id: str, request: Request):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)

    # Parse UUID
    try:
        alert_uuid = _uuid.UUID(alert_id)
    except ValueError:
        if settings.MOCK_MODE:
            for fixture in _build_fixtures():
                if fixture["id"] == alert_id:
                    return {
                        "requestId": request_id,
                        "dataStatus": "normal",
                        "timestamp": now.isoformat(),
                        "data": fixture,
                    }
        raise NotFound(f"Alert {alert_id} not found", request_id=request_id)

    alert = await _try_get_alert(alert_uuid)

    if alert is not None:
        return {
            "requestId": request_id,
            "dataStatus": "normal",
            "timestamp": now.isoformat(),
            "data": alert,
        }

    # Not found in DB or DB unavailable — try fixtures in MOCK_MODE
    if settings.MOCK_MODE:
        for fixture in _build_fixtures():
            if fixture["id"] == alert_id:
                return {
                    "requestId": request_id,
                    "dataStatus": "normal",
                    "timestamp": now.isoformat(),
                    "data": fixture,
                }

    raise NotFound(f"Alert {alert_id} not found", request_id=request_id)
