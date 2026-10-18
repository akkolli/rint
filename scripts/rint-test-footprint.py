"""Report test-source lines, including fixtures and helpers."""

# ruff: noqa: T201 -- command-line report

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 94_537  # Nonblank source lines before this reduction.
LIMIT = 18_907  # At least an 80% reduction from the same baseline.
DIRECTORIES = (
    "fittrackee/tests",
    "fittrackee_client/tests",
    "tests_rint",
    "scripts/tests",
    "apple/Tests",
    "e2e",
)
EXTENSIONS = {".py", ".ts", ".swift", ".js", ".vue"}


def main() -> int:
    total = 0
    for directory in DIRECTORIES:
        count = sum(
            sum(bool(line.strip()) for line in path.read_text().splitlines())
            for path in (ROOT / directory).rglob("*")
            if path.is_file() and path.suffix in EXTENSIONS
        )
        total += count
        print(f"{directory}: {count:,}")
    print(f"Total: {total:,} nonblank lines (comments and fixtures included)")
    print(f"Reduction: {100 * (1 - total / BASELINE):.2f}% from {BASELINE:,}")
    print(f"Budget: {LIMIT:,} lines")
    return int(total > LIMIT)


if __name__ == "__main__":
    raise SystemExit(main())
