"""Generate a private Compose configuration without shared secrets."""

import secrets
from pathlib import Path

destination = Path(".env.rint")
if destination.exists():
    raise SystemExit(
        ".env.rint already exists; edit it to preserve your data."
    )
content = (
    f"APP_SECRET_KEY={secrets.token_hex(32)}\n"
    f"POSTGRES_PASSWORD={secrets.token_hex(24)}\n"
    "UI_URL=http://localhost:5080\n"
    "HOST_APP_PORT=5080\n"
    "RINT_SOURCE_URL=\n"
    "EMAIL_URL=\nSENDER_EMAIL=\n"
)
with destination.open("x") as target:
    destination.chmod(0o600)
    target.write(content)
