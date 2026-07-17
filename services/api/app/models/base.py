from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'operator', 'community', 'emergency', 'viewer')",
            name="ck_user_role_valid",
        ),
    )

    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="viewer")
    organization_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("organizations.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    organization: Mapped[Organization | None] = relationship(back_populates="members")


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    org_type: Mapped[str] = mapped_column(String(64), default="government")
    members: Mapped[list[User]] = relationship(back_populates="organization")


class AuditLog(TimestampMixin, Base):
    __tablename__ = "audit_logs"

    actor_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class OfficialAlert(TimestampMixin, Base):
    __tablename__ = "official_alerts"

    source: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    alert_type: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    area_geojson: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    effective_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Observation(TimestampMixin, Base):
    __tablename__ = "observations"

    source: Mapped[str] = mapped_column(String(64), nullable=False)
    station_id: Mapped[str] = mapped_column(String(64), nullable=False)
    obs_type: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(16), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    quality_flag: Mapped[str] = mapped_column(String(16), default="normal")
    location_geojson: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class RiskSnapshot(TimestampMixin, Base):
    __tablename__ = "risk_snapshots"
    __table_args__ = (
        CheckConstraint(
            "risk_level IN ('normal', 'attention', 'high', 'critical', 'unknown')",
            name="ck_risk_level_valid",
        ),
        CheckConstraint(
            "risk_score >= -1.0 AND risk_score <= 1.0",
            name="ck_risk_score_range",
        ),
    )

    area_id: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    rule_version: Mapped[str] = mapped_column(String(32), default="v1.0")
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class HazardReport(TimestampMixin, Base):
    __tablename__ = "hazard_reports"

    reporter_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    report_type: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    location_geojson: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending_review")
    location_fuzzed_geojson: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    verified_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RoadEvent(TimestampMixin, Base):
    __tablename__ = "road_events"

    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    road_name: Mapped[str] = mapped_column(String(256), nullable=False)
    location_geojson: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    effective_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(String(64), default="manual")


class Shelter(TimestampMixin, Base):
    __tablename__ = "shelters"
    __table_args__ = (
        CheckConstraint("current_occupancy >= 0", name="ck_shelter_occupancy_non_negative"),
        CheckConstraint("current_occupancy <= capacity", name="ck_shelter_occupancy_within_capacity"),
    )

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    address: Mapped[str] = mapped_column(String(512), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    current_occupancy: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="open")
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    facilities: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    location_geojson: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class RouteRequest(TimestampMixin, Base):
    __tablename__ = "route_requests"

    requester_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    origin_geojson: Mapped[dict] = mapped_column(JSONB, nullable=False)
    destination_geojson: Mapped[dict] = mapped_column(JSONB, nullable=False)
    transport_mode: Mapped[str] = mapped_column(String(32), default="walking")
    avoid_hazards: Mapped[bool] = mapped_column(Boolean, default=True)


class RouteResult(TimestampMixin, Base):
    __tablename__ = "route_results"

    request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("route_requests.id"), nullable=False)
    route_geojson: Mapped[dict] = mapped_column(JSONB, nullable=False)
    distance_m: Mapped[float] = mapped_column(Float, nullable=False)
    duration_s: Mapped[float] = mapped_column(Float, nullable=False)
    safety_score: Mapped[float] = mapped_column(Float, nullable=False)
    warnings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    is_viable: Mapped[bool] = mapped_column(Boolean, default=True)


class NotificationDelivery(TimestampMixin, Base):
    __tablename__ = "notification_deliveries"

    subscription_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    recipient: Mapped[str] = mapped_column(String(256), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class NotificationSubscription(TimestampMixin, Base):
    __tablename__ = "notification_subscriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    area_id: Mapped[str] = mapped_column(String(64), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), default="push")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    priority: Mapped[str] = mapped_column(String(16), default="medium")
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
