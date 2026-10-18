import zipfile

import pytest

from rint_core import analyze, interval, parse_recording
from rint_core.archive import manifest


def recording(points, **kwargs):
    return {"points": points, **kwargs}


def test_irregular_splits_interpolate_and_keep_partial():
    result = analyze(
        recording([{"t": t, "d": t * 5} for t in range(0, 451, 15)])
    )
    assert [s["elapsed_s"] for s in result["splits_km"]] == [200, 200, 50]
    assert [s["complete"] for s in result["splits_km"]] == [True, True, False]
    assert result["splits_mile"][0]["elapsed_s"] == pytest.approx(321.8688)


def test_best_effort_can_start_between_samples_and_includes_pause():
    points = [{"t": t, "d": t * 10} for t in range(0, 151, 10)]
    points += [
        {"t": 180, "d": 1500, "active": False},
        {"t": 190, "d": 1500},
        {"t": 200, "d": 1600},
    ]
    result = analyze(recording(points))
    mile = next(b for b in result["best_efforts"] if b["distance_m"] == 1000)
    assert mile["elapsed_s"] == 100
    assert result["summary"]["paused_s"] == 10


def test_indoor_sensor_only_preserves_zero_and_missing():
    result = analyze(
        recording(
            [
                {"t": 0, "power": 0},
                {"t": 10, "power": 200},
                {"t": 20, "heart_rate": 150},
            ]
        )
    )
    assert result["summary"]["averages"]["power"] == 100
    assert result["summary"]["coverage_s"]["power"] == 10
    assert "heart_rate" not in result["summary"]["averages"]
    assert result["summary"]["active_s"] == 20
    assert result["summary"]["paused_s"] == 0
    assert result["best_efforts"] == []


def test_gap_prevents_false_record():
    result = analyze(recording([{"t": 0, "d": 0}, {"t": 100, "d": 5000}]))
    assert not result["best_efforts"]
    assert result["warnings"]


def test_gps_zero_coordinates_and_spike():
    result = analyze(
        recording(
            [
                {"t": 0, "lat": 0, "lon": 0},
                {"t": 10, "lat": 0, "lon": 0.001},
                {"t": 11, "lat": 40, "lon": 70},
            ]
        )
    )
    assert result["summary"]["distance_m"] == pytest.approx(111.195, rel=0.001)
    assert result["warnings"]


def test_tcx_without_gps_keeps_distance_lap_and_heart_rate():
    xml = b"""<TrainingCenterDatabase><Activities><Activity><Lap StartTime="2026-01-01T00:00:00Z"><TotalTimeSeconds>10</TotalTimeSeconds><Track><Trackpoint><Time>2026-01-01T00:00:00Z</Time><DistanceMeters>0</DistanceMeters><HeartRateBpm><Value>120</Value></HeartRateBpm></Trackpoint><Trackpoint><Time>2026-01-01T00:00:10Z</Time><DistanceMeters>50</DistanceMeters><HeartRateBpm><Value>140</Value></HeartRateBpm></Trackpoint></Track></Lap></Activity></Activities></TrainingCenterDatabase>"""
    result = analyze(parse_recording(xml, "tcx"))
    assert result["laps"][0]["distance_m"] == 50
    assert result["summary"]["averages"]["heart_rate"] == 130
    assert "lat" not in result["recording"]["points"][0]


def test_archive_rejects_traversal(tmp_path):
    path = tmp_path / "bad.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("../activities.csv", "Activity ID\n1")
    with pytest.raises(ValueError, match="unsafe"):
        manifest(path)


def test_archive_preserves_metadata_and_hash(tmp_path):
    path = tmp_path / "strava.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "activities.csv",
            "Activity ID,Activity Name,Filename,Activity Type\n123,Morning run,activities/123.gpx,Run",
        )
        archive.writestr("activities/123.gpx", "original")
        archive.writestr("photos/123_1.jpg", b"photo")
    row = manifest(path)[0]
    assert row["title"] == "Morning run"
    assert row["digest"]
    assert row["photos"] == ["photos/123_1.jpg"]


def test_interval_rejects_invalid_and_weights_time():
    points = [
        {"t": 0, "d": 0, "heart_rate": 100, "active": True},
        {"t": 10, "d": 50, "heart_rate": 120, "active": True},
    ]
    assert interval(points, 2, 8)["averages"]["heart_rate"] == 110
    with pytest.raises(ValueError):
        interval(points, 8, 2)


def test_strava_duplicate_distance_headers_use_precise_metres(tmp_path):
    path = tmp_path / "strava.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "activities.csv",
            "Activity ID,Activity Name,Activity Date,Activity Type,Elapsed Time,Distance,Elapsed Time,Distance,Media\n"
            "123,Lunch run,2026-01-01T00:00:00Z,Run,100,0.5,100.0,500.125,photos/example.jpg",
        )
        archive.writestr("photos/example.jpg", b"photo")
    row = manifest(str(path))[0]
    assert row["distance_unit"] == "m"
    assert float(row["distance"]) == 500.125
    assert row["photos"] == ["photos/example.jpg"]
