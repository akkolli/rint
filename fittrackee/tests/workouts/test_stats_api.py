import json

from flask import Flask

from fittrackee.tests.custom_asserts import assert_response
from fittrackee.users.models import User
from fittrackee.workouts.models import Sport, Workout

from ..mixins import ApiTestCaseMixin


class TestGetAllStats(ApiTestCaseMixin):
    def test_it_returns_error_if_user_is_not_authenticated(
        self, app: Flask, user_1: User
    ) -> None:
        client = app.test_client()

        response = client.get("/api/stats/all")

        self.assert_401(response)

    def test_it_returns_error_when_user_is_suspended(
        self, app: Flask, suspended_user: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, suspended_user.email
        )

        response = client.get(
            "/api/stats/all",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_403(response)

    def test_it_returns_all_stats_when_users_have_no_workouts(
        self, app: Flask, user_1_moderator: User, user_2: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )

        response = client.get(
            "/api/stats/all",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert response.status_code == 200
        assert "success" in data["status"]
        assert data["data"]["workouts"] == 0
        assert data["data"]["sports"] == 0
        assert data["data"]["users"] == 2
        assert "uploads_dir_size" in data["data"]

    def test_it_does_not_count_inactive_user(
        self, app: Flask, user_1_moderator: User, inactive_user: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )

        response = client.get(
            "/api/stats/all",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert response.status_code == 200
        assert "success" in data["status"]
        assert data["data"]["workouts"] == 0
        assert data["data"]["sports"] == 0
        assert data["data"]["users"] == 1
        assert "uploads_dir_size" in data["data"]

    def test_it_gets_app_all_stats_with_workouts(
        self,
        app: Flask,
        user_1_moderator: User,
        user_2: User,
        user_3: User,
        sport_1_cycling: Sport,
        sport_2_running: Sport,
        workout_cycling_user_1: Workout,
        workout_cycling_user_2: Workout,
        workout_running_user_1: Workout,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )

        response = client.get(
            "/api/stats/all",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert response.status_code == 200
        assert "success" in data["status"]
        assert data["data"]["workouts"] == 3
        assert data["data"]["sports"] == 2
        assert data["data"]["users"] == 3
        assert "uploads_dir_size" in data["data"]

    def test_it_returns_stats_if_user_has_admin_rights(
        self,
        app: Flask,
        user_1_admin: User,
        sport_1_cycling: Sport,
        workout_cycling_user_1: Workout,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_admin.email
        )

        response = client.get(
            "/api/stats/all",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = assert_response(response, 200, contains={"status": "success"})
        assert data["data"]["workouts"] == 1
        assert data["data"]["sports"] == 1
        assert data["data"]["users"] == 1
        assert "uploads_dir_size" in data["data"]

    def test_it_returns_error_if_user_has_no_moderator_rights(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
        user_3: User,
        sport_1_cycling: Sport,
        sport_2_running: Sport,
        workout_cycling_user_1: Workout,
        workout_cycling_user_2: Workout,
        workout_running_user_1: Workout,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            "/api/stats/all",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_403(response)
