"""Seed synthetic activities in the isolated local development database."""

import json
import math
import secrets
from datetime import datetime, timezone
from pathlib import Path

from fittrackee import create_app, db
from fittrackee.rint.service import create_activity, sport_for
from fittrackee.users.models import User

app = create_app()
if (
    not app.debug
    or "localhost:55432/rint" not in app.config["SQLALCHEMY_DATABASE_URI"]
):
    raise RuntimeError(
        "Demo fixtures are restricted to the project-local database."
    )
with app.app_context():
    user = User.query.filter_by(email="demo@rint.invalid").first()
    if not user:
        password = secrets.token_urlsafe(18)
        user = User("RintDemo", "demo@rint.invalid", password)
        user.is_active = True
        user.accepted_policy_date = datetime.now(timezone.utc)
        db.session.add(user)
        db.session.commit()
        Path(".local/demo.json").write_text(
            json.dumps({"email": user.email, "password": password})
        )
        Path(".local/demo.json").chmod(0o600)
    for index, title in enumerate(
        [
            "Demo · Riverside morning",
            "Demo · Easy miles",
            "Demo · Tempo session",
        ]
    ):
        recording = {
            "started_at": f"2026-10-{8 + index:02}T12:00:00Z",
            "points": [
                {
                    "t": t,
                    "d": t * (3.7 + index * 0.4),
                    "lat": 40.78 + t * 0.00001,
                    "lon": -73.97 + math.sin(t / 300) * 0.003,
                    "heart_rate": 130 + math.sin(t / 150) * 12 + index * 5,
                    "elevation": 20 + math.sin(t / 400) * 8,
                    "cadence": 85 + math.sin(t / 80) * 3,
                }
                for t in range(0, 1801, 5)
            ],
            "laps": [
                {"start": 0, "end": 600, "name": "Warm-up"},
                {"start": 600, "end": 1200, "name": "Steady"},
                {"start": 1200, "end": 1800, "name": "Cool-down"},
            ],
        }
        create_activity(
            user,
            recording,
            source_id=f"demo:{index}",
            original=json.dumps(recording).encode(),
            extension="json",
            title=title,
            sport=sport_for("Run"),
            description="Synthetic activity for local interface testing.",
        )
    # Independent sensor clocks and deliberate gaps exercise linked inspection.
    points = []
    for t in range(0, 1801, 5):
        route = {
            "t": t,
            "d": t * 3.6,
            "elevation": 20 + math.sin(t / 200) * 12,
        }
        if 1000 <= t <= 1020:
            route["route_gap"] = True
        else:
            route.update(
                lat=40.78 + t * 0.000007,
                lon=-73.97 + math.sin(t / 300) * 0.003,
            )
        points.append(route)
        if t < 1800:
            points.append(
                {"t": t + 0.4, "heart_rate": 142 + math.sin(t / 110) * 18}
            )
            if t % 10 == 0 and not 700 <= t <= 770:
                points.append(
                    {"t": t + 1.2, "power": 220 + math.sin(t / 130) * 70}
                )
    recording = {
        "started_at": "2026-10-13T12:00:00Z",
        "points": sorted(points, key=lambda point: point["t"]),
        "laps": [
            {"start": 0, "end": 600, "name": "Warm-up"},
            {"start": 600, "end": 1200, "name": "Hills"},
            {"start": 1200, "end": 1800, "name": "Cool-down"},
        ],
    }
    create_activity(
        user,
        recording,
        source_id="demo:route-intensity",
        original=json.dumps(recording).encode(),
        extension="json",
        title="Demo · Hills & intervals",
        sport=sport_for("Run"),
        description=(
            "Synthetic workout with separate sensor clocks, "
            "a missing power interval and a route privacy break."
        ),
    )
    db.session.commit()
