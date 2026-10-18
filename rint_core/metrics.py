"""SI streams and reproducible metrics without fabricated sensor data."""

import math
from bisect import bisect_left, bisect_right
from itertools import pairwise
from typing import Any, TypeGuard

VERSION = "1.0.0"
SENSORS = ("heart_rate", "cadence", "power", "elevation")
DISTANCES = (400, 1000, 1609.344, 5000, 10000, 21097.5, 42195)
MAX_GAP = 60


def number(value: Any) -> TypeGuard[float]:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def haversine(a: dict[str, Any], b: dict[str, Any]) -> float:
    lat1, lat2 = math.radians(a["lat"]), math.radians(b["lat"])
    dlat = lat2 - lat1
    dlon = math.radians(b["lon"] - a["lon"])
    return (
        6371008.8
        * 2
        * math.asin(
            min(
                1,
                math.sqrt(
                    math.sin(dlat / 2) ** 2
                    + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
                ),
            )
        )
    )


def normalize(recording: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(recording, dict) or not isinstance(
        recording.get("points"), list
    ):
        raise ValueError("A recording must contain a points array.")
    if len(recording["points"]) > 250000:
        raise ValueError("A recording exceeds 250,000 samples.")
    samples: dict[float, dict[str, Any]] = {}
    warnings = set()
    for raw in recording["points"]:
        if (
            not isinstance(raw, dict)
            or not number(raw.get("t"))
            or raw["t"] < 0
        ):
            raise ValueError(
                "Every sample needs a finite, non-negative elapsed time."
            )
        p = {
            "t": float(raw["t"]),
            "active": raw.get("active", True) is not False,
        }
        for key in ("d", *SENSORS):
            if number(raw.get(key)) and (key == "elevation" or raw[key] >= 0):
                p[key] = float(raw[key])
        if (
            number(raw.get("lat"))
            and number(raw.get("lon"))
            and abs(raw["lat"]) <= 90
            and abs(raw["lon"]) <= 180
        ):
            p.update(lat=float(raw["lat"]), lon=float(raw["lon"]))
        # Merge duplicate timestamps, retaining complementary sensor fields.
        samples[p["t"]] = {**samples.get(p["t"], {}), **p}
    points = sorted(samples.values(), key=lambda p: p["t"])
    if len(points) < 2:
        raise ValueError(
            "At least two timed samples are required for analysis."
        )
    if points[-1]["t"] > 7 * 86400:
        raise ValueError("A recording cannot exceed seven days.")
    distance = 0.0
    previous_device = None
    offset = 0.0
    anchors = []
    for p in points:
        if "d" in p:
            device = p["d"]
            if device > 20_000_000:
                raise ValueError(
                    "Device distance exceeds the 20,000 km limit."
                )
            if previous_device is not None and device < previous_device:
                offset = distance - device
                warnings.add(
                    (
                        "Device distance reset; distance continued from the "
                        "preceding sample."
                    )
                )
            distance = max(distance, device + offset)
            if distance > 20_000_000:
                raise ValueError("Accumulated distance exceeds 20,000 km.")
            previous_device = device
            anchors.append({"t": p["t"], "d": distance})
    anchor_times = [p["t"] for p in anchors]
    distance = 0.0
    gps_anchor = None
    gps_distances = []
    state = True
    for i, p in enumerate(points):
        prev = points[i - 1] if i else None
        if anchors:
            # Device distance is the single authority when present. Mixing
            # route
            # increments with cumulative device samples would double count.
            j = bisect_right(anchor_times, p["t"]) - 1
            if j < 0:
                distance = anchors[0]["d"]
            elif j == len(anchors) - 1:
                distance = anchors[-1]["d"]
            else:
                a, b = anchors[j], anchors[j + 1]
                distance = a["d"] + (b["d"] - a["d"]) * (p["t"] - a["t"]) / (
                    b["t"] - a["t"]
                )
                if b["t"] - a["t"] > MAX_GAP:
                    p["distance_gap"] = True
                    warnings.add(
                        (
                            "Device distance gaps over 60 seconds "
                            "are excluded from sustained efforts."
                        )
                    )
        elif "lat" in p:
            if gps_anchor and p["active"] and gps_anchor["active"]:
                dt = p["t"] - gps_anchor["t"]
                step = haversine(gps_anchor, p)
                if dt > MAX_GAP:
                    p["distance_gap"] = True
                    warnings.add(
                        (
                            "GPS gaps over 60 seconds are excluded from "
                            "sustained efforts."
                        )
                    )
                elif step / dt > 30:
                    p.pop("lat")
                    p.pop("lon")
                    warnings.add(
                        (
                            "A GPS jump was excluded from "
                            "route-derived distance and the displayed route."
                        )
                    )
                elif step / dt >= 0.3:
                    distance += step
            if "lat" in p:
                gps_anchor = p
                gps_distances.append({"t": p["t"], "d": distance})
        elif p["active"] != state:
            # Pause boundaries also bound interpolation in sensor-only
            # intervals.
            gps_distances.append({"t": p["t"], "d": distance})
            gps_anchor = None
        state = bool(p["active"])
        p["d"] = distance
        if prev and p["t"] - prev["t"] > MAX_GAP:
            warnings.add(
                (
                    "Sampling gaps over 60 seconds are excluded "
                    "from sustained efforts."
                )
            )
    if not anchors and len(gps_distances) >= 2:
        gps_times = [p["t"] for p in gps_distances]
        for p in points:
            j = bisect_right(gps_times, p["t"]) - 1
            if 0 <= j < len(gps_distances) - 1:
                a, b = gps_distances[j], gps_distances[j + 1]
                p["d"] = a["d"] + (b["d"] - a["d"]) * (p["t"] - a["t"]) / (
                    b["t"] - a["t"]
                )
                if b["t"] - a["t"] > MAX_GAP:
                    p["distance_gap"] = True
    laps: list[dict[str, Any]] = []
    raw_laps = recording.get("laps") or []
    if not isinstance(raw_laps, list):
        raise ValueError("Device laps must be a list of timed intervals.")
    for lap in raw_laps:
        if not isinstance(lap, dict):
            raise ValueError("Every lap must contain start and end times.")
        if (
            number(lap.get("start"))
            and number(lap.get("end"))
            and points[0]["t"] <= lap["start"] < lap["end"] <= points[-1]["t"]
        ):
            laps.append(
                {
                    "start": float(lap["start"]),
                    "end": float(lap["end"]),
                    "name": str(lap.get("name", f"Lap {len(laps) + 1}"))[:100],
                }
            )
    return {
        "version": 1,
        "started_at": recording.get("started_at"),
        "points": points,
        "laps": laps,
        "warnings": sorted(warnings),
    }


class StreamIndex:
    def __init__(self, points: list[dict[str, Any]]) -> None:
        self.times = [p["t"] for p in points]
        self.distances = [p["d"] for p in points]
        self.sensors = {
            key: [p for p in points if key in p] for key in SENSORS
        }
        self.sensor_times = {
            key: [p["t"] for p in rows] for key, rows in self.sensors.items()
        }


def value_at(
    points: list[dict[str, Any]],
    t: float,
    key: str = "d",
    times: list[float] | None = None,
) -> Any:
    times = times if times is not None else [p["t"] for p in points]
    i = max(0, min(len(points) - 2, bisect_right(times, t) - 1))
    a, b = points[i], points[i + 1]
    if key not in a or key not in b:
        return None
    return a[key] + (b[key] - a[key]) * (t - a["t"]) / (b["t"] - a["t"])


def interval(
    points: list[dict[str, Any]],
    start: float | None,
    end: float | None,
    index: StreamIndex | None = None,
) -> dict[str, Any]:
    if (
        not number(start)
        or not number(end)
        or not points[0]["t"] <= start < end <= points[-1]["t"]
    ):
        raise ValueError("Choose an interval inside the recorded time range.")
    index = index or StreamIndex(points)
    distance = value_at(points, end, times=index.times) - value_at(
        points, start, times=index.times
    )
    first = max(0, bisect_right(index.times, start) - 1)
    last = bisect_left(index.times, end) + 1
    timed = points[first:last]
    moving = 0.0
    sums: dict[str, float] = {}
    coverage: dict[str, float] = {}
    for a, b in pairwise(timed):
        dt = max(0, min(end, b["t"]) - max(start, a["t"]))
        if not dt:
            continue
        if (
            a["active"]
            and not a.get("distance_gap")
            and b["t"] - a["t"] <= MAX_GAP
            and b["d"] > a["d"]
        ):
            moving += dt
    for key in SENSORS:
        times = index.sensor_times[key]
        first = max(0, bisect_right(times, start) - 1)
        last = bisect_left(times, end) + 1
        sensor = index.sensors[key][first:last]
        for a, b in pairwise(sensor):
            dt = max(0, min(end, b["t"]) - max(start, a["t"]))
            if dt and b["t"] - a["t"] <= MAX_GAP:
                lo, hi = max(start, a["t"]), min(end, b["t"])
                weight = (
                    value_at([a, b], lo, key) + value_at([a, b], hi, key)
                ) / 2
                sums[key] = sums.get(key, 0) + weight * dt
                coverage[key] = coverage.get(key, 0) + dt
    # Indoor timed workouts can be active without distance. Do not call them
    # pauses.
    active = sum(
        max(0, min(end, b["t"]) - max(start, a["t"]))
        for a, b in pairwise(timed)
        if a["active"]
    )
    return {
        "start": start,
        "end": end,
        "distance_m": distance,
        "elapsed_s": end - start,
        "moving_s": moving,
        "active_s": active,
        "paused_s": end - start - active,
        "pace_s_km": (end - start) * 1000 / distance if distance else None,
        "averages": {k: sums[k] / coverage[k] for k in sums},
        "coverage_s": coverage,
    }


def crossings(
    points: list[dict[str, Any]],
    distance: float,
    latest: bool = False,
    ds: list[float] | None = None,
) -> float:
    ds = ds if ds is not None else [p["d"] for p in points]
    i = bisect_right(ds, distance) - 1 if latest else bisect_left(ds, distance)
    i = max(0, min(i, len(points) - 1))
    if ds[i] == distance:
        return points[i]["t"]
    if latest:
        i += 1
    a, b = points[i - 1], points[i]
    return a["t"] + (b["t"] - a["t"]) * (distance - a["d"]) / (b["d"] - a["d"])


def splits(
    points: list[dict[str, Any]], size: float, index: StreamIndex | None = None
) -> list[dict[str, Any]]:
    index = index or StreamIndex(points)
    result, start, origin = [], points[0]["t"], points[0]["d"]
    total = points[-1]["d"] - origin
    for n in range(1, math.ceil(total / size) + 1):
        distance = min(n * size, total)
        end = crossings(points, origin + distance, ds=index.distances)
        if end <= start:
            continue
        result.append(
            {
                "index": n,
                "complete": distance == n * size,
                **interval(points, start, end, index),
            }
        )
        start = end
    return result


def best_efforts(points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    # Split at gaps; never award a best effort across an unobserved interval.
    runs: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for p in points:
        if p.get("distance_gap"):
            if current:
                runs.append(current)
                current = []
            continue
        if current and p["t"] - current[-1]["t"] > MAX_GAP:
            runs.append(current)
            current = []
        current.append(p)
    runs.append(current)
    for size in DISTANCES:
        best = None
        for run in runs:
            if len(run) < 2 or run[-1]["d"] - run[0]["d"] < size:
                continue
            candidates = {p["d"] for p in run} | {p["d"] - size for p in run}
            distances = [p["d"] for p in run]
            for distance in candidates:
                if distance < run[0]["d"] or distance + size > run[-1]["d"]:
                    continue
                start, end = (
                    crossings(run, distance, True, distances),
                    crossings(run, distance + size, ds=distances),
                )
                if end > start and (
                    best is None or end - start < best["elapsed_s"]
                ):
                    best = {
                        "distance_m": size,
                        "start": start,
                        "end": end,
                        "elapsed_s": end - start,
                        "pace_s_km": (end - start) * 1000 / size,
                    }
        if best:
            results.append(best)
    return results


def analyze(recording: dict[str, Any]) -> dict[str, Any]:
    data = normalize(recording)
    points = data["points"]
    index = StreamIndex(points)
    result = {
        "method_version": VERSION,
        "recording": data,
        "summary": interval(points, points[0]["t"], points[-1]["t"], index),
        "splits_km": splits(points, 1000, index),
        "splits_mile": splits(points, 1609.344, index),
        "laps": [
            {
                "name": lap["name"],
                **interval(points, lap["start"], lap["end"], index),
            }
            for lap in data["laps"]
        ],
        "best_efforts": best_efforts(points),
        "warnings": data["warnings"],
    }
    if recording.get("summary_only"):
        data["summary_only"] = True
        result["splits_km"] = []
        result["splits_mile"] = []
        result["best_efforts"] = []
        result["warnings"].append(
            (
                "Summary-only activity: no sampled splits or "
                "sustained efforts can be verified."
            )
        )
    return result
