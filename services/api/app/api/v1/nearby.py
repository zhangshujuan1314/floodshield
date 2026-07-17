import math
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query, Request
from sqlalchemy import and_, cast, Float, select

from app.core.config import settings
from app.core.deps import DbSession
from app.models.base import OfficialAlert, Observation, RiskSnapshot, RoadEvent, Shelter
from app.services.risk_engine import compute_risk, SignalInput

router = APIRouter()
TZ_SHANGHAI = timezone(timedelta(hours=8))

# --- Geo helpers (bounding box + Haversine, no PostGIS) ---

DEG_LAT_PER_M = 1.0 / 111_000


def _bbox(lat: float, lon: float, radius_m: int) -> tuple[float, float, float, float]:
    """Return (min_lat, max_lat, min_lon, max_lon) bounding box."""
    deg_lat = radius_m * DEG_LAT_PER_M
    deg_lon = radius_m * DEG_LAT_PER_M / max(math.cos(math.radians(lat)), 1e-6)
    return lat - deg_lat, lat + deg_lat, lon - deg_lon, lon + deg_lon


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _point_from_geojson(geojson: dict | None) -> tuple[float, float] | None:
    """Extract (lat, lon) from a GeoJSON Point."""
    if not geojson or geojson.get("type") != "Point":
        return None
    coords = geojson.get("coordinates")
    if not coords or len(coords) < 2:
        return None
    return (coords[1], coords[0])  # GeoJSON is [lon, lat]


def _geo_bbox_filter(model, min_lat, max_lat, min_lon, max_lon):
    """SQLAlchemy filter: GeoJSON Point within bounding box."""
    lat_col = cast(model.location_geojson["coordinates"][1].astext, Float)
    lon_col = cast(model.location_geojson["coordinates"][0].astext, Float)
    return and_(
        lat_col >= min_lat, lat_col <= max_lat,
        lon_col >= min_lon, lon_col <= max_lon,
    )


def _severity_to_numeric(sev: str) -> float:
    return {"minor": 1.0, "moderate": 2.0, "severe": 3.0, "extreme": 4.0}.get(
        (sev or "").lower(), 0.0
    )


def _closest_obs(obs_list: list, lat: float, lon: float):
    """Return (value, observed_at) for the closest observation, or (None, None)."""
    best_dist = float("inf")
    best_value = None
    best_at = None
    for obs in obs_list:
        pt = _point_from_geojson(obs.location_geojson)
        if pt is None:
            continue
        d = _haversine_m(lat, lon, pt[0], pt[1])
        if d < best_dist:
            best_dist = d
            best_value = obs.value
            best_at = obs.observed_at
    return best_value, best_at


