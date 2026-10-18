"""Indoor sport labels for independent sensor recordings."""

import sqlalchemy as sa
from alembic import op

revision = "rint_indoor_02"
down_revision = "rint_recordings_01"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    for label in [
        "Indoor Running",
        "Indoor Cycling",
        "Pool Swimming",
        "Strength Training",
        "Workout",
    ]:
        connection.execute(
            sa.text(
                "INSERT INTO sports "
                "(label, is_active, stopped_speed_threshold) "
                "SELECT :label, true, 0 WHERE NOT EXISTS "
                "(SELECT 1 FROM sports WHERE label=:label)"
            ),
            {"label": label},
        )


def downgrade():
    # Preserve user activities and sport mappings when downgrading.
    pass
