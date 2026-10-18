from datetime import datetime, timezone
from typing import List

import pytest
from flask import Flask
from time_machine import travel

from fittrackee import db
from fittrackee.comments.models import Comment
from fittrackee.reports.models import (
    USER_ACTION_TYPES,
    Report,
    ReportAction,
)
from fittrackee.users.models import User
from fittrackee.visibility_levels import VisibilityLevel
from fittrackee.workouts.models import Sport, Workout

from ..comments.mixins import CommentMixin
from ..mixins import ApiTestCaseMixin, ReportMixin


class ReportTestCase(CommentMixin, ReportMixin, ApiTestCaseMixin):
    route = "/api/reports"

    def create_reports(
        self,
        user_2: User,
        user_3: User,
        user_4: User,
        workout_cycling_user_2: Workout,
    ) -> List[Report]:
        reports = [self.create_report(reporter=user_2, reported_object=user_4)]
        workout_cycling_user_2.workout_visibility = VisibilityLevel.PUBLIC
        reports.append(
            self.create_report(
                reporter=user_3, reported_object=workout_cycling_user_2
            )
        )
        comment = self.create_comment(
            user_3,
            workout_cycling_user_2,
            text_visibility=VisibilityLevel.PUBLIC,
        )
        reports.append(
            self.create_report(reporter=user_2, reported_object=comment)
        )
        return reports


class TestGetReportsAsUser(ReportTestCase):
    def test_it_does_not_return_reports(
        self,
        app: Flask,
        user_1: User,
        user_2: User,
        user_3: User,
        user_4: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
    ) -> None:
        self.create_reports(user_2, user_3, user_4, workout_cycling_user_2)
        self.create_report(
            reporter=user_1, reported_object=workout_cycling_user_2
        )
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            self.route,
            content_type="application/json",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_403(response)


class TestGetReportsAsUnauthenticatedUser(ReportTestCase):
    def test_it_returns_401_when_user_is_not_authenticated(
        self, app: Flask
    ) -> None:
        client = app.test_client()

        response = client.get(self.route, content_type="application/json")

        self.assert_401(response)


class GetReportTestCase(ReportTestCase):
    route = "/api/reports/{report_id}"


