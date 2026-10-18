import copy
import csv
import hashlib
import io
import json
import os
import zipfile
from typing import Any
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fitdecode.exceptions import FitError
from flask import Blueprint, Response, jsonify, request
from lxml import etree
from sqlalchemy.exc import IntegrityError

from fittrackee import db
from fittrackee.files import get_absolute_file_path
from fittrackee.oauth2.server import require_auth
from fittrackee.visibility_levels import VisibilityLevel, can_view
from fittrackee.workouts.decorators import check_workout
from fittrackee.workouts.models import Sport, Workout
from rint_core import analyze, interval, parse_recording
from rint_core.archive import manifest, read_member

from .locking import serialize_import, serialize_recording
from .models import (
    ActivityAnalysisCache,
    ActivityRecording,
    HealthWorkout,
    ImportBatch,
)
from .preview import route_preview
from .service import (
    create_activity,
    import_photo,
    metadata_recording,
    public_analysis,
    sport_for,
)

blueprint = Blueprint("rint", __name__)


@blueprint.before_request
def request_limits() -> None:
    request.max_content_length = (
        (512 if request.endpoint == "rint.imports" else 32) * 1024 * 1024
    )


@blueprint.errorhandler(ValueError)
def invalid(error: Any) -> Any:
    return jsonify(status="fail", message=str(error)), 400


@blueprint.route("/rint/imports", methods=["GET", "POST"])
@require_auth(scopes=["workouts:write"])
def imports(user: Any) -> Any:
    if request.method == "GET":
        return jsonify(
            data=[
                b.serialize()
                for b in ImportBatch.query.filter_by(user_id=user.id)
                .order_by(ImportBatch.created_at.desc())
                .limit(20)
            ]
        )
    upload = request.files.get("file")
    if (
        not upload
        or not upload.filename
        or not upload.filename.lower().endswith(".zip")
    ):
        raise ValueError("Choose a Strava account export ZIP.")
    batch_id = str(uuid4())
    relative = f"rint_imports/{user.id}/{batch_id}.zip"
    absolute = get_absolute_file_path(relative)
    os.makedirs(os.path.dirname(absolute), exist_ok=True)
    try:
        size = 0
        with open(absolute, "wb") as target:
            while chunk := upload.stream.read(1024 * 1024):
                size += len(chunk)
                if size > 512 * 1024 * 1024:
                    raise ValueError(
                        (
                            "This ZIP exceeds 512 MB. Split very "
                            "large archives before uploading."
                        )
                    )
                target.write(chunk)
        items = manifest(absolute)
        for item in items:
            if (
                item["digest"]
                and ActivityRecording.query.filter_by(
                    user_id=user.id, digest=item["digest"]
                ).first()
            ):
                item["status"] = "duplicate"
        batch = ImportBatch(
            id=batch_id, user_id=user.id, archive_path=relative, items=items
        )
        db.session.add(batch)
        db.session.commit()
        return jsonify(data=batch.serialize()), 201
    except (ValueError, zipfile.BadZipFile, UnicodeError) as exc:
        db.session.rollback()
        if os.path.exists(absolute):
            os.remove(absolute)
        raise ValueError(f"Unable to inspect this export: {exc}") from exc