@router.get("/summary")
async def nearby_summary(
    request: Request,
    db: DbSession,
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    radius_m: int = Query(default=5000, ge=100, le=50000, alias="radiusM"),
    area_id: str | None = Query(default=None, alias="areaId"),
):
    request_id = getattr(request.state, "request_id", "")
    now = datetime.now(TZ_SHANGHAI)
    effective_area_id = area_id or f"area-{lat:.2f}-{lon:.2f}"

    min_lat, max_lat, min_lon, max_lon = _bbox(lat, lon, radius_m)

    # --- 1. Active official alerts ---
    alert_q = select(OfficialAlert).where(
        OfficialAlert.is_active == True,  # noqa: E712
        (OfficialAlert.expires_at.is_(None)) | (OfficialAlert.expires_at > now),
    )
    active_alerts = (await db.execute(alert_q)).scalars().all()
    active_alert_count = len(active_alerts)

    # Worst severity among active alerts
    alert_severity_val = 0.0
    alert_severity_at = None
    if active_alerts:
        alert_severity_val = max(_severity_to_numeric(a.severity) for a in active_alerts)
        alert_severity_at = max(
            (a.effective_at or a.created_at for a in active_alerts),
            default=now,
        )

    # --- 2. Rainfall observations (closest station, last 1h) ---
    rainfall_q = (
        select(Observation)
        .where(
            Observation.obs_type == "rainfall",
            Observation.observed_at >= now - timedelta(hours=1),
            _geo_bbox_filter(Observation, min_lat, max_lat, min_lon, max_lon),
        )
        .order_by(Observation.observed_at.desc())
        .limit(20)
    )
    rainfall_obs = (await db.execute(rainfall_q)).scalars().all()
    rainfall_mm, rainfall_at = _closest_obs(rainfall_obs, lat, lon)

    # --- 3. Water level observations (closest station, last 1h) ---
    water_q = (
        select(Observation)
        .where(
            Observation.obs_type == "water_level",
            Observation.observed_at >= now - timedelta(hours=1),
            _geo_bbox_filter(Observation, min_lat, max_lat, min_lon, max_lon),
        )
        .order_by(Observation.observed_at.desc())
        .limit(20)
    )
    water_obs = (await db.execute(water_q)).scalars().all()
    water_level_m, water_at = _closest_obs(water_obs, lat, lon)

    # --- 4. Risk snapshot (if area_id provided) ---
    snapshot = None
    if area_id:
        snap_q = (
            select(RiskSnapshot)
            .where(RiskSnapshot.area_id == area_id)
            .order_by(RiskSnapshot.computed_at.desc())
            .limit(1)
        )
        snapshot = (await db.execute(snap_q)).scalar_one_or_none()

    # --- 5. Ground saturation & drainage capacity from observations ---
    gs_q = (
        select(Observation)
        .where(
            Observation.obs_type == "ground_saturation",
            Observation.observed_at >= now - timedelta(hours=4),
        )
        .order_by(Observation.observed_at.desc())
        .limit(1)
    )
    gs_obs = (await db.execute(gs_q)).scalar_one_or_none()
    ground_sat = gs_obs.value if gs_obs else None
    ground_sat_at = gs_obs.observed_at if gs_obs else None

    dc_q = (
        select(Observation)
        .where(
            Observation.obs_type == "drainage_capacity",
            Observation.observed_at >= now - timedelta(hours=4),
        )
        .order_by(Observation.observed_at.desc())
        .limit(1)
    )
    dc_obs = (await db.execute(dc_q)).scalar_one_or_none()
    drainage_cap = dc_obs.value if dc_obs else None
    drainage_at = dc_obs.observed_at if dc_obs else None

    # Fill missing signals from snapshot evidence
    if snapshot and snapshot.evidence:
        ev = snapshot.evidence
        if ground_sat is None and "ground_saturation" in ev:
            ground_sat = ev["ground_saturation"]
            ground_sat_at = snapshot.computed_at
        if drainage_cap is None and "drainage_capacity" in ev:
            drainage_cap = ev["drainage_capacity"]
            drainage_at = snapshot.computed_at

    # --- 6. Nearby shelters ---
    shelter_q = select(Shelter).where(
        _geo_bbox_filter(Shelter, min_lat, max_lat, min_lon, max_lon),
    )
    all_shelters = (await db.execute(shelter_q)).scalars().all()
    nearby_shelters = []
    for s in all_shelters:
        pt = _point_from_geojson(s.location_geojson)
        if pt and _haversine_m(lat, lon, pt[0], pt[1]) <= radius_m:
            nearby_shelters.append(s)

    # --- 7. Road closures ---
    road_q = select(RoadEvent).where(RoadEvent.is_active == True)  # noqa: E712
    road_count = len((await db.execute(road_q)).scalars().all())

    # --- 8. Build signal inputs ---
    signals = {
        "rainfall_mm": SignalInput(value=rainfall_mm, observed_at=rainfall_at, source="observation"),
        "water_level_m": SignalInput(value=water_level_m, observed_at=water_at, source="observation"),
        "alert_severity": SignalInput(
            value=alert_severity_val or None, observed_at=alert_severity_at, source="official_alerts"
        ),
        "ground_saturation": SignalInput(value=ground_sat, observed_at=ground_sat_at, source="observation"),
        "drainage_capacity": SignalInput(value=drainage_cap, observed_at=drainage_at, source="observation"),
    }

    has_any_data = any(s.value is not None for s in signals.values())

    # --- 9. MOCK_MODE fallback when DB is empty ---
    if settings.MOCK_MODE and not has_any_data:
        signals = {
            "rainfall_mm": SignalInput(value=25.4, observed_at=now - timedelta(minutes=15), source="mock"),
            "water_level_m": SignalInput(value=2.1, observed_at=now - timedelta(minutes=10), source="mock"),
            "alert_severity": SignalInput(value=2.0, observed_at=now - timedelta(hours=1), source="mock"),
            "ground_saturation": SignalInput(value=0.55, observed_at=now - timedelta(hours=2), source="mock"),
            "drainage_capacity": SignalInput(value=0.6, observed_at=now - timedelta(hours=1), source="mock"),
        }
        active_alert_count = 2
        nearby_shelters_count = 3
        road_closures_count = 1
    else:
        nearby_shelters_count = len(nearby_shelters)
        road_closures_count = road_count

    # --- 10. Compute risk ---
    try:
        risk = compute_risk(signals, now=now)
    except Exception:
        return {
            "requestId": request_id,
            "dataStatus": "degraded",
            "timestamp": now.isoformat(),
            "message": "暂无法计算风险等级，请参考官方预警信息",
            "data": {
                "risk": {
                    "areaId": effective_area_id,
                    "riskLevel": "unknown",
                    "riskScore": 0.0,
                    "confidence": 0.0,
                    "dataStatus": "degraded",
                    "evidence": [],
                    "updatedAt": now.isoformat(),
                },
                "activeAlerts": active_alert_count,
                "nearbyShelters": nearby_shelters_count,
                "roadClosures": road_closures_count,
            },
        }

    return {
        "requestId": request_id,
        "dataStatus": risk.data_status,
        "timestamp": now.isoformat(),
        "data": {
            "risk": {
                "areaId": effective_area_id,
                "riskLevel": risk.risk_level,
                "riskScore": risk.risk_score,
                "confidence": risk.confidence,
                "dataStatus": risk.data_status,
                "evidence": [
                    {
                        "signal": s.signal,
                        "value": s.value,
                        "subScore": s.sub_score,
                        "status": s.data_status,
                        "message": s.message,
                    }
                    for s in risk.signals
                ],
                "updatedAt": risk.computed_at.isoformat(),
            },
            "activeAlerts": active_alert_count,
            "nearbyShelters": nearby_shelters_count,
            "roadClosures": road_closures_count,
        },
    }
