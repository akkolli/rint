#!/usr/bin/env python3
"""Validate iPhone and embedded Watch bundle metadata before installation."""

import argparse
import plistlib
import re
import subprocess
from pathlib import Path


def validate(path: Path) -> dict:
    info = plistlib.loads((path / "Info.plist").read_bytes())
    for key in ("CFBundleShortVersionString", "CFBundleVersion"):
        value = info.get(key, "")
        if not isinstance(value, str) or not re.fullmatch(
            r"\d+(?:\.\d+){0,2}", value
        ):
            raise ValueError(f"{path.name}: missing or invalid {key}")
    for key in (
        "CFBundleExecutable",
        "CFBundleIdentifier",
        "NSHealthShareUsageDescription",
        "NSHealthUpdateUsageDescription",
    ):
        if not info.get(key):
            raise ValueError(f"{path.name}: missing {key}")
    if not (path / info["CFBundleExecutable"]).is_file():
        raise ValueError(f"{path.name}: executable is missing")
    return info


def check_device_profile(path: Path, udid: str) -> None:
    profile_path = path / "embedded.mobileprovision"
    if not profile_path.is_file():
        raise ValueError(f"{path.name}: development profile is missing")
    result = subprocess.run(  # noqa: S603 - fixed executable, no shell
        ["/usr/bin/security", "cms", "-D", "-i", str(profile_path)],
        capture_output=True,
        check=True,
    )
    profile = plistlib.loads(result.stdout)
    if udid not in profile.get("ProvisionedDevices", []):
        raise ValueError(
            f"{path.name}: profile does not include the target device; "
            "rebuild for that device with provisioning registration enabled"
        )


def check_bundle(
    root: Path, phone_udid: str | None = None, watch_udid: str | None = None
) -> None:
    phone = validate(root)
    companions = list((root / "Watch").glob("*.app"))
    if len(companions) != 1:
        raise ValueError("The iPhone bundle must embed exactly one Watch app")
    watch = validate(companions[0])
    for key in ("CFBundleShortVersionString", "CFBundleVersion"):
        if phone[key] != watch[key]:
            raise ValueError(f"Phone and Watch have different {key}")
    if (
        watch.get("WKCompanionAppBundleIdentifier")
        != phone["CFBundleIdentifier"]
    ):
        raise ValueError("The Watch companion identifier does not match")
    if watch.get("WKApplication") is not True:
        raise ValueError("The Watch bundle is not marked as a watchOS app")
    if "workout-processing" not in watch.get("WKBackgroundModes", []):
        raise ValueError("Watch background workout processing is missing")
    if phone_udid:
        check_device_profile(root, phone_udid)
    if watch_udid:
        check_device_profile(companions[0], watch_udid)
    print(  # noqa: T201
        f"Bundle metadata OK: version {phone['CFBundleShortVersionString']}, "
        f"build {phone['CFBundleVersion']}; matching Watch companion."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", type=Path, help="Path to the built Rint.app")
    parser.add_argument("--phone-udid", help="Check phone profile membership")
    parser.add_argument("--watch-udid", help="Check Watch profile membership")
    args = parser.parse_args()
    try:
        check_bundle(args.app, args.phone_udid, args.watch_udid)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Bundle check failed: {error}\n")
