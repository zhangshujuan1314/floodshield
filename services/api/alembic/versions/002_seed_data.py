"""Seed data – deterministic demo records for development and testing.

Revision ID: 002_seed
Revises: 001_initial
Create Date: 2026-07-15

All UUIDs are generated via uuid5 with a fixed namespace so tests can
reference them by constant.  All timestamps use Asia/Shanghai (+08:00).
Geometry values use PostGIS ST_GeomFromText / ST_SetSRID.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_seed"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ---------------------------------------------------------------------------
# Fixed namespace for deterministic UUID5 generation
# ---------------------------------------------------------------------------
_NS = uuid.UUID("a3f1b2c4-d5e6-7890-abcd-ef1234567890")

# ---------------------------------------------------------------------------
# Timezone helper
# ---------------------------------------------------------------------------
TZ_SHANGHAI = timezone(timedelta(hours=8))


def _dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0) -> str:
    """Return an ISO-8601 timestamp string in Asia/Shanghai."""
    return datetime(year, month, day, hour, minute, second, tzinfo=TZ_SHANGHAI).isoformat()


def _uid(name: str) -> str:
    """Return a deterministic UUID string from a human-readable name."""
    return str(uuid.uuid5(_NS, name))


# ---------------------------------------------------------------------------
# Deterministic IDs – importable by tests
# ---------------------------------------------------------------------------
# Organizations
ORG_COMMUNITY = _uid("org.community_committee")
ORG_EMERGENCY = _uid("org.emergency_station")

# Users
USER_ADMIN = _uid("user.admin")
USER_COMMUNITY_MGR = _uid("user.community_manager")
USER_EMERGENCY_OFF = _uid("user.emergency_officer")
USER_RESIDENT_1 = _uid("user.resident_1")
USER_RESIDENT_2 = _uid("user.resident_2")

# Data sources
SRC_CMA = "cma_warning"
SRC_RAIN = "local_rain"
SRC_PUBLIC = "public_report"

# Official alerts
ALERT_YELLOW = _uid("alert.yellow_rainstorm")
ALERT_BLUE = _uid("alert.blue_expired")
ALERT_ORANGE = _uid("alert.orange_revoked")

# Observations
OBS_RAIN_1 = _uid("obs.rain_1")
OBS_RAIN_2 = _uid("obs.rain_2")
OBS_RAIN_3 = _uid("obs.rain_3")
OBS_RAIN_4 = _uid("obs.rain_4")
OBS_RAIN_5 = _uid("obs.rain_5")

# Hazard reports
HAZ_SUBMITTED = _uid("haz.submitted")
HAZ_PENDING = _uid("haz.pending_review")
HAZ_VERIFIED = _uid("haz.verified")
HAZ_REJECTED = _uid("haz.rejected")
HAZ_EXPIRED = _uid("haz.expired")

# Road events
ROAD_BLOCKED = _uid("road.blocked")
ROAD_RESTRICTED = _uid("road.restricted")
ROAD_RESOLVED = _uid("road.resolved_debris")

# Shelters
SHELTER_OPEN = _uid("shelter.open")
SHELTER_LIMITED = _uid("shelter.limited")
SHELTER_FULL = _uid("shelter.full")
SHELTER_CLOSED = _uid("shelter.closed")

# Risk snapshots
RISK_NORMAL = _uid("risk.normal")
RISK_HIGH = _uid("risk.high")
RISK_UNKNOWN = _uid("risk.unknown")

# Tasks
TASK_PATROL = _uid("task.patrol")
TASK_SUPPLY = _uid("task.supply")

# Notification deliveries
NOTIF_SENT = _uid("notif.sent")
NOTIF_FAILED = _uid("notif.failed")
NOTIF_ACKED = _uid("notif.acknowledged")


def upgrade() -> None:
    """Insert seed data."""
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    conn = op.get_bind()

    # ==================================================================
    # Organizations
    # ==================================================================
    conn.execute(sa.text("""
        INSERT INTO organizations (id, name, type, geometry, status, created_at, updated_at)
        VALUES
        (
            :org1_id, '示范社区居委会', 'community',
            ST_SetSRID(ST_GeomFromText('POLYGON((116.38 39.90, 116.42 39.90, 116.42 39.93, 116.38 39.93, 116.38 39.90))'), 4326),
            'active', :now, :now
        ),
        (
            :org2_id, '应急管理站', 'emergency_station',
            ST_SetSRID(ST_GeomFromText('POLYGON((116.35 39.88, 116.45 39.88, 116.45 39.95, 116.35 39.95, 116.35 39.88))'), 4326),
            'active', :now, :now
        )
    """), {
        "org1_id": ORG_COMMUNITY,
        "org2_id": ORG_EMERGENCY,
        "now": _dt(2026, 1, 1, 8, 0),
    })

    # ==================================================================
    # Users
    # ==================================================================
    conn.execute(sa.text("""
        INSERT INTO users (id, display_name, phone_hash, phone_encrypted, role, organization_id, accessibility_preferences, location_consent_at, created_at, updated_at, disabled_at)
        VALUES
        (
            :u1, '系统管理员', NULL, NULL, 'admin', NULL,
            '{}'::jsonb, NULL, :now, :now, NULL
        ),
        (
            :u2, '社区管理员', 'sha256_phone_mgr', NULL, 'community', :org1,
            '{"font_size": "large"}'::jsonb, :now, :now, :now, NULL
        ),
        (
            :u3, '应急管理员', 'sha256_phone_emg', NULL, 'emergency_station', :org2,
            '{}'::jsonb, :now, :now, :now, NULL
        ),
        (
            :u4, '居民甲', 'sha256_phone_r1', NULL, 'resident', :org1,
            '{"high_contrast": true}'::jsonb, :now, :now, :now, NULL
        ),
        (
            :u5, '居民乙', 'sha256_phone_r2', NULL, 'resident', :org1,
            '{}'::jsonb, NULL, :now, :now, NULL
        )
    """), {
        "u1": USER_ADMIN,
        "u2": USER_COMMUNITY_MGR,
        "u3": USER_EMERGENCY_OFF,
        "u4": USER_RESIDENT_1,
        "u5": USER_RESIDENT_2,
        "org1": ORG_COMMUNITY,
        "org2": ORG_EMERGENCY,
        "now": _dt(2026, 1, 1, 8, 0),
    })

    # ==================================================================
    # Data Sources
    # ==================================================================
    conn.execute(sa.text("""
        INSERT INTO data_sources (id, name, source_type, authorization_status, geometry, refresh_interval_seconds, field_mapping_json, trust_level, is_active, responsible_person, created_at, updated_at)
        VALUES
        (
            :ds1, '中国气象局预警', 'official', 'authorized',
            ST_SetSRID(ST_GeomFromText('POLYGON((116.0 39.5, 117.0 39.5, 117.0 40.5, 116.0 40.5, 116.0 39.5))'), 4326),
            600,
            '{"level_field": "level", "type_field": "type"}'::jsonb,
            0.95, true, '气象局对接人', :now, :now
        ),
        (
            :ds2, '本地雨量站', 'sensor', 'authorized',
            NULL,
            300,
            '{"value_field": "rainfall_mm", "unit": "mm/h"}'::jsonb,
            0.90, true, '水务局技术员', :now, :now
        ),
        (
            :ds3, '公众上报', 'crowdsourced', 'authorized',
            NULL,
            0,
            '{}'::jsonb,
            0.60, true, '社区管理员', :now, :now
        )
    """), {
        "ds1": SRC_CMA,
        "ds2": SRC_RAIN,
        "ds3": SRC_PUBLIC,
        "now": _dt(2026, 1, 1, 8, 0),
    })

    # ==================================================================
    # Official Alerts
    # ==================================================================
    conn.execute(sa.text("""
        INSERT INTO official_alerts (id, source_id, source_event_id, hazard_type, official_level, official_color, geometry, issued_at, updated_at, expires_at, revoked_at, raw_payload, source_url, action_guide, language, collected_at)
        VALUES
        (
            :a1, :src_cma, 'CMA-2026-0042', 'rainstorm', 'yellow', 'yellow',
            ST_SetSRID(ST_GeomFromText('POLYGON((116.2 39.8, 116.6 39.8, 116.6 40.1, 116.2 40.1, 116.2 39.8))'), 4326),
            :issued1, :now, :expires1, NULL,
            '{"raw": "暴雨黄色预警信号"}'::jsonb,
            'http://cma.example/alert/2026-0042',
            '请减少外出，注意交通安全，远离低洼地带。',
            'zh-CN', :now
        ),
        (
            :a2, :src_cma, 'CMA-2026-0010', 'rainstorm', 'blue', 'blue',
            ST_SetSRID(ST_GeomFromText('POLYGON((116.0 39.6, 116.8 39.6, 116.8 40.2, 116.0 40.2, 116.0 39.6))'), 4326),
            :issued2, :issued2, :expired2, NULL,
            '{"raw": "暴雨蓝色预警信号"}'::jsonb,
            'http://cma.example/alert/2026-0010',
            '请关注天气变化。',
            'zh-CN', :issued2
        ),
        (
            :a3, :src_cma, 'CMA-2026-0038', 'flood', 'orange', 'orange',
            ST_SetSRID(ST_GeomFromText('POLYGON((116.3 39.85, 116.5 39.85, 116.5 40.0, 116.3 40.0, 116.3 39.85))'), 4326),
            :issued3, :now, :expires3, :revoked3,
            '{"raw": "洪水橙色预警信号"}'::jsonb,
            'http://cma.example/alert/2026-0038',
            '请立即转移至安全区域。',
            'zh-CN', :issued3
        )
    """), {
        "a1": ALERT_YELLOW,
        "a2": ALERT_BLUE,
        "a3": ALERT_ORANGE,
        "src_cma": SRC_CMA,
        "now": _dt(2026, 7, 15, 10, 0),
        "issued1": _dt(2026, 7, 15, 8, 0),
        "expires1": _dt(2026, 7, 16, 8, 0),
        "issued2": _dt(2026, 7, 10, 6, 0),
        "expired2": _dt(2026, 7, 10, 18, 0),
        "issued3": _dt(2026, 7, 14, 14, 0),
        "expires3": _dt(2026, 7, 16, 14, 0),
        "revoked3": _dt(2026, 7, 15, 9, 0),
    })

    # ==================================================================
    # Observations – rainfall readings
    # ==================================================================
    conn.execute(sa.text("""
        INSERT INTO observations (id, source_id, type, geometry, value_json, observed_at, expires_at, verification_status, created_by, created_at)
        VALUES
        (
            :o1, :src_rain, 'rainfall',
            ST_SetSRID(ST_GeomFromText('POINT(116.40 39.91)'), 4326),
            '{"rainfall_mm": 12.5, "duration_min": 60}'::jsonb,
            :obs_time1, :exp1, 'verified', :admin, :now
        ),
        (
            :o2, :src_rain, 'rainfall',
            ST_SetSRID(ST_GeomFromText('POINT(116.41 39.92)'), 4326),
            '{"rainfall_mm": 28.3, "duration_min": 60}'::jsonb,
            :obs_time2, :exp2, 'verified', :admin, :now
        ),
        (
            :o3, :src_rain, 'rainfall',
            ST_SetSRID(ST_GeomFromText('POINT(116.39 39.90)'), 4326),
            '{"rainfall_mm": 5.1, "duration_min": 60}'::jsonb,
            :obs_time3, :exp3, 'verified', :admin, :now
        ),
        (
            :o4, :src_rain, 'rainfall',
            ST_SetSRID(ST_GeomFromText('POINT(116.42 39.89)'), 4326),
            '{"rainfall_mm": 45.0, "duration_min": 60}'::jsonb,
            :obs_time4, :exp4, 'pending', NULL, :now
        ),
        (
            :o5, :src_rain, 'water_level',
            ST_SetSRID(ST_GeomFromText('POINT(116.40 39.91)'), 4326),
            '{"water_level_m": 3.2, "warning_level_m": 4.5}'::jsonb,
            :obs_time5, :exp5, 'verified', :admin, :now
        )
    """), {
        "o1": OBS_RAIN_1, "o2": OBS_RAIN_2, "o3": OBS_RAIN_3,
        "o4": OBS_RAIN_4, "o5": OBS_RAIN_5,
        "src_rain": SRC_RAIN,
        "admin": USER_ADMIN,
        "now": _dt(2026, 7, 15, 10, 0),
        "obs_time1": _dt(2026, 7, 15, 9, 0), "exp1": _dt(2026, 7, 15, 15, 0),
        "obs_time2": _dt(2026, 7, 15, 9, 0), "exp2": _dt(2026, 7, 15, 15, 0),
        "obs_time3": _dt(2026, 7, 15, 9, 0), "exp3": _dt(2026, 7, 15, 15, 0),
        "obs_time4": _dt(2026, 7, 15, 10, 0), "exp4": _dt(2026, 7, 15, 16, 0),
        "obs_time5": _dt(2026, 7, 15, 9, 30), "exp5": _dt(2026, 7, 15, 15, 30),
    })

    # ==================================================================
    # Hazard Reports (various states)
    # ==================================================================
    conn.execute(sa.text("""
        INSERT INTO hazard_reports (id, reporter_id, event_type, state, rough_location, exact_location_encrypted, observation_json, media_refs, priority, submitted_at, verified_at, expires_at, verified_by, reject_reason, created_at, updated_at)
        VALUES
        (
            :h1, :r1, 'flood', 'submitted',
            ST_SetSRID(ST_GeomFromText('POINT(116.405 39.915)'), 4326),
            NULL,
            '{"depth_cm": 20, "note": "路面积水严重"}'::jsonb,
            '["media/001.jpg"]'::jsonb,
            1, :now, NULL, :exp1, NULL, NULL, :now, :now
        ),
        (
            :h2, :r2, 'debris', 'pending_review',
            ST_SetSRID(ST_GeomFromText('POINT(116.410 39.920)'), 4326),
            NULL,
            '{"description": "树枝堵塞排水口"}'::jsonb,
            '[]'::jsonb,
            2, :now, NULL, :exp2, NULL, NULL, :now, :now
        ),
        (
            :h3, :r1, 'flood', 'verified',
            ST_SetSRID(ST_GeomFromText('POINT(116.395 39.905)'), 4326),
            NULL,
            '{"depth_cm": 50, "note": "地下室进水"}'::jsonb,
            '["media/003a.jpg", "media/003b.jpg"]'::jsonb,
            3, :submit3, :verify3, :exp3, :verifier, NULL, :submit3, :now
        ),
        (
            :h4, :r2, 'road_damage', 'rejected',
            ST_SetSRID(ST_GeomFromText('POINT(116.430 39.930)'), 4326),
            NULL,
            '{"note": "路面裂缝"}'::jsonb,
            '[]'::jsonb,
            0, :submit4, :verify4, NULL, :verifier, '经核实为正常路面伸缩缝，非险情。', :submit4, :now
        ),
        (
            :h5, :r1, 'flood', 'expired',
            ST_SetSRID(ST_GeomFromText('POINT(116.400 39.910)'), 4326),
            NULL,
            '{"depth_cm": 10, "note": "已退水"}'::jsonb,
            '[]'::jsonb,
            1, :submit5, NULL, :exp5, NULL, NULL, :submit5, :now
        )
    """), {
        "h1": HAZ_SUBMITTED, "h2": HAZ_PENDING, "h3": HAZ_VERIFIED,
        "h4": HAZ_REJECTED, "h5": HAZ_EXPIRED,
        "r1": USER_RESIDENT_1, "r2": USER_RESIDENT_2,
        "verifier": USER_EMERGENCY_OFF,
        "now": _dt(2026, 7, 15, 10, 0),
        "exp1": _dt(2026, 7, 16, 10, 0),
        "exp2": _dt(2026, 7, 16, 10, 0),
        "submit3": _dt(2026, 7, 14, 16, 0), "verify3": _dt(2026, 7, 14, 18, 0), "exp3": _dt(2026, 7, 16, 16, 0),
        "submit4": _dt(2026, 7, 13, 10, 0), "verify4": _dt(2026, 7, 13, 14, 0),
        "submit5": _dt(2026, 7, 10, 8, 0), "exp5": _dt(2026, 7, 11, 8, 0),
    })

    # ==================================================================
    # Road Events
    # ==================================================================
    conn.execute(sa.text("""
        INSERT INTO road_events (id, road_segment_ref, event_type, severity, state, source_id, geometry, valid_from, valid_until, verified_by, created_at, updated_at)
        VALUES
        (
            :re1, 'SEG-A001-朝阳路', 'closure', 'blocked', 'active', :src_rain,
            ST_SetSRID(ST_GeomFromText('LINESTRING(116.400 39.910, 116.405 39.912, 116.410 39.915)'), 4326),
            :now, :until1, :verifier, :now, :now
        ),
        (
            :re2, 'SEG-B002-长安街', 'flood', 'restricted', 'active', :src_cma,
            ST_SetSRID(ST_GeomFromText('LINESTRING(116.390 39.905, 116.395 39.908)'), 4326),
            :now, :until2, :verifier, :now, :now
        ),
        (
            :re3, 'SEG-C003-建国路', 'debris', 'advisory', 'resolved', :src_public,
            ST_SetSRID(ST_GeomFromText('LINESTRING(116.415 39.900, 116.418 39.902)'), 4326),
            :from3, :until3, :verifier, :from3, :now
        )
    """), {
        "re1": ROAD_BLOCKED, "re2": ROAD_RESTRICTED, "re3": ROAD_RESOLVED,
        "src_rain": SRC_RAIN, "src_cma": SRC_CMA, "src_public": SRC_PUBLIC,
        "verifier": USER_EMERGENCY_OFF,
        "now": _dt(2026, 7, 15, 10, 0),
        "until1": _dt(2026, 7, 17, 10, 0),
        "until2": _dt(2026, 7, 16, 10, 0),
        "from3": _dt(2026, 7, 14, 8, 0), "until3": _dt(2026, 7, 15, 8, 0),
    })

    # ==================================================================
    # Shelters
    # ==================================================================
    conn.execute(sa.text("""
        INSERT INTO shelters (id, name, address, geometry, status, capacity_total, capacity_estimated, capacity_updated_at, accessibility_json, contact_json, source_id, verified_at, expires_at, created_at, updated_at)
        VALUES
        (
            :s1, '朝阳区第一避难所', '朝阳区幸福路100号',
            ST_SetSRID(ST_GeomFromText('POINT(116.405 39.918)'), 4326),
            'open', 500, 320, :now,
            '{"wheelchair": true, "elevator": true}'::jsonb,
            '{"phone": "010-12345678", "contact_person": "张主任"}'::jsonb,
            :src_public, :now, :exp, :now, :now
        ),
        (
            :s2, '朝阳区第二避难所', '朝阳区光明街50号',
            ST_SetSRID(ST_GeomFromText('POINT(116.412 39.925)'), 4326),
            'capacity_limited', 200, 180, :now,
            '{"wheelchair": false}'::jsonb,
            '{"phone": "010-12345679"}'::jsonb,
            :src_public, :now, :exp, :now, :now
        ),
        (
            :s3, '体育馆临时安置点', '海淀区体育馆路1号',
            ST_SetSRID(ST_GeomFromText('POINT(116.320 39.980)'), 4326),
            'full', 1000, 1000, :now,
            '{"wheelchair": true, "generator": true}'::jsonb,
            '{"phone": "010-87654321"}'::jsonb,
            :src_public, :now, :exp, :now, :now
        ),
        (
            :s4, '社区活动中心', '西城区文化路20号',
            ST_SetSRID(ST_GeomFromText('POINT(116.360 39.910)'), 4326),
            'closed', 100, 0, :now,
            '{}'::jsonb,
            '{"phone": "010-11112222"}'::jsonb,
            :src_public, :close_verified, :exp, :now, :now
        )
    """), {
        "s1": SHELTER_OPEN, "s2": SHELTER_LIMITED, "s3": SHELTER_FULL, "s4": SHELTER_CLOSED,
        "src_public": SRC_PUBLIC,
        "now": _dt(2026, 7, 15, 10, 0),
        "exp": _dt(2026, 7, 22, 10, 0),
        "close_verified": _dt(2026, 7, 10, 8, 0),
    })

    # ==================================================================
    # Risk Snapshots
    # ==================================================================
    conn.execute(sa.text("""
        INSERT INTO risk_snapshots (id, area_id, risk_band, risk_score, confidence, data_status, evidence_json, rule_version, input_snapshot_json, conflicts_json, calculated_at, expires_at)
        VALUES
        (
            :rs1, 'AREA-朝阳区-001', 'normal', 0.15, 0.92, 'fresh',
            '{"rainfall_mm": 5.1, "water_level_m": 1.2, "alert_active": false}'::jsonb,
            'v1.2.0',
            '{"observations": 3, "alerts": 1}'::jsonb,
            '[]'::jsonb,
            :calc1, :exp1
        ),
        (
            :rs2, 'AREA-朝阳区-002', 'high', 0.78, 0.85, 'partial',
            '{"rainfall_mm": 45.0, "water_level_m": 3.8, "alert_active": true, "hazard_reports": 2}'::jsonb,
            'v1.2.0',
            '{"observations": 5, "alerts": 2, "reports": 2}'::jsonb,
            '[{"field": "water_level", "sources_disagree": true}]'::jsonb,
            :calc2, :exp2
        ),
        (
            :rs3, 'AREA-海淀区-001', 'unknown', 0.0, 0.10, 'unknown',
            '{"reason": "no_data"}'::jsonb,
            'v1.2.0',
            '{"observations": 0, "alerts": 0}'::jsonb,
            '[]'::jsonb,
            :calc3, :exp3
        )
    """), {
        "rs1": RISK_NORMAL, "rs2": RISK_HIGH, "rs3": RISK_UNKNOWN,
        "calc1": _dt(2026, 7, 15, 9, 0), "exp1": _dt(2026, 7, 15, 12, 0),
        "calc2": _dt(2026, 7, 15, 9, 30), "exp2": _dt(2026, 7, 15, 12, 30),
        "calc3": _dt(2026, 7, 15, 8, 0), "exp3": _dt(2026, 7, 15, 11, 0),
    })

    # ==================================================================
    # Tasks
    # ==================================================================
    conn.execute(sa.text("""
        INSERT INTO tasks (id, task_type, title, description, status, priority, assigned_to, organization_id, related_resource_type, related_resource_id, created_by, created_at, assigned_at, acknowledged_at, completed_at, result_notes, expires_at)
        VALUES
        (
            :t1, 'patrol', '朝阳路积水巡查', '前往朝阳路积水路段进行现场巡查，确认积水深度并上报。',
            'assigned', 2, :emg_off, :org2, 'road_event', :road_blocked,
            :admin, :now, :assign1, NULL, NULL, NULL, :exp1
        ),
        (
            :t2, 'supply', '避难所物资配送', '向朝阳区第一避难所配送饮用水和应急物资。',
            'completed', 1, :comm_mgr, :org1, 'shelter', :shelter_open,
            :admin, :submit2, :assign2, :ack2, :complete2,
            '物资已全部送达，共200箱饮用水、100条毛毯。', :exp2
        )
    """), {
        "t1": TASK_PATROL, "t2": TASK_SUPPLY,
        "emg_off": USER_EMERGENCY_OFF, "comm_mgr": USER_COMMUNITY_MGR,
        "org1": ORG_COMMUNITY, "org2": ORG_EMERGENCY,
        "road_blocked": ROAD_BLOCKED, "shelter_open": SHELTER_OPEN,
        "admin": USER_ADMIN,
        "now": _dt(2026, 7, 15, 10, 0),
        "assign1": _dt(2026, 7, 15, 10, 5),
        "exp1": _dt(2026, 7, 16, 10, 0),
        "submit2": _dt(2026, 7, 14, 14, 0),
        "assign2": _dt(2026, 7, 14, 14, 10),
        "ack2": _dt(2026, 7, 14, 14, 30),
        "complete2": _dt(2026, 7, 14, 18, 0),
        "exp2": _dt(2026, 7, 15, 14, 0),
    })

    # ==================================================================
    # Notification Deliveries
    # ==================================================================
    import json as _json

    meta1 = _json.dumps({"alert_id": ALERT_YELLOW})
    meta2 = _json.dumps({"provider_error": "timeout"})
    meta3 = _json.dumps({"wechat_msg_id": "MSG-20260715-001"})

    conn.execute(sa.text("""
        INSERT INTO notification_deliveries (id, idempotency_key, subscription_id, channel, recipient, message, status, created_at, sent_at, delivered_at, acknowledged_at, retry_count, max_retries, error_message, metadata_json)
        VALUES
        (
            :n1, 'idem-001', 'sub-alert-001', 'push', 'device:abc123',
            '暴雨黄色预警生效中，请减少外出，注意安全。',
            'delivered', :create1, :sent1, :delivered1, NULL,
            0, 3, NULL, :meta1::jsonb
        ),
        (
            :n2, 'idem-002', 'sub-alert-002', 'sms', '+8613800000001',
            '【防汛预警】暴雨黄色预警，请注意防范。',
            'failed', :create2, :sent2, NULL, NULL,
            3, 3, '运营商网关超时，已达到最大重试次数。',
            :meta2::jsonb
        ),
        (
            :n3, 'idem-003', 'sub-alert-003', 'wechat', 'wxid_user001',
            '您所在区域暴雨预警生效，建议减少出行。',
            'acknowledged', :create3, :sent3, :delivered3, :acked3,
            0, 3, NULL, :meta3::jsonb
        )
    """), {
        "n1": NOTIF_SENT, "n2": NOTIF_FAILED, "n3": NOTIF_ACKED,
        "meta1": meta1, "meta2": meta2, "meta3": meta3,
        "create1": _dt(2026, 7, 15, 8, 5),
        "sent1": _dt(2026, 7, 15, 8, 5, 10),
        "delivered1": _dt(2026, 7, 15, 8, 5, 30),
        "create2": _dt(2026, 7, 15, 8, 5),
        "sent2": _dt(2026, 7, 15, 8, 5, 15),
        "create3": _dt(2026, 7, 15, 8, 5),
        "sent3": _dt(2026, 7, 15, 8, 5, 20),
        "delivered3": _dt(2026, 7, 15, 8, 6, 0),
        "acked3": _dt(2026, 7, 15, 8, 10, 0),
    })


def downgrade() -> None:
    """Remove all seed data (tables remain intact)."""
    conn = op.get_bind()

    # Delete in reverse dependency order
    for table in [
        "notification_deliveries",
        "tasks",
        "risk_snapshots",
        "shelters",
        "road_events",
        "hazard_reports",
        "observations",
        "official_alerts",
        "data_sources",
        "users",
        "organizations",
    ]:
        conn.execute(sa.text(f"DELETE FROM {table}"))
