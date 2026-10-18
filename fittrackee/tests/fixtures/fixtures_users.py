from datetime import datetime, timezone

import pytest

from fittrackee import db
from fittrackee.users.models import FollowRequest, User
from fittrackee.users.roles import UserRole

from ..utils import generate_follow_request, random_string


@pytest.fixture()
def user_1() -> User:
    user = User(username="test", email="test@test.com", password="12345678")
    user.is_active = True
    user.hide_profile_in_users_directory = False
    user.accepted_policy_date = datetime.now(timezone.utc)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def user_1_admin(user_1: User) -> User:
    user_1.username = "admin"
    user_1.email = "admin@example.com"
    user_1.role = UserRole.ADMIN.value
    db.session.commit()
    return user_1


@pytest.fixture()
def user_1_moderator(user_1: User) -> User:
    user_1.username = "moderator"
    user_1.email = "moderator@example.com"
    user_1.role = UserRole.MODERATOR.value
    db.session.commit()
    return user_1


@pytest.fixture()
def user_1_owner(user_1: User) -> User:
    user_1.username = "owner"
    user_1.email = "owner@example.com"
    user_1.role = UserRole.OWNER.value
    db.session.commit()
    return user_1


@pytest.fixture()
def user_2() -> User:
    user = User(username="toto", email="toto@toto.com", password="12345678")
    user.is_active = True
    user.hide_profile_in_users_directory = False
    user.accepted_policy_date = datetime.now(timezone.utc)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def user_2_admin(user_2: User) -> User:
    user_2.role = UserRole.ADMIN.value
    db.session.commit()
    return user_2


@pytest.fixture()
def user_2_moderator(user_2: User) -> User:
    user_2.role = UserRole.MODERATOR.value
    db.session.commit()
    return user_2


@pytest.fixture()
def user_3() -> User:
    user = User(username="sam", email="sam@test.com", password="12345678")
    user.is_active = True
    user.hide_profile_in_users_directory = False
    user.weekm = True
    user.accepted_policy_date = datetime.now(timezone.utc)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def user_3_admin(user_3: User) -> User:
    user_3.role = UserRole.ADMIN.value
    db.session.commit()
    return user_3


@pytest.fixture()
def user_4() -> User:
    user = User(username="john", email="john@doe.com", password="12345678")
    user.is_active = True
    user.hide_profile_in_users_directory = False
    user.weekm = True
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def inactive_user() -> User:
    user = User(
        username="inactive", email="inactive@example.com", password="12345678"
    )
    user.confirmation_token = random_string()
    user.accepted_policy_date = datetime.now(timezone.utc)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def suspended_user() -> User:
    user = User(
        username="suspended_user",
        email="suspended_user@example.com",
        password="12345678",
    )
    user.is_active = True
    user.hide_profile_in_users_directory = False
    user.accepted_policy_date = datetime.now(timezone.utc)
    user.suspended_at = datetime.now(timezone.utc)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def follow_request_from_user_1_to_user_2(
    user_1: User, user_2: User
) -> FollowRequest:
    return generate_follow_request(user_1, user_2)


@pytest.fixture()
def follow_request_from_user_2_to_user_1(
    user_1: User, user_2: User
) -> FollowRequest:
    return generate_follow_request(user_2, user_1)


@pytest.fixture()
def follow_request_from_user_3_to_user_2(
    user_2: User, user_3: User
) -> FollowRequest:
    return generate_follow_request(user_3, user_2)
