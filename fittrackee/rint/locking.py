from functools import wraps
from typing import Any

from flask import jsonify, request
from sqlalchemy import text

from fittrackee import db


def serialize_import(function: Any) -> Any:
    @wraps(function)
    def wrapped(user: Any, batch_id: Any) -> Any:
        if request.method == "GET":
            return function(user, batch_id)
        # Separate transaction keeps this lock through per-activity commits.
        # Connection rollback releases it on failure or an interrupted request.
        with db.engine.connect() as connection:
            locked = connection.scalar(
                text(
                    (
                        "SELECT "
                        "pg_try_advisory_xact_lock("
                        "hashtextextended(:batch, 0))"
                    )
                ),
                {"batch": batch_id},
            )
            if not locked:
                return jsonify(
                    message=(
                        "This import is already running. Refresh its progress."
                    )
                ), 409
            return function(user, batch_id)

    return wrapped


def serialize_recording(function: Any) -> Any:
    @wraps(function)
    def wrapped(user: Any) -> Any:
        # Identity resolution and enrichment commit as one operation
        # per account, including concurrent phone/background uploads.
        with db.engine.connect() as connection:
            locked = connection.scalar(
                text(
                    "SELECT pg_try_advisory_xact_lock("
                    "hashtextextended(:account, 0))"
                ),
                {"account": f"rint-recording:{user.id}"},
            )
            if not locked:
                return jsonify(
                    message="Another workout is syncing. Retry shortly."
                ), 503
            return function(user)

    return wrapped
