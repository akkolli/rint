import json
import os
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import MagicMock

import pytest
from flask import Flask

from fittrackee import db
from fittrackee.media.models import Media
from fittrackee.reports.models import Report
from fittrackee.tests.custom_asserts import assert_response
from fittrackee.users.models import (
    FollowRequest,
    Notification,
    User,
    UserTask,
)
from fittrackee.users.roles import UserRole
from fittrackee.workouts.models import Sport, Workout

from ..mixins import ApiTestCaseMixin, EquipmentMixin, MediaMixin, ReportMixin
from ..utils import jsonify_dict


class TestGetUserAsUser(ApiTestCaseMixin):
    def test_it_returns_error_if_user_does_not_exist(
        self, app: Flask, user_1: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            "/api/users/not_existing",
            content_type="application/json",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = assert_response(response, 404, contains={"status": "not found"})
        assert "user does not exist" in data["message"]

    def test_it_does_not_get_inactive_user(
        self, app: Flask, user_1: User, inactive_user: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            f"/api/users/{inactive_user.username}",
            content_type="application/json",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = assert_response(response, 404, contains={"status": "not found"})
        assert "user does not exist" in data["message"]

    def test_it_gets_single_user_without_workouts(
        self, app: Flask, user_1: User, user_2: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            f"/api/users/{user_2.username}",
            content_type="application/json",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = assert_response(response, 200, status="success")
        assert len(data["data"]["users"]) == 1
        assert data["data"]["users"][0] == jsonify_dict(
            user_2.serialize(current_user=user_1, light=False)
        )

    def test_it_gets_single_user_with_workouts(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            f"/api/users/{user_2.username}",
            content_type="application/json",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = assert_response(response, 200, status="success")
        assert len(data["data"]["users"]) == 1
        assert data["data"]["users"][0] == jsonify_dict(
            user_2.serialize(current_user=user_1, light=False)
        )

    def test_it_gets_authenticated_user(
        self,
        app: Flask,
        user_1: User,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            f"/api/users/{user_1.username}",
            content_type="application/json",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = assert_response(response, 200, status="success")
        assert len(data["data"]["users"]) == 1
        assert data["data"]["users"][0] == jsonify_dict(
            user_1.serialize(current_user=user_1, light=False)
        )

    def test_it_gets_hidden_user(
        self, app: Flask, user_1: User, user_2: User
    ) -> None:
        user_2.hide_profile_in_users_directory = True
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            f"/api/users/{user_2.username}",
            content_type="application/json",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert response.status_code == 200
        assert data["status"] == "success"
        assert len(data["data"]["users"]) == 1
        user = data["data"]["users"][0]
        assert user == jsonify_dict(
            user_2.serialize(current_user=user_1, light=False)
        )


class TestGetUserAsUnauthenticatedUser(ApiTestCaseMixin):
    def test_it_returns_error_if_user_does_not_exist(
        self, app: Flask, user_1: User
    ) -> None:
        client = app.test_client()

        response = client.get(
            "/api/users/not_existing",
            content_type="application/json",
        )

        data = assert_response(response, 404, contains={"status": "not found"})
        assert "user does not exist" in data["message"]

    def test_it_does_not_get_inactive_user(
        self, app: Flask, user_1_admin: User, inactive_user: User
    ) -> None:
        client = app.test_client()

        response = client.get(
            f"/api/users/{inactive_user.username}",
            content_type="application/json",
        )

        data = assert_response(response, 404, contains={"status": "not found"})
        assert "user does not exist" in data["message"]

    def test_it_gets_single_user_without_workouts(
        self, app: Flask, user_2: User
    ) -> None:
        client = app.test_client()

        response = client.get(
            f"/api/users/{user_2.username}",
            content_type="application/json",
        )

        data = json.loads(response.data.decode())
        assert response.status_code == 200
        assert data["status"] == "success"
        assert len(data["data"]["users"]) == 1
        assert data["data"]["users"][0] == jsonify_dict(
            user_2.serialize(light=False)
        )

    def test_it_gets_single_user_with_workouts(
        self,
        app: Flask,
        user_1: User,
        sport_1_cycling: Sport,
        sport_2_running: Sport,
        workout_cycling_user_1: Workout,
        workout_running_user_1: Workout,
    ) -> None:
        client = app.test_client()

        response = client.get(
            f"/api/users/{user_1.username}",
            content_type="application/json",
        )

        data = json.loads(response.data.decode())
        assert response.status_code == 200
        assert data["status"] == "success"
        assert len(data["data"]["users"]) == 1
        assert data["data"]["users"][0] == jsonify_dict(
            user_1.serialize(light=False)
        )

    def test_it_gets_hidden_user(self, app: Flask, user_1: User) -> None:
        user_1.hide_profile_in_users_directory = True
        client = app.test_client()

        response = client.get(
            f"/api/users/{user_1.username}",
            content_type="application/json",
        )

        data = json.loads(response.data.decode())
        assert response.status_code == 200
        assert data["status"] == "success"
        assert len(data["data"]["users"]) == 1
        user = data["data"]["users"][0]
        assert user == jsonify_dict(user_1.serialize(light=False))


class TestGetUsersAsModerator(ApiTestCaseMixin):
    @pytest.mark.parametrize(
        "input_description, input_params",
        [
            ("without params", ""),
            ("with inactive users", "?with_inactive=true"),
            ("with hidden users", "?with_hidden=true"),
            ("with suspended users", "?with_suspended=true"),
            (
                "all params",
                "?with_hidden=true&with_inactive=true&with_suspended=true",
            ),
        ],
    )
    def test_it_gets_users_list_without_inactive_hidden_or_suspended_users(
        self,
        app: Flask,
        user_1_moderator: User,
        user_2: User,
        inactive_user: User,
        user_3: User,
        user_4: User,
        input_description: str,
        input_params: str,
    ) -> None:
        user_2.hide_profile_in_users_directory = True
        user_4.suspended_at = datetime.now(timezone.utc)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )

        response = client.get(
            f"/api/users{input_params}",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = assert_response(response, 200, contains={"status": "success"})
        assert len(data["data"]["users"]) == 2
        assert data["data"]["users"][0] == jsonify_dict(
            user_1_moderator.serialize(current_user=user_1_moderator)
        )
        assert data["data"]["users"][1] == jsonify_dict(
            user_3.serialize(current_user=user_1_moderator)
        )
        assert data["pagination"] == {
            "has_next": False,
            "has_prev": False,
            "page": 1,
            "pages": 1,
            "total": 2,
        }

    def test_it_gets_following_user_when_profile_is_hidden(
        self,
        app: Flask,
        user_1_moderator: User,
        user_2: User,
        user_3: User,
    ) -> None:
        user_2.hide_profile_in_users_directory = True
        user_3.hide_profile_in_users_directory = True
        user_1_moderator.send_follow_request_to(user_2)
        user_2.approves_follow_request_from(user_1_moderator)
        db.session.commit()
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )

        response = client.get(
            "/api/users?with_following=true",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert response.status_code == 200
        assert data["status"] == "success"
        assert len(data["data"]["users"]) == 2
        assert data["data"]["users"][0] == jsonify_dict(
            user_1_moderator.serialize(current_user=user_1_moderator)
        )
        assert data["data"]["users"][1] == jsonify_dict(
            user_2.serialize(current_user=user_1_moderator)
        )


class TestGetUsersAsUser(ApiTestCaseMixin):
    @pytest.mark.parametrize(
        "input_description, input_params",
        [
            ("without params", ""),
            ("with inactive users", "?with_inactive=true"),
            ("with hidden users", "?with_hidden=true"),
            ("with suspended users", "?with_suspended=true"),
            (
                "all params",
                "?with_hidden=true&with_inactive=true&with_suspended=true",
            ),
        ],
    )
    def test_it_gets_users_list_without_inactive_hidden_or_suspended_users(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
        inactive_user: User,
        user_3: User,
        user_4: User,
        input_description: str,
        input_params: str,
    ) -> None:
        user_2.hide_profile_in_users_directory = True
        user_4.suspended_at = datetime.now(timezone.utc)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            f"/api/users{input_params}",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = assert_response(response, 200, contains={"status": "success"})
        assert len(data["data"]["users"]) == 2
        assert data["data"]["users"][0] == jsonify_dict(
            user_3.serialize(current_user=user_1)
        )
        assert data["data"]["users"][1] == jsonify_dict(
            user_1.serialize(current_user=user_1)
        )
        assert data["pagination"] == {
            "has_next": False,
            "has_prev": False,
            "page": 1,
            "pages": 1,
            "total": 2,
        }

    def test_it_gets_following_user_when_profile_is_hidden(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
        user_3: User,
    ) -> None:
        user_2.hide_profile_in_users_directory = True
        user_3.hide_profile_in_users_directory = True
        user_1.send_follow_request_to(user_2)
        user_2.approves_follow_request_from(user_1)
        db.session.commit()
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            "/api/users?with_following=true",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert response.status_code == 200
        assert data["status"] == "success"
        assert len(data["data"]["users"]) == 2
        assert data["data"]["users"][0] == jsonify_dict(
            user_1.serialize(current_user=user_1)
        )
        assert data["data"]["users"][1] == jsonify_dict(
            user_2.serialize(current_user=user_1)
        )

    def test_it_gets_users_list_with_workouts(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
        user_3: User,
        sport_1_cycling: Sport,
        workout_cycling_user_1: Workout,
        sport_2_running: Sport,
        workout_running_user_1: Workout,
        workout_cycling_user_2: Workout,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            "/api/users",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = assert_response(response, 200, contains={"status": "success"})
        assert len(data["data"]["users"]) == 3
        assert data["data"]["users"][0] == jsonify_dict(
            user_3.serialize(current_user=user_1)
        )

        assert data["data"]["users"][1] == jsonify_dict(
            user_1.serialize(current_user=user_1)
        )
        assert data["data"]["users"][2] == jsonify_dict(
            user_2.serialize(current_user=user_1)
        )
        assert data["pagination"] == {
            "has_next": False,
            "has_prev": False,
            "page": 1,
            "pages": 1,
            "total": 3,
        }


class TestUpdateUser(ReportMixin, ApiTestCaseMixin):
    def test_it_returns_error_if_auth_user_has_no_admin_rights(
        self, app: Flask, user_1: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.patch(
            f"/api/users/{user_1.username}",
            content_type="application/json",
            data=json.dumps(dict(role="admin")),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_403(response)

    @pytest.mark.parametrize("input_role", ["admin", "moderator"])
    def test_it_updates_user_role(
        self, app: Flask, user_1_admin: User, user_2: User, input_role: str
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_admin.email
        )

        response = client.patch(
            f"/api/users/{user_2.username}",
            content_type="application/json",
            data=json.dumps(dict(role=input_role)),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = assert_response(response, 200, contains={"status": "success"})
        assert len(data["data"]["users"]) == 1
        user = data["data"]["users"][0]
        assert user["email"] == user_2.email
        assert user["role"] == UserRole[input_role.upper()].name.lower()

    def test_it_returns_error_when_setting_owner_role_to_user(
        self, app: Flask, user_1_admin: User, user_2: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_admin.email
        )

        response = client.patch(
            f"/api/users/{user_2.username}",
            content_type="application/json",
            data=json.dumps(dict(role="owner")),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_400(
            response, "'owner' can not be set via API, please user CLI instead"
        )

    def test_it_returns_error_when_setting_owner_role_to_moderator(
        self, app: Flask, user_1_admin: User, user_2_moderator: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_admin.email
        )

        response = client.patch(
            f"/api/users/{user_2_moderator.username}",
            content_type="application/json",
            data=json.dumps(dict(role="owner")),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_400(
            response, "'owner' can not be set via API, please user CLI instead"
        )

    def test_it_returns_error_when_setting_owner_role_to_admin(
        self, app: Flask, user_1_admin: User, user_2_admin: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_admin.email
        )

        response = client.patch(
            f"/api/users/{user_2_admin.username}",
            content_type="application/json",
            data=json.dumps(dict(role="owner")),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_400(
            response, "'owner' can not be set via API, please user CLI instead"
        )

    def test_it_returns_error_when_modifying_owner_role(
        self, app: Flask, user_1_owner: User, user_2_admin: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_2_admin.email
        )

        response = client.patch(
            f"/api/users/{user_1_owner.username}",
            content_type="application/json",
            data=json.dumps(dict(role="admin")),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_400(response, "user with owner rights can not be modified")

    def test_it_resets_user_password(
        self,
        app: Flask,
        user_1_admin: User,
        user_2: User,
        users_send_email_mock: MagicMock,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_admin.email
        )
        user_2_password = user_2.password

        response = client.patch(
            f"/api/users/{user_2.username}",
            content_type="application/json",
            data=json.dumps(dict(reset_password=True)),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert response.status_code == 200
        assert user_2.password != user_2_password

    def test_it_activates_user_account(
        self, app: Flask, user_1_admin: User, inactive_user: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_admin.email
        )

        response = client.patch(
            f"/api/users/{inactive_user.username}",
            content_type="application/json",
            data=json.dumps(dict(activate=True)),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = assert_response(response, 200, contains={"status": "success"})
        assert len(data["data"]["users"]) == 1
        user = data["data"]["users"][0]
        assert user["email"] == inactive_user.email
        assert user["is_active"] is True
        assert inactive_user.confirmation_token is None

    def test_it_deactivates_user_account(
        self, app: Flask, user_1_admin: User, user_2: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_admin.email
        )

        response = client.patch(
            f"/api/users/{user_2.username}",
            content_type="application/json",
            data=json.dumps(dict(activate=False)),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = assert_response(response, 200, contains={"status": "success"})
        assert len(data["data"]["users"]) == 1
        user = data["data"]["users"][0]
        assert user["email"] == user_2.email
        assert user["is_active"] is False

    def test_a_user_can_not_deactivate_his_own_user_account(
        self, app: Flask, user_1_admin: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_admin.email
        )

        response = client.patch(
            f"/api/users/{user_1_admin.username}",
            content_type="application/json",
            data=json.dumps(dict(activate=False)),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_403(response)


class TestDeleteUser(
    ApiTestCaseMixin, ReportMixin, EquipmentMixin, MediaMixin
):
    def test_user_with_workout_can_delete_its_own_account(
        self, app: Flask, user_1: User, sport_1_cycling: Sport, gpx_file: str
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )
        client.post(
            "/api/workouts",
            data=dict(
                file=(BytesIO(str.encode(gpx_file)), "example.gpx"),
                data='{"sport_id": 1}',
            ),
            headers=dict(
                content_type="multipart/form-data",
                Authorization=f"Bearer {auth_token}",
            ),
        )

        response = client.delete(
            f"/api/users/{user_1.username}",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert response.status_code == 204
        assert User.query.first() is None

    def test_user_with_media_attachments_can_delete_its_own_account(
        self, app: Flask, user_1: User
    ) -> None:
        _, media_file_path, thumbnail_file_path = self.create_and_store_media(
            app, user_1
        )
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.delete(
            f"/api/users/{user_1.username}",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert response.status_code == 204
        assert User.query.first() is None
        assert Media.query.count() == 0
        assert os.path.isfile(media_file_path) is False
        assert os.path.isfile(thumbnail_file_path) is False

    def test_user_with_export_request_can_delete_its_own_account(
        self, app: Flask, user_1: User, sport_1_cycling: Sport, gpx_file: str
    ) -> None:
        db.session.add(
            UserTask(user_id=user_1.id, task_type="user_data_export")
        )
        db.session.commit()
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )
        client.post(
            "/api/auth/picture",
            data=dict(file=(BytesIO(b"avatar"), "avatar.png")),
            headers=dict(
                content_type="multipart/form-data",
                Authorization=f"Bearer {auth_token}",
            ),
        )

        response = client.delete(
            f"/api/users/{user_1.username}",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert response.status_code == 204
        assert User.query.first() is None

    def test_user_with_reports_can_delete_its_own_account(
        self,
        app: Flask,
        user_1: User,
        user_2_admin: User,
        user_3: User,
        user_4: User,
    ) -> None:
        report_from_user_3 = self.create_report(
            reporter=user_3, reported_object=user_1
        )
        report_from_user_1 = self.create_report(
            reporter=user_1, reported_object=user_4
        )
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )
        client.post(
            "/api/auth/picture",
            data=dict(file=(BytesIO(b"avatar"), "avatar.png")),
            headers=dict(
                content_type="multipart/form-data",
                Authorization=f"Bearer {auth_token}",
            ),
        )

        response = client.delete(
            f"/api/users/{user_1.username}",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert response.status_code == 204
        assert (
            FollowRequest.query.filter_by(followed_user_id=user_1.id).first()
            is None
        )
        assert set(Report.query.all()) == {
            report_from_user_3,
            report_from_user_1,
        }
        assert (
            Notification.query.filter_by(to_user_id=user_2_admin.id).first()
            is not None
        )

    def test_user_can_not_delete_another_user_account(
        self, app: Flask, user_1: User, user_2: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.delete(
            f"/api/users/{user_2.username}",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_403(response)

    def test_moderator_can_not_delete_another_user_account(
        self, app: Flask, user_1_moderator: User, user_2: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )

        response = client.delete(
            f"/api/users/{user_2.username}",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_403(response)

    def test_admin_can_delete_another_user_account(
        self, app: Flask, user_1_admin: User, user_2: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_admin.email
        )
        deleted_user_id = user_2.id

        response = client.delete(
            f"/api/users/{user_2.username}",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert response.status_code == 204
        assert User.query.filter_by(id=deleted_user_id).first() is None

    def test_admin_can_not_delete_owner_account(
        self,
        app: Flask,
        user_1_owner: User,
        user_2_admin: User,
        user_3_admin: User,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_2_admin.email
        )

        response = client.delete(
            f"/api/users/{user_1_owner.username}",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_403(
            response,
            "you can not delete owner account",
        )

    def test_admin_can_not_delete_its_own_account_if_no_other_user_with_admin_rights(  # noqa
        self, app: Flask, user_1_admin: User, user_2: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_admin.email
        )

        response = client.delete(
            f"/api/users/{user_1_admin.username}",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_403(
            response,
            "you can not delete your account, no other user has admin rights",
        )

    def test_owner_can_delete_his_own_account(
        self, app: Flask, user_1_owner: User, user_2_admin: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_owner.email
        )

        response = client.delete(
            f"/api/users/{user_1_owner.username}",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert response.status_code == 204
        assert User.query.filter_by(id=user_1_owner.id).first() is None

    def test_owner_can_not_delete_his_own_account_if_no_other_user_with_admin_rights(  # noqa
        self, app: Flask, user_1_owner: User, user_2: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_owner.email
        )

        response = client.delete(
            f"/api/users/{user_1_owner.username}",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_403(
            response,
            "you can not delete your account, no other user has admin rights",
        )


class TestBlockUser(ApiTestCaseMixin):
    route = "/api/users/{username}/block"

    def test_it_returns_error_if_user_is_not_authenticated(
        self, app: Flask, user_1: User
    ) -> None:
        client = app.test_client()

        response = client.post(
            self.route.format(username=user_1.username),
            content_type="application/json",
        )

        self.assert_401(response)

    def test_it_returns_error_when_user_does_not_exist(
        self, app: Flask, user_1: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
            self.route.format(username=self.random_string()),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_404_with_entity(response, "user")

    def test_it_returns_error_when_user_is_suspended(
        self, app: Flask, user_1: User, suspended_user: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, suspended_user.email
        )

        response = client.post(
            self.route.format(username=user_1.username),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_403(response)

    def test_it_blocks_user(
        self, app: Flask, user_1: User, user_2: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
            self.route.format(username=user_2.username),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert_response(response, 200, status="success")
        assert user_2.is_blocked_by(user_1)

    def test_it_removes_follow_request_if_exists(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
        follow_request_from_user_2_to_user_1: FollowRequest,
    ) -> None:
        user_1.approves_follow_request_from(user_2)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
            self.route.format(username=user_2.username),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert_response(response, 200, status="success")
        assert user_1.is_followed_by(user_2) == "false"

    def test_user_can_not_block_itself(self, app: Flask, user_1: User) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
            self.route.format(username=user_1.username),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_400(response)


class TestUnBlockUser(ApiTestCaseMixin):
    route = "/api/users/{username}/unblock"

    def test_it_returns_error_if_user_is_not_authenticated(
        self, app: Flask, user_1: User
    ) -> None:
        client = app.test_client()

        response = client.post(
            self.route.format(username=user_1.username),
            content_type="application/json",
        )

        self.assert_401(response)

    def test_it_returns_error_when_user_does_not_exist(
        self, app: Flask, user_1: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
            self.route.format(username=self.random_string()),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_404_with_entity(response, "user")

    def test_it_returns_error_when_user_is_suspended(
        self, app: Flask, user_1: User, suspended_user: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, suspended_user.email
        )

        response = client.post(
            self.route.format(username=user_1.username),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_403(response)

    def test_it_unblocks_user(
        self, app: Flask, user_1: User, user_2: User
    ) -> None:
        user_1.blocks_user(user_2)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
            self.route.format(username=user_2.username),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert_response(response, 200, status="success")
        assert user_2.is_blocked_by(user_1) is False

    def test_it_does_not_return_error_if_user_is_not_block(
        self, app: Flask, user_1: User, user_2: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
            self.route.format(username=user_2.username),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert_response(response, 200, status="success")
        assert user_2.is_blocked_by(user_1) is False