@blueprint.route("/rint/imports/<batch_id>", methods=["GET", "POST", "DELETE"])
@require_auth(scopes=["workouts:write"])
@serialize_import
def import_batch(user: Any, batch_id: Any) -> Any:
    batch = (
        ImportBatch.query.filter_by(id=batch_id, user_id=user.id)
        .with_for_update()
        .first()
    )
    if not batch:
        return jsonify(message="Import not found."), 404
    if request.method == "GET":
        return jsonify(data=batch.serialize())
    if request.method == "DELETE":
        absolute = get_absolute_file_path(batch.archive_path)
        db.session.delete(batch)
        db.session.commit()
        if os.path.exists(absolute):
            os.remove(absolute)
        return "", 204
    options = request.get_json(silent=True) or {}
    visibility = VisibilityLevel(options.get("visibility", batch.visibility))
    batch.visibility = visibility.value
    items = copy.deepcopy(batch.items)
    if options.get("retry_errors"):
        for item in items:
            if item["status"] == "error":
                item.update(status="pending", error=None)
    with zipfile.ZipFile(
        get_absolute_file_path(batch.archive_path)
    ) as archive:
        # Short requests, persisted after every activity. A browser can
        # reconnect and continue.
        selected = [i["index"] for i in items if i["status"] == "pending"][:5]
        for index in selected:
            item = items[index]
            try:
                mapping = options.get("sport_mappings", {}).get(
                    item["sport"]
                ) or item.get("mapped_sport_id")
                if mapping:
                    item["mapped_sport_id"] = int(mapping)
                sport = (
                    db.session.get(Sport, int(mapping))
                    if mapping
                    else sport_for(item["sport"])
                )
                if not sport:
                    raise ValueError("Select an available sport.")
                if item["filename"]:
                    content = read_member(archive, item["filename"])
                    extension = (
                        item["filename"]
                        .lower()
                        .removesuffix(".gz")
                        .rsplit(".", 1)[-1]
                    )
                    recording = parse_recording(content, extension)
                else:
                    recording = metadata_recording(item)
                    content, extension = (
                        json.dumps(item, sort_keys=True).encode(),
                        "json",
                    )
                workout, duplicate = create_activity(
                    user,
                    recording,
                    source_id="strava:"
                    + (
                        item["source_id"]
                        or item["digest"]
                        or f"{batch.id}:{index}"
                    ),
                    original=content,
                    extension=extension,
                    title=item["title"],
                    description=item["description"],
                    sport=sport,
                    metadata=item,
                )
                if not duplicate:
                    workout.workout_visibility = (
                        workout.analysis_visibility
                    ) = workout.media_visibility = visibility
                item.update(
                    status="duplicate" if duplicate else "imported",
                    workout_id=workout.short_id,
                    error=None,
                )
                batch.items = copy.deepcopy(items)
                db.session.commit()
                if not duplicate:
                    for photo in item["photos"][:20]:
                        try:
                            import_photo(
                                user,
                                workout,
                                read_member(archive, photo),
                                photo,
                            )
                        except Exception:
                            db.session.rollback()
                            item.setdefault("warnings", []).append(
                                f"Photo {photo} could not be imported. "
                                "It remains in your original ZIP."
                            )
                    batch.items = copy.deepcopy(items)
                    db.session.commit()
            except Exception as exc:
                db.session.rollback()
                # Human-readable format errors; do not disclose server/database
                # internals.
                item.update(
                    status="error",
                    error=str(exc)
                    if isinstance(exc, ValueError)
                    else (
                        "The activity could not be saved. Retry; if it "
                        "fails again, review the original recording."
                    ),
                )
                batch.items = copy.deepcopy(items)
                db.session.commit()
    return jsonify(data=batch.serialize())


