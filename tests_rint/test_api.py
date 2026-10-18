"""Run with RINT_INTEGRATION=1 against the isolated rint_test database."""

import io
import os
import zipfile
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from PIL import Image

pytestmark = pytest.mark.skipif(
    os.getenv("RINT_INTEGRATION") != "1",
    reason="Requires isolated PostGIS test database",
)


@pytest.fixture
def context(tmp_path):
    os.environ["APP_SETTINGS"] = "fittrackee.config.TestingConfig"
    from fittrackee import create_app, db, limiter
    from fittrackee.application.models import AppConfig
    from fittrackee.users.models import User
    from fittrackee.workouts.models import Sport

    app = create_app()
    app.config["UPLOAD_FOLDER"] = str(tmp_path / "uploads")
    limiter.enabled = False
    with app.app_context():
        db.create_all()
        db.session.add(AppConfig())
        owner = User("rint_test", "rint@example.org", "test-fixture-password")
        owner.is_active = True
        owner.accepted_policy_date = datetime.now(timezone.utc)
        other = User(
            "other_test", "other@example.org", "test-fixture-password"
        )
        other.is_active = True
        other.accepted_policy_date = datetime.now(timezone.utc)
        sport = Sport("Running")
        db.session.add_all([owner, other, sport])
        db.session.commit()
        headers = {
            "Authorization": "Bearer " + owner.encode_auth_token(owner.id)
        }
        other_headers = {
            "Authorization": "Bearer " + other.encode_auth_token(other.id)
        }
        yield app.test_client(), headers, other_headers, sport.id, owner
        db.session.remove()
        db.drop_all()


def payload(sport):
    return {
        "id": str(uuid4()),
        "sport_id": sport,
        "title": "Evening run",
        "recording": {
            "started_at": "2026-10-10T20:00:00Z",
            "points": [
                {
                    "t": t,
                    "d": t * 5,
                    "lat": 40,
                    "lon": -73 + t * 0.00006,
                    "heart_rate": 140,
                }
                for t in range(0, 601, 10)
            ],
        },
    }


def test_recording_idempotency_analysis_export_and_share(context):
    client, headers, other, sport, _ = context
    data = payload(sport)
    response = client.post("/api/rint/recordings", json=data, headers=headers)
    assert response.status_code == 201, response.json
    activity = response.json["data"]["workout_id"]
    repeated = client.post("/api/rint/recordings", json=data, headers=headers)
    assert repeated.status_code == 200
    assert repeated.json["data"]["duplicate"]
    path = f"/api/rint/activities/{activity}"
    analysis = client.get(path + "/analysis", headers=headers)
    assert analysis.status_code == 200
    assert analysis.json["data"]["summary"]["distance_m"] == 3000
    assert len(analysis.json["data"]["splits_km"]) == 3
    assert client.get(path + "/analysis", headers=other).status_code == 404
    assert client.get(path + "/export", headers=other).status_code == 404
    assert (
        "heart_rate"
        in client.get(path + "/export?format=csv", headers=headers).text
    )
    changed = payload(sport)
    changed["id"] = data["id"]
    changed["recording"]["points"][1]["d"] = 51
    assert (
        client.post(
            "/api/rint/recordings", json=changed, headers=headers
        ).status_code
        == 409
    )
    assert (
        client.post(
            path + "/sharing",
            json={"visibility": "public", "map_visibility": "public"},
            headers=headers,
        ).status_code
        == 200
    )
    public = client.get(path + "/analysis").json["data"]
    assert "lat" not in public["recording"]["points"][0]
    assert "lat" not in public["recording"]["points"][-1]
    assert "lat" in public["recording"]["points"][30]
    assert "heart_rate" not in public["summary"]["averages"]
    assert "heart_rate" not in public["recording"]["points"][30]
    legacy = client.get(f"/api/workouts/{activity}/geojson", headers=other)
    assert legacy.status_code == 200, legacy.json
    assert legacy.json["data"]["geojson"]["coordinates"][0][0] != [-73, 40]
    assert (
        client.post(
            path + "/sharing", json={"visibility": "private"}, headers=headers
        ).status_code
        == 200
    )
    assert client.get(path + "/analysis").status_code == 404