class TestGetReportAsUser(GetReportTestCase):
    def test_it_does_not_return_report(
        self, app: Flask, user_1: User, user_2: User
    ) -> None:
        report = self.create_report(reporter=user_1, reported_object=user_2)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.get(
            self.route.format(report_id=report.id),
            content_type="application/json",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_403(response)


class TestGetReportAsUnauthenticatedUser(GetReportTestCase):
    def test_it_returns_401_when_user_is_not_authenticated(
        self, app: Flask, user_1: User, user_2: User
    ) -> None:
        report = self.create_report(reporter=user_1, reported_object=user_2)
        client = app.test_client()

        response = client.get(
            self.route.format(report_id=report.id),
            content_type="application/json",
        )

        self.assert_401(response)


class TestPostReportAction(ReportTestCase):
    route = "/api/reports/{report_id}/actions"

    def test_it_returns_401_if_user_is_not_authenticated(
        self,
        app: Flask,
        user_1: User,
    ) -> None:
        client = app.test_client()

        response = client.post(
            self.route.format(report_id=self.random_int()),
            content_type="application/json",
            json={
                "action_type": "user_suspension",
                "username": user_1.username,
            },
        )

        self.assert_401(response)

    def test_it_returns_403_if_user_has_no_moderation_rights(
        self, app: Flask, user_1: User, user_2: User
    ) -> None:
        report = self.create_report(reporter=user_1, reported_object=user_2)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
            self.route.format(report_id=report.id),
            content_type="application/json",
            json={
                "action_type": "user_suspension",
                "username": user_2.username,
            },
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_403(response)

    def test_it_returns_404_when_no_report(
        self, app: Flask, user_1_moderator: User, user_2: User
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )
        report_id = self.random_int()

        response = client.post(
            self.route.format(report_id=report_id),
            content_type="application/json",
            json={
                "action_type": "user_suspension",
                "username": user_2.username,
            },
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_404_with_message(
            response, f"report not found (id: {report_id})"
        )

    def test_it_returns_400_when_action_type_is_missing(
        self, app: Flask, user_1_moderator: User, user_2: User, user_3: User
    ) -> None:
        report = self.create_report(reporter=user_3, reported_object=user_2)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )

        response = client.post(
            self.route.format(report_id=report.id),
            content_type="application/json",
            json={
                "username": user_2.username,
            },
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_400(response)

    def test_it_returns_400_when_action_type_is_invalid(
        self, app: Flask, user_1_moderator: User, user_2: User, user_3: User
    ) -> None:
        report = self.create_report(reporter=user_3, reported_object=user_2)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )

        response = client.post(
            self.route.format(report_id=report.id),
            content_type="application/json",
            json={
                "action_type": self.random_string(),
                "username": user_2.username,
            },
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_400(response, "invalid 'action_type'")


class TestPostReportActionForUserAction(ReportTestCase):
    route = "/api/reports/{report_id}/actions"

    def test_it_suspends_user(
        self, app: Flask, user_1_moderator: User, user_2: User, user_3: User
    ) -> None:
        report = self.create_report(reporter=user_3, reported_object=user_2)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )
        now = datetime.now(timezone.utc)

        with travel(now, tick=False):
            response = client.post(
                self.route.format(report_id=report.id),
                content_type="application/json",
                json={
                    "action_type": "user_suspension",
                    "username": user_2.username,
                },
                headers=dict(Authorization=f"Bearer {auth_token}"),
            )

        assert response.status_code == 200
        assert (
            User.query.filter_by(username=user_2.username).one().suspended_at
            == now
        )

    def test_it_returns_400_when_when_user_already_suspended(
        self, app: Flask, user_1_moderator: User, user_2: User, user_3: User
    ) -> None:
        report = self.create_report(reporter=user_3, reported_object=user_2)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )
        user_2.suspended_at = datetime.now(timezone.utc)
        db.session.commit()

        response = client.post(
            self.route.format(report_id=report.id),
            content_type="application/json",
            json={
                "action_type": "user_suspension",
                "username": user_2.username,
            },
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_400(response, "user account already suspended")

    def test_it_returns_400_when_when_user_already_warned(
        self, app: Flask, user_1_moderator: User, user_2: User, user_3: User
    ) -> None:
        report = self.create_report(reporter=user_3, reported_object=user_2)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )
        self.create_report_action(
            user_1_moderator,
            user_2,
            action_type="user_warning",
            report_id=report.id,
        )
        db.session.commit()

        response = client.post(
            self.route.format(report_id=report.id),
            content_type="application/json",
            json={
                "action_type": "user_warning",
                "username": user_2.username,
            },
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_400(response, "user already warned")

    def test_it_reactivates_user(
        self, app: Flask, user_1_moderator: User, user_2: User, user_3: User
    ) -> None:
        report = self.create_report(reporter=user_3, reported_object=user_2)
        user_2.suspended_at = datetime.now(timezone.utc)
        db.session.commit()
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )

        response = client.post(
            self.route.format(report_id=report.id),
            content_type="application/json",
            json={
                "action_type": "user_unsuspension",
                "username": user_2.username,
            },
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert response.status_code == 200
        assert (
            User.query.filter_by(username=user_2.username).one().suspended_at
            is None
        )

    @pytest.mark.parametrize("input_action_type", USER_ACTION_TYPES)
    def test_it_creates_report_action(
        self,
        app: Flask,
        user_1_moderator: User,
        user_2: User,
        user_3: User,
        input_action_type: str,
    ) -> None:
        report = self.create_report(reporter=user_3, reported_object=user_2)
        if input_action_type == "user_unsuspension":
            user_2.suspended_at = datetime.now(timezone.utc)
            db.session.commit()
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )

        response = client.post(
            self.route.format(report_id=report.id),
            content_type="application/json",
            json={
                "action_type": input_action_type,
                "username": user_2.username,
            },
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert response.status_code == 200
        assert (
            ReportAction.query.filter_by(
                moderator_id=user_1_moderator.id,
                user_id=user_2.id,
                action_type=input_action_type,
            ).first()
            is not None
        )


class TestPostReportActionForWorkoutAction(ReportTestCase):
    route = "/api/reports/{report_id}/actions"

    def test_it_suspends_workout_by_setting_moderation_date(
        self,
        app: Flask,
        user_1_moderator: User,
        user_2: User,
        user_3: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
    ) -> None:
        workout_cycling_user_2.workout_visibility = VisibilityLevel.PUBLIC
        report = self.create_report(
            reporter=user_3, reported_object=workout_cycling_user_2
        )
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )
        now = datetime.now(timezone.utc)

        with travel(now, tick=False):
            response = client.post(
                self.route.format(report_id=report.id),
                content_type="application/json",
                json={
                    "action_type": "workout_suspension",
                    "workout_id": workout_cycling_user_2.short_id,
                },
                headers=dict(Authorization=f"Bearer {auth_token}"),
            )

        assert response.status_code == 200
        assert (
            Workout.query.filter_by(id=workout_cycling_user_2.id)
            .one()
            .suspended_at
            == now
        )

    def test_it_returns_400_when_when_workout_already_suspended(
        self,
        app: Flask,
        user_1_moderator: User,
        user_2: User,
        user_3: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
    ) -> None:
        workout_cycling_user_2.workout_visibility = VisibilityLevel.PUBLIC
        report = self.create_report(
            reporter=user_3, reported_object=workout_cycling_user_2
        )
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )
        workout_cycling_user_2.suspended_at = datetime.now(timezone.utc)
        db.session.commit()

        response = client.post(
            self.route.format(report_id=report.id),
            content_type="application/json",
            json={
                "action_type": "workout_suspension",
                "workout_id": workout_cycling_user_2.short_id,
            },
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_400(
            response,
            "workout already suspended",
        )

    def test_it_unsuspends_workout(
        self,
        app: Flask,
        user_1_moderator: User,
        user_2: User,
        user_3: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
    ) -> None:
        workout_cycling_user_2.workout_visibility = VisibilityLevel.PUBLIC
        report = self.create_report(
            reporter=user_3, reported_object=workout_cycling_user_2
        )
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )
        workout_cycling_user_2.suspended_at = datetime.now(timezone.utc)

        response = client.post(
            self.route.format(report_id=report.id),
            content_type="application/json",
            json={
                "action_type": "workout_unsuspension",
                "workout_id": workout_cycling_user_2.short_id,
            },
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert response.status_code == 200
        assert (
            Workout.query.filter_by(id=workout_cycling_user_2.id)
            .one()
            .suspended_at
            is None
        )

    def test_it_creates_report_action(
        self,
        app: Flask,
        user_1_moderator: User,
        user_2: User,
        user_3: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
    ) -> None:
        workout_cycling_user_2.workout_visibility = VisibilityLevel.PUBLIC
        report = self.create_report(
            reporter=user_3, reported_object=workout_cycling_user_2
        )
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )

        response = client.post(
            self.route.format(report_id=report.id),
            content_type="application/json",
            json={
                "action_type": "workout_suspension",
                "workout_id": workout_cycling_user_2.short_id,
            },
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert response.status_code == 200
        assert (
            ReportAction.query.filter_by(
                moderator_id=user_1_moderator.id, user_id=user_2.id
            ).first()
            is not None
        )


class TestPostReportActionForCommentAction(ReportTestCase):
    route = "/api/reports/{report_id}/actions"

    def test_it_suspends_comment_by_setting_moderation_date(
        self,
        app: Flask,
        user_1_moderator: User,
        user_2: User,
        user_3: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
    ) -> None:
        workout_cycling_user_2.workout_visibility = VisibilityLevel.PUBLIC
        comment = self.create_comment(
            user_3, workout_cycling_user_2, VisibilityLevel.PUBLIC
        )
        report = self.create_report(reporter=user_2, reported_object=comment)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )
        now = datetime.now(timezone.utc)

        with travel(now, tick=False):
            response = client.post(
                self.route.format(report_id=report.id),
                content_type="application/json",
                json={
                    "action_type": "comment_suspension",
                    "comment_id": comment.short_id,
                },
                headers=dict(Authorization=f"Bearer {auth_token}"),
            )

        assert response.status_code == 200
        assert Comment.query.filter_by(id=comment.id).one().suspended_at == now

    def test_it_returns_400_when_when_comment_already_suspended(
        self,
        app: Flask,
        user_1_moderator: User,
        user_2: User,
        user_3: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
    ) -> None:
        workout_cycling_user_2.workout_visibility = VisibilityLevel.PUBLIC
        comment = self.create_comment(
            user_3, workout_cycling_user_2, VisibilityLevel.PUBLIC
        )
        report = self.create_report(reporter=user_2, reported_object=comment)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )
        comment.suspended_at = datetime.now(timezone.utc)
        db.session.commit()
        now = datetime.now(timezone.utc)

        with travel(now, tick=False):
            response = client.post(
                self.route.format(report_id=report.id),
                content_type="application/json",
                json={
                    "action_type": "comment_suspension",
                    "comment_id": comment.short_id,
                },
                headers=dict(Authorization=f"Bearer {auth_token}"),
            )

        self.assert_400(
            response,
            "comment already suspended",
        )

    def test_it_unsuspends_comment(
        self,
        app: Flask,
        user_1_moderator: User,
        user_2: User,
        user_3: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
    ) -> None:
        workout_cycling_user_2.workout_visibility = VisibilityLevel.PUBLIC
        comment = self.create_comment(
            user_3, workout_cycling_user_2, VisibilityLevel.PUBLIC
        )
        report = self.create_report(reporter=user_2, reported_object=comment)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )
        comment.suspended_at = datetime.now(timezone.utc)

        response = client.post(
            self.route.format(report_id=report.id),
            content_type="application/json",
            json={
                "action_type": "comment_unsuspension",
                "comment_id": comment.short_id,
            },
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert response.status_code == 200
        assert (
            Comment.query.filter_by(id=comment.id).one().suspended_at is None
        )

    def test_it_creates_report_action(
        self,
        app: Flask,
        user_1_moderator: User,
        user_2: User,
        user_3: User,
        sport_1_cycling: Sport,
        workout_cycling_user_2: Workout,
    ) -> None:
        workout_cycling_user_2.workout_visibility = VisibilityLevel.PUBLIC
        comment = self.create_comment(
            user_3, workout_cycling_user_2, VisibilityLevel.PUBLIC
        )
        report = self.create_report(reporter=user_2, reported_object=comment)
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1_moderator.email
        )

        response = client.post(
            self.route.format(report_id=report.id),
            content_type="application/json",
            json={
                "action_type": "comment_suspension",
                "comment_id": comment.short_id,
            },
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        assert response.status_code == 200
        assert (
            ReportAction.query.filter_by(
                moderator_id=user_1_moderator.id, user_id=user_3.id
            ).first()
            is not None
        )
