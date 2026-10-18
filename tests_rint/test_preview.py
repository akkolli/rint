from fittrackee.rint.preview import has_route_preview, route_preview

pytest_plugins = ["tests_rint.test_api"]


def test_preview_is_bounded_and_never_bridges_hidden_locations_or_gaps():
    points = [
        {"t": t, "lat": 40, "lon": -73 + t * 0.000001, "heart_rate": 140}
        for t in range(10000)
    ]
    points[2000] = {"t": 2000, "route_gap": True}
    for point in points[6000:]:
        point["t"] += 120
    result = route_preview(points)
    assert len(result) <= 543
    assert all(set(row) <= {"t", "lat", "lon", "active", "route_gap"} for row in result)
    assert sum("lat" not in row for row in result) == 2
    assert result[0]["t"] == 0 and result[-1]["t"] == 10119
    assert route_preview([{"t": 0}, {"t": 1}]) == []


def test_sensor_samples_do_not_fragment_routes_but_privacy_markers_do():
    points = [
        {"t": 0, "lat": 40, "lon": -73},
        {"t": 1, "heart_rate": 140},
        {"t": 2, "lat": 40, "lon": -72.999},
    ]
    assert has_route_preview(points)
    assert len(route_preview(points)) == 2
    assert not has_route_preview([points[0], {"t": 1, "route_gap": True}, points[2]])
    assert not has_route_preview([points[0], {**points[2], "t": 100}])
    points.append({"t": 3, "lat": 40, "lon": -72.998})
    assert has_route_preview(points)
    assert not has_route_preview(points, privacy_radius_m=200)


def test_route_preview_respects_activity_privacy_and_endpoint_redaction(
    context,
):
    from tests_rint.test_api import payload

    client, headers, other, sport, _ = context
    created = client.post(
        "/api/rint/recordings", json=payload(sport), headers=headers
    )
    activity = created.json["data"]["workout_id"]
    path = f"/api/rint/activities/{activity}"
    own = client.get(path + "/preview", headers=headers)
    assert own.status_code == 200
    assert own.json["data"]["points"][0]["lon"] == -73
    assert client.get(path + "/preview", headers=other).status_code == 404
    client.post(
        path + "/sharing", json={"visibility": "public"}, headers=headers
    )
    assert client.get(path + "/preview").json["data"]["points"] == []
    client.post(
        path + "/sharing",
        json={
            "visibility": "public",
            "map_visibility": "public",
            "privacy_radius_m": 200,
        },
        headers=headers,
    )
    visible = client.get(path + "/preview").json["data"]["points"]
    assert visible and visible[0]["lon"] != -73
    assert (
        visible[-1]["lon"] != payload(sport)["recording"]["points"][-1]["lon"]
    )
    client.post(
        path + "/sharing", json={"privacy_radius_m": 10000}, headers=headers
    )
    hidden = client.get("/api/users/rint_test/workouts", headers=other)
    assert not next(
        w for w in hidden.json["data"]["workouts"] if w["id"] == activity
    )["with_geometry"]
    assert (
        client.get(path + "/preview", headers=other).json["data"]["points"]
        == []
    )
    client.post(
        path + "/sharing", json={"visibility": "private"}, headers=headers
    )
    assert client.get(path + "/preview").status_code == 404
