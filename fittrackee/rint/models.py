from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, UniqueConstraint

from fittrackee import BaseModel, db


class ActivityRecording(BaseModel):
    __tablename__ = "rint_recordings"
    __table_args__ = (
        UniqueConstraint("user_id", "source_id"),
        UniqueConstraint("user_id", "digest"),
    )
    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(
        db.Integer,
        db.ForeignKey("workouts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id = db.Column(db.String(160), nullable=False)
    digest = db.Column(db.String(64), nullable=False)
    data = db.Column(JSON, nullable=False)
    analysis = db.Column(JSON, nullable=False)
    privacy_radius_m = db.Column(db.Integer, nullable=False, default=200)
    workout = db.relationship(
        "Workout",
        backref=db.backref(
            "rint_recording", uselist=False, cascade="all, delete-orphan"
        ),
    )

    def __init__(self, **values: Any) -> None:
        super().__init__(**values)


class ImportBatch(BaseModel):
    __tablename__ = "rint_imports"
    id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid4())
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    archive_path = db.Column(db.String(255), nullable=False)
    items = db.Column(JSON, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )
    visibility = db.Column(db.String(30), nullable=False, default="private")

    def __init__(self, **values: Any) -> None:
        super().__init__(**values)

    def serialize(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "visibility": self.visibility,
            "items": self.items,
            "total": len(self.items),
            "completed": sum(
                i["status"] in ("imported", "duplicate", "error")
                for i in self.items
            ),
        }


class HealthWorkout(BaseModel):
    """Health identity and source data, independent of delivery IDs."""

    __tablename__ = "rint_health_workouts"
    __table_args__ = (UniqueConstraint("user_id", "health_id"),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workout_id = db.Column(
        db.Integer,
        db.ForeignKey("workouts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    health_id = db.Column(db.String(36), nullable=False)
    sync_key = db.Column(db.String(64), nullable=True, index=True)
    digest = db.Column(db.String(64), nullable=False)
    data = db.Column(JSON, nullable=False)
    origin = db.Column(JSON, nullable=False)
    workout = db.relationship(
        "Workout",
        backref=db.backref("health_sources", cascade="all, delete-orphan"),
    )

    def __init__(self, **values: Any) -> None:
        super().__init__(**values)

    def serialize(self) -> dict[str, Any]:
        return {
            "health_id": self.health_id,
            "recording": self.data,
            "origin": self.origin,
        }


class ActivityAnalysisCache(BaseModel):
    """Reproducible analysis for earlier FitTrackee uploads, without changing
    their recording identity or the importer's account-level deduplication."""

    __tablename__ = "rint_analysis_cache"
    workout_id = db.Column(
        db.Integer,
        db.ForeignKey("workouts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    data = db.Column(JSON, nullable=False)
    analysis = db.Column(JSON, nullable=False)
    privacy_radius_m = db.Column(db.Integer, nullable=False, default=200)
    workout = db.relationship(
        "Workout",
        backref=db.backref(
            "rint_analysis_cache", uselist=False, cascade="all, delete-orphan"
        ),
    )

    def __init__(self, **values: Any) -> None:
        super().__init__(**values)