@blueprint.route("/rint/recordings", methods=["POST"])
@require_auth(scopes=["workouts:write"])
@serialize_recording
def upload_recording(user: Any) -> Any:
    payload = request.get_json() or {}
    identifier = str(UUID(str(payload.get("id", ""))))
    recording = payload.get("recording", {})
    content = json.dumps(
        recording, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    if len(content) > 32 * 1024 * 1024:
        raise ValueError("A recording exceeds 32 MB.")
    if "health_origin" in payload:
        from .health import upload_health

        return upload_health(user, payload, recording, content)
    source_id = "apple:" + identifier
    existing = ActivityRecording.query.filter_by(
        user_id=user.id, source_id=source_id
    ).first()
    if existing:
        if existing.digest != hashlib.sha256(content).hexdigest():
            return jsonify(
                message="This recording ID already belongs to different data."
            ), 409
        return jsonify(
            data={"workout_id": existing.workout.short_id, "duplicate": True}
        )
    health_native = HealthWorkout.query.filter(
        HealthWorkout.user_id == user.id,
        HealthWorkout.origin["rint_recording_id"].as_string() == identifier,
    ).first()
    if health_native:
        # Health can finish syncing before the Watch delivers the original.
        # Promote the original without making a second workout.
        from .health import enrich

        primary = health_native.workout.rint_recording
        if primary:
            primary.source_id = source_id
            primary.digest = hashlib.sha256(content).hexdigest()
            primary.data = recording
            primary.analysis = analyze(recording)
            if health_native.workout.original_file:
                with open(
                    get_absolute_file_path(
                        health_native.workout.original_file
                    ),
                    "wb",
                ) as stream:
                    stream.write(content)
            enrich(health_native.workout)
            db.session.commit()
            return jsonify(
                data={
                    "workout_id": health_native.workout.short_id,
                    "duplicate": True,
                }
            )
    sport = db.session.get(Sport, int(payload.get("sport_id", 0)))
    if not sport:
        raise ValueError("Choose a sport available on your server.")
    try:
        workout, duplicate = create_activity(
            user,
            recording,
            source_id=source_id,
            original=content,
            extension="json",
            title=str(payload.get("title", "Apple workout")),
            sport=sport,
        )
        db.session.commit()
        return jsonify(
            data={"workout_id": workout.short_id, "duplicate": duplicate}
        ), 201
    except IntegrityError:
        db.session.rollback()
        existing = ActivityRecording.query.filter_by(
            user_id=user.id, source_id=source_id
        ).first()
        if existing and existing.digest == hashlib.sha256(content).hexdigest():
            return jsonify(
                data={
                    "workout_id": existing.workout.short_id,
                    "duplicate": True,
                }
            )
        return jsonify(
            message="Another upload saved conflicting recording data."
        ), 409


def analysis_for(workout: Workout) -> dict[str, Any]:
    if workout.rint_recording:
        from .health import MERGE_VERSION, enrich

        if (
            workout.rint_recording.analysis.get("health_merge_version", 0)
            < MERGE_VERSION
            and HealthWorkout.query.filter_by(workout_id=workout.id).first()
        ):
            # Repair older derived data from retained sources without requiring
            # another upload or changes to original files/sharing settings.
            enrich(workout)
            db.session.commit()
        return workout.rint_recording.analysis
    if workout.rint_analysis_cache:
        return workout.rint_analysis_cache.analysis
    if not workout.original_file:
        raise ValueError(
            "This activity has no underlying recording for detailed analysis."
        )
    extension = workout.original_file.rsplit(".", 1)[-1]
    with open(get_absolute_file_path(workout.original_file), "rb") as stream:
        return analyze(parse_recording(stream.read(), extension))


@blueprint.route("/rint/activities/<workout_short_id>/analysis")
@require_auth(scopes=["workouts:read"], optional_auth_user=True)
@check_workout(only_owner=False)
def activity_analysis(user: Any, workout: Any, **kwargs: Any) -> Any:
    if not can_view(workout, "calculated_analysis_visibility", user):
        return jsonify(message="Analysis is private."), 404
    return jsonify(data=public_analysis(workout, user, analysis_for(workout)))


@blueprint.route("/rint/activities/<workout_short_id>/preview")
@require_auth(scopes=["workouts:read"], optional_auth_user=True)
@check_workout(only_owner=False)
def activity_preview(user: Any, workout: Any, **kwargs: Any) -> Any:
    if not can_view(workout, "calculated_analysis_visibility", user):
        return jsonify(message="Analysis is private."), 404
    visible = public_analysis(workout, user, analysis_for(workout))
    return jsonify(
        data={"points": route_preview(visible["recording"]["points"])}
    )


@blueprint.route(
    "/rint/activities/<workout_short_id>/interval", methods=["POST"]
)
@require_auth(scopes=["workouts:read"], optional_auth_user=True)
@check_workout(only_owner=False)
def activity_interval(user: Any, workout: Any, **kwargs: Any) -> Any:
    if not can_view(workout, "calculated_analysis_visibility", user):
        return jsonify(message="Analysis is private."), 404
    data = public_analysis(workout, user, analysis_for(workout))
    options = request.get_json() or {}
    return jsonify(
        data=interval(
            data["recording"]["points"],
            options.get("start"),
            options.get("end"),
        )
    )


@blueprint.route("/rint/activities/<workout_short_id>/export")
@require_auth(scopes=["workouts:read"])
@check_workout()
def export_activity(user: Any, workout: Any, **kwargs: Any) -> Any:
    analysis = analysis_for(workout)
    if request.args.get("format") == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "t",
                "d",
                "active",
                "lat",
                "lon",
                "heart_rate",
                "cadence",
                "power",
                "elevation",
            ],
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(analysis["recording"]["points"])
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{workout.short_id}.csv"'
                )
            },
        )
    return Response(
        json.dumps(
            {
                "analysis": analysis,
                "original_recording": workout.rint_recording.data
                if workout.rint_recording
                else (
                    workout.rint_analysis_cache.data
                    if workout.rint_analysis_cache
                    else None
                ),
                "health_sources": [
                    source.serialize()
                    for source in HealthWorkout.query.filter_by(
                        workout_id=workout.id
                    ).all()
                ],
            }
        ),
        mimetype="application/json",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{workout.short_id}.json"'
            )
        },
    )


