"""Analysis and endpoint privacy for existing FitTrackee recordings."""

import sqlalchemy as sa
from alembic import op

revision = "rint_analysis_05"
down_revision = "rint_health_04"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "rint_analysis_cache",
        sa.Column(
            "workout_id",
            sa.Integer,
            sa.ForeignKey("workouts.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("data", sa.JSON, nullable=False),
        sa.Column("analysis", sa.JSON, nullable=False),
        sa.Column(
            "privacy_radius_m",
            sa.Integer,
            nullable=False,
            server_default="200",
        ),
    )
    op.create_index(
        "ix_rint_analysis_cache_user_id", "rint_analysis_cache", ["user_id"]
    )


def downgrade():
    op.drop_table("rint_analysis_cache")
