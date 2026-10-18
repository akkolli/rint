import json
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from fittrackee import db
from fittrackee.tests.custom_asserts import assert_response
from fittrackee.visibility_levels import VisibilityLevel
from fittrackee.workouts.services.workouts_from_file_refresh_service import (
    WorkoutFromFileRefreshService,
)

from ..mixins import MediaMixin
from ..utils import jsonify_dict
from .mixins import WorkoutApiTestCaseMixin
from .utils import create_a_workout_with_file

if TYPE_CHECKING:
    from flask import Flask

    from fittrackee.equipments.models import Equipment
    from fittrackee.users.models import FollowRequest, User
    from fittrackee.workouts.models import Sport, Workout


class TestEditWorkout(WorkoutApiTestCaseMixin, MediaMixin):
    def test_it_returns_401_when_no_authenticated(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        workout_cycling_user_1: "Workout",
    ) -> None:
        workout_cycling_user_1.workout_visibility = VisibilityLevel.PUBLIC
        client = app.test_client()

        response = client.patch(
            f"/api/workouts/{workout_cycling_user_1}",
            content_type="application/json",
            json={"sport_id": 2, "title": "Workout test"},
        )

        assert response.status_code == 401

    def test_it_returns_403_when_user_is_suspended(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        workout_cycling_user_1: "Workout",
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )
        user_1.suspended_at = datetime.now(timezone.utc)
        db.session.commit()

        response = client.patch(
            f"/api/workouts/{workout_cycling_user_1.short_id}",
            content_type="application/json",
            data=json.dumps(dict(sport_id=2, title="Workout test")),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_403(response)

    def test_it_returns_404_when_workout_does_not_exist(
        self, app: "Flask", user_1: "User", sport_1_cycling: "Sport"
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )
        response = client.patch(
            f"/api/workouts/{self.random_short_id()}",
            content_type="application/json",
            json={"sport_id": 2, "title": "Workout test"},
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = self.assert_404(response)
        assert len(data["data"]["workouts"]) == 0

    @pytest.mark.parametrize(
        "input_desc,input_workout_visibility,expected_status_code",
        [
            ("workout visibility: private", VisibilityLevel.PRIVATE, 404),
            (
                "workout visibility: followers_only",
                VisibilityLevel.FOLLOWERS,
                403,
            ),
            ("workout visibility: public", VisibilityLevel.PUBLIC, 403),
        ],
    )
    def test_it_returns_error_when_updating_workout_from_followed_user(
        self,
        input_desc: str,
        input_workout_visibility: "VisibilityLevel",
        expected_status_code: int,
        app: "Flask",
        user_1: "User",
        user_2: "User",
        sport_1_cycling: "Sport",
        workout_cycling_user_1: "Workout",
        follow_request_from_user_2_to_user_1: "FollowRequest",
    ) -> None:
        workout_cycling_user_1.workout_visibility = input_workout_visibility
        user_1.approves_follow_request_from(user_2)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_2.email
        )

        response = client.patch(
            f"/api/workouts/{workout_cycling_user_1.short_id}",
            content_type="application/json",
            json={"sport_id": 2, "title": "Workout test"},
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert response.status_code == expected_status_code

    @pytest.mark.parametrize(
        "input_desc,input_workout_visibility,expected_status_code",
        [
            ("workout visibility: private", VisibilityLevel.PRIVATE, 404),
            (
                "workout visibility: followers_only",
                VisibilityLevel.FOLLOWERS,
                404,
            ),
            ("workout visibility: public", VisibilityLevel.PUBLIC, 403),
        ],
    )
    def test_returns_403_when_updating_workout_from_another_user(
        self,
        input_desc: str,
        input_workout_visibility: "VisibilityLevel",
        expected_status_code: int,
        app: "Flask",
        user_1: "User",
        user_2: "User",
        sport_1_cycling: "Sport",
        workout_cycling_user_2: "Workout",
    ) -> None:
        workout_cycling_user_2.workout_visibility = input_workout_visibility
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.patch(
            f"/api/workouts/{workout_cycling_user_2.short_id}",
            content_type="application/json",
            data=json.dumps(
                dict(
                    sport_id=2,
                    duration=3600,
                    workout_date="2018-05-15 15:05",
                    distance=8,
                    title="Workout test",
                )
            ),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert response.status_code == expected_status_code

    def test_it_returns_400_if_payload_is_empty(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        workout_cycling_user_1: "Workout",
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.patch(
            f"/api/workouts/{workout_cycling_user_1.short_id}",
            content_type="application/json",
            json={},
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_400(response)

    def test_it_raises_400_if_sport_does_not_exist(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        workout_cycling_user_1: "Workout",
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.patch(
            f"/api/workouts/{workout_cycling_user_1.short_id}",
            content_type="application/json",
            json={"sport_id": 2},
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_400(response, "sport id 2 not found", "invalid")

    @pytest.mark.parametrize(
        "input_attribute", ["description", "notes", "title"]
    )
    def test_it_updates_value_with_special_characters_for_a_workout_with_gpx(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        sport_2_running: "Sport",
        workout_cycling_user_1: "Workout",
        input_attribute: str,
    ) -> None:
        content = "test \nworkout ©"
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.patch(
            f"/api/workouts/{workout_cycling_user_1.short_id}",
            content_type="application/json",
            json={input_attribute: content},
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert response.status_code == 200
        assert "success" in data["status"]
        assert len(data["data"]["workouts"]) == 1
        assert data["data"]["workouts"][0][input_attribute] == content

    def test_it_adds_equipment(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        workout_cycling_user_1: "Workout",
        equipment_bike_user_1: "Equipment",
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.patch(
            f"/api/workouts/{workout_cycling_user_1.short_id}",
            content_type="application/json",
            json={"equipment_ids": [equipment_bike_user_1.short_id]},
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = assert_response(response, 200, contains={"status": "success"})
        assert data["data"]["workouts"][0]["equipments"] == [
            jsonify_dict(equipment_bike_user_1.serialize(current_user=user_1))
        ]

    def test_it_updates_workout_equipment(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        sport_2_running: "Sport",
        workout_running_user_1: "Workout",
        equipment_shoes_user_1: "Equipment",
        equipment_another_shoes_user_1: "Equipment",
    ) -> None:
        workout_running_user_1.equipments = [equipment_shoes_user_1]
        db.session.commit()
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.patch(
            f"/api/workouts/{workout_running_user_1.short_id}",
            content_type="application/json",
            json={"equipment_ids": [equipment_another_shoes_user_1.short_id]},
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert response.status_code == 200
        assert "success" in data["status"]
        assert len(data["data"]["workouts"]) == 1
        assert data["data"]["workouts"][0]["equipments"] == [
            jsonify_dict(
                equipment_another_shoes_user_1.serialize(current_user=user_1)
            )
        ]
        assert equipment_another_shoes_user_1.total_workouts == 1
        assert (
            equipment_another_shoes_user_1.total_distance
            == workout_running_user_1.distance
        )
        assert (
            equipment_another_shoes_user_1.total_duration
            == workout_running_user_1.duration
        )
        assert (
            equipment_another_shoes_user_1.total_moving
            == workout_running_user_1.moving
        )

    def test_it_updates_workout_equipment_with_multiple_pieces(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        gpx_file: str,
        equipment_shoes_user_1: "Equipment",
        equipment_bike_user_1: "Equipment",
    ) -> None:
        workout = create_a_workout_with_file(user_1, gpx_file)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.patch(
            f"/api/workouts/{workout.short_id}",
            content_type="application/json",
            json={
                "equipment_ids": [
                    equipment_shoes_user_1.short_id,
                    equipment_bike_user_1.short_id,
                ]
            },
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert response.status_code == 200
        assert "success" in data["status"]
        assert len(data["data"]["workouts"]) == 1
        assert len(data["data"]["workouts"][0]["equipments"]) == 2

    def test_it_returns_400_when_equipment_ids_are_invalid(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        gpx_file: str,
        equipment_bike_user_1: "Equipment",
    ) -> None:
        workout = create_a_workout_with_file(user_1, gpx_file)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.patch(
            f"/api/workouts/{workout.short_id}",
            content_type="application/json",
            json={"equipment_ids": equipment_bike_user_1.short_id},
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_400(
            response,
            "equipment_ids must be an array of strings",
        )

    def test_it_updates_media_attachments(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        gpx_file: str,
    ) -> None:
        media = self.create_media(user_1)
        workout = create_a_workout_with_file(user_1, gpx_file)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.patch(
            f"/api/workouts/{workout.short_id}",
            content_type="application/json",
            data=json.dumps(dict(media_attachment_ids=[media.short_id])),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert response.status_code == 200
        assert "success" in data["status"]
        assert len(data["data"]["workouts"]) == 1
        assert data["data"]["workouts"][0]["media_attachments"] == [
            media.serialize()
        ]

    @patch("fittrackee.workouts.workouts.MAX_MEDIA_ATTACHMENTS", 2)
    def test_it_returns_400_when_number_of_media_exceeds_limit(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        gpx_file: str,
    ) -> None:
        workout = create_a_workout_with_file(user_1, gpx_file)
        media_1 = self.create_media(user_1, workout_id=workout.id)
        media_2 = self.create_media(user_1)
        media_3 = self.create_media(user_1)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.patch(
            f"/api/workouts/{workout.short_id}",
            content_type="application/json",
            data=json.dumps(
                dict(
                    media_attachment_ids=[
                        media_1.short_id,
                        media_2.short_id,
                        media_3.short_id,
                    ],
                )
            ),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_400(
            response,
            "up to 2 media attachments can be associated with a workout",
        )


class TestEditWorkoutWithFile(WorkoutApiTestCaseMixin):
    @pytest.mark.parametrize(
        "input_description,input_workout_visibility",
        [
            ("private", VisibilityLevel.PRIVATE),
            ("followers_only", VisibilityLevel.FOLLOWERS),
            ("public", VisibilityLevel.PUBLIC),
        ],
    )
    def test_it_updates_workout_visibility_for_workout_with_gpx(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        workout_cycling_user_1: "Workout",
        input_description: str,
        input_workout_visibility: "VisibilityLevel",
    ) -> None:
        workout_cycling_user_1.original_file = "file.gpx"
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.patch(
            f"/api/workouts/{workout_cycling_user_1.short_id}",
            content_type="application/json",
            json={"workout_visibility": input_workout_visibility.value},
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = assert_response(response, 200, contains={"status": "success"})
        assert len(data["data"]["workouts"]) == 1
        assert (
            data["data"]["workouts"][0]["workout_visibility"]
            == input_workout_visibility.value
        )

    @pytest.mark.parametrize(
        "input_description,input_analysis_visibility",
        [
            ("private", VisibilityLevel.PRIVATE),
            ("followers_only", VisibilityLevel.FOLLOWERS),
            ("public", VisibilityLevel.PUBLIC),
        ],
    )
    def test_it_updates_analysis_visibility_for_workout_with_gpx(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        workout_cycling_user_1: "Workout",
        input_description: str,
        input_analysis_visibility: "VisibilityLevel",
    ) -> None:
        workout_cycling_user_1.workout_visibility = VisibilityLevel.PUBLIC
        workout_cycling_user_1.original_file = "file.gpx"
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.patch(
            f"/api/workouts/{workout_cycling_user_1.short_id}",
            content_type="application/json",
            json={"analysis_visibility": input_analysis_visibility.value},
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = assert_response(response, 200, contains={"status": "success"})
        assert len(data["data"]["workouts"]) == 1
        assert (
            data["data"]["workouts"][0]["analysis_visibility"]
            == input_analysis_visibility.value
        )
        assert (
            workout_cycling_user_1.analysis_visibility.value
            == input_analysis_visibility.value
        )

    @pytest.mark.parametrize(
        "input_description,input_map_visibility",
        [
            ("private", VisibilityLevel.PRIVATE),
            ("followers_only", VisibilityLevel.FOLLOWERS),
            ("public", VisibilityLevel.PUBLIC),
        ],
    )
    def test_it_updates_map_visibility_for_workout_with_gpx(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        workout_cycling_user_1: "Workout",
        input_description: str,
        input_map_visibility: "VisibilityLevel",
    ) -> None:
        workout_cycling_user_1.workout_visibility = VisibilityLevel.PUBLIC
        workout_cycling_user_1.analysis_visibility = VisibilityLevel.PUBLIC
        workout_cycling_user_1.original_file = "file.gpx"
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.patch(
            f"/api/workouts/{workout_cycling_user_1.short_id}",
            content_type="application/json",
            json={"map_visibility": input_map_visibility.value},
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = assert_response(response, 200, contains={"status": "success"})
        assert len(data["data"]["workouts"]) == 1
        assert (
            data["data"]["workouts"][0]["map_visibility"]
            == input_map_visibility.value
        )
        assert (
            workout_cycling_user_1.map_visibility.value
            == input_map_visibility.value
        )


class TestEditWorkoutWithoutFile(WorkoutApiTestCaseMixin):
    def test_it_updates_a_workout_without_file(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        sport_2_running: "Sport",
        workout_cycling_user_1: "Workout",
    ) -> None:
        workout_short_id = workout_cycling_user_1.short_id
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        with patch.object(
            WorkoutFromFileRefreshService, "refresh"
        ) as refresh_mock:
            response = client.patch(
                f"/api/workouts/{workout_short_id}",
                content_type="application/json",
                json={
                    "sport_id": 2,
                    "duration": 3600,
                    "workout_date": "2018-05-15 15:05",
                    "distance": 8,
                    "title": "Workout test",
                },
                headers=dict(Authorization=f"Bearer {auth_token}"),
            )

        data = json.loads(response.data.decode())

        db.session.refresh(workout_cycling_user_1)
        assert workout_cycling_user_1.duration == timedelta(seconds=3600)
        assert workout_cycling_user_1.distance == 8
        assert workout_cycling_user_1.ave_speed == 8.0
        assert workout_cycling_user_1.max_speed == 8.0
        assert workout_cycling_user_1.ave_pace == timedelta(
            minutes=7, seconds=30
        )
        assert workout_cycling_user_1.best_pace == timedelta(
            minutes=7, seconds=30
        )
        refresh_mock.assert_not_called()
        assert response.status_code == 200
        assert "success" in data["status"]
        assert len(data["data"]["workouts"]) == 1
        assert "creation_date" in data["data"]["workouts"][0]
        assert (
            data["data"]["workouts"][0]["workout_date"]
            == "Tue, 15 May 2018 15:05:00 GMT"
        )
        assert data["data"]["workouts"][0]["user"] == jsonify_dict(
            user_1.serialize()
        )
        assert data["data"]["workouts"][0]["sport_id"] == sport_2_running.id
        assert data["data"]["workouts"][0]["duration"] == "1:00:00"
        assert data["data"]["workouts"][0]["title"] == "Workout test"
        assert data["data"]["workouts"][0]["ascent"] is None
        assert data["data"]["workouts"][0]["ave_pace"] == "0:07:30"
        assert data["data"]["workouts"][0]["ave_speed"] is None
        assert data["data"]["workouts"][0]["best_pace"] == "0:07:30"
        assert data["data"]["workouts"][0]["descent"] is None
        assert data["data"]["workouts"][0]["description"] is None
        assert data["data"]["workouts"][0]["distance"] == 8.0
        assert data["data"]["workouts"][0]["max_alt"] is None
        assert data["data"]["workouts"][0]["max_speed"] is None
        assert data["data"]["workouts"][0]["min_alt"] is None
        assert data["data"]["workouts"][0]["moving"] == "1:00:00"
        assert data["data"]["workouts"][0]["pauses"] is None
        assert data["data"]["workouts"][0]["with_file"] is False
        assert data["data"]["workouts"][0]["map"] is None
        assert data["data"]["workouts"][0]["weather_start"] is None
        assert data["data"]["workouts"][0]["weather_end"] is None
        assert data["data"]["workouts"][0]["notes"] is None

        records = data["data"]["workouts"][0]["records"]
        assert len(records) == 4
        for record in records:
            assert record["sport_id"] == sport_2_running.id
            assert record["workout_id"] == workout_short_id
            assert record["workout_date"] == "Tue, 15 May 2018 15:05:00 GMT"
        assert records[0]["record_type"] == "AP"
        assert records[0]["value"] == "0:07:30"
        assert records[1]["record_type"] == "BP"
        assert records[1]["value"] == "0:07:30"
        assert records[2]["record_type"] == "FD"
        assert records[2]["value"] == 8.0
        assert records[3]["record_type"] == "LD"
        assert records[3]["value"] == "1:00:00"