def cache_legacy_analysis(workout: Workout) -> ActivityAnalysisCache:
    if workout.rint_analysis_cache:
        return workout.rint_analysis_cache
    if not workout.original_file:
        raise ValueError("This activity has no original recording to analyze.")
    extension = workout.original_file.rsplit(".", 1)[-1]
    with open(get_absolute_file_path(workout.original_file), "rb") as stream:
        data = parse_recording(stream.read(), extension)
    row = ActivityAnalysisCache(
        workout_id=workout.id,
        user_id=workout.user_id,
        data=data,
        analysis=analyze(data),
    )
    db.session.add(row)
    db.session.flush()
    return row


@blueprint.route("/rint/bests/refresh", methods=["POST"])
@require_auth(scopes=["workouts:write"])
@serialize_recording
def refresh_earlier_analyses(user: Any) -> Any:
    cursor = max(0, int((request.get_json() or {}).get("cursor", 0)))
    rows = (
        Workout.query.filter(
            Workout.user_id == user.id,
            Workout.id > cursor,
            Workout.original_file.isnot(None),
            Workout.id.notin_(db.session.query(ActivityRecording.workout_id)),
            Workout.id.notin_(db.session.query(ActivityAnalysisCache.workout_id)),
        )
        .order_by(Workout.id)
        .limit(6)
        .all()
    )
    failures = []
    for workout in rows[:5]:
        cursor = workout.id
        try:
            with db.session.begin_nested():
                cache_legacy_analysis(workout)
            db.session.commit()
        except (ValueError, OSError, etree.XMLSyntaxError, FitError) as exc:
            db.session.rollback()
            failures.append(
                {
                    "workout_id": workout.short_id,
                    "title": workout.title,
                    "message": str(exc),
                }
            )
    return jsonify(
        data={
            "cursor": cursor,
            "processed": len(rows[:5]),
            "has_more": len(rows) > 5,
            "errors": failures,
        }
    )


def sharing_settings(workout: Workout) -> dict[str, Any]:
    return {
        "visibility": workout.workout_visibility.value,
        "map_visibility": workout.map_visibility.value,
        "privacy_radius_m": (
            workout.rint_recording.privacy_radius_m
            if workout.rint_recording
            else (
                workout.rint_analysis_cache.privacy_radius_m
                if workout.rint_analysis_cache
                else 200
            )
        ),
        "url": f"/workouts/{workout.short_id}",
    }


@blueprint.route("/rint/activities/<workout_short_id>/sharing")
@require_auth(scopes=["workouts:write"])
@check_workout()
def get_sharing(user: Any, workout: Any, **kwargs: Any) -> Any:
    return jsonify(data=sharing_settings(workout))


@blueprint.route(
    "/rint/activities/<workout_short_id>/sharing", methods=["POST"]
)
@require_auth(scopes=["workouts:write"])
@check_workout()
def share_activity(user: Any, workout: Any, **kwargs: Any) -> Any:
    options = request.get_json() or {}
    # Validate the whole patch before mutating. Omitted settings retain their
    # saved value, including independently chosen map and sensor visibility.
    visibility = VisibilityLevel(
        options.get("visibility", workout.workout_visibility.value)
    )
    map_visibility = VisibilityLevel(
        options.get("map_visibility", workout.map_visibility.value)
    )
    current = sharing_settings(workout)
    radius = int(options.get("privacy_radius_m", current["privacy_radius_m"]))
    if not 200 <= radius <= 10000:
        raise ValueError("Route protection must be between 200 m and 10 km.")
    if "visibility" in options:
        workout.workout_visibility = visibility
        workout.analysis_visibility = visibility
        workout.media_visibility = visibility
    workout.map_visibility = map_visibility
    if workout.rint_recording:
        workout.rint_recording.privacy_radius_m = radius
    elif workout.original_file:
        cache_legacy_analysis(workout).privacy_radius_m = radius
    db.session.commit()
    return jsonify(data=sharing_settings(workout))


