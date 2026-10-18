import json
from datetime import datetime, timezone

import pytest
from flask import Flask
from werkzeug.test import TestResponse

from fittrackee import db
from fittrackee.tests.custom_asserts import assert_response
from fittrackee.users.models import FollowRequest, User
from fittrackee.visibility_levels import VisibilityLevel
from fittrackee.workouts.models import Sport, Workout

from ..mixins import MediaMixin
from .mixins import WorkoutApiTestCaseMixin


class GetUserTimelineTestCase(WorkoutApiTestCaseMixin, MediaMixin):
    @staticmethod
    def assert_no_workout_returned(response: TestResponse) -> None:
        data = assert_response(response, 200, contains={"status": "success"})
        assert len(data["data"]["workouts"]) == 0

    @staticmethod
    def assert_workout_returned(
        response: TestResponse, workout: Workout
    ) -> None:
        data = assert_response(response, 200, contains={"status": "success"})
        assert len(data["data"]["workouts"]) == 1
        assert data["data"]["workouts"][0]["id"] == workout.short_id


class TestGetUserTimelineForFollowedUserWorkouts(GetUserTimelineTestCase):
    def test_it_does_not_return_followed_user_private_workout(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
        follow_request_from_user_1_to_user_2: FollowRequest,
    ) -> None:
        user_2.approves_follow_request_from(user_1)
        workout_cycling_user_2.workout_visibility = VisibilityLevel.PRIVATE
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            "/api/timeline",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_no_workout_returned(response)

    @pytest.mark.parametrize(
        "input_desc,input_workout_visibility",
        [
            (
                "workout visibility: followers_only",
                VisibilityLevel.FOLLOWERS,
            ),
            ("workout visibility: public", VisibilityLevel.PUBLIC),
        ],
    )
    def test_it_returns_followed_user_workout_when_visibility_allows_it(
        self,
        input_desc: str,
        input_workout_visibility: VisibilityLevel,
        app: Flask,
        user_1: User,
        user_2: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
        follow_request_from_user_1_to_user_2: FollowRequest,
    ) -> None:
        user_2.approves_follow_request_from(user_1)
        workout_cycling_user_2.workout_visibility = input_workout_visibility
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            "/api/timeline",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_workout_returned(response, workout_cycling_user_2)

    @pytest.mark.parametrize(
        "input_desc,input_workout_visibility",
        [
            (
                "workout visibility: followers_only",
                VisibilityLevel.FOLLOWERS,
            ),
            ("workout visibility: public", VisibilityLevel.PUBLIC),
        ],
    )
    def test_it_does_not_return_workout_from_blocked_user(
        self,
        input_desc: str,
        input_workout_visibility: VisibilityLevel,
        app: Flask,
        user_1: User,
        user_2: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
        follow_request_from_user_1_to_user_2: FollowRequest,
    ) -> None:
        user_2.approves_follow_request_from(user_1)
        workout_cycling_user_2.workout_visibility = input_workout_visibility
        user_1.blocks_user(user_2)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            "/api/timeline",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_no_workout_returned(response)

    def test_blocked_user_can_not_get_workout_in_timeline(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
        follow_request_from_user_1_to_user_2: FollowRequest,
    ) -> None:
        user_2.approves_follow_request_from(user_1)
        workout_cycling_user_2.workout_visibility = VisibilityLevel.PUBLIC
        user_2.blocks_user(user_1)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            "/api/timeline",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_no_workout_returned(response)

    @pytest.mark.parametrize(
        "input_desc,input_workout_visibility",
        [
            (
                "workout visibility: followers_only",
                VisibilityLevel.FOLLOWERS,
            ),
            ("workout visibility: public", VisibilityLevel.PUBLIC),
        ],
    )
    def test_it_does_not_return_followed_user_suspended_workouts(
        self,
        input_desc: str,
        input_workout_visibility: VisibilityLevel,
        app: Flask,
        user_1: User,
        user_2: User,
        sport_1_cycling: Sport,
        workout_cycling_user_1: Workout,
        workout_cycling_user_2: Workout,
        follow_request_from_user_1_to_user_2: FollowRequest,
    ) -> None:
        user_2.approves_follow_request_from(user_1)
        workout_cycling_user_2.workout_visibility = input_workout_visibility
        workout_cycling_user_2.suspended_at = datetime.now(timezone.utc)
        user_1.blocks_user(user_2)
        db.session.commit()
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            "/api/timeline",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_workout_returned(response, workout_cycling_user_1)

    @pytest.mark.parametrize(
        "input_desc,input_workout_visibility",
        [
            (
                "workout visibility: followers_only",
                VisibilityLevel.FOLLOWERS,
            ),
            ("workout visibility: public", VisibilityLevel.PUBLIC),
        ],
    )
    def test_it_does_not_return_followed_user_workout_map_when_private(
        self,
        input_desc: str,
        input_workout_visibility: VisibilityLevel,
        app: Flask,
        user_1: User,
        user_2: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
        follow_request_from_user_1_to_user_2: FollowRequest,
    ) -> None:
        user_2.approves_follow_request_from(user_1)
        workout_cycling_user_2.workout_visibility = input_workout_visibility
        workout_cycling_user_2.map_visibility = VisibilityLevel.PRIVATE
        workout_cycling_user_2.map_id = self.random_string()
        workout_cycling_user_2.map = self.random_string()
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            "/api/timeline",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert data["data"]["workouts"][0]["map"] is None

    @pytest.mark.parametrize(
        "input_desc,input_visibility",
        [
            (
                "workout and map visibility: followers_only",
                VisibilityLevel.FOLLOWERS,
            ),
            ("workout and map visibility: public", VisibilityLevel.PUBLIC),
        ],
    )
    def test_it_returns_followed_user_workout_map_when_visibility_allows_it(
        self,
        input_desc: str,
        input_visibility: VisibilityLevel,
        app: Flask,
        user_1: User,
        user_2: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
        follow_request_from_user_1_to_user_2: FollowRequest,
    ) -> None:
        user_2.approves_follow_request_from(user_1)
        workout_cycling_user_2.workout_visibility = input_visibility
        workout_cycling_user_2.analysis_visibility = input_visibility
        workout_cycling_user_2.map_visibility = input_visibility
        map_id = self.random_string()
        workout_cycling_user_2.map_id = map_id
        workout_cycling_user_2.map = self.random_string()
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            "/api/timeline",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert data["data"]["workouts"][0]["map"] == map_id

    def test_it_returns_workout_with_media_attachments_if_user_can_see_media(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
        follow_request_from_user_1_to_user_2: FollowRequest,
    ) -> None:
        user_2.approves_follow_request_from(user_1)
        workout_cycling_user_2.workout_visibility = VisibilityLevel.FOLLOWERS
        workout_cycling_user_2.media_visibility = VisibilityLevel.FOLLOWERS
        media = self.create_media(user_2, workout_id=workout_cycling_user_2.id)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            "/api/timeline",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert data["data"]["workouts"][0]["media_attachments"] == [
            media.serialize(can_see_map_data=True)
        ]

    def test_it_does_not_return_media_attachments_if_user_can_not_see_media(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
        follow_request_from_user_1_to_user_2: FollowRequest,
    ) -> None:
        user_2.approves_follow_request_from(user_1)
        workout_cycling_user_2.workout_visibility = VisibilityLevel.FOLLOWERS
        workout_cycling_user_2.media_visibility = VisibilityLevel.PRIVATE
        self.create_media(user_2, workout_id=workout_cycling_user_2.id)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            "/api/timeline",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert data["data"]["workouts"][0]["media_attachments"] == []


class TestGetUserTimelineForNotFollowedUserWorkouts(GetUserTimelineTestCase):
    @pytest.mark.parametrize(
        "input_desc,input_workout_visibility",
        [
            (
                "workout visibility: private",
                VisibilityLevel.PRIVATE,
            ),
            (
                "workout visibility: followers_only",
                VisibilityLevel.FOLLOWERS,
            ),
            ("workout visibility: public", VisibilityLevel.PUBLIC),
        ],
    )
    def test_it_does_not_return_workout(
        self,
        input_desc: str,
        input_workout_visibility: VisibilityLevel,
        app: Flask,
        user_1: User,
        user_2: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
    ) -> None:
        workout_cycling_user_2.workout_visibility = input_workout_visibility
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            "/api/timeline",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_no_workout_returned(response)
