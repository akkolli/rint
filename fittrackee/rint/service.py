import hashlib
import io
import json
import os
from datetime import timedelta, timezone
from typing import Any
from uuid import uuid4

from dateutil.parser import parse as parse_date
from PIL import Image, ImageOps
from shapely.geometry import LineString
from werkzeug.datastructures import FileStorage

from fittrackee import db
from fittrackee.files import get_absolute_file_path
from fittrackee.media.media_service import MediaService
from fittrackee.visibility_levels import VisibilityLevel
from fittrackee.workouts.models import Sport, Workout, WorkoutSegment
from rint_core import analyze
from rint_core.metrics import haversine
from rint_core.parsers import date

from .models import ActivityRecording

SPORTS = {
    "Run": "Running",
    "Trail Run": "Trail",
    "Ride": "Cycling (Sport)",
    "Virtual Ride": "Cycling (Virtual)",
    "Virtual Run": "Indoor Running",
    "Walk": "Walking",
    "Hike": "Hiking",
    "Swim": "Pool Swimming",
    "Weight Training": "Strength Training",
}


def sport_for(label: str) -> Sport:
    mapped = SPORTS.get(label, label)
    sport = Sport.query.filter(
        db.func.lower(Sport.label) == mapped.lower()
    ).first()
    if not sport:
        raise ValueError(
            f"Sport '{label}' needs a sport mapping. "
            "Select an available sport and retry."
        )
    return sport


def create_activity(
    user: Any,
    recording: dict[str, Any],
    *,
    source_id: Any,
    original: Any,
    extension: Any,
    title: Any,
    sport: Any,
    description: Any = "",
    metadata: Any = None,
) -> tuple[Workout, bool]:
    digest = hashlib.sha256(original).hexdigest()
    duplicate = ActivityRecording.query.filter(
        ActivityRecording.user_id == user.id,
        db.or_(
            ActivityRecording.source_id == source_id,
            ActivityRecording.digest == digest,
        ),
    ).first()
    if duplicate:
        return duplicate.workout, True
    analysis = analyze(recording)
    data = analysis["recording"]
    summary = analysis["summary"]
    started = date(data["started_at"])
    workout = Workout(
        user.id,
        sport.id,
        started,
        summary["distance_m"] / 1000,
        timedelta(seconds=summary["elapsed_s"]),
    )
    workout.uuid = uuid4()
    workout.title = title[:255]
    workout.description = description[:10000] if description else None
    if metadata:
        note = metadata.get("original_metadata", {}).get(
            "Activity Private Note"
        )
        workout.notes = note[:10000] if note else None
    workout.source = "Rint / " + source_id.split(":")[0]
    workout.workout_visibility = workout.analysis_visibility = (
        workout.map_visibility
    ) = workout.media_visibility = VisibilityLevel.PRIVATE
    workout.moving = timedelta(seconds=summary["moving_s"])
    workout.pauses = timedelta(seconds=summary["paused_s"])
    workout.ave_speed = (
        summary["distance_m"] / summary["elapsed_s"] * 3.6
        if summary["elapsed_s"]
        else 0
    )
    if summary["pace_s_km"] is not None:
        workout.ave_pace = timedelta(seconds=summary["pace_s_km"])
    for key, suffix in (
        ("heart_rate", "hr"),
        ("cadence", "cadence"),
        ("power", "power"),
    ):
        values = [p[key] for p in data["points"] if key in p]
        if values:
            setattr(workout, f"max_{suffix}", round(max(values)))
        if key in summary["averages"]:
            setattr(workout, f"ave_{suffix}", round(summary["averages"][key]))
    elevation = [p["elevation"] for p in data["points"] if "elevation" in p]
    if elevation:
        workout.min_alt, workout.max_alt = min(elevation), max(elevation)
    db.session.add(workout)
    db.session.flush()
    # Original bytes and metadata remain separate from normalized and
    # calculated data.
    folder = os.path.join("workouts", str(user.id))
    os.makedirs(get_absolute_file_path(folder), exist_ok=True)
    relative = os.path.join(folder, f"rint_{workout.uuid}.{extension}")
    with open(get_absolute_file_path(relative), "wb") as stream:
        stream.write(original)
    workout.original_file = relative
    route = [p for p in data["points"] if "lat" in p]
    if len(route) >= 2:
        segment = WorkoutSegment(workout.id, workout.uuid)
        segment.start_date = started
        segment.duration, segment.moving, segment.pauses = (
            workout.duration,
            workout.moving,
            workout.pauses,
        )
        segment.distance, segment.ave_speed = (
            workout.distance,
            workout.ave_speed,
        )
        segment.geom = LineString([(p["lon"], p["lat"]) for p in route]).wkt
        segment.points = [
            {
                "duration": p["t"],
                "distance": p["d"],
                "time": (started + timedelta(seconds=p["t"])).isoformat(),
                "latitude": p["lat"],
                "longitude": p["lon"],
                **{
                    k: p[k]
                    for k in ("elevation", "heart_rate", "cadence", "power")
                    if k in p
                },
            }
            for p in route
        ]
        db.session.add(segment)
    raw = {**recording, "source_metadata": metadata or {}}
    db.session.add(
        ActivityRecording(
            workout_id=workout.id,
            user_id=user.id,
            source_id=source_id,
            digest=digest,
            data=raw,
            analysis=analysis,
        )
    )
    return workout, False