def strava_zip(count=7):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        rows = [
            "Activity ID,Activity Name,Filename,Activity Type,Activity Date,Elapsed Time,Distance"
        ]
        for i in range(count):
            rows.append(
                f"{i + 100},Run {i},activities/{i}.gpx,Run,2026-01-{i + 1:02}T00:00:00Z,60,0.3"
            )
            archive.writestr(
                f"activities/{i}.gpx",
                f'<gpx><trk><trkseg><trkpt lat="40" lon="-73"><time>2026-01-{i + 1:02}T00:00:00Z</time></trkpt><trkpt lat="40" lon="-72.999"><time>2026-01-{i + 1:02}T00:00:10Z</time></trkpt></trkseg></trk></gpx>',
            )
        archive.writestr("activities.csv", "\n".join(rows))
        photo = io.BytesIO()
        Image.new("RGB", (32, 32), "red").save(photo, "JPEG")
        archive.writestr("photos/100_1.jpg", photo.getvalue())
    buffer.seek(0)
    return buffer


def test_resumable_strava_import_photo_access_and_cross_import_deduplication(
    context,
):
    client, headers, other, _, owner = context
    preview = client.post(
        "/api/rint/imports",
        data={"file": (strava_zip(), "strava.zip")},
        headers=headers,
    )
    assert preview.status_code == 201, preview.json
    identifier = preview.json["data"]["id"]
    path = f"/api/rint/imports/{identifier}"
    assert client.get(path, headers=other).status_code == 404
    first = client.post(path, json={"visibility": "private"}, headers=headers)
    assert first.json["data"]["completed"] == 5, first.json
    resumed = client.post(path, json={}, headers=headers)
    assert resumed.json["data"]["completed"] == 7
    assert all(
        i["status"] == "imported" for i in resumed.json["data"]["items"]
    ), resumed.json
    from fittrackee import db
    from fittrackee.media.models import Media
    from fittrackee.workouts.models import Workout

    media = Media.query.filter_by(user_id=owner.id).first()
    assert media is not None
    from flask import g

    with client.application.test_request_context():
        g.media_viewer = owner
        ticket_url = media.serialize()["url"].split("/media/")[1]
    visitor = client.application.test_client()
    assert visitor.get("/media/" + media.file_name).status_code == 404
    assert client.get("/media/" + ticket_url).status_code == 200
    workout = db.session.get(Workout, media.workout_id)
    assert workout.workout_visibility.value == "private"
    client.post(
        f"/api/rint/activities/{workout.short_id}/sharing",
        json={"visibility": "public"},
        headers=headers,
    )
    assert visitor.get("/media/" + media.file_name).status_code == 200
    client.post(
        f"/api/rint/activities/{workout.short_id}/sharing",
        json={"visibility": "private"},
        headers=headers,
    )
    assert visitor.get("/media/" + media.file_name).status_code == 404
    preview_again = client.post(
        "/api/rint/imports",
        data={"file": (strava_zip(), "strava.zip")},
        headers=headers,
    )
    assert all(
        i["status"] == "duplicate" for i in preview_again.json["data"]["items"]
    )
    assert client.delete(path, headers=headers).status_code == 204
    assert Workout.query.filter_by(user_id=owner.id).count() == 7


def test_indoor_sensors_laps_and_interval(context):
    client, headers, _, sport, _ = context
    data = payload(sport)
    data["recording"]["points"] = [
        {"t": 0, "heart_rate": 120, "power": 0},
        {"t": 10, "heart_rate": 160, "power": 200},
    ]
    data["recording"]["laps"] = [{"start": 0, "end": 10, "name": "Warm-up"}]
    created = client.post("/api/rint/recordings", json=data, headers=headers)
    assert created.status_code == 201, created.json
    activity = created.json["data"]["workout_id"]
    analysis = client.get(
        f"/api/rint/activities/{activity}/analysis", headers=headers
    ).json["data"]
    assert analysis["laps"][0]["averages"]["heart_rate"] == 140
    assert not analysis["best_efforts"]
    result = client.post(
        f"/api/rint/activities/{activity}/interval",
        json={"start": 2, "end": 8},
        headers=headers,
    )
    assert result.json["data"]["averages"]["power"] == 100


