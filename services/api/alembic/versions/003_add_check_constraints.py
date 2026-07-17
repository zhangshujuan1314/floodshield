"""add check constraints

Revision ID: 003
Revises: 002
Create Date: 2026-07-16
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # User role constraint
    op.create_check_constraint(
        "ck_user_role_valid",
        "users",
        "role IN ('admin', 'operator', 'community', 'emergency', 'viewer')",
    )

    # RiskSnapshot risk_level constraint
    op.create_check_constraint(
        "ck_risk_level_valid",
        "risk_snapshots",
        "risk_level IN ('normal', 'attention', 'high', 'critical', 'unknown')",
    )

    # RiskSnapshot risk_score range constraint
    op.create_check_constraint(
        "ck_risk_score_range",
        "risk_snapshots",
        "risk_score >= -1.0 AND risk_score <= 1.0",
    )

    # Shelter occupancy constraints
    op.create_check_constraint(
        "ck_shelter_occupancy_non_negative",
        "shelters",
        "current_occupancy >= 0",
    )
    op.create_check_constraint(
        "ck_shelter_occupancy_within_capacity",
        "shelters",
        "current_occupancy <= capacity",
    )


def downgrade() -> None:
    op.drop_constraint("ck_shelter_occupancy_within_capacity", "shelters")
    op.drop_constraint("ck_shelter_occupancy_non_negative", "shelters")
    op.drop_constraint("ck_risk_score_range", "risk_snapshots")
    op.drop_constraint("ck_risk_level_valid", "risk_snapshots")
    op.drop_constraint("ck_user_role_valid", "users")
