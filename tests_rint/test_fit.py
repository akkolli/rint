from pathlib import Path

from rint_core import analyze, parse_recording


def test_upstream_apple_watch_fixture_keeps_distance_sensors_and_device_lap():
    recording = parse_recording(
        Path("fittrackee/tests/files/apple_watch.fit").read_bytes(), "fit"
    )
    result = analyze(recording)
    assert result["summary"]["distance_m"] == 1200.95
    assert result["laps"]
    assert result["best_efforts"]
    assert any("heart_rate" in p for p in result["recording"]["points"])


def test_upstream_fit_fixture_does_not_require_every_point_to_have_coordinates():
    recording = parse_recording(
        Path("fittrackee/tests/files/example.fit").read_bytes(), "fit"
    )
    result = analyze(recording)
    assert result["summary"]["distance_m"] == 316.8
    assert result["summary"]["elapsed_s"] > 0
