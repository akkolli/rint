import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, call, patch

import jwt
import pytest
from flask import Flask
from time_machine import travel

from fittrackee import db
from fittrackee.constants import ElevationDataSource
from fittrackee.tests.custom_asserts import assert_response
from fittrackee.users.models import (
    BlacklistedToken,
    User,
)
from fittrackee.users.roles import UserRole
from fittrackee.users.utils.tokens import get_user_token
from fittrackee.visibility_levels import VisibilityLevel

from ..mixins import (
    ApiTestCaseMixin,
    TokenMixin,
    UserTaskMixin,
)
from ..utils import jsonify_dict

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0"
)


class TestUserRegistration(ApiTestCaseMixin):
    def test_it_returns_error_if_password_is_too_short(
        self, app: Flask
    ) -> None:
        client = app.test_client()

        response = client.post(
            "/api/auth/register",
            data=json.dumps(
                dict(
                    username=self.random_string(),
                    email=self.random_email(),
                    password=self.random_string(length=7),
                    accepted_policy=True,
                )
            ),
            content_type="application/json",
        )

        self.assert_400(response, "password: 8 characters required\n")

    def test_it_returns_success_if_payload_is_valid(self, app: Flask) -> None:
        client = app.test_client()

        response = client.post(
            "/api/auth/register",
            data=json.dumps(
                dict(
                    username=self.random_string(),
                    email=self.random_email(),
                    password=self.random_string(),
                    accepted_policy=True,
                )
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        assert response.content_type == "application/json"
        data = json.loads(response.data.decode())
        assert data["status"] == "success"
        assert "auth_token" not in data

    def test_it_creates_inactive_user_with_default_values_when_minimal_data_are_provided(  # noqa
        self, app: Flask
    ) -> None:
        client = app.test_client()
        username = self.random_string()

        client.post(
            "/api/auth/register",
            data=json.dumps(
                dict(
                    username=username,
                    email=self.random_email(),
                    password=self.random_string(),
                    accepted_policy=True,
                )
            ),
            content_type="application/json",
        )

        new_user = User.query.filter_by(username=username).one()
        assert new_user.date_format == "MM/dd/yyyy"
        assert new_user.timezone == "Europe/Paris"
        assert new_user.language == "en"
        assert new_user.is_active is False
        assert new_user.role == UserRole.USER.value
        # preferences
        assert new_user.start_elevation_at_zero is True
        assert new_user.use_raw_gpx_speed is False
        assert new_user.use_dark_mode is None
        assert new_user.manually_approves_followers is True
        assert new_user.hide_profile_in_users_directory is True
        assert new_user.workouts_visibility == VisibilityLevel.PRIVATE
        assert new_user.map_visibility == VisibilityLevel.PRIVATE
        assert new_user.analysis_visibility == VisibilityLevel.PRIVATE
        assert new_user.notification_preferences is None
        assert new_user.hr_visibility == VisibilityLevel.PRIVATE
        assert new_user.segments_creation_event == "only_manual"
        assert new_user.split_workout_charts is True
        assert new_user.messages_preferences is None
        assert (
            new_user.missing_elevations_processing == ElevationDataSource.FILE
        )
        assert new_user.calories_visibility == VisibilityLevel.PRIVATE
        assert new_user.media_visibility == VisibilityLevel.PRIVATE

    @pytest.mark.parametrize(
        "text_transformation",
        ["upper", "lower"],
    )
    def test_it_does_not_return_error_if_a_user_already_exists_with_same_email(
        self, app: Flask, user_1: User, text_transformation: str
    ) -> None:
        client = app.test_client()
        response = client.post(
            "/api/auth/register",
            data=json.dumps(
                dict(
                    username=self.random_string(),
                    email=(
                        user_1.email.upper()
                        if text_transformation == "upper"
                        else user_1.email.lower()
                    ),
                    password=self.random_string(),
                    accepted_policy=True,
                )
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        assert response.content_type == "application/json"
        data = json.loads(response.data.decode())
        assert data["status"] == "success"
        assert "auth_token" not in data


class TestUserLogin(ApiTestCaseMixin):
    def test_it_returns_error_if_payload_is_empty(self, app: Flask) -> None:
        client = app.test_client()

        response = client.post(
            "/api/auth/login",
            data=json.dumps(dict()),
            content_type="application/json",
        )

        self.assert_400(response)

    def test_it_returns_error_if_user_does_not_exist(self, app: Flask) -> None:
        client = app.test_client()

        response = client.post(
            "/api/auth/login",
            data=json.dumps(
                dict(email=self.random_email(), password=self.random_string())
            ),
            content_type="application/json",
        )

        self.assert_401(response, "invalid credentials")

    def test_it_returns_error_if_user_account_is_inactive(
        self, app: Flask, inactive_user: User
    ) -> None:
        client = app.test_client()

        response = client.post(
            "/api/auth/login",
            data=json.dumps(
                dict(email=inactive_user.email, password="12345678")
            ),
            content_type="application/json",
        )

        self.assert_401(response, "invalid credentials")

    def test_it_returns_error_if_password_is_invalid(
        self, app: Flask, user_1: User
    ) -> None:
        client = app.test_client()

        response = client.post(
            "/api/auth/login",
            data=json.dumps(
                dict(email=user_1.email, password=self.random_email())
            ),
            content_type="application/json",
        )

        self.assert_401(response, "invalid credentials")

    @pytest.mark.parametrize(
        "text_transformation",
        ["upper", "lower"],
    )
    def test_user_can_login_regardless_username_case(
        self, app: Flask, user_1: User, text_transformation: str
    ) -> None:
        client = app.test_client()

        response = client.post(
            "/api/auth/login",
            data=json.dumps(
                dict(
                    email=(
                        user_1.email.upper()
                        if text_transformation == "upper"
                        else user_1.email.lower()
                    ),
                    password="12345678",
                )
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        assert response.content_type == "application/json"
        data = json.loads(response.data.decode())
        assert data["status"] == "success"
        assert data["message"] == "successfully logged in"
        assert data["auth_token"]


class TestUserProfile(ApiTestCaseMixin, TokenMixin):
    def test_it_returns_error_if_auth_token_is_missing(
        self, app: Flask
    ) -> None:
        client = app.test_client()

        response = client.get("/api/auth/profile")

        self.assert_401(response, "provide a valid auth token")

    def test_it_returns_error_if_auth_token_is_invalid(
        self, app: Flask
    ) -> None:
        client = app.test_client()

        response = client.get(
            "/api/auth/profile", headers=dict(Authorization="Bearer invalid")
        )

        self.assert_invalid_token(response)

    def test_it_returns_error_if_token_is_blacklisted(
        self, app: Flask, user_1: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )
        db.session.add(BlacklistedToken(token=auth_token))
        db.session.commit()

        response = client.get(
            "/api/auth/profile",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_invalid_token(response)

    def test_it_returns_error_if_token_without_jti_is_blacklisted(
        self, app: Flask, user_1: User
    ) -> None:
        client = app.test_client()
        auth_token = self.generate_token_without_jti(app, user_1.id)
        db.session.add(BlacklistedToken(token=auth_token))
        db.session.commit()

        response = client.get(
            "/api/auth/profile",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_invalid_token(response)

    def test_it_returns_user(self, app: Flask, user_1: User) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            "/api/auth/profile",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = assert_response(response, 200, status="success")
        assert data["data"] == jsonify_dict(
            user_1.serialize(current_user=user_1, light=False)
        )

    def test_it_returns_suspended_user(
        self, app: Flask, suspended_user: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, suspended_user.email
        )

        response = client.get(
            "/api/auth/profile",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = assert_response(response, 200, status="success")
        assert data["data"] == jsonify_dict(
            suspended_user.serialize(current_user=suspended_user, light=False)
        )


class TestUserAccountUpdate(ApiTestCaseMixin):
    def test_it_returns_error_if_current_password_is_missing(
        self, app: Flask, user_1: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.patch(
            "/api/auth/profile/edit/account",
            content_type="application/json",
            data=json.dumps(
                dict(
                    email=user_1.email,
                    new_password=self.random_string(),
                )
            ),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_400(response, error_message="current password is missing")

    def test_it_returns_error_if_current_password_is_invalid(
        self, app: Flask, user_1: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.patch(
            "/api/auth/profile/edit/account",
            content_type="application/json",
            data=json.dumps(
                dict(
                    email=user_1.email,
                    password=self.random_string(),
                    new_password=self.random_string(),
                )
            ),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_401(response, error_message="invalid credentials")

    def test_it_only_updates_email_to_confirm_if_new_email_provided(
        self,
        app: Flask,
        user_1: User,
        auth_send_email_mock: MagicMock,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )
        current_email = user_1.email
        new_email = "new.email@example.com"

        response = client.patch(
            "/api/auth/profile/edit/account",
            content_type="application/json",
            data=json.dumps(
                dict(
                    email=new_email,
                    password="12345678",
                )
            ),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert response.status_code == 200
        assert current_email == user_1.email
        assert new_email == user_1.email_to_confirm
        assert user_1.confirmation_token is not None

    def test_it_calls_send_email_for_current_and_new_email_when_new_email_provided(  # noqa
        self,
        app: Flask,
        user_1: User,
        auth_send_email_mock: MagicMock,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )
        new_email = "new.email@example.com"
        expected_token = self.random_string()

        with patch("secrets.token_urlsafe", return_value=expected_token):
            client.patch(
                "/api/auth/profile/edit/account",
                content_type="application/json",
                data=json.dumps(
                    dict(
                        email=new_email,
                        password="12345678",
                    )
                ),
                headers=dict(Authorization=f"Bearer {auth_token}"),
                environ_base={"HTTP_USER_AGENT": USER_AGENT},
            )

        auth_send_email_mock.send.assert_has_calls(
            [
                call(
                    {
                        "language": "en",
                        "email": user_1.email,
                    },
                    {
                        "username": user_1.username,
                        "fittrackee_url": app.config["UI_URL"],
                        "operating_system": "Linux",
                        "browser_name": "Firefox",
                        "new_email_address": new_email,
                    },
                    template="email_update_to_current_email",
                ),
                call(
                    {
                        "language": "en",
                        "email": user_1.email_to_confirm,
                    },
                    {
                        "username": user_1.username,
                        "fittrackee_url": app.config["UI_URL"],
                        "operating_system": "Linux",
                        "browser_name": "Firefox",
                        "email_confirmation_url": (
                            f"{app.config['UI_URL']}/email-update"
                            f"?token={expected_token}"
                        ),
                    },
                    template="email_update_to_new_email",
                ),
            ]
        )

    def test_it_returns_error_if_controls_fail_on_new_password(
        self,
        app: Flask,
        user_1: User,
        auth_send_email_mock: MagicMock,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.patch(
            "/api/auth/profile/edit/account",
            content_type="application/json",
            data=json.dumps(
                dict(
                    email=user_1.email,
                    password="12345678",
                    new_password=self.random_string(length=3),
                )
            ),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_400(response, "password: 8 characters required")

    def test_new_password_is_hashed(
        self,
        app: Flask,
        user_1: User,
        auth_send_email_mock: MagicMock,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )
        new_password = self.random_string()

        response = client.patch(
            "/api/auth/profile/edit/account",
            content_type="application/json",
            data=json.dumps(
                dict(
                    email=user_1.email,
                    password="12345678",
                    new_password=new_password,
                )
            ),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert response.status_code == 200
        assert new_password != user_1.password

    def test_it_updates_email_to_confirm_and_password_when_new_email_and_password_provided(  # noqa
        self,
        app: Flask,
        user_1: User,
        auth_send_email_mock: MagicMock,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )
        current_email = user_1.email
        current_hashed_password = user_1.password
        new_email = "new.email@example.com"

        response = client.patch(
            "/api/auth/profile/edit/account",
            content_type="application/json",
            data=json.dumps(
                dict(
                    email=new_email,
                    password="12345678",
                    new_password=self.random_string(),
                )
            ),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert_response(
            response, 200, status="success", message="user account updated"
        )
        assert user_1.email == current_email
        assert user_1.email_to_confirm == new_email
        assert user_1.password != current_hashed_password


class TestPasswordResetRequest(ApiTestCaseMixin):
    def test_it_returns_error_on_empty_payload(self, app: Flask) -> None:
        client = app.test_client()

        response = client.post(
            "/api/auth/password/reset-request",
            data=json.dumps(dict()),
            content_type="application/json",
        )

        self.assert_400(response)

    def test_it_returns_error_on_invalid_payload(self, app: Flask) -> None:
        client = app.test_client()

        response = client.post(
            "/api/auth/password/reset-request",
            data=json.dumps(dict(username=self.random_string())),
            content_type="application/json",
        )

        self.assert_400(response)

    def test_it_returns_error_when_email_sending_is_disabled(
        self, app_wo_email_activation: Flask
    ) -> None:
        client = app_wo_email_activation.test_client()

        response = client.post(
            "/api/auth/password/reset-request",
            data=json.dumps(dict(email="test@test.com")),
            content_type="application/json",
        )

        self.assert_404_with_message(
            response, "the requested URL was not found on the server"
        )

    def test_it_requests_password_reset_when_user_exists(
        self, app: Flask, user_1: User, auth_send_email_mock: Mock
    ) -> None:
        client = app.test_client()

        response = client.post(
            "/api/auth/password/reset-request",
            data=json.dumps(dict(email="test@test.com")),
            content_type="application/json",
        )

        assert_response(
            response,
            200,
            status="success",
            message="password reset request processed",
        )

    def test_it_requests_password_reset_when_user_is_suspended(
        self, app: Flask, suspended_user: User, auth_send_email_mock: Mock
    ) -> None:
        client = app.test_client()

        response = client.post(
            "/api/auth/password/reset-request",
            data=json.dumps(dict(email=suspended_user.email)),
            content_type="application/json",
        )

        assert_response(
            response,
            200,
            status="success",
            message="password reset request processed",
        )

    def test_it_calls_send_email_for_password_reset_request_when_user_exists(
        self, app: Flask, user_1: User, auth_send_email_mock: Mock
    ) -> None:
        client = app.test_client()
        token = self.random_string()

        with patch("jwt.encode", return_value=token):
            client.post(
                "/api/auth/password/reset-request",
                data=json.dumps(dict(email="test@test.com")),
                content_type="application/json",
                environ_base={"HTTP_USER_AGENT": USER_AGENT},
            )

        auth_send_email_mock.send.assert_called_once_with(
            {
                "language": "en",
                "email": user_1.email,
            },
            {
                "expiration_delay": "a minute",
                "username": user_1.username,
                "password_reset_url": (
                    f"{app.config['UI_URL']}/password-reset?token={token}"
                ),
                "fittrackee_url": app.config["UI_URL"],
                "operating_system": "Linux",
                "browser_name": "Firefox",
            },
            template="password_reset_request",
        )

    def test_it_does_not_return_error_when_user_does_not_exist(
        self, app: Flask
    ) -> None:
        client = app.test_client()

        response = client.post(
            "/api/auth/password/reset-request",
            data=json.dumps(dict(email="test@test.com")),
            content_type="application/json",
        )

        assert_response(
            response,
            200,
            status="success",
            message="password reset request processed",
        )

    def test_it_does_not_call_send_email_for_password_reset_request_when_user_does_not_exist(  # noqa
        self, app: Flask, auth_send_email_mock: Mock
    ) -> None:
        client = app.test_client()

        client.post(
            "/api/auth/password/reset-request",
            data=json.dumps(dict(email="test@test.com")),
            content_type="application/json",
        )

        auth_send_email_mock.assert_not_called()


class TestPasswordUpdate(ApiTestCaseMixin):
    def test_it_returns_error_if_payload_is_empty(self, app: Flask) -> None:
        client = app.test_client()

        response = client.post(
            "/api/auth/password/update",
            data=json.dumps(dict()),
            content_type="application/json",
        )

        self.assert_400(response)

    def test_it_returns_error_if_token_is_missing(self, app: Flask) -> None:
        client = app.test_client()

        response = client.post(
            "/api/auth/password/update",
            data=json.dumps(
                dict(
                    password=self.random_string(),
                )
            ),
            content_type="application/json",
        )

        self.assert_400(response)

    def test_it_returns_error_if_password_is_missing(self, app: Flask) -> None:
        client = app.test_client()

        response = client.post(
            "/api/auth/password/update",
            data=json.dumps(
                dict(
                    token=self.random_string(),
                )
            ),
            content_type="application/json",
        )

        self.assert_400(response)

    def test_it_returns_error_if_token_is_invalid(self, app: Flask) -> None:
        token = get_user_token(1)
        client = app.test_client()

        response = client.post(
            "/api/auth/password/update",
            data=json.dumps(
                dict(
                    token=token,
                    password=self.random_string(),
                )
            ),
            content_type="application/json",
        )

        self.assert_401(response, "invalid token, please request a new token")

    def test_it_returns_error_if_token_is_expired(
        self, app: Flask, user_1: User
    ) -> None:
        now = datetime.now(timezone.utc)
        token = get_user_token(user_1.id, password_reset=True)
        client = app.test_client()

        with travel(now + timedelta(seconds=61), tick=False):
            response = client.post(
                "/api/auth/password/update",
                data=json.dumps(
                    dict(
                        token=token,
                        password=self.random_string(),
                    )
                ),
                content_type="application/json",
            )

            self.assert_401(
                response, "invalid token, please request a new token"
            )

    def test_it_returns_error_if_password_is_invalid(
        self, app: Flask, user_1: User
    ) -> None:
        token = get_user_token(user_1.id, password_reset=True)
        client = app.test_client()

        response = client.post(
            "/api/auth/password/update",
            data=json.dumps(
                dict(
                    token=token,
                    password=self.random_string(length=7),
                )
            ),
            content_type="application/json",
        )

        self.assert_400(response, "password: 8 characters required\n")

    def test_it_does_not_send_email_after_error(
        self,
        app: Flask,
        user_1: User,
        auth_send_email_mock: MagicMock,
    ) -> None:
        token = get_user_token(user_1.id, password_reset=True)
        client = app.test_client()

        client.post(
            "/api/auth/password/update",
            data=json.dumps(
                dict(
                    token=token,
                    password=self.random_string(length=7),
                )
            ),
            content_type="application/json",
        )

        auth_send_email_mock.assert_not_called()

    def test_it_updates_password(
        self,
        app: Flask,
        user_1: User,
        auth_send_email_mock: MagicMock,
    ) -> None:
        token = get_user_token(user_1.id, password_reset=True)
        client = app.test_client()

        response = client.post(
            "/api/auth/password/update",
            data=json.dumps(
                dict(
                    token=token,
                    password=self.random_string(),
                )
            ),
            content_type="application/json",
        )

        assert_response(
            response, 200, status="success", message="password updated"
        )

    def test_it_updates_password_when_user_is_suspended(
        self,
        app: Flask,
        suspended_user: User,
        auth_send_email_mock: MagicMock,
    ) -> None:
        token = get_user_token(suspended_user.id, password_reset=True)
        client = app.test_client()

        response = client.post(
            "/api/auth/password/update",
            data=json.dumps(
                dict(
                    token=token,
                    password=self.random_string(),
                )
            ),
            content_type="application/json",
        )

        assert_response(
            response, 200, status="success", message="password updated"
        )

    def test_it_sends_email_for_password_change_after_successful_update(
        self,
        app: Flask,
        user_1: User,
        auth_send_email_mock: MagicMock,
    ) -> None:
        token = get_user_token(user_1.id, password_reset=True)
        client = app.test_client()

        response = client.post(
            "/api/auth/password/update",
            data=json.dumps(
                dict(
                    token=token,
                    password=self.random_string(),
                )
            ),
            content_type="application/json",
            environ_base={"HTTP_USER_AGENT": USER_AGENT},
        )

        assert response.status_code == 200
        auth_send_email_mock.send.assert_called_once_with(
            user_data={
                "language": "en",
                "email": user_1.email,
            },
            email_data={
                "username": user_1.username,
                "fittrackee_url": app.config["UI_URL"],
                "operating_system": "Linux",
                "browser_name": "Firefox",
            },
            template="password_change",
        )

    def test_it_does_not_send_email_for_password_change_when_email_sending_is_disabled(  # noqa
        self,
        app_wo_email_activation: Flask,
        user_1: User,
        auth_send_email_mock: MagicMock,
    ) -> None:
        token = get_user_token(user_1.id, password_reset=True)
        client = app_wo_email_activation.test_client()

        client.post(
            "/api/auth/password/update",
            data=json.dumps(
                dict(
                    token=token,
                    password=self.random_string(),
                )
            ),
            content_type="application/json",
            environ_base={"HTTP_USER_AGENT": USER_AGENT},
        )

        auth_send_email_mock.send.assert_not_called()


class TestEmailUpdateWitUnauthenticatedUser(ApiTestCaseMixin):
    def test_it_returns_error_if_token_is_missing(self, app: Flask) -> None:
        client = app.test_client()

        response = client.post(
            "/api/auth/email/update",
            data=json.dumps(dict()),
            content_type="application/json",
        )

        self.assert_400(response)

    def test_it_returns_error_if_token_is_invalid(self, app: Flask) -> None:
        client = app.test_client()

        response = client.post(
            "/api/auth/email/update",
            data=json.dumps(dict(token=self.random_string())),
            content_type="application/json",
        )

        self.assert_400(response)

    def test_it_does_not_update_email_if_token_mismatches(
        self, app: Flask, user_1: User
    ) -> None:
        user_1.confirmation_token = self.random_string()
        new_email = "new.email@example.com"
        user_1.email_to_confirm = new_email
        client = app.test_client()

        response = client.post(
            "/api/auth/email/update",
            data=json.dumps(dict(token=self.random_string())),
            content_type="application/json",
        )

        self.assert_400(response)

    def test_it_updates_email(self, app: Flask, user_1: User) -> None:
        token = self.random_string()
        user_1.confirmation_token = token
        new_email = "new.email@example.com"
        user_1.email_to_confirm = new_email
        client = app.test_client()

        response = client.post(
            "/api/auth/email/update",
            data=json.dumps(dict(token=token)),
            content_type="application/json",
        )

        assert_response(
            response, 200, status="success", message="email updated"
        )
        assert user_1.email == new_email
        assert user_1.email_to_confirm is None
        assert user_1.confirmation_token is None


class TestConfirmationAccount(ApiTestCaseMixin):
    def test_it_returns_error_if_token_is_missing(self, app: Flask) -> None:
        client = app.test_client()

        response = client.post(
            "/api/auth/account/confirm",
            data=json.dumps(dict()),
            content_type="application/json",
        )

        self.assert_400(response)

    def test_it_returns_error_if_token_is_invalid(self, app: Flask) -> None:
        client = app.test_client()

        response = client.post(
            "/api/auth/account/confirm",
            data=json.dumps(dict(token=self.random_string())),
            content_type="application/json",
        )

        self.assert_400(response)

    def test_it_activates_user_account(
        self, app: Flask, inactive_user: User
    ) -> None:
        token = self.random_string()
        inactive_user.confirmation_token = token
        client = app.test_client()

        response = client.post(
            "/api/auth/account/confirm",
            data=json.dumps(dict(token=token)),
            content_type="application/json",
        )

        assert_response(
            response,
            200,
            status="success",
            message="account confirmation successful",
        )
        assert inactive_user.is_active is True
        assert inactive_user.confirmation_token is None


class TestUserLogout(ApiTestCaseMixin, TokenMixin):
    def test_it_returns_error_when_headers_are_missing(
        self, app: Flask
    ) -> None:
        client = app.test_client()

        response = client.post("/api/auth/logout", headers=dict())

        self.assert_401(response, "provide a valid auth token")

    def test_it_returns_error_when_token_is_invalid(self, app: Flask) -> None:
        client = app.test_client()

        response = client.post(
            "/api/auth/logout", headers=dict(Authorization="Bearer invalid")
        )

        self.assert_401(response)

    def test_it_returns_error_when_token_is_expired(
        self, app: Flask, user_1: User
    ) -> None:
        now = datetime.now(timezone.utc)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )
        with travel(now + timedelta(seconds=61), tick=False):
            response = client.post(
                "/api/auth/logout",
                headers=dict(Authorization=f"Bearer {auth_token}"),
            )

            self.assert_401(response)

    def test_user_can_logout(self, app: Flask, user_1: User) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
            "/api/auth/logout",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert data["status"] == "success"
        assert data["message"] == "successfully logged out"
        assert response.status_code == 200

    def test_suspended_user_can_logout(
        self, app: Flask, suspended_user: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, suspended_user.email
        )

        response = client.post(
            "/api/auth/logout",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert data["status"] == "success"
        assert data["message"] == "successfully logged out"
        assert response.status_code == 200

    def test_token_is_blacklisted_on_logout(
        self, app: Flask, user_1: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        client.post(
            "/api/auth/logout",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        payload = jwt.decode(
            auth_token,
            app.config["SECRET_KEY"],
            algorithms=["HS256"],
        )
        token = BlacklistedToken.query.filter_by(token=auth_token).one()
        assert token.jti == payload["jti"]
        assert token.blacklisted_on is not None

    def test_token_without_jti_is_blacklisted_on_logout(
        self, app: Flask, user_1: User
    ) -> None:
        """
        temporary before all tokens without jti claim are expired
        """
        client = app.test_client()
        auth_token = self.generate_token_without_jti(app, user_1.id)

        client.post(
            "/api/auth/logout",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        token = BlacklistedToken.query.filter_by(token=auth_token).one()
        assert token.jti is None
        assert token.blacklisted_on is not None

    def test_it_returns_error_if_token_is_already_blacklisted(
        self, app: Flask, user_1: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )
        db.session.add(BlacklistedToken(token=auth_token))
        db.session.commit()

        response = client.post(
            "/api/auth/logout",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_401(response)


class TestDownloadExportDataArchive(UserTaskMixin, ApiTestCaseMixin):
    def test_it_returns_404_when_request_export_does_not_exist(
        self, app: Flask, user_1: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            f"/api/auth/account/export/{self.random_string()}",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_404_with_message(response, "file not found")

    def test_it_returns_404_when_request_export_from_another_user(
        self, app: Flask, user_1: User, user_2: User
    ) -> None:
        archive_file_name = self.random_string()
        self.create_user_data_export_task(
            user_2, progress=100, file_path=archive_file_name
        )
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            f"/api/auth/account/export/{archive_file_name}",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_404_with_message(response, "file not found")

    def test_it_returns_404_when_file_name_does_not_match(
        self, app: Flask, user_1: User
    ) -> None:
        self.create_user_data_export_task(
            user_1, progress=100, file_path=self.random_string()
        )
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            f"/api/auth/account/export/{self.random_string()}",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_404_with_message(response, "file not found")

    def test_it_calls_send_from_directory_if_request_exist(
        self, app: Flask, user_1: User
    ) -> None:
        archive_file_name = self.random_string()
        self.create_user_data_export_task(
            user_1, progress=100, file_path=archive_file_name
        )
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )
        with patch("fittrackee.users.auth.send_from_directory") as mock:
            mock.return_value = "file"

            client.get(
                f"/api/auth/account/export/{archive_file_name}",
                headers=dict(Authorization=f"Bearer {auth_token}"),
            )

        mock.assert_called_once_with(
            app.config["UPLOAD_FOLDER"],
            archive_file_name,
            mimetype="application/zip",
            as_attachment=True,
        )

    def test_suspended_user_can_download_data_export(
        self,
        app: Flask,
        suspended_user: User,
    ) -> None:
        archive_file_name = self.random_string()
        self.create_user_data_export_task(
            suspended_user, progress=100, file_path=archive_file_name
        )
        client, auth_token = self.get_test_client_and_auth_token(
            app, suspended_user.email
        )
        with patch("fittrackee.users.auth.send_from_directory") as mock:
            mock.return_value = "file"

            client.get(
                f"/api/auth/account/export/{archive_file_name}",
                headers=dict(Authorization=f"Bearer {auth_token}"),
            )

        mock.assert_called_once_with(
            app.config["UPLOAD_FOLDER"],
            archive_file_name,
            mimetype="application/zip",
            as_attachment=True,
        )