def refresh_activity(workout: Workout, analysis: dict[str, Any]) -> None:
    """Recalculate without changing user edits or sharing."""
    summary = analysis["summary"]
    data = analysis["recording"]
    workout.distance = summary["distance_m"] / 1000
    workout.duration = timedelta(seconds=summary["elapsed_s"])
    workout.moving = timedelta(seconds=summary["moving_s"])
    workout.pauses = timedelta(seconds=summary["paused_s"])
    workout.ave_speed = (
        summary["distance_m"] / summary["elapsed_s"] * 3.6
        if summary["elapsed_s"]
        else 0
    )
    workout.ave_pace = (
        timedelta(seconds=summary["pace_s_km"])
        if summary["pace_s_km"] is not None
        else None
    )
    for key, suffix in (
        ("heart_rate", "hr"),
        ("cadence", "cadence"),
        ("power", "power"),
    ):
        values = [p[key] for p in data["points"] if key in p]
        setattr(
            workout, f"max_{suffix}", round(max(values)) if values else None
        )
        average = summary["averages"].get(key)
        setattr(
            workout,
            f"ave_{suffix}",
            round(average) if average is not None else None,
        )
    elevation = [p["elevation"] for p in data["points"] if "elevation" in p]
    if elevation:
        workout.min_alt, workout.max_alt = min(elevation), max(elevation)
    # Replace generated geometry so a late route is reflected by every map API.
    for segment in list(workout.segments):
        db.session.delete(segment)
    workout.segments = []
    db.session.flush()
    route = [p for p in data["points"] if "lat" in p]
    if len(route) >= 2:
        started = date(data["started_at"])
        segment = WorkoutSegment(workout.id, workout.uuid)
        segment.start_date = started
        segment.duration, segment.moving, segment.pauses = (
            workout.duration,
            workout.moving,
            workout.pauses,
        )
        segment.distance, segment.ave_speed = (
            workout.distance,
            workout.ave_speed,
        )
        segment.geom = LineString([(p["lon"], p["lat"]) for p in route]).wkt
        segment.points = [
            {
                "duration": p["t"],
                "distance": p["d"],
                "time": (started + timedelta(seconds=p["t"])).isoformat(),
                "latitude": p["lat"],
                "longitude": p["lon"],
                **{
                    k: p[k]
                    for k in ("elevation", "heart_rate", "cadence", "power")
                    if k in p
                },
            }
            for p in route
        ]
        workout.segments.append(segment)


