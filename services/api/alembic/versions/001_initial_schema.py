"""Initial FloodShield schema – all core tables with PostGIS geometry.

Revision ID: 001_initial
Revises: None
Create Date: 2026-07-15

Tables created:
  organizations, users, audit_logs, data_sources, official_alerts,
  observations, hazard_reports, road_events, shelters, risk_snapshots,
  route_requests, route_results, tasks, notification_deliveries
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geometry

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all FloodShield tables."""
    # Always ensure PostGIS is available
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # ------------------------------------------------------------------
    # organizations
    # ------------------------------------------------------------------
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),  # community, property, emergency_station, operator
        sa.Column("geometry", Geometry("POLYGON", srid=4326), nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("phone_hash", sa.String(64), nullable=True),
        sa.Column("phone_encrypted", postgresql.BYTEA, nullable=True),
        sa.Column("role", sa.String(50), nullable=False),  # resident, community, emergency_station, admin, operator
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("accessibility_preferences", postgresql.JSONB, server_default="{}"),
        sa.Column("location_consent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ------------------------------------------------------------------
    # audit_logs  (IMMUTABLE – no updated_at)
    # ------------------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("before_json", postgresql.JSONB, nullable=True),
        sa.Column("after_json", postgresql.JSONB, nullable=True),
        sa.Column("request_id", sa.String(36), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ------------------------------------------------------------------
    # data_sources
    # ------------------------------------------------------------------
    op.create_table(
        "data_sources",
        sa.Column("id", sa.String(50), primary_key=True),  # e.g. "cma_warning", "local_rain"
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("authorization_status", sa.String(50), server_default="authorized"),
        sa.Column("geometry", Geometry("POLYGON", srid=4326), nullable=True),
        sa.Column("refresh_interval_seconds", sa.Integer, server_default="3600"),
        sa.Column("field_mapping_json", postgresql.JSONB, nullable=True),
        sa.Column("trust_level", sa.Float, server_default="0.8"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("responsible_person", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ------------------------------------------------------------------
    # official_alerts
    # ------------------------------------------------------------------
    op.create_table(
        "official_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", sa.String(50), sa.ForeignKey("data_sources.id"), nullable=False),
        sa.Column("source_event_id", sa.String(200), nullable=False),
        sa.Column("hazard_type", sa.String(50), nullable=False),  # rainstorm, flood, typhoon, etc.
        sa.Column("official_level", sa.String(20), nullable=False),  # blue, yellow, orange, red
        sa.Column("official_color", sa.String(20), nullable=True),
        sa.Column("geometry", Geometry("GEOMETRY", srid=4326), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB, nullable=True),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("action_guide", sa.Text, nullable=True),
        sa.Column("language", sa.String(10), server_default="zh-CN"),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("source_id", "source_event_id", name="uq_official_alerts_source_event"),
    )

    # ------------------------------------------------------------------
    # observations
    # ------------------------------------------------------------------
    op.create_table(
        "observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", sa.String(50), sa.ForeignKey("data_sources.id"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),  # rainfall, water_level, pump_station
        sa.Column("geometry", Geometry("POINT", srid=4326), nullable=True),
        sa.Column("value_json", postgresql.JSONB, nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_status", sa.String(30), server_default="pending"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ------------------------------------------------------------------
    # hazard_reports
    # ------------------------------------------------------------------
    op.create_table(
        "hazard_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("reporter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("state", sa.String(30), server_default="submitted"),  # submitted, pending_review, verified, active, expired, rejected
        sa.Column("rough_location", Geometry("POINT", srid=4326), nullable=True),
        sa.Column("exact_location_encrypted", postgresql.BYTEA, nullable=True),
        sa.Column("observation_json", postgresql.JSONB, nullable=True),
        sa.Column("media_refs", postgresql.JSONB, server_default="[]"),
        sa.Column("priority", sa.Integer, server_default="0"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reject_reason", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ------------------------------------------------------------------
    # road_events
    # ------------------------------------------------------------------
    op.create_table(
        "road_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("road_segment_ref", sa.String(200), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=False),  # closure, flood, debris, construction
        sa.Column("severity", sa.String(30), nullable=False),  # blocked, restricted, advisory
        sa.Column("state", sa.String(30), server_default="active"),  # active, expired, resolved
        sa.Column("source_id", sa.String(50), sa.ForeignKey("data_sources.id"), nullable=True),
        sa.Column("geometry", Geometry("LINESTRING", srid=4326), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ------------------------------------------------------------------
    # shelters
    # ------------------------------------------------------------------
    op.create_table(
        "shelters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("geometry", Geometry("POINT", srid=4326), nullable=True),
        sa.Column("status", sa.String(30), server_default="unknown"),  # unknown, open, opening_soon, capacity_limited, full, closed
        sa.Column("capacity_total", sa.Integer, nullable=True),
        sa.Column("capacity_estimated", sa.Integer, nullable=True),
        sa.Column("capacity_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accessibility_json", postgresql.JSONB, server_default="{}"),
        sa.Column("contact_json", postgresql.JSONB, server_default="{}"),
        sa.Column("source_id", sa.String(50), sa.ForeignKey("data_sources.id"), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ------------------------------------------------------------------
    # risk_snapshots
    # ------------------------------------------------------------------
    op.create_table(
        "risk_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("area_id", sa.String(100), nullable=False),
        sa.Column("risk_band", sa.String(20), nullable=False),  # normal, attention, high, critical, unknown
        sa.Column("risk_score", sa.Float, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("data_status", sa.String(20), nullable=False),  # fresh, partial, stale, unknown
        sa.Column("evidence_json", postgresql.JSONB, nullable=False),
        sa.Column("rule_version", sa.String(50), nullable=False),
        sa.Column("input_snapshot_json", postgresql.JSONB, nullable=False),
        sa.Column("conflicts_json", postgresql.JSONB, server_default="[]"),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_risk_snapshots_area_calculated",
        "risk_snapshots",
        ["area_id", sa.text("calculated_at DESC")],
    )

    # ------------------------------------------------------------------
    # route_requests
    # ------------------------------------------------------------------
    op.create_table(
        "route_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("origin_geometry", Geometry("POINT", srid=4326), nullable=True),
        sa.Column("destination_geometry", Geometry("POINT", srid=4326), nullable=True),
        sa.Column("constraints_json", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ------------------------------------------------------------------
    # route_results
    # ------------------------------------------------------------------
    op.create_table(
        "route_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("route_requests.id"), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("route_geometry", Geometry("LINESTRING", srid=4326), nullable=True),
        sa.Column("travel_time_seconds", sa.Integer, nullable=True),
        sa.Column("risk_cost", sa.Float, nullable=True),
        sa.Column("route_label", sa.String(50), nullable=True),  # recommended, alternative, high_risk
        sa.Column("evidence_json", postgresql.JSONB, nullable=False),
        sa.Column("data_status", sa.String(20), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ------------------------------------------------------------------
    # tasks
    # ------------------------------------------------------------------
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_type", sa.String(50), nullable=False),  # patrol, blockade, transfer, supply, notification
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(30), server_default="created"),  # created, assigned, acknowledged, in_progress, completed, failed, escalated
        sa.Column("priority", sa.Integer, server_default="0"),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("related_resource_type", sa.String(50), nullable=True),
        sa.Column("related_resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result_notes", sa.Text, nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ------------------------------------------------------------------
    # notification_deliveries
    # ------------------------------------------------------------------
    op.create_table(
        "notification_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("idempotency_key", sa.String(100), unique=True, nullable=True),
        sa.Column("subscription_id", sa.String(100), nullable=True),
        sa.Column("channel", sa.String(30), nullable=False),  # sms, push, wechat, email, phone
        sa.Column("recipient", sa.String(200), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("status", sa.String(30), server_default="pending"),  # pending, queued, sent, delivered, acknowledged, failed, retrying
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer, server_default="0"),
        sa.Column("max_retries", sa.Integer, server_default="3"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, server_default="{}"),
    )


def downgrade() -> None:
    """Drop all FloodShield tables in reverse dependency order."""
    op.drop_table("notification_deliveries")
    op.drop_table("tasks")
    op.drop_table("route_results")
    op.drop_table("route_requests")
    op.drop_index("ix_risk_snapshots_area_calculated", table_name="risk_snapshots")
    op.drop_table("risk_snapshots")
    op.drop_table("shelters")
    op.drop_table("road_events")
    op.drop_table("hazard_reports")
    op.drop_table("observations")
    op.drop_table("official_alerts")
    op.drop_table("data_sources")
    op.drop_table("audit_logs")
    op.drop_table("users")
    op.drop_table("organizations")
