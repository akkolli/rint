"""Bounded Strava ZIP inspection. Never extract user-controlled paths."""

import csv
import gzip
import hashlib
import io
import posixpath
import re
import zipfile
from typing import Any

MAX_MEMBER = 64 * 1024 * 1024
MAX_TOTAL = 2 * 1024 * 1024 * 1024


def members(archive: zipfile.ZipFile) -> set[str]:
    infos = archive.infolist()
    if len(infos) > 100000 or sum(i.file_size for i in infos) > MAX_TOTAL:
        raise ValueError(
            "The archive exceeds the 2 GB expanded-size or 100,000-file limit."
        )
    names = set()
    for info in infos:
        name = info.filename
        if (
            name.startswith("/")
            or ".." in name.split("/")
            or "\\" in name
            or info.flag_bits & 1
        ):
            raise ValueError(
                "The archive contains an unsafe path or an encrypted file."
            )
        if name in names:
            raise ValueError("The archive contains duplicate filenames.")
        names.add(name)
        if info.file_size > MAX_MEMBER:
            raise ValueError(f"{name}: file exceeds the 64 MB limit.")
    return names


def read_member(archive: zipfile.ZipFile, name: str) -> bytes:
    data = archive.read(name)
    if name.lower().endswith(".gz"):
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
            data = stream.read(MAX_MEMBER + 1)
    if len(data) > MAX_MEMBER:
        raise ValueError(f"{name}: expanded recording exceeds 64 MB.")
    return data


def manifest(path: str) -> list[dict[str, Any]]:
    with zipfile.ZipFile(path) as archive:
        names = members(archive)
        csv_names = sorted(
            n
            for n in names
            if posixpath.basename(n).lower() == "activities.csv"
        )
        if not csv_names:
            raise ValueError(
                (
                    "No activities.csv found. Select the ZIP from Strava's "
                    "account data export."
                )
            )
        rows = csv.DictReader(
            io.StringIO(archive.read(csv_names[0]).decode("utf-8-sig"))
        )
        # Strava repeats several headings. The later Distance column is SI
        # metres; the earlier human-readable column may use km or pool units.
        distance_unit = (
            "m" if (rows.fieldnames or []).count("Distance") > 1 else "km"
        )
        result = []
        for index, row in enumerate(rows):
            filename = row.get("Filename", "")
            match = (
                filename
                if filename in names
                else next(
                    (n for n in sorted(names) if n.endswith("/" + filename)),
                    None,
                )
                if filename
                else None
            )
            source = row.get("Activity ID", "")
            photos = sorted(
                n
                for n in names
                if n.lower().endswith((".jpg", ".jpeg", ".png"))
                and source
                and (
                    posixpath.basename(n).split("_")[0] == source
                    or f"/{source}/" in n
                )
            )
            for reference in re.split(r"[;,|\n]", row.get("Media", "") or ""):
                reference = reference.strip()
                if reference in names and reference.lower().endswith(
                    (".jpg", ".jpeg", ".png")
                ):
                    photos.append(reference)
            photos = sorted(set(photos))
            error = None
            digest = None
            if match:
                extension = (
                    match.lower().removesuffix(".gz").rsplit(".", 1)[-1]
                )
                if extension not in ("fit", "gpx", "tcx"):
                    error = (
                        "Unsupported recording format; FIT, GPX and TCX "
                        "are supported."
                    )
                else:
                    try:
                        digest = hashlib.sha256(
                            read_member(archive, match)
                        ).hexdigest()
                    except (OSError, ValueError) as exc:
                        error = str(exc)
            elif filename:
                error = (
                    "The recording referenced by activities.csv is "
                    "missing from this export."
                )
            result.append(
                {
                    "index": index,
                    "source_id": source,
                    "filename": match,
                    "digest": digest,
                    "title": row.get("Activity Name", "Untitled activity"),
                    "sport": row.get("Activity Type", "Workout"),
                    "date": row.get("Activity Date", ""),
                    "description": row.get("Activity Description", ""),
                    "elapsed": row.get("Elapsed Time", "0"),
                    "distance": row.get("Distance", "0"),
                    "distance_unit": distance_unit,
                    "original_metadata": row,
                    "photos": photos,
                    "status": "error" if error else "pending",
                    "error": error,
                }
            )
        if not result:
            raise ValueError("activities.csv contains no activities.")
        return result
