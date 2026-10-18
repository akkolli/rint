import json
import os
import time
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union
from urllib.parse import parse_qs
from uuid import uuid4

import jwt
from flask import Flask
from flask.testing import FlaskClient
from geoalchemy2.shape import to_shape
from shapely import to_geojson
from shapely.geometry.multilinestring import MultiLineString
from urllib3.util import parse_url
from werkzeug.datastructures import FileStorage
from werkzeug.test import TestResponse

from fittrackee import db
from fittrackee.comments.models import Comment
from fittrackee.media.models import Media
from fittrackee.oauth2.client import create_oauth2_client
from fittrackee.oauth2.models import OAuth2Client, OAuth2Token
from fittrackee.reports.models import Report, ReportAction
from fittrackee.users.models import (
    User,
    UserTask,
)
from fittrackee.utils import encode_uuid
from fittrackee.workouts.models import Workout

from .custom_asserts import (
    assert_errored_response,
    assert_oauth_errored_response,
)
from .utils import (
    TEST_OAUTH_CLIENT_METADATA,
    get_date_string,
    random_email,
    random_int,
    random_string,
    random_uri,
)

if TYPE_CHECKING:
    from geoalchemy2.elements import WKBElement


class RandomMixin:
    @staticmethod
    def random_string(
        length: Optional[int] = None,
        prefix: Optional[str] = None,
        suffix: Optional[str] = None,
    ) -> str:
        return random_string(length, prefix, suffix)

    @staticmethod
    def random_uri(scheme: str = "https://", tld: str = ".social") -> str:
        return random_uri(scheme, tld)

    @staticmethod
    def random_email() -> str:
        return random_email()

    @staticmethod
    def random_int(min_value: int = 0, max_value: int = 999999) -> int:
        return random_int(min_value, max_value)

    @staticmethod
    def random_short_id() -> str:
        return encode_uuid(uuid4())

    @staticmethod
    def get_date_string(
        *,
        date_format: Optional[str] = None,
        date: Optional[datetime] = None,
    ) -> str:
        return get_date_string(
            date_format if date_format else "%a, %d %b %Y %H:%M:%S GMT", date
        )


class OAuth2Mixin(RandomMixin):
    @staticmethod
    def create_oauth2_client(
        user: User,
        metadata: Optional[Dict] = None,
        scope: Optional[str] = None,
    ) -> OAuth2Client:
        client_metadata = (
            TEST_OAUTH_CLIENT_METADATA if metadata is None else metadata
        )
        if scope is not None:
            client_metadata["scope"] = scope
        oauth_client = create_oauth2_client(client_metadata, user)
        db.session.add(oauth_client)
        db.session.commit()
        return oauth_client

    def create_oauth2_token(
        self,
        oauth_client: OAuth2Client,
        issued_at: Optional[int] = None,
        access_token_revoked_at: Optional[int] = 0,
        expires_in: Optional[int] = 1000,
    ) -> OAuth2Token:
        issued_at = issued_at if issued_at else int(time.time())
        token = OAuth2Token(
            client_id=oauth_client.client_id,
            access_token=self.random_string(),
            refresh_token=self.random_string(),
            issued_at=issued_at,
            access_token_revoked_at=access_token_revoked_at,
            expires_in=expires_in,
        )
        db.session.add(token)
        db.session.commit()
        return token


