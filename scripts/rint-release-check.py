#!/usr/bin/env python3
"""Check Git-visible source files for local artifacts and obvious credentials.

Read-only: includes tracked files even if they now match .gitignore. Reports
paths and issue types, never credential values. This is a working-tree check,
not an audit of Git history or a guarantee that all secrets are detected.
"""

import re
import subprocess
import sys
from pathlib import Path

SAFE_ENV_FILES = {".env.example", ".env.docker.example", ".env.docker.dev", "fittrackee_client/.env.example"}
PRIVATE_PARTS = {".local", "DerivedData", ".device-build", "node_modules"}
PRIVATE_SUFFIXES = {".p12", ".p8", ".mobileprovision", ".ipa", ".xcuserstate"}
PATTERNS = {
    "private key": re.compile(
        rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----"
    ),
    "GitHub credential": re.compile(
        rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b"
    ),
    "AWS access key": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
}


def inspect_file(root: Path, name: str) -> list[str]:
    relative = Path(name)
    path = root / relative
    issues = []
    if not path.exists() and not path.is_symlink():
        return issues
    if (
        PRIVATE_PARTS.intersection(relative.parts)
        or relative.suffix in PRIVATE_SUFFIXES
        or any(part.endswith(".xcarchive") for part in relative.parts)
        or (relative.name.startswith(".env") and name not in SAFE_ENV_FILES)
    ):
        issues.append("private configuration or generated artifact")
    if len(relative.parts) == 1 and relative.suffix.lower() in {
        ".pdf", ".zip", ".tar", ".gz", ".dmg"
    }:
        issues.append("root-level personal document or archive; review exclusion")
    if path.is_symlink():
        if not path.resolve().is_relative_to(root.resolve()):
            issues.append("symlink points outside the repository")
        return issues
    if not path.is_file():
        return issues  # A locally deleted tracked file is not shipped.
    content = path.read_bytes()
    if b"\0" not in content[:8192]:
        for label, pattern in PATTERNS.items():
            if pattern.search(content):
                issues.append(label)
    return issues


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root, check=True, capture_output=True,
    )
    names = sorted(set(result.stdout.decode().split("\0")) - {""})
    findings = [
        (name, issue)
        for name in names
        for issue in inspect_file(root, name)
    ]
    for name, issue in findings:
        print(f"BLOCK: {name}: {issue}")
    if findings:
        print(f"Release source check failed: {len(findings)} finding(s).")
        return 1
    print(f"Release source check passed: {len(names)} Git-visible files.")
    print("Scope: working tree only; inspect history before a first public push.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