def test_history_sport_bests_social_interactions_and_complete_export(context):
    client, headers, other, sport, owner = context
    from fittrackee import db
    from fittrackee.users.export_data import UserDataExporter
    from fittrackee.workouts.models import Sport

    cycling = Sport("Cycling (Sport)")
    db.session.add(cycling)
    db.session.commit()
    for i, category in enumerate([sport, sport, cycling.id]):
        data = payload(category)
        data["recording"]["started_at"] = f"2026-0{i + 1}-01T00:00:00Z"
        response = client.post(
            "/api/rint/recordings", json=data, headers=headers
        )
        assert response.status_code == 201, response.json
        activity = response.json["data"]["workout_id"]
    history = client.get("/api/rint/history", headers=headers).json["data"]
    assert sum(row["activities"] for row in history) == 3
    assert sum(row["distance_m"] for row in history) == 9000
    assert sum(row["elapsed_s"] for row in history) == 1800
    assert (
        len(
            client.get(
                f"/api/rint/history?sport_id={sport}", headers=headers
            ).json["data"]
        )
        == 2
    )
    bests = client.get("/api/rint/bests", headers=headers).json["data"]
    assert {row["sport_id"] for row in bests} == {sport, cycling.id}
    assert client.get("/api/rint/bests", headers=other).json["data"] == []
    client.post(
        f"/api/rint/activities/{activity}/sharing",
        json={"visibility": "public"},
        headers=headers,
    )
    assert (
        client.post(
            f"/api/workouts/{activity}/like", headers=other
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/workouts/{activity}/like/undo", headers=other
        ).status_code
        == 200
    )
    comment = client.post(
        f"/api/workouts/{activity}/comments",
        json={"text": "Great session @rint_test", "text_visibility": "public"},
        headers=other,
    )
    assert comment.status_code == 201, comment.json
    comments = client.get(
        f"/api/workouts/{activity}/comments", headers=headers
    )
    assert "Great session" in comments.text
    archive, name = UserDataExporter(owner).generate_archive()
    assert name is not None and archive is not None
    with zipfile.ZipFile(archive) as exported:
        names = exported.namelist()
        assert (
            len(
                [
                    name
                    for name in names
                    if name.startswith("workout_files/")
                    and name.endswith(".json")
                ]
            )
            == 3
        )
        assert (
            "rint_recording"
            in exported.read("user_workouts_data.json").decode()
        )


def test_media_cookie_is_revoked_when_its_login_is_revoked(context):
    client, headers, _, _, owner = context
    from fittrackee.media.models import Media

    response = client.post(
        "/api/rint/imports",
        data={"file": (strava_zip(1), "strava.zip")},
        headers=headers,
    )
    batch = response.json["data"]["id"]
    client.post(f"/api/rint/imports/{batch}", json={}, headers=headers)
    media = Media.query.filter_by(user_id=owner.id).first()
    cookie = client.get_cookie("rint_media", path="/media/")
    assert cookie is not None
    assert client.get("/media/" + media.file_name).status_code == 200
    assert client.post("/api/auth/logout", headers=headers).status_code == 200
    replay = client.application.test_client()
    replay.set_cookie("rint_media", cookie.value, path="/media/")
    assert replay.get("/media/" + media.file_name).status_code == 404