def import_photo(user: Any, workout: Workout, data: bytes, name: str) -> None:
    # Remove metadata before FitTrackee sees the image, including GPS
    # coordinates.
    with Image.open(io.BytesIO(data)) as image:
        converted = ImageOps.exif_transpose(image).convert("RGB")
        output = io.BytesIO()
        converted.save(output, format="JPEG")
    output.seek(0)
    media = MediaService(
        user,
        FileStorage(output, filename="import.jpg", content_type="image/jpeg"),
    ).create_image_media()
    media.workout_id = workout.id
    db.session.commit()


def metadata_recording(item: dict[str, Any]) -> dict[str, Any]:
    started = parse_date(item["date"])
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    elapsed = float(item["elapsed"] or 0)
    # The repeated, precise Strava Distance column is metres. The single
    # display column in simplified CSVs is kilometres; preserve this choice.
    if elapsed <= 0:
        raise ValueError(
            (
                "This activity has neither a recording nor a valid elapsed "
                "duration."
            )
        )
    return {
        "version": 1,
        "started_at": started.isoformat(),
        "points": [
            {"t": 0, "d": 0},
            {
                "t": elapsed,
                "d": float(item["distance"] or 0)
                * (1 if item.get("distance_unit") == "m" else 1000),
            },
        ],
        "laps": [],
        "summary_only": True,
    }


def public_analysis(
    workout: Workout, auth_user: Any, analysis: dict[str, Any]
) -> dict[str, Any]:
    from fittrackee.visibility_levels import can_view, can_view_workout_data

    result = json.loads(json.dumps(analysis))
    owner = auth_user and auth_user.id == workout.user_id
    if owner:
        return result
    allow_map = can_view(workout, "calculated_map_visibility", auth_user)
    allow_hr = can_view_workout_data("hr", workout.user, auth_user)
    route = [p for p in result["recording"]["points"] if "lat" in p]
    endpoints = [dict(route[0]), dict(route[-1])] if route else []
    radius = (
        workout.rint_recording.privacy_radius_m
        if workout.rint_recording
        else (
            workout.rint_analysis_cache.privacy_radius_m
            if workout.rint_analysis_cache
            else 200
        )
    )
    for p in result["recording"]["points"]:
        if not allow_map or (
            route
            and (
                haversine(p, endpoints[0]) < radius
                or haversine(p, endpoints[-1]) < radius
            )
            if "lat" in p
            else False
        ):
            if "lat" in p:
                # Distinguish privacy redaction from an ordinary sensor-only
                # sample. Clients may join GPS fixes across sensor samples,
                # but must never draw through a hidden location.
                p["route_gap"] = True
            p.pop("lat", None)
            p.pop("lon", None)
        if not allow_hr:
            p.pop("heart_rate", None)
    if not allow_hr:
        for row in [
            result["summary"],
            *result["splits_km"],
            *result["splits_mile"],
            *result["laps"],
        ]:
            row["averages"].pop("heart_rate", None)
            row["coverage_s"].pop("heart_rate", None)
    return result


def redact_legacy_route(
    workout: Workout, data: dict[str, Any]
) -> dict[str, Any]:
    result = copy_data = json.loads(json.dumps(data))
    recording = workout.rint_recording or workout.rint_analysis_cache
    if recording is None:
        return result
    points = [
        p for p in recording.analysis["recording"]["points"] if "lat" in p
    ]
    if not points:
        return result
    radius = recording.privacy_radius_m

    def visible(lat: float, lon: float) -> bool:
        p = {"lat": lat, "lon": lon}
        return (
            haversine(p, points[0]) >= radius
            and haversine(p, points[-1]) >= radius
        )

    if "chart_data" in copy_data:
        for p in copy_data["chart_data"] or []:
            if "latitude" in p and not visible(p["latitude"], p["longitude"]):
                p.pop("latitude", None)
                p.pop("longitude", None)
    if "geojson" in result:
        # Preserve breaks when the route re-enters a protected location.
        lines, line = [], []
        for p in points:
            if visible(p["lat"], p["lon"]):
                line.append([p["lon"], p["lat"]])
            else:
                if len(line) >= 2:
                    lines.append(line)
                line = []
        if len(line) >= 2:
            lines.append(line)
        result["geojson"] = {"type": "MultiLineString", "coordinates": lines}
    return result
