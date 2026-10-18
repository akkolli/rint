"""Shared OAuth scope contracts for protected upstream API routes.

Keep route/scope expectations together. Each role scenario checks its complete
matrix with real login/token issuance and an independent scope-declaration spy.
"""

from unittest.mock import call, patch

import pytest
from flask import Flask

from fittrackee.oauth2.models import OAuth2Token
from fittrackee.oauth2.server import CustomResourceProtector
from fittrackee.users.models import User

from .mixins import ApiTestCaseMixin

# required scope, invalid token scope, HTTP method, route
SCOPE_CONTRACTS = {
    "user_1": (
        ("equipments:read", "equipments:write", "get", "/api/equipment-types"),
        (
            "equipments:read",
            "equipments:write",
            "get",
            "/api/equipment-types/999999",
        ),
        ("equipments:read", "workouts:read", "get", "/api/equipments"),
        (
            "equipments:read",
            "workouts:read",
            "get",
            "/api/equipments/C4asMMbRJsxTirSjTVWeWU",
        ),
        (
            "equipments:write",
            "equipments:read",
            "delete",
            "/api/equipments/C4asMMbRJsxTirSjTVWeWU",
        ),
        (
            "equipments:write",
            "equipments:read",
            "patch",
            "/api/equipments/C4asMMbRJsxTirSjTVWeWU",
        ),
        ("equipments:write", "equipments:read", "post", "/api/equipments"),
        ("follow:read", "workouts:read", "get", "/api/follow-requests"),
        (
            "follow:read",
            "workouts:read",
            "get",
            "/api/users/{username}/followers",
        ),
        (
            "follow:read",
            "workouts:read",
            "get",
            "/api/users/{username}/following",
        ),
        (
            "follow:write",
            "follow:read",
            "post",
            "/api/follow-requests/missing-user/accept",
        ),
        (
            "follow:write",
            "follow:read",
            "post",
            "/api/follow-requests/missing-user/reject",
        ),
        (
            "follow:write",
            "follow:read",
            "post",
            "/api/users/missing-user/follow",
        ),
        (
            "follow:write",
            "follow:read",
            "post",
            "/api/users/missing-user/unfollow",
        ),
        ("geocode:read", "workouts:read", "get", "/api/geocode/search"),
        ("geocode:read", "workouts:read", "get", "/api/geocode/lookup"),
        (
            "media:write",
            "profile:read",
            "delete",
            "/api/media/C4asMMbRJsxTirSjTVWeWU",
        ),
        (
            "media:write",
            "profile:read",
            "patch",
            "/api/media/C4asMMbRJsxTirSjTVWeWU",
        ),
        ("media:write", "profile:read", "post", "/api/media"),
        (
            "notifications:read",
            "notifications:write",
            "get",
            "/api/notifications",
        ),
        (
            "notifications:write",
            "notifications:read",
            "patch",
            "/api/notifications/C4asMMbRJsxTirSjTVWeWU",
        ),
        (
            "notifications:write",
            "notifications:read",
            "post",
            "/api/notifications/mark-all-as-read",
        ),
        (
            "profile:read",
            "profile:write",
            "get",
            "/api/auth/account/sanctions/C4asMMbRJsxTirSjTVWeWU",
        ),
        (
            "profile:read",
            "profile:write",
            "get",
            "/api/auth/account/suspension",
        ),
        ("profile:read", "profile:write", "get", "/api/auth/blocked-users"),
        ("profile:read", "profile:write", "get", "/api/auth/profile"),
        (
            "profile:write",
            "profile:read",
            "delete",
            "/api/auth/profile/reset/sports/999999",
        ),
        (
            "profile:write",
            "profile:read",
            "patch",
            "/api/auth/profile/edit/account",
        ),
        (
            "profile:write",
            "profile:read",
            "post",
            "/api/auth/account/suspension/appeal",
        ),
        ("profile:write", "profile:read", "post", "/api/auth/picture"),
        ("profile:write", "profile:read", "post", "/api/auth/profile/edit"),
        (
            "profile:write",
            "profile:read",
            "post",
            "/api/auth/profile/edit/messages",
        ),
        (
            "profile:write",
            "profile:read",
            "post",
            "/api/auth/profile/edit/notifications",
        ),
        (
            "profile:write",
            "profile:read",
            "post",
            "/api/auth/profile/edit/preferences",
        ),
        (
            "profile:write",
            "profile:read",
            "post",
            "/api/auth/profile/edit/sports",
        ),
        ("reports:write", "reports:read", "post", "/api/reports"),
        ("users:write", "users:read", "post", "/api/users/missing-user/block"),
        (
            "users:write",
            "users:read",
            "post",
            "/api/users/missing-user/unblock",
        ),
        (
            "workouts:read",
            "workouts:write",
            "get",
            "/api/comments/C4asMMbRJsxTirSjTVWeWU",
        ),
        (
            "workouts:read",
            "workouts:write",
            "get",
            "/api/comments/C4asMMbRJsxTirSjTVWeWU/likes",
        ),
        ("workouts:read", "workouts:write", "get", "/api/sports"),
        ("workouts:read", "workouts:write", "get", "/api/sports/999999"),
        (
            "workouts:read",
            "workouts:write",
            "get",
            "/api/stats/{username}/by_sport",
        ),
        (
            "workouts:read",
            "workouts:write",
            "get",
            "/api/stats/{username}/by_time",
        ),
        ("workouts:read", "workouts:write", "get", "/api/timeline"),
        (
            "workouts:read",
            "workouts:write",
            "get",
            "/api/users/{username}/workouts",
        ),
        ("workouts:read", "workouts:write", "get", "/api/workouts"),
        (
            "workouts:read",
            "workouts:write",
            "get",
            "/api/workouts/C4asMMbRJsxTirSjTVWeWU",
        ),
        (
            "workouts:read",
            "workouts:write",
            "get",
            "/api/workouts/C4asMMbRJsxTirSjTVWeWU/chart_data",
        ),
        (
            "workouts:read",
            "workouts:write",
            "get",
            "/api/workouts/C4asMMbRJsxTirSjTVWeWU/chart_data/segment/1",
        ),
        (
            "workouts:read",
            "workouts:write",
            "get",
            "/api/workouts/C4asMMbRJsxTirSjTVWeWU/comments",
        ),
        (
            "workouts:read",
            "workouts:write",
            "get",
            "/api/workouts/C4asMMbRJsxTirSjTVWeWU/gpx",
        ),
        (
            "workouts:read",
            "workouts:write",
            "get",
            "/api/workouts/C4asMMbRJsxTirSjTVWeWU/gpx/download",
        ),
        (
            "workouts:read",
            "workouts:write",
            "get",
            "/api/workouts/C4asMMbRJsxTirSjTVWeWU/gpx/segment/1",
        ),
        (
            "workouts:read",
            "workouts:write",
            "get",
            "/api/workouts/C4asMMbRJsxTirSjTVWeWU/likes",
        ),
        (
            "workouts:read",
            "workouts:write",
            "get",
            "/api/workouts/C4asMMbRJsxTirSjTVWeWU/original/download",
        ),
        ("workouts:read", "workouts:write", "get", "/api/workouts/collection"),
        ("workouts:read", "workouts:write", "get", "/api/workouts/global-map"),
        (
            "workouts:read",
            "workouts:write",
            "get",
            "/api/workouts/upload-tasks",
        ),
        (
            "workouts:read",
            "workouts:write",
            "get",
            "/api/workouts/upload-tasks/C4asMMbRJsxTirSjTVWeWU",
        ),
        (
            "workouts:read",
            "workouts:write",
            "get",
            "/api/workouts/upload-tasks/C4asMMbRJsxTirSjTVWeWU",
        ),
        (
            "workouts:write",
            "workouts:read",
            "delete",
            "/api/comments/C4asMMbRJsxTirSjTVWeWU",
        ),
        (
            "workouts:write",
            "workouts:read",
            "delete",
            "/api/workouts/C4asMMbRJsxTirSjTVWeWU",
        ),
        (
            "workouts:write",
            "workouts:read",
            "patch",
            "/api/comments/C4asMMbRJsxTirSjTVWeWU",
        ),
        (
            "workouts:write",
            "workouts:read",
            "patch",
            "/api/workouts/C4asMMbRJsxTirSjTVWeWU",
        ),
        (
            "workouts:write",
            "workouts:read",
            "post",
            "/api/comments/C4asMMbRJsxTirSjTVWeWU/like",
        ),
        (
            "workouts:write",
            "workouts:read",
            "post",
            "/api/comments/C4asMMbRJsxTirSjTVWeWU/like/undo",
        ),
        (
            "workouts:write",
            "workouts:read",
            "post",
            "/api/comments/C4asMMbRJsxTirSjTVWeWU/suspension/appeal",
        ),
        ("workouts:write", "workouts:read", "post", "/api/workouts"),
        (
            "workouts:write",
            "workouts:read",
            "post",
            "/api/workouts/C4asMMbRJsxTirSjTVWeWU/comments",
        ),
        (
            "workouts:write",
            "workouts:read",
            "post",
            "/api/workouts/C4asMMbRJsxTirSjTVWeWU/like",
        ),
        (
            "workouts:write",
            "workouts:read",
            "post",
            "/api/workouts/C4asMMbRJsxTirSjTVWeWU/like/undo",
        ),
        (
            "workouts:write",
            "workouts:read",
            "post",
            "/api/workouts/C4asMMbRJsxTirSjTVWeWU/suspension/appeal",
        ),
        ("workouts:write", "workouts:read", "post", "/api/workouts/no_gpx"),
        (
            "workouts:write",
            "workouts:read",
            "post",
            "/api/workouts/upload-tasks/C4asMMbRJsxTirSjTVWeWU/abort",
        ),
    ),
    "user_1_admin": (
        ("application:write", "workouts:read", "patch", "/api/config"),
        (
            "equipments:write",
            "equipments:read",
            "patch",
            "/api/equipment-types/999999",
        ),
        (
            "notifications:read",
            "notifications:write",
            "get",
            "/api/notifications/unread",
        ),
        (
            "profile:write",
            "profile:read",
            "post",
            "/api/auth/account/sanctions/C4asMMbRJsxTirSjTVWeWU/appeal",
        ),
        ("reports:read", "reports:write", "get", "/api/reports/999999"),
        ("users:read", "users:write", "get", "/api/users"),
        ("users:read", "users:write", "get", "/api/users/not_existing"),
        ("users:read", "users:write", "get", "api/users/tasks/queued"),
        (
            "users:read",
            "users:write",
            "get",
            "api/users/tasks/queued/workouts_archive_upload",
        ),
        ("users:write", "users:read", "delete", "/api/users/missing-user"),
        ("users:write", "users:read", "patch", "/api/users/{username}"),
        ("workouts:read", "workouts:write", "get", "/api/records"),
        ("workouts:read", "workouts:write", "get", "/api/stats/all"),
        ("workouts:write", "workouts:read", "patch", "/api/sports/999999"),
    ),
    "user_1_moderator": (
        ("reports:read", "reports:write", "get", "/api/reports"),
        ("reports:read", "reports:write", "get", "/api/reports/unresolved"),
        ("users:write", "users:read", "patch", "/api/appeals/999999"),
    ),
}


