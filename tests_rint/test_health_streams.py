from fittrackee.rint.health import combine
from rint_core import analyze


def test_partial_health_route_is_enriched_without_losing_sensor_samples():
    base = {
        "started_at": "2026-01-01T00:00:00Z",
        "points": [
            {"t": 0, "d": 0, "lat": 40, "lon": -73, "heart_rate": 120},
            {"t": 30, "d": 150, "lat": 40, "lon": -72.999},
            {"t": 60, "d": 300, "heart_rate": 130},
        ],
    }
    later = {
        "started_at": base["started_at"],
        "points": [
            {"t": 0, "d": 0},
            {"t": 15, "d": 75, "heart_rate": 125},
            {"t": 30, "d": 150},
            {"t": 45, "d": 225, "lat": 40, "lon": -72.9985},
            {"t": 60, "d": 300, "lat": 40, "lon": -72.998},
        ],
    }
    result = analyze(combine(base, later, health_primary=True))
    assert len([p for p in result["recording"]["points"] if "lat" in p]) == 4
    assert result["summary"]["distance_m"] == 300
    assert any(
        p.get("heart_rate") == 125 for p in result["recording"]["points"]
    )


def test_health_fills_original_sensor_gaps_without_replacing_measured_values():
    base = {
        "started_at": "2026-01-01T00:00:00Z",
        "points": [
            {"t": 0, "d": 0, "heart_rate": 120},
            {"t": 10, "d": 50, "heart_rate": 122},
            {"t": 200, "d": 1000, "heart_rate": 140},
        ],
    }
    supplement = {
        "started_at": "2026-01-01T00:00:02Z",
        "points": [
            {"t": 0, "heart_rate": 999},
            {"t": 8, "heart_rate": 999},
            {"t": 100, "heart_rate": 135},
            {"t": 198, "heart_rate": 999},
        ],
    }
    result = combine(base, supplement, health_primary=False)
    assert not any(p.get("heart_rate") == 999 for p in result["points"])
    assert (
        next(p for p in result["points"] if p["t"] == 102)["heart_rate"] == 135
    )
    assert (
        next(p for p in result["points"] if p["t"] == 10)["heart_rate"] == 122
    )
    assert analyze(result)["summary"]["distance_m"] == 1000


def test_late_gps_route_replaces_unverifiable_total_for_distance_calculation():
    base = {
        "started_at": "2026-01-01T00:00:00Z",
        "summary_only": True,
        "points": [{"t": 0, "d": 0}, {"t": 60, "d": 300}],
    }
    route = {
        "started_at": base["started_at"],
        "points": [
            {"t": t, "lat": 40, "lon": -73 + t * 0.00001}
            for t in range(0, 61, 10)
        ],
    }
    result = analyze(combine(base, route, health_primary=True))
    assert 50 < result["summary"]["distance_m"] < 52
    assert not result["recording"].get("summary_only")
    assert not any(
        p.get("distance_gap") for p in result["recording"]["points"]
    )
