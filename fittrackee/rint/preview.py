"""Bounded feed route outlines, after access and location redaction."""

import math
from typing import Any

from rint_core.metrics import haversine


def has_route_preview(
    points: list[dict[str, Any]], privacy_radius_m: int | None = None
) -> bool:
    """Detect a drawable, visible section without building a full preview."""

    def located(point: dict[str, Any]) -> bool:
        return all(
            isinstance(point.get(key), (int, float))
            and math.isfinite(point[key])
            for key in ("lat", "lon")
        )

    first = next((p for p in points if located(p)), None)
    last = next((p for p in reversed(points) if located(p)), None)
    previous = None
    for point in points:
        if point.get("route_gap"):
            previous = None
        visible = located(point)
        if visible and privacy_radius_m is not None and first and last:
            visible = (
                haversine(point, first) >= privacy_radius_m
                and haversine(point, last) >= privacy_radius_m
            )
        if visible:
            if previous is not None and point["t"] - previous["t"] <= 60:
                return True
            previous = point
        elif located(point):
            # A located but protected fix is a break; a sensor sample is not.
            previous = None
    return False


def route_preview(points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    segments: list[list[dict[str, Any]]] = []
    segment: list[dict[str, Any]] = []
    previous: dict[str, Any] | None = None
    for point in points:
        located = all(
            isinstance(point.get(key), (int, float))
            and math.isfinite(point[key])
            for key in ("lat", "lon")
        )
        if point.get("route_gap") or (
            located and previous and point["t"] - previous["t"] > 60
        ):
            if len(segment) > 1:
                segments.append(segment)
            segment = []
            previous = None
        if located:
            segment.append(point)
            previous = point
    if len(segment) > 1:
        segments.append(segment)
    # Keep meaningful disconnected sections; never join across redaction or
    # sampling gaps. This is an outline, not an input to metric calculations.
    selected = sorted(
        sorted(enumerate(segments), key=lambda row: -len(row[1]))[:32]
    )
    if not selected:
        return []
    allowance = max(2, 512 // len(selected))
    result: list[dict[str, Any]] = []
    for _, row in selected:
        if result:
            result.append(
                {"t": row[0]["t"], "active": True, "route_gap": True}
            )
        indices = (
            list(range(len(row)))
            if len(row) <= allowance
            else [
                round(index * (len(row) - 1) / (allowance - 1))
                for index in range(allowance)
            ]
        )
        result.extend(
            {
                "t": row[index]["t"],
                "lat": row[index]["lat"],
                "lon": row[index]["lon"],
                "active": True,
            }
            for index in indices
        )
    return result
