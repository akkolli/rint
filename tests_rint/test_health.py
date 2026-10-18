"""Health history uploads use the isolated PostGIS integration fixture."""

import copy
from uuid import uuid4

from tests_rint.test_api import payload, pytestmark  # noqa: F401

pytest_plugins = ["tests_rint.test_api"]


def health_payload(sport):
    data = payload(sport)
    data["health_origin"] = {
        "workout_id": str(uuid4()),
        "source_bundle": "com.apple.health",
        "source_name": "Apple Watch",
        "product_type": "Watch7,1",
        "activity_type": 37,
        "indoor": False,
        "reported_duration_s": 600,
        "active_energy_kcal": 210,
        "warnings": [],
    }
    return data


def post(client, headers, data):
    return client.post("/api/rint/recordings", json=data, headers=headers)


def test_health_retries_late_sensor_data_free_charts_exports_and_privacy(
    context,
):
    client, headers, other, sport, owner = context
    from fittrackee import db
    from fittrackee.rint.models import HealthWorkout
    from fittrackee.users.export_data import UserDataExporter
    from fittrackee.workouts.models import Workout

    data = health_payload(sport)
    for p in data["recording"]["points"]:
        p.pop("lat")
        p.pop("lon")
        p.pop("heart_rate")
    created = post(client, headers, data)
    assert created.status_code == 201, created.json
    activity = created.json["data"]["workout_id"]
    for _ in range(3):
        data["id"] = str(uuid4())
        repeated = post(client, headers, data)
        assert repeated.status_code == 200, repeated.json
        assert repeated.json["data"]["workout_id"] == activity
    path = f"/api/rint/activities/{activity}"
    workout = Workout.query.one()
    workout.title = "My edited title"
    db.session.commit()
    client.post(
        path + "/sharing",
        json={"visibility": "public", "map_visibility": "public"},
        headers=headers,
    )
    later = copy.deepcopy(data)
    later["id"] = str(uuid4())
    later["recording"]["points"] = payload(sport)["recording"]["points"]
    later["recording"]["points"][30]["power"] = 250
    updated = post(client, headers, later)
    assert updated.status_code == 200, updated.json
    assert updated.json["data"]["updated"]
    assert Workout.query.count() == HealthWorkout.query.count() == 1
    assert workout.title == "My edited title"
    assert workout.workout_visibility.value == "public"
    analysis = client.get(path + "/analysis", headers=headers).json["data"]
    assert len(analysis["splits_km"]) == 3
    assert analysis["summary"]["active_energy_kcal"] == 210
    assert any(p.get("power") == 250 for p in analysis["recording"]["points"])
    assert (
        client.get(
            f"/api/workouts/{activity}/geojson", headers=headers
        ).status_code
        == 200
    )
    public = client.get(path + "/analysis", headers=other).json["data"]
    assert "lat" not in public["recording"]["points"][0]
    assert not any("heart_rate" in p for p in public["recording"]["points"])
    exported = client.get(path + "/export", headers=headers).json
    assert (
        exported["health_sources"][0]["origin"]["source_name"] == "Apple Watch"
    )
    assert (
        "heart_rate"
        in client.get(path + "/export?format=csv", headers=headers).text
    )
    assert client.get(path + "/export", headers=other).status_code == 403
    assert UserDataExporter(owner).get_user_workouts_data()[0][
        "health_sources"
    ]
    # Limited later permissions must not erase previously retained sensors or routes.
    assert post(client, headers, data).status_code == 200
    preserved = client.get(path + "/analysis", headers=headers).json["data"]
    assert any("lat" in p for p in preserved["recording"]["points"])
    assert any(p.get("power") == 250 for p in preserved["recording"]["points"])


