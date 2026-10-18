"""Health uploads, source retention and explicit duplicate review."""

import copy
import hashlib
import json
import math
from bisect import bisect_right
from datetime import timedelta
from typing import Any
from uuid import UUID

from flask import jsonify

from fittrackee import db
from fittrackee.files import get_absolute_file_path
from fittrackee.workouts.models import Sport, Workout
from rint_core import analyze, parse_recording
from rint_core.parsers import date

from .models import ActivityRecording, HealthWorkout
from .service import create_activity, refresh_activity

MERGE_VERSION = 2


def validated_origin(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("Health source information is required.")
    origin: dict[str, Any] = {
        "workout_id": str(UUID(str(raw.get("workout_id", ""))))
    }
    for field in (
        "source_bundle",
        "source_name",
        "product_type",
        "sync_identifier",
        "external_uuid",
        "rint_recording_id",
    ):
        value = raw.get(field)
        if value is not None:
            if not isinstance(value, str) or len(value) > 1024:
                raise ValueError(f"Invalid Health {field}.")
            origin[field] = value
    if not origin.get("source_bundle"):
        raise ValueError("Health source bundle is required.")
    if origin.get("rint_recording_id"):
        origin["rint_recording_id"] = str(UUID(origin["rint_recording_id"]))
    for field in (
        "reported_duration_s",
        "reported_distance_m",
        "active_energy_kcal",
    ):
        value = raw.get(field)
        if value is not None:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
            ):
                raise ValueError(f"Invalid Health {field}.")
            origin[field] = value
    for field in ("sync_version", "activity_type"):
        if field in raw and raw[field] is not None:
            value = raw[field]
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < 0
                or value > 2**63 - 1
            ):
                raise ValueError(f"Invalid Health {field}.")
            origin[field] = value
    origin["indoor"] = raw.get("indoor") is True
    warnings = raw.get("warnings", [])
    if (
        not isinstance(warnings, list)
        or len(warnings) > 30
        or any(not isinstance(w, str) or len(w) > 1000 for w in warnings)
    ):
        raise ValueError("Invalid Health warnings.")
    origin["warnings"] = warnings
    return origin


def combine(
    base: dict[str, Any], supplement: dict[str, Any], *, health_primary: bool
) -> dict[str, Any]:
    """Keep distance/route authority; add independently timed streams."""
    result = copy.deepcopy(base)
    supplement = copy.deepcopy(supplement)
    # Health streams arrive as separate samples at the same timestamp. A dict
    # comprehension would silently keep only the last sensor/route sample.
    for recording in (result, supplement):
        timed: dict[float, dict[str, Any]] = {}
        for point in recording["points"]:
            timed.setdefault(point["t"], {}).update(point)
        recording["points"] = sorted(timed.values(), key=lambda p: p["t"])
    points = result["points"]
    shift = (
        date(supplement["started_at"]) - date(base["started_at"])
    ).total_seconds()
    end = max(p["t"] for p in points)
    fields = ["heart_rate", "cadence", "power", "elevation"]
    coverage = {k: sorted(p["t"] for p in points if k in p) for k in fields}
    # A newer equally sampled Health revision can correct distance values too.
    # Limited rereads with fewer anchors must not erase richer distance data.
    source_distances = sum("d" in p for p in supplement["points"])
    if health_primary and source_distances > 0 and source_distances >= sum(
        "d" in p for p in points
    ):
        for p in points:
            p.pop("d", None)
        fields.append("d")
        result["summary_only"] = supplement.get("summary_only", False)
    elif (
        result.get("summary_only")
        and sum("lat" in p for p in supplement["points"]) >= 2
    ):
        for p in points:
            p.pop("d", None)
        result["summary_only"] = False
    if health_primary or not any("lat" in p for p in points):
        fields.extend(("lat", "lon"))
    # New Health pause events supersede the incomplete initial timer timeline.
    supplement_timer = health_primary and any(
        p.get("active") is False for p in supplement["points"]
    )
    timeline = supplement["points"] if supplement_timer else points
    timeline = sorted(timeline, key=lambda p: p["t"])
    times = [p["t"] for p in timeline]
    merged = {p["t"]: p for p in points}
    for source in supplement["points"]:
        t = source["t"] + shift
        if not 0 <= t <= end:
            continue
        extra = {}
        for key in fields:
            if key not in source:
                continue
            measured = coverage.get(key, [])
            j = bisect_right(measured, t)
            if (
                not health_primary
                and measured
                and (
                    (j > 0 and measured[j - 1] == t)
                    or (
                        0 < j < len(measured)
                        and measured[j] - measured[j - 1] <= 60
                    )
                )
            ):
                continue
            extra[key] = source[key]
        if not extra:
            continue
        i = max(
            0, bisect_right(times, t - shift if supplement_timer else t) - 1
        )
        p = merged.setdefault(
            t, {"t": t, "active": timeline[i].get("active", True)}
        )
        for key, value in extra.items():
            if health_primary:
                p[key] = value
            else:
                p.setdefault(key, value)
    if health_primary and any(
        p.get("active") is False for p in supplement["points"]
    ):
        event_points = sorted(supplement["points"], key=lambda p: p["t"])
        event_times = [p["t"] + shift for p in event_points]
        for source in event_points:
            t = source["t"] + shift
            if 0 <= t <= end:
                merged.setdefault(t, {"t": t})
        for t, p in merged.items():
            i = max(0, bisect_right(event_times, t) - 1)
            p["active"] = event_points[i].get("active", True)
    result["points"] = sorted(merged.values(), key=lambda p: p["t"])
    if not result.get("laps") and supplement.get("laps"):
        result["laps"] = [
            {**lap, "start": lap["start"] + shift, "end": lap["end"] + shift}
            for lap in supplement["laps"]
        ]
    return result