class ApiTestCaseMixin(OAuth2Mixin, RandomMixin):
    @staticmethod
    def get_test_client_and_auth_token(
        app: Flask, user_email: str
    ) -> Tuple[FlaskClient, str]:
        client = app.test_client()
        resp_login = client.post(
            "/api/auth/login",
            data=json.dumps(
                dict(
                    email=user_email,
                    password="12345678",
                )
            ),
            content_type="application/json",
        )
        auth_token = json.loads(resp_login.data.decode())["auth_token"]
        return client, auth_token

    @staticmethod
    def authorize_client(
        client: FlaskClient,
        oauth_client: OAuth2Client,
        auth_token: str,
        scope: Optional[str] = None,
        code_challenge: Optional[Dict] = None,
    ) -> Union[List[str], str]:
        if code_challenge is None:
            code_challenge = {}
        response = client.post(
            "/api/oauth/authorize",
            data={
                "client_id": oauth_client.client_id,
                "confirm": True,
                "response_type": "code",
                "scope": "read" if not scope else scope,
                **code_challenge,
            },
            headers=dict(
                Authorization=f"Bearer {auth_token}",
                content_type="multipart/form-data",
            ),
        )
        data = json.loads(response.data.decode())
        parsed_url = parse_url(data["redirect_url"])
        code = parse_qs(parsed_url.query).get("code", "")
        return code

    def create_oauth2_client_and_issue_token(
        self, app: Flask, user: User, scope: Optional[str] = None
    ) -> Tuple[FlaskClient, OAuth2Client, str, str]:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user.email
        )
        oauth_client = self.create_oauth2_client(user, scope=scope)
        code = self.authorize_client(
            client, oauth_client, auth_token, scope=scope
        )
        response = client.post(
            "/api/oauth/token",
            data={
                "client_id": oauth_client.client_id,
                "client_secret": oauth_client.client_secret,
                "grant_type": "authorization_code",
                "code": code,
            },
            headers=dict(content_type="multipart/form-data"),
        )
        data = json.loads(response.data.decode())
        return client, oauth_client, data.get("access_token"), auth_token

    @staticmethod
    def assert_400(
        response: TestResponse,
        error_message: Optional[str] = "invalid payload",
        status: Optional[str] = "error",
    ) -> Dict:
        return assert_errored_response(
            response, 400, error_message=error_message, status=status
        )

    @staticmethod
    def assert_401(
        response: TestResponse,
        error_message: Optional[str] = "provide a valid auth token",
    ) -> Dict:
        return assert_errored_response(
            response, 401, error_message=error_message
        )

    @staticmethod
    def assert_403(
        response: TestResponse,
        error_message: Optional[str] = "you do not have permissions",
    ) -> Dict:
        return assert_errored_response(response, 403, error_message)

    @staticmethod
    def assert_404(response: TestResponse) -> Dict:
        return assert_errored_response(response, 404, status="not found")

    @staticmethod
    def assert_404_with_entity(response: TestResponse, entity: str) -> Dict:
        error_message = f"{entity} does not exist"
        return assert_errored_response(
            response, 404, error_message=error_message, status="not found"
        )

    @staticmethod
    def assert_404_with_message(
        response: TestResponse, error_message: str
    ) -> Dict:
        return assert_errored_response(
            response, 404, error_message=error_message, status="not found"
        )

    @staticmethod
    def assert_413(
        response: TestResponse,
        error_message: Optional[str] = None,
        match: Optional[str] = None,
    ) -> Dict:
        return assert_errored_response(
            response,
            413,
            error_message=error_message,
            status="fail",
            match=match,
        )

    @staticmethod
    def assert_500(
        response: TestResponse,
        error_message: Optional[str] = (
            "error, please try again or contact the administrator"
        ),
        status: Optional[str] = "error",
    ) -> Dict:
        return assert_errored_response(
            response, 500, error_message=error_message, status=status
        )

    @staticmethod
    def assert_unsupported_grant_type(response: TestResponse) -> Dict:
        return assert_oauth_errored_response(
            response, 400, error="unsupported_grant_type"
        )

    @staticmethod
    def assert_invalid_client(response: TestResponse) -> Dict:
        return assert_oauth_errored_response(
            response,
            400,
            error="invalid_client",
        )

    @staticmethod
    def assert_invalid_grant(
        response: TestResponse, error_description: Optional[str] = None
    ) -> Dict:
        return assert_oauth_errored_response(
            response,
            400,
            error="invalid_grant",
            error_description=error_description,
        )

    @staticmethod
    def assert_invalid_request(
        response: TestResponse, error_description: Optional[str] = None
    ) -> Dict:
        return assert_oauth_errored_response(
            response,
            400,
            error="invalid_request",
            error_description=error_description,
        )

    @staticmethod
    def assert_invalid_token(response: TestResponse) -> Dict:
        return assert_oauth_errored_response(
            response,
            401,
            error="invalid_token",
            error_description=(
                "The access token provided is expired, revoked, malformed, "
                "or invalid for other reasons."
            ),
        )

    @staticmethod
    def assert_return_not_found(
        url: str, client: FlaskClient, auth_token: str, message: str
    ) -> None:
        response = client.post(
            url,
            content_type="application/json",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert response.status_code == 404
        data = json.loads(response.data.decode())
        assert data["status"] == "not found"
        assert data["message"] == message

    def assert_return_user_not_found(
        self, url: str, client: FlaskClient, auth_token: str
    ) -> None:
        self.assert_return_not_found(
            url, client, auth_token, "user does not exist"
        )


class ReportMixin(RandomMixin):
    def create_report(
        self,
        *,
        reporter: User,
        reported_object: Union[Comment, User, Workout],
        note: Optional[str] = None,
    ) -> Report:
        report = Report(
            note=note if note else self.random_string(),
            reported_by=reporter.id,
            reported_object=reported_object,
        )
        db.session.add(report)
        db.session.commit()
        return report

    def create_user_report(self, reporter: User, user: User) -> Report:
        return self.create_report(reporter=reporter, reported_object=user)

    @staticmethod
    def create_report_action(
        moderator: User,
        user: User,
        report_id: int,
        *,
        action_type: Optional[str] = None,
        comment_id: Optional[int] = None,
        workout_id: Optional[int] = None,
    ) -> ReportAction:
        report_action = ReportAction(
            moderator_id=moderator.id,
            action_type=action_type if action_type else "user_suspension",
            comment_id=(
                comment_id
                if (
                    comment_id
                    and action_type
                    and action_type.startswith("comment_")
                )
                else None
            ),
            report_id=report_id,
            user_id=user.id,
            workout_id=(
                workout_id
                if (
                    workout_id
                    and action_type
                    and action_type.startswith("workout_")
                )
                else None
            ),
        )
        db.session.add(report_action)
        db.session.commit()
        return report_action

    def create_report_comment_action(
        self,
        admin: User,
        user: User,
        comment: Comment,
        action_type: str = "comment_suspension",
    ) -> ReportAction:
        report_action = ReportAction(
            action_type=action_type,
            moderator_id=admin.id,
            comment_id=comment.id,
            report_id=self.create_report(
                reporter=admin, reported_object=comment
            ).id,
            user_id=user.id,
        )
        db.session.add(report_action)
        comment.suspended_at = (
            datetime.now(timezone.utc)
            if action_type == "comment_suspension"
            else None
        )
        return report_action


class UserTaskMixin:
    @staticmethod
    def create_user_data_export_task(
        user: "User",
        *,
        created_at: Optional[datetime] = None,
        progress: int = 0,
        errored: bool = False,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        message_id: Optional[str] = None,
    ) -> "UserTask":
        data_export_task = UserTask(
            user_id=user.id,
            created_at=created_at,
            task_type="user_data_export",
        )
        data_export_task.progress = progress
        data_export_task.errored = errored
        data_export_task.file_path = file_path
        data_export_task.file_size = file_size
        data_export_task.message_id = message_id
        db.session.add(data_export_task)
        db.session.commit()
        return data_export_task


class ImageMixin:
    @staticmethod
    def get_image_content(
        app: "Flask", file_name: str = "image_without_exif.png"
    ) -> BytesIO:
        file_path = os.path.join(app.root_path, f"tests/files/{file_name}")
        with open(file_path, "rb") as image_file:
            return BytesIO(image_file.read())

    def get_image_file_storage(
        self, app: "Flask", file_name: str = "image_without_exif.png"
    ) -> "FileStorage":
        return FileStorage(
            filename="profile.png",
            stream=self.get_image_content(app, file_name),
        )


class EquipmentMixin:
    pass


class GeometryMixin:
    @staticmethod
    def get_geojson_from_geom(geometry: "WKBElement") -> Dict:
        return json.loads(to_geojson(to_shape(geometry)))

    @staticmethod
    def get_multilinestring_geojson_from_geom(
        geometries: List["WKBElement"],
    ) -> Dict:
        line_strings = [to_shape(geometry) for geometry in geometries]
        return json.loads(to_geojson(MultiLineString(line_strings)))


class MediaMixin:
    @staticmethod
    def create_media(
        user: "User",
        *,
        file_name: Optional[str] = None,
        file_size: int = 1000,
        workout_id: Optional[int] = None,
        description: str = "",
        with_coordinates: bool = False,
    ) -> "Media":
        if not file_name:
            image_name = uuid4().hex
            file_name = f"{image_name}.jpg"
            thumbnail = f"{image_name}.thumbnail.jpg"
        else:
            image_name, extension = file_name.split()
            thumbnail = f"{image_name}.thumbnail.{extension}"
        media = Media(
            user_id=user.id,
            file_name=file_name,
            file_size=file_size,
            file_content_type="image/jpeg",
        )
        db.session.add(media)
        media.workout_id = workout_id
        media.description = description
        media.meta = {
            "coordinates": {
                "latitude": 45.755833333333335,
                "longitude": 4.8308333333333335,
            }
            if with_coordinates
            else None,
            "thumbnail": {"file_name": thumbnail, "file_size": 10},
        }
        db.session.commit()
        return media

    def create_and_store_media(
        self, app: "Flask", user: "User", workout_id: Optional[int] = None
    ) -> Tuple["Media", str, str]:
        media = self.create_media(user, workout_id=workout_id)
        os.makedirs(
            os.path.join(app.config["UPLOAD_FOLDER"], "media", str(user.id)),
            exist_ok=True,
        )
        expected_paths = []
        for path in [media.file_path, media.thumbnail_file_path]:
            expected_path = os.path.join(app.config["UPLOAD_FOLDER"], path)
            with open(expected_path, "w") as f:
                f.write("image_content")
            expected_paths.append(expected_path)
        return media, expected_paths[0], expected_paths[1]


class TokenMixin:
    @staticmethod
    def generate_token_without_jti(app: "Flask", user_id: int) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "exp": now + timedelta(hours=1),
            "iat": now,
            "sub": str(user_id),
        }
        return jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")

    @staticmethod
    def decode_token(app: "Flask", auth_token: str) -> Dict:
        return jwt.decode(
            auth_token,
            app.config["SECRET_KEY"],
            algorithms=["HS256"],
        )