def test_possible_strava_duplicate_requires_review_and_retains_both_sources(
    context,
):
    client, headers, _, sport, owner = context
    from fittrackee import db
    from fittrackee.rint.models import ActivityRecording
    from fittrackee.workouts.models import Workout

    original = payload(sport)
    for p in original["recording"]["points"]:
        p.pop("heart_rate")
    activity = post(client, headers, original).json["data"]["workout_id"]
    primary = ActivityRecording.query.one()
    primary.source_id = "strava:123456"
    db.session.commit()
    original_bytes = open(
        client.application.config["UPLOAD_FOLDER"]
        + "/"
        + primary.workout.original_file,
        "rb",
    ).read()
    data = health_payload(sport)
    response = post(client, headers, data)
    assert response.status_code == 409, response.json
    assert response.json["code"] == "possible_duplicate"
    assert response.json["candidates"][0]["id"] == activity
    assert Workout.query.filter_by(user_id=owner.id).count() == 1
    data["duplicate_workout_id"] = activity
    linked = post(client, headers, data)
    assert linked.status_code == 200, linked.json
    assert linked.json["data"]["workout_id"] == activity
    assert Workout.query.count() == 1
    exported = client.get(
        f"/api/rint/activities/{activity}/export", headers=headers
    ).json
    assert any(
        "heart_rate" in p for p in exported["analysis"]["recording"]["points"]
    )
    assert not any(
        "heart_rate" in p for p in exported["original_recording"]["points"]
    )
    assert exported["health_sources"][0]["recording"] == data["recording"]
    assert (
        open(
            client.application.config["UPLOAD_FOLDER"]
            + "/"
            + primary.workout.original_file,
            "rb",
        ).read()
        == original_bytes
    )


def test_duplicate_review_can_keep_distinct_sessions_and_rejects_foreign_link(
    context,
):
    client, headers, other, sport, _ = context
    from fittrackee.workouts.models import Workout

    first = post(client, headers, payload(sport)).json["data"]["workout_id"]
    foreign = post(client, other, payload(sport)).json["data"]["workout_id"]
    data = health_payload(sport)
    data["duplicate_workout_id"] = foreign
    assert post(client, headers, data).status_code == 400
    data.pop("duplicate_workout_id")
    data["keep_separate"] = True
    separate = post(client, headers, data)
    assert separate.status_code == 201, separate.json
    assert separate.json["data"]["workout_id"] != first
    assert Workout.query.count() == 3


def test_health_sync_identifier_and_rint_watch_upload_order(context):
    client, headers, _, sport, _ = context
    from fittrackee.workouts.models import Workout

    original = payload(sport)
    health = health_payload(sport)
    health["health_origin"].update(
        rint_recording_id=original["id"],
        sync_identifier="watch-session",
        sync_version=1,
    )
    created = post(client, headers, health)
    assert created.status_code == 201, created.json
    activity = created.json["data"]["workout_id"]
    # The Health upload can beat delivery of the original Watch recording.
    native = post(client, headers, original)
    assert native.status_code == 200, native.json
    assert native.json["data"]["workout_id"] == activity
    repeated = copy.deepcopy(health)
    repeated["id"] = str(uuid4())
    repeated["health_origin"]["workout_id"] = str(uuid4())
    repeated["health_origin"]["sync_version"] = 2
    repeated["recording"]["points"][5]["power"] = 260
    assert post(client, headers, repeated).status_code == 200
    assert Workout.query.count() == 1
    # Ordinary native IDs still reject a conflicting re-upload.
    original["recording"]["points"][1]["d"] = 52
    assert post(client, headers, original).status_code == 409


def test_health_identity_is_account_scoped_and_native_first_deduplicates(
    context,
):
    client, headers, other, sport, _ = context
    from fittrackee.workouts.models import Workout

    native = payload(sport)
    first = post(client, headers, native).json["data"]["workout_id"]
    health = health_payload(sport)
    health["health_origin"]["rint_recording_id"] = native["id"]
    assert post(client, headers, health).json["data"]["workout_id"] == first
    assert post(client, other, health).status_code == 201
    assert Workout.query.count() == 2


