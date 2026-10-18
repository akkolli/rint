from typing import cast

from flask import Response, current_app, g, request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from fittrackee import db
from fittrackee.users.models import User


def media_cookie(response: Response) -> Response:
    """Authenticate image requests without credentials in URLs."""
    if request.path == "/api/auth/logout":
        response.delete_cookie("rint_media", path="/media/")
        response.delete_cookie("rint_map", path="/api/workouts/map/")
    else:
        auth_token = getattr(g, "media_auth_token", None)
        if auth_token and response.status_code < 400:
            token = URLSafeTimedSerializer(
                cast("str", current_app.secret_key), salt="media-session"
            ).dumps(auth_token)
            response.set_cookie(
                "rint_media",
                token,
                max_age=86400,
                secure=request.is_secure,
                httponly=True,
                samesite="Lax",
                path="/media/",
            )
            response.set_cookie(
                "rint_map",
                token,
                max_age=86400,
                secure=request.is_secure,
                httponly=True,
                samesite="Lax",
                path="/api/workouts/map/",
            )
    return response


def media_viewer() -> User | None:
    token = request.cookies.get("rint_media") or request.cookies.get(
        "rint_map"
    )
    if not token:
        return None
    try:
        credential = URLSafeTimedSerializer(
            cast("str", current_app.secret_key), salt="media-session"
        ).loads(token, max_age=86400)
        if not isinstance(credential, str):
            return None
        identifier = User.decode_auth_token(credential)
        if not isinstance(identifier, int):
            return None
        user = db.session.get(User, identifier)
        return (
            user if user and user.is_active and not user.suspended_at else None
        )
    except BadSignature:
        return None