@blueprint.route("/rint/bests")
@require_auth(scopes=["workouts:read"])
@serialize_recording
def personal_bests(user: Any) -> Any:
    from .health import MERGE_VERSION

    # Repair old Health derivations without keeping a streaming cursor open
    # across commits. Current recordings need no stream download or parsing.
    cursor = 0
    while True:
        stale = (
            Workout.query.join(ActivityRecording)
            .filter(
                Workout.user_id == user.id,
                Workout.id > cursor,
                db.func.coalesce(
                    ActivityRecording.analysis["health_merge_version"].as_integer(), 0
                ) < MERGE_VERSION,
                Workout.id.in_(db.session.query(HealthWorkout.workout_id)),
            )
            .order_by(Workout.id).limit(5).all()
        )
        if not stale:
            break
        cursor = stale[-1].id
        for workout in stale:
            analysis_for(workout)
    results: dict[tuple[int, float], dict[str, Any]] = {}
    winners: dict[tuple[int, float], Any] = {}
    for model in (ActivityRecording, ActivityAnalysisCache):
        query = db.session.query(Workout, model.analysis["best_efforts"]).join(
            model, model.workout_id == Workout.id
        ).filter(Workout.user_id == user.id)
        if request.args.get("sport_id"):
            query = query.filter(Workout.sport_id == int(request.args["sport_id"]))
        # Select just the small effort array, not the full JSON sensor streams.
        for workout, efforts in query.order_by(Workout.id).yield_per(100):
            for effort in efforts or []:
                key = (workout.sport_id, effort["distance_m"])
                rank = (effort["elapsed_s"], workout.workout_date, workout.id)
                if key not in winners or rank < winners[key]:
                    winners[key] = rank
                    results[key] = {
                        **effort,
                        "sport_id": workout.sport_id,
                        "workout_id": workout.short_id,
                        "date": workout.workout_date.isoformat(),
                        "title": workout.title or workout.sport.label,
                    }
    pending = Workout.query.filter(
        Workout.user_id == user.id,
        Workout.original_file.isnot(None),
        Workout.id.notin_(db.session.query(ActivityRecording.workout_id)),
        Workout.id.notin_(db.session.query(ActivityAnalysisCache.workout_id)),
    ).count()
    return jsonify(
        data=sorted(results.values(), key=lambda row: (
            row["sport_id"], row["distance_m"]
        )),
        coverage={"pending": pending},
    )


@blueprint.route("/rint/history")
@require_auth(scopes=["workouts:read"])
def training_history(user: Any) -> Any:
    # Aggregate the full account in PostgreSQL, without a workout cap.
    period = request.args.get("period", "month")
    if period not in ("month", "week"):
        raise ValueError("Choose weekly or monthly history.")
    timezone = request.args.get("timezone", user.timezone or "UTC")
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError("Choose a valid time zone for your history.") from exc
    # TZDateTime stores a UTC timestamp without a timezone in PostgreSQL.
    # Convert UTC -> the requested local clock before finding Monday midnight.
    local_date = db.func.timezone(
        timezone, db.func.timezone("UTC", Workout.workout_date)
    )
    month = db.func.date_trunc(period, local_date)
    query = db.session.query(
        month,
        Workout.sport_id,
        db.func.count(Workout.id),
        db.func.sum(Workout.distance),
        db.func.sum(db.func.extract("epoch", Workout.duration)),
    ).filter(Workout.user_id == user.id)
    if request.args.get("sport_id"):
        query = query.filter(Workout.sport_id == int(request.args["sport_id"]))
    return jsonify(
        data=[
            {
                ("week" if period == "week" else "month"): row[0].date().isoformat(),
                "sport_id": row[1],
                "activities": row[2],
                "distance_m": float(row[3] or 0) * 1000,
                "elapsed_s": float(row[4] or 0),
            }
            for row in query.group_by(month, Workout.sport_id).order_by(month)
        ]
    )