def enrich(workout: Workout) -> None:
    primary = workout.rint_recording
    if not primary:
        if not workout.original_file:
            raise ValueError(
                "This activity has no recording to link. Keep it separate."
            )
        with open(
            get_absolute_file_path(workout.original_file), "rb"
        ) as stream:
            original = stream.read()
        raw = parse_recording(
            original, workout.original_file.rsplit(".", 1)[-1]
        )
        primary = ActivityRecording(
            workout_id=workout.id,
            user_id=workout.user_id,
            source_id="existing:" + str(workout.uuid),
            digest=hashlib.sha256(original).hexdigest(),
            data=raw,
            analysis=analyze(raw),
        )
        db.session.add(primary)
        db.session.flush()
    raw = copy.deepcopy(primary.data)
    metadata = primary.data.get("source_metadata")
    health_primary = primary.source_id.startswith("health:") or (
        isinstance(metadata, dict)
        and metadata.get("health_origin") is not None
    )
    sources = (
        HealthWorkout.query.filter_by(workout_id=workout.id)
        .order_by(HealthWorkout.id)
        .all()
    )
    newest: dict[str, int] = {}
    for source in sources:
        if source.sync_key:
            newest[source.sync_key] = max(
                newest.get(source.sync_key, 0),
                source.origin.get("sync_version", 0),
            )
    active_sources = []
    for source in sources:
        if (
            source.sync_key
            and source.origin.get("sync_version", 0) < newest[source.sync_key]
        ):
            continue
        active_sources.append(source)
        raw = combine(raw, source.data, health_primary=health_primary)
    analysis = analyze(raw)
    analysis["health_merge_version"] = MERGE_VERSION
    for source in active_sources:
        analysis["warnings"] = list(
            dict.fromkeys(
                [*analysis["warnings"], *source.origin.get("warnings", [])]
            )
        )
        # Reported totals remain separate from measured sensor streams.
        if "active_energy_kcal" in source.origin:
            analysis["summary"]["active_energy_kcal"] = source.origin[
                "active_energy_kcal"
            ]
        if health_primary and "reported_duration_s" in source.origin:
            analysis["summary"]["health_reported_active_s"] = source.origin[
                "reported_duration_s"
            ]
    primary.analysis = analysis
    refresh_activity(workout, analysis)


def candidates_for(user: Any, analysis: dict[str, Any]) -> list[Workout]:
    started = date(analysis["recording"]["started_at"])
    summary = analysis["summary"]
    candidates = (
        Workout.query.filter(
            Workout.user_id == user.id,
            Workout.workout_date >= started - timedelta(seconds=30),
            Workout.workout_date <= started + timedelta(seconds=30),
        )
        .limit(20)
        .all()
    )
    return [
        w
        for w in candidates
        if abs(w.duration.total_seconds() - summary["elapsed_s"])
        <= max(5, summary["elapsed_s"] * 0.02)
        and abs(float(w.distance or 0) * 1000 - summary["distance_m"])
        <= max(10, summary["distance_m"] * 0.02)
    ]


