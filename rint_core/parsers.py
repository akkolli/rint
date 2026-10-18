"""Read original recordings without requiring a route or dropping sensors."""

import io
from bisect import bisect_right
from datetime import datetime, timezone
from typing import Any

import fitdecode
from lxml import etree


def date(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return (
        parsed.replace(tzinfo=timezone.utc)
        if parsed.tzinfo is None
        else parsed.astimezone(timezone.utc)
    )


def scalar(element: Any, *names: str) -> float | None:
    for name in names:
        matches = element.xpath(f'.//*[local-name()="{name}"]/text()')
        if matches:
            try:
                return float(matches[0])
            except ValueError:
                continue
    return None


def xml_recording(content: bytes, extension: str) -> dict[str, Any]:
    root = etree.fromstring(
        content, etree.XMLParser(resolve_entities=False, no_network=True)
    )
    if root.getroottree().docinfo.doctype:
        raise ValueError("XML documents with a DTD are not supported.")
    raw: list[dict[str, Any]] = []
    laps: list[dict[str, Any]] = []
    nodes = root.xpath(
        '//*[local-name()="trkpt"]'
        if extension == "gpx"
        else '//*[local-name()="Trackpoint"]'
    )
    for node in nodes:
        times = node.xpath(
            './/*[local-name()="time" or local-name()="Time"]/text()'
        )
        if not times:
            continue
        p: dict[str, Any] = {"timestamp": date(times[0])}
        if extension == "gpx":
            if node.get("lat") is not None and node.get("lon") is not None:
                p.update(
                    lat=float(node.get("lat")), lon=float(node.get("lon"))
                )
        else:
            p.update(
                lat=scalar(node, "LatitudeDegrees"),
                lon=scalar(node, "LongitudeDegrees"),
                d=scalar(node, "DistanceMeters"),
            )
        p.update(
            heart_rate=scalar(node, "hr", "Value"),
            cadence=scalar(node, "cad", "Cadence", "RunCadence"),
            power=scalar(node, "power", "watts", "Watts"),
            elevation=scalar(node, "ele", "AltitudeMeters"),
        )
        raw.append(p)
    if not raw:
        raise ValueError(
            (
                "The file contains no timestamped samples. Original files are "
                "retained for review."
            )
        )
    origin = min(p["timestamp"] for p in raw)
    for p in raw:
        p["t"] = (p.pop("timestamp") - origin).total_seconds()
    if extension == "tcx":
        for node in root.xpath('//*[local-name()="Lap"]'):
            if node.get("StartTime"):
                start = (date(node.get("StartTime")) - origin).total_seconds()
                duration = scalar(node, "TotalTimeSeconds")
                if duration:
                    laps.append({"start": start, "end": start + duration})
    return {
        "version": 1,
        "started_at": origin.isoformat(),
        "points": raw,
        "laps": laps,
    }


def fit_recording(content: bytes) -> dict[str, Any]:
    raw, laps, events = [], [], []
    with fitdecode.FitReader(io.BytesIO(content)) as reader:
        for frame in reader:
            if not isinstance(frame, fitdecode.FitDataMessage):
                continue
            values = {field.name: field.value for field in frame.fields}
            timestamp = values.get("timestamp")
            if frame.name == "record" and timestamp:
                p = {
                    "timestamp": timestamp,
                    "d": values.get("distance"),
                    "heart_rate": values.get("heart_rate"),
                    "cadence": values.get("cadence"),
                    "power": values.get("power"),
                    "elevation": values.get(
                        "enhanced_altitude", values.get("altitude")
                    ),
                }
                if (
                    values.get("position_lat") is not None
                    and values.get("position_long") is not None
                ):
                    p.update(
                        lat=values["position_lat"] * 180 / 2**31,
                        lon=values["position_long"] * 180 / 2**31,
                    )
                raw.append(p)
            elif (
                frame.name == "event"
                and timestamp
                and values.get("event") == "timer"
            ):
                events.append((timestamp, str(values.get("event_type"))))
            elif (
                frame.name == "lap" and values.get("start_time") and timestamp
            ):
                laps.append((values["start_time"], timestamp))
    if not raw:
        raise ValueError(
            "The FIT file contains no timestamped record messages."
        )
    origin = min([p["timestamp"] for p in raw] + [t for t, _ in events])
    ordered = sorted(events)
    active = True
    index = 0
    for p in sorted(raw, key=lambda p: p["timestamp"]):
        while index < len(ordered) and ordered[index][0] <= p["timestamp"]:
            active = ordered[index][1] in ("start", "begin")
            index += 1
        p["active"] = active
        p["t"] = (p.pop("timestamp") - origin).total_seconds()
    # Explicit boundary samples keep pauses accurate even when the device stops
    # sampling.
    timeline = sorted(raw, key=lambda p: p["t"])
    times = [p["t"] for p in timeline]
    for timestamp, kind in events:
        t = (timestamp - origin).total_seconds()
        previous = bisect_right(times, t) - 1
        d = (
            timeline[previous].get("d")
            if previous >= 0
            else (0 if kind in ("start", "begin") else None)
        )
        raw.append({"t": t, "d": d, "active": kind in ("start", "begin")})
    return {
        "version": 1,
        "started_at": origin.isoformat(),
        "points": raw,
        "laps": [
            {
                "start": (a - origin).total_seconds(),
                "end": (b - origin).total_seconds(),
            }
            for a, b in laps
        ],
    }


def parse_recording(content: bytes, extension: str) -> dict[str, Any]:
    extension = extension.lower().lstrip(".")
    if extension == "fit":
        return fit_recording(content)
    if extension in ("gpx", "tcx"):
        return xml_recording(content, extension)
    raise ValueError("Supported recordings are FIT, GPX and TCX.")