def test_summary_total_does_not_invent_bests_and_late_distance_unlocks_splits(
    context,
):
    client, headers, _, sport, _ = context
    data = health_payload(sport)
    data["recording"] = {
        "started_at": data["recording"]["started_at"],
        "summary_only": True,
        "points": [
            {"t": 0, "d": 0, "heart_rate": 120},
            {"t": 600, "d": 3000, "heart_rate": 150},
        ],
    }
    activity = post(client, headers, data).json["data"]["workout_id"]
    path = f"/api/rint/activities/{activity}/analysis"
    summary = client.get(path, headers=headers).json["data"]
    assert not summary["best_efforts"] and not summary["splits_km"]
    later = copy.deepcopy(data)
    later["recording"] = payload(sport)["recording"]
    assert post(client, headers, later).status_code == 200
    complete = client.get(path, headers=headers).json["data"]
    assert len(complete["splits_km"]) == 3
    assert complete["best_efforts"]


def test_health_sensor_samples_at_same_time_preserve_distance_and_revisions(
    context,
):
    client, headers, _, sport, _ = context
    from fittrackee.workouts.models import Workout

    data = health_payload(sport)
    separate = []
    for point in data["recording"]["points"]:
        separate.extend(
            [
                {"t": point["t"], "d": point["d"]},
                {"t": point["t"], "heart_rate": point["heart_rate"]},
                {"t": point["t"], "lat": point["lat"], "lon": point["lon"]},
            ]
        )
    data["recording"]["points"] = separate
    created = post(client, headers, data)
    assert created.status_code == 201
    activity = created.json["data"]["workout_id"]
    path = f"/api/rint/activities/{activity}/analysis"
    initial = client.get(path, headers=headers).json["data"]
    assert initial["summary"]["distance_m"] == 3000
    assert initial["summary"]["averages"]["heart_rate"] == 140

    corrected = copy.deepcopy(data)
    corrected["id"] = str(uuid4())
    for point in corrected["recording"]["points"]:
        if "d" in point:
            point["d"] *= 1.6
    assert post(client, headers, corrected).json["data"]["workout_id"] == activity
    updated = client.get(path, headers=headers).json["data"]
    assert updated["summary"]["distance_m"] == 4800
    assert len(updated["splits_km"]) == 5
    assert updated["summary"]["averages"]["heart_rate"] == 140
    assert Workout.query.count() == 1

    limited = copy.deepcopy(corrected)
    limited["id"] = str(uuid4())
    for point in limited["recording"]["points"]:
        point.pop("d", None)
        point.pop("heart_rate", None)
    assert post(client, headers, limited).status_code == 200
    retained = client.get(path, headers=headers).json["data"]
    assert retained["summary"]["distance_m"] == 4800
    assert retained["summary"]["averages"]["heart_rate"] == 140

    # Reading an activity created before this repair upgrades its derived cache.
    from fittrackee import db

    workout = Workout.query.one()
    cached = copy.deepcopy(workout.rint_recording.analysis)
    cached.pop("health_merge_version")
    cached["summary"]["distance_m"] = 4100
    workout.rint_recording.analysis = cached
    db.session.commit()
    repaired = client.get(path, headers=headers).json["data"]
    assert repaired["summary"]["distance_m"] == 4800
    assert repaired["health_merge_version"] == 2
    assert float(workout.distance) == 4.8


def test_invalid_health_source_is_rejected_without_creating_activity(context):
    client, headers, _, sport, _ = context
    from fittrackee.workouts.models import Workout

    for key, value in (
        ("workout_id", "invalid"),
        ("source_bundle", ""),
        ("active_energy_kcal", -1),
        ("warnings", [100]),
    ):
        data = health_payload(sport)
        data["health_origin"][key] = value
        assert post(client, headers, data).status_code == 400
    assert Workout.query.count() == 0