@pytest.fixture
def scope_user(request: pytest.FixtureRequest) -> tuple[str, User]:
    return request.param, request.getfixturevalue(request.param)


class TestOAuthScopeContracts(ApiTestCaseMixin):
    @pytest.mark.parametrize(
        "scope_user",
        SCOPE_CONTRACTS,
        indirect=True,
        ids=["user", "admin", "moderator"],
    )
    def test_protected_routes_require_their_declared_scope(
        self,
        app: Flask,
        scope_user: tuple[str, User],
    ) -> None:
        role_fixture, user = scope_user
        tokens = {}
        for required, invalid, method, route in SCOPE_CONTRACTS[role_fixture]:
            if invalid not in tokens:
                client, _, token, _ = (
                    self.create_oauth2_client_and_issue_token(
                        app,
                        user,
                        scope=invalid,
                    )
                )
                tokens[invalid] = (client, token)
            client, token = tokens[invalid]
            with patch.object(
                CustomResourceProtector,
                "acquire_token",
                return_value=OAuth2Token(),
            ) as acquire_token:
                getattr(client, method)(
                    route.format(username=user.username),
                    headers={"Authorization": f"Bearer {token}"},
                )
            assert acquire_token.call_args_list == [call([required])], (
                f"{method.upper()} {route}: expected {required}"
            )
