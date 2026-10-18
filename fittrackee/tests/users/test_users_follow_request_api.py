from datetime import datetime, timezone

from flask import Flask
from flask.testing import FlaskClient

from fittrackee.tests.custom_asserts import assert_response
from fittrackee.users.models import FollowRequest, User

from ..mixins import ApiTestCaseMixin
from ..utils import random_string


class FollowRequestTestCase(ApiTestCaseMixin):
    def assert_it_returns_follow_request_not_found(
        self,
        client: FlaskClient,
        auth_token: str,
        user_name: str,
        action: str,
    ) -> None:
        url = f"/api/follow-requests/{user_name}/{action}"
        self.assert_return_not_found(
            url, client, auth_token, "Follow request does not exist."
        )

    @staticmethod
    def assert_it_returns_follow_request_already_processed(
        client: FlaskClient,
        auth_token: str,
        user_name: str,
        action: str,
    ) -> None:
        url = f"/api/follow-requests/{user_name}/{action}"
        response = client.post(
            url,
            content_type="application/json",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = assert_response(response, 400, status="error")
        assert data["message"] == (
            f"Follow request from user '{user_name}' already {action}ed."
        )

    @staticmethod
    def assert_it_returns_follow_request_processed(
        client: FlaskClient,
        auth_token: str,
        user_name: str,
        action: str,
    ) -> None:
        url = f"/api/follow-requests/{user_name}/{action}"
        response = client.post(
            url,
            content_type="application/json",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = assert_response(response, 200, status="success")
        assert data["message"] == (
            f"Follow request from user '{user_name}' is {action}ed."
        )


class TestAcceptFollowRequest(FollowRequestTestCase):
    def test_it_returns_error_if_user_is_not_authenticated(
        self, app: Flask, user_1: User
    ) -> None:
        client = app.test_client()

        response = client.post(
            f"/api/follow-requests/{user_1.username}/accept",
            content_type="application/json",
        )

        self.assert_401(response)

    def test_it_returns_error_if_user_is_suspended(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
        follow_request_from_user_2_to_user_1: FollowRequest,
    ) -> None:
        user_1.suspended_at = datetime.now(timezone.utc)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
            f"/api/follow-requests/{user_1.username}/accept",
            content_type="application/json",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )
        self.assert_403(response)

    def test_it_raises_error_if_target_user_does_not_exist(
        self,
        app: Flask,
        user_1: User,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        self.assert_return_user_not_found(
            f"/api/follow-requests/{random_string()}/accept",
            client,
            auth_token,
        )

    def test_it_raises_error_if_follow_request_does_not_exist(
        self, app: Flask, user_1: User, user_2: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        self.assert_it_returns_follow_request_not_found(
            client, auth_token, user_2.username, "accept"
        )

    def test_it_raises_error_if_follow_request_already_accepted(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
        follow_request_from_user_2_to_user_1: FollowRequest,
    ) -> None:
        follow_request_from_user_2_to_user_1.updated_at = datetime.now(
            timezone.utc
        )
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        self.assert_it_returns_follow_request_already_processed(
            client, auth_token, user_2.username, "accept"
        )

    def test_it_accepts_follow_request(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
        follow_request_from_user_2_to_user_1: FollowRequest,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        self.assert_it_returns_follow_request_processed(
            client, auth_token, user_2.username, "accept"
        )


class TestRejectFollowRequest(FollowRequestTestCase):
    def test_it_returns_error_if_user_is_not_authenticated(
        self, app: Flask, user_1: User
    ) -> None:
        client = app.test_client()

        response = client.post(
            f"/api/follow-requests/{user_1.username}/reject",
            content_type="application/json",
        )

        self.assert_401(response)

    def test_it_returns_error_if_user_is_suspended(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
        follow_request_from_user_2_to_user_1: FollowRequest,
    ) -> None:
        user_1.suspended_at = datetime.now(timezone.utc)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
            f"/api/follow-requests/{user_1.username}/reject",
            content_type="application/json",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )
        self.assert_403(response)

    def test_it_raises_error_if_target_user_does_not_exist(
        self,
        app: Flask,
        user_1: User,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        self.assert_return_user_not_found(
            f"/api/follow-requests/{random_string()}/reject",
            client,
            auth_token,
        )

    def test_it_raises_error_if_follow_request_does_not_exist(
        self, app: Flask, user_1: User, user_2: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        self.assert_it_returns_follow_request_not_found(
            client, auth_token, user_2.username, "reject"
        )

    def test_it_raises_error_if_follow_request_already_rejected(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
        follow_request_from_user_2_to_user_1: FollowRequest,
    ) -> None:
        follow_request_from_user_2_to_user_1.updated_at = datetime.now(
            timezone.utc
        )
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        self.assert_it_returns_follow_request_already_processed(
            client, auth_token, user_2.username, "reject"
        )

    def test_it_rejects_follow_request(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
        follow_request_from_user_2_to_user_1: FollowRequest,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        self.assert_it_returns_follow_request_processed(
            client, auth_token, user_2.username, "reject"
        )