def test_static_map_cannot_bypass_route_privacy_or_revoked_login(context):
    client, headers, other, sport, _ = context
    from pathlib import Path

    from fittrackee import db
    from fittrackee.workouts.models import Workout

    saved = client.post(
        "/api/rint/recordings", json=payload(sport), headers=headers
    )
    activity = saved.json["data"]["workout_id"]
    workout = Workout.query.one()
    workout.map_id = "private-route-test"
    workout.map = "private-route-test.png"
    folder = Path(client.application.config["UPLOAD_FOLDER"])
    folder.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (32, 32), "green").save(folder / workout.map)
    db.session.commit()
    path = "/api/workouts/map/private-route-test"
    anonymous = client.application.test_client()
    assert anonymous.get(path).status_code == 404
    assert client.get(path, headers=other).status_code == 404
    assert client.get(path, headers=headers).status_code == 200
    cookie = client.get_cookie("rint_map", path="/api/workouts/map/")
    assert cookie is not None
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "private, no-store"
    client.post(
        f"/api/rint/activities/{activity}/sharing",
        json={"visibility": "public", "map_visibility": "public"},
        headers=headers,
    )
    # Even a public activity's original thumbnail contains unprotected endpoints.
    assert anonymous.get(path).status_code == 404
    assert client.get(path, headers=other).status_code == 404
    public_card = client.get(f"/api/workouts/{activity}", headers=other).json[
        "data"
    ]["workouts"][0]
    assert public_card["map"] is None
    assert client.post("/api/auth/logout", headers=headers).status_code == 200
    anonymous.set_cookie("rint_map", cookie.value, path="/api/workouts/map/")
    assert anonymous.get(path).status_code == 404


def test_sharing_round_trip_retains_radius_and_independent_visibility(context):
    client, headers, other, sport, _ = context
    activity = client.post(
        "/api/rint/recordings", json=payload(sport), headers=headers
    ).json["data"]["workout_id"]
    path = f"/api/rint/activities/{activity}/sharing"
    saved = client.post(
        path,
        json={
            "visibility": "public",
            "map_visibility": "followers_only",
            "privacy_radius_m": 1500,
        },
        headers=headers,
    )
    assert saved.status_code == 200
    assert client.get(path, headers=headers).json == saved.json
    assert client.get(path, headers=other).status_code == 403
    assert client.get(path).status_code == 401
    patched = client.post(
        path, json={"visibility": "private"}, headers=headers
    )
    assert patched.json["data"]["privacy_radius_m"] == 1500
    assert patched.json["data"]["map_visibility"] == "followers_only"
    invalid = client.post(
        path,
        json={
            "visibility": "public",
            "privacy_radius_m": 100,
        },
        headers=headers,
    )
    assert invalid.status_code == 400
    assert client.get(path, headers=headers).json == patched.json


def test_earlier_fittrackee_uploads_backfill_bests_and_preserve_route_privacy(
    context,
):
    from pathlib import Path

    from fittrackee import db
    from fittrackee.rint.models import ActivityRecording
    from fittrackee.workouts.models import Workout

    client, headers, other, sport, _ = context
    activity = client.post(
        "/api/rint/recordings", json=payload(sport), headers=headers
    ).json["data"]["workout_id"]
    from fittrackee.utils import decode_short_id

    workout = Workout.query.filter_by(uuid=decode_short_id(activity)).one()
    db.session.delete(workout.rint_recording)
    workout.original_file = "legacy/run.gpx"
    original = (
        Path(client.application.config["UPLOAD_FOLDER"])
        / workout.original_file
    )
    original.parent.mkdir(parents=True, exist_ok=True)
    original.write_text(
        '<gpx version="1.1"><trk><trkseg>'
        + "".join(
            f'<trkpt lat="40" lon="{-73 + i * 0.003}"><time>2026-01-01T00:{i:02d}:00Z</time></trkpt>'
            for i in range(20)
        )
        + "</trkseg></trk></gpx>"
    )
    db.session.commit()
    db.session.expire_all()
    refreshed = client.post(
        "/api/rint/bests/refresh", json={}, headers=headers
    )
    assert refreshed.status_code == 200, refreshed.json
    assert refreshed.json["data"]["processed"] == 1
    assert refreshed.json["data"]["errors"] == []
    assert (
        client.post("/api/rint/bests/refresh", json={}, headers=headers).json[
            "data"
        ]["processed"]
        == 0
    )
    assert client.get("/api/rint/bests", headers=headers).json["data"]
    assert ActivityRecording.query.count() == 0
    path = f"/api/rint/activities/{activity}"
    saved = client.post(
        path + "/sharing",
        json={
            "visibility": "public",
            "map_visibility": "public",
            "privacy_radius_m": 1500,
        },
        headers=headers,
    )
    assert saved.status_code == 200
    assert (
        client.get(path + "/sharing", headers=headers).json["data"][
            "privacy_radius_m"
        ]
        == 1500
    )
    visible = client.get(path + "/analysis", headers=other).json["data"][
        "recording"
    ]["points"]
    assert "lat" not in visible[0] and "lat" not in visible[-1]
    assert "lat" in visible[10]
    exported = client.get(path + "/export", headers=headers).json
    assert exported["original_recording"]["points"][0]["lat"] == 40


