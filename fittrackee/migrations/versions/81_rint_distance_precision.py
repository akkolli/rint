"""Retain ultra-distance recordings without overflowing legacy km columns."""

import sqlalchemy as sa
from alembic import op

revision = "rint_distance_03"
down_revision = "rint_indoor_02"
branch_labels = None
depends_on = None


def upgrade():
    for table in ("workouts", "workout_segments"):
        op.alter_column(
            table,
            "distance",
            type_=sa.Numeric(9, 3),
            existing_type=sa.Numeric(6, 3),
        )


def downgrade():
    for table in ("workouts", "workout_segments"):
        op.alter_column(
            table,
            "distance",
            type_=sa.Numeric(6, 3),
            existing_type=sa.Numeric(9, 3),
        )
