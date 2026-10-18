"""Account-scoped Health identities and retained workout source data."""

import sqlalchemy as sa
from alembic import op

revision = "rint_health_04"
down_revision = "rint_distance_03"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "rint_health_workouts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "workout_id",
            sa.Integer,
            sa.ForeignKey("workouts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("health_id", sa.String(36), nullable=False),
        sa.Column("sync_key", sa.String(64), nullable=True),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.Column("data", sa.JSON, nullable=False),
        sa.Column("origin", sa.JSON, nullable=False),
        sa.UniqueConstraint("user_id", "health_id"),
    )
    for column in ("user_id", "workout_id", "sync_key"):
        op.create_index(
            f"ix_rint_health_workouts_{column}",
            "rint_health_workouts",
            [column],
        )


def downgrade():
    op.drop_table("rint_health_workouts")