def test_profile_location_does_not_require_a_bio(context):
    client, headers, _, _, _ = context
    client.application.config["privacy_policy_date"] = datetime(
        2018, 1, 1, tzinfo=timezone.utc
    )
    response = client.post(
        "/api/auth/profile/edit",
        json={
            "first_name": "",
            "last_name": "",
            "bio": "",
            "birth_date": "",
            "location": "A town",
        },
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json["data"]["location"] == "A town"
    assert response.json["data"]["bio"] is None
    response = client.post(
        "/api/auth/profile/edit",
        json={
            "first_name": "",
            "last_name": "",
            "bio": "About me",
            "birth_date": "",
            "location": "",
        },
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json["data"]["location"] is None


def test_feed_route_placeholder_respects_map_permissions(context):
    client, headers, other, sport, _ = context
    created = client.post(
        "/api/rint/recordings", json=payload(sport), headers=headers
    )
    activity = created.json["data"]["workout_id"]
    own = client.get("/api/timeline", headers=headers).json["data"]["workouts"]
    assert next(w for w in own if w["id"] == activity)["with_geometry"] is True
    path = f"/api/rint/activities/{activity}/sharing"
    client.post(
        path,
        json={"visibility": "public", "map_visibility": "private"},
        headers=headers,
    )
    hidden = client.get("/api/users/rint_test/workouts", headers=other).json[
        "data"
    ]["workouts"]
    assert (
        next(w for w in hidden if w["id"] == activity)["with_geometry"]
        is False
    )
    client.post(path, json={"map_visibility": "public"}, headers=headers)
    visible = client.get("/api/users/rint_test/workouts", headers=other).json[
        "data"
    ]["workouts"]
    assert (
        next(w for w in visible if w["id"] == activity)["with_geometry"]
        is True
    )


def test_weekly_history_uses_local_monday_and_keeps_accounts_separate(context):
    client, headers, other, sport, _ = context
    for started in ["2026-10-12T03:50:00Z", "2026-10-12T04:10:00Z", "2026-11-02T04:30:00Z"]:
        data = payload(sport)
        data["recording"]["started_at"] = started
        assert client.post("/api/rint/recordings", json=data, headers=headers).status_code == 201
    path = "/api/rint/history?period=week&timezone=America/New_York"
    response = client.get(path, headers=headers)
    assert response.status_code == 200, response.json
    buckets = {row["week"]: row for row in response.json["data"]}
    assert set(buckets) == {"2026-10-05", "2026-10-12", "2026-10-26"}
    assert sum(row["distance_m"] for row in buckets.values()) == 9000
    assert all(row["activities"] == 1 for row in buckets.values())
    assert client.get(path, headers=other).json["data"] == []
    assert client.get("/api/rint/history?period=week&timezone=invalid", headers=headers).status_code == 400
    assert client.get("/api/rint/history?period=day", headers=headers).status_code == 400
    record = client.get("/api/rint/bests", headers=headers).json
    assert record["coverage"]["pending"] == 0
    assert all("start" in row and "end" in row and "date" in row for row in record["data"])