def upload_health(
    user: Any,
    payload: dict[str, Any],
    recording: dict[str, Any],
    content: bytes,
) -> Any:
    origin = validated_origin(payload["health_origin"])
    analysis = analyze(recording)
    sport = db.session.get(Sport, int(payload.get("sport_id", 0)))
    if not sport:
        raise ValueError("Choose a sport available on your server.")
    health_id = origin["workout_id"]
    digest = hashlib.sha256(
        content + json.dumps(origin, sort_keys=True).encode()
    ).hexdigest()
    sync_key = (
        hashlib.sha256(
            (
                origin["source_bundle"] + "|" + origin["sync_identifier"]
            ).encode()
        ).hexdigest()
        if origin.get("sync_identifier")
        else None
    )
    existing = HealthWorkout.query.filter_by(
        user_id=user.id, health_id=health_id
    ).first()
    if existing and existing.digest == digest:
        return jsonify(
            data={
                "workout_id": existing.workout.short_id,
                "duplicate": True,
                "updated": False,
            }
        )
    linked = existing or (
        HealthWorkout.query.filter_by(
            user_id=user.id, sync_key=sync_key
        ).first()
        if sync_key
        else None
    )
    latest_version = (
        max(
            (
                source.origin.get("sync_version", 0)
                for source in HealthWorkout.query.filter_by(
                    user_id=user.id, sync_key=sync_key
                ).all()
            ),
            default=0,
        )
        if sync_key
        else (existing.origin.get("sync_version", 0) if existing else 0)
    )
    workout = linked.workout if linked else None
    if not workout:
        ids = ["apple:" + health_id, "health:" + health_id]
        if origin.get("rint_recording_id"):
            ids.append("apple:" + origin["rint_recording_id"])
        primary = ActivityRecording.query.filter(
            ActivityRecording.user_id == user.id,
            ActivityRecording.source_id.in_(ids),
        ).first()
        if primary:
            workout = primary.workout
    if workout and existing:
        if (
            abs(
                (
                    date(existing.data["started_at"])
                    - date(analysis["recording"]["started_at"])
                ).total_seconds()
            )
            > 30
        ):
            raise ValueError(
                "The same Health ID cannot refer to a different workout date."
            )
    if not workout:
        candidates = candidates_for(user, analysis)
        selected = payload.get("duplicate_workout_id")
        if selected:
            workout = next(
                (w for w in candidates if w.short_id == selected), None
            )
            if not workout:
                raise ValueError(
                    "Choose one of your matching activities to link."
                )
        elif candidates and payload.get("keep_separate") is not True:
            return jsonify(
                message="Review matching activities before importing.",
                code="possible_duplicate",
                candidates=[
                    {
                        "id": w.short_id,
                        "title": w.title or "Activity",
                        "started_at": w.workout_date.isoformat(),
                    }
                    for w in candidates
                ],
            ), 409
    created = workout is None
    if created:
        # The retained Health source identifies the recording. Sessions
        # explicitly kept separate may have identical samples and timestamps.
        original = json.dumps(
            {"recording": recording, "health_origin": origin},
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
        workout, _ = create_activity(
            user,
            recording,
            source_id="health:" + health_id,
            original=original,
            extension="json",
            title=str(payload.get("title", "Apple Health workout")),
            sport=sport,
            metadata={"health_origin": origin},
        )
    if workout is None:
        raise ValueError("The Health workout could not be saved. Retry.")
    stale = origin.get("sync_version", 0) < latest_version
    if existing:
        if not stale:
            existing.data = combine(
                existing.data, recording, health_primary=True
            )
            existing.digest, existing.origin = digest, origin
            existing.sync_key = sync_key
    else:
        db.session.add(
            HealthWorkout(
                user_id=user.id,
                workout_id=workout.id,
                health_id=health_id,
                sync_key=sync_key,
                digest=digest,
                data=recording,
                origin=origin,
            )
        )
    db.session.flush()
    if not stale:
        enrich(workout)
    db.session.commit()
    return jsonify(
        data={
            "workout_id": workout.short_id,
            "duplicate": not created,
            "updated": not created and not stale,
        }
    ), 201 if created else 200
