from rint_core import analyze


def test_device_distance_and_sensor_route_samples_do_not_double_count():
    result = analyze(
        {
            "points": [
                {"t": 0, "d": 0, "lat": 0, "lon": 0},
                {"t": 5, "lat": 0, "lon": 0.001, "heart_rate": 130},
                {"t": 10, "d": 100, "lat": 0, "lon": 0.002},
            ]
        }
    )
    assert result["summary"]["distance_m"] == 100
    assert result["recording"]["points"][1]["d"] == 50


def test_sensor_sampling_cannot_hide_distance_sampling_gaps():
    points = [{"t": t, "heart_rate": 130} for t in range(0, 601, 10)]
    points[0]["d"] = 0
    points[-1]["d"] = 5000
    result = analyze({"points": points})
    assert result["summary"]["distance_m"] == 5000
    assert result["best_efforts"] == []


def test_summary_csv_never_creates_verified_records():
    result = analyze(
        {
            "summary_only": True,
            "points": [{"t": 0, "d": 0}, {"t": 50, "d": 1000}],
        }
    )
    assert result["summary"]["distance_m"] == 1000
    assert result["best_efforts"] == []
    assert result["splits_km"] == []


def test_sensor_averages_are_independent_of_route_sampling():
    result = analyze(
        {
            "points": [
                {"t": 0, "d": 0, "heart_rate": 100},
                {"t": 5, "d": 25},
                {"t": 10, "d": 50, "heart_rate": 140},
            ]
        }
    )
    assert result["summary"]["averages"]["heart_rate"] == 120
    assert result["summary"]["coverage_s"]["heart_rate"] == 10


def test_gps_distance_survives_interleaved_sensor_only_samples():
    result = analyze(
        {
            "points": [
                {"t": 0, "lat": 0, "lon": 0},
                {"t": 5, "heart_rate": 130},
                {"t": 10, "lat": 0, "lon": 0.001},
            ]
        }
    )
    assert round(result["summary"]["distance_m"], 1) == 111.2
    assert round(result["recording"]["points"][1]["d"], 1) == 55.6
