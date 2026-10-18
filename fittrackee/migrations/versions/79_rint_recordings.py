"""Independent activity streams and resumable Strava migration."""

import sqlalchemy as sa
from alembic import op

revision = "rint_recordings_01"
down_revision = "2e3a59ebbc59"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "rint_recordings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "workout_id",
            sa.Integer,
            sa.ForeignKey("workouts.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_id", sa.String(160), nullable=False),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.Column("data", sa.JSON, nullable=False),
        sa.Column("analysis", sa.JSON, nullable=False),
        sa.Column(
            "privacy_radius_m",
            sa.Integer,
            nullable=False,
            server_default="200",
        ),
        sa.UniqueConstraint("user_id", "source_id"),
        sa.UniqueConstraint("user_id", "digest"),
    )
    op.create_index(
        "ix_rint_recordings_user_id", "rint_recordings", ["user_id"]
    )
    op.create_table(
        "rint_imports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("archive_path", sa.String(255), nullable=False),
        sa.Column("items", sa.JSON, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "visibility",
            sa.String(30),
            nullable=False,
            server_default="private",
        ),
    )
    op.create_index("ix_rint_imports_user_id", "rint_imports", ["user_id"])


def downgrade():
    op.drop_table("rint_imports")
    op.drop_table("rint_recordings")
