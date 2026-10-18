import json
import os
from io import BytesIO
from typing import TYPE_CHECKING, Dict, Optional

from flask import Flask

from fittrackee.tests.custom_asserts import assert_response
from fittrackee.users.models import User, UserTask

from ..mixins import MediaMixin, UserTaskMixin
from ..utils import jsonify_dict
from .mixins import (
    WorkoutApiTestCaseMixin,
    WorkoutFileMixin,
    WorkoutGpxInfoMixin,
)

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from fittrackee.workouts.models import Sport


def assert_workout_data_with_gpx(data: Dict, user: User) -> None:
    assert "creation_date" in data["data"]["workouts"][0]
    assert (
        "Tue, 13 Mar 2018 12:44:45 GMT"
        == data["data"]["workouts"][0]["workout_date"]
    )
    assert data["data"]["workouts"][0]["user"] == jsonify_dict(
        user.serialize()
    )
    assert 1 == data["data"]["workouts"][0]["sport_id"]
    assert "0:04:10" == data["data"]["workouts"][0]["duration"]
    assert data["data"]["workouts"][0]["ascent"] == 0.4
    assert data["data"]["workouts"][0]["ave_speed"] == 4.61
    assert data["data"]["workouts"][0]["bounds"] == [
        44.67822,
        6.07355,
        44.68095,
        6.07442,
    ]
    assert data["data"]["workouts"][0]["descent"] == 23.4
    assert data["data"]["workouts"][0]["description"] is None
    assert data["data"]["workouts"][0]["distance"] == 0.32
    assert data["data"]["workouts"][0]["max_alt"] == 998.0
    assert data["data"]["workouts"][0]["max_speed"] == 5.12
    assert data["data"]["workouts"][0]["min_alt"] == 975.0
    assert data["data"]["workouts"][0]["moving"] == "0:04:10"
    assert data["data"]["workouts"][0]["pauses"] is None
    assert data["data"]["workouts"][0]["with_file"] is True
    assert data["data"]["workouts"][0]["map"] is not None
    assert data["data"]["workouts"][0]["weather_start"] is None
    assert data["data"]["workouts"][0]["weather_end"] is None
    assert data["data"]["workouts"][0]["notes"] is None
    assert len(data["data"]["workouts"][0]["segments"]) == 1

    segment = data["data"]["workouts"][0]["segments"][0]
    assert segment["workout_id"] == data["data"]["workouts"][0]["id"]
    assert segment["segment_id"] is not None
    assert segment["duration"] == "0:04:10"
    assert segment["ascent"] == 0.4
    assert segment["ave_speed"] == 4.61
    assert segment["descent"] == 23.4
    assert segment["distance"] == 0.32
    assert segment["max_alt"] == 998.0
    assert segment["max_speed"] == 5.12
    assert segment["min_alt"] == 975.0
    assert segment["moving"] == "0:04:10"
    assert segment["pauses"] is None

    records = data["data"]["workouts"][0]["records"]
    assert len(records) == 5
    assert records[0]["sport_id"] == 1
    assert records[0]["workout_id"] == data["data"]["workouts"][0]["id"]
    assert records[0]["record_type"] == "AS"
    assert records[0]["workout_date"] == "Tue, 13 Mar 2018 12:44:45 GMT"
    assert records[0]["value"] == 4.61
    assert records[1]["sport_id"] == 1
    assert records[1]["workout_id"] == data["data"]["workouts"][0]["id"]
    assert records[1]["record_type"] == "FD"
    assert records[1]["workout_date"] == "Tue, 13 Mar 2018 12:44:45 GMT"
    assert records[1]["value"] == 0.32
    assert records[2]["sport_id"] == 1
    assert records[2]["workout_id"] == data["data"]["workouts"][0]["id"]
    assert records[2]["record_type"] == "HA"
    assert records[2]["value"] == 0.4
    assert records[2]["workout_date"] == "Tue, 13 Mar 2018 12:44:45 GMT"
    assert records[3]["sport_id"] == 1
    assert records[3]["workout_id"] == data["data"]["workouts"][0]["id"]
    assert records[3]["record_type"] == "LD"
    assert records[3]["workout_date"] == "Tue, 13 Mar 2018 12:44:45 GMT"
    assert records[3]["value"] == "0:04:10"
    assert records[4]["sport_id"] == 1
    assert records[4]["workout_id"] == data["data"]["workouts"][0]["id"]
    assert records[4]["record_type"] == "MS"
    assert records[4]["workout_date"] == "Tue, 13 Mar 2018 12:44:45 GMT"
    assert records[4]["value"] == 5.12


def assert_workout_data_with_gpx_segments(data: Dict, user: User) -> None:
    assert "creation_date" in data["data"]["workouts"][0]
    assert (
        "Tue, 13 Mar 2018 12:44:45 GMT"
        == data["data"]["workouts"][0]["workout_date"]
    )
    assert data["data"]["workouts"][0]["user"] == jsonify_dict(
        user.serialize()
    )
    assert 1 == data["data"]["workouts"][0]["sport_id"]
    assert "0:04:10" == data["data"]["workouts"][0]["duration"]
    assert data["data"]["workouts"][0]["ascent"] == 0.4
    assert data["data"]["workouts"][0]["ave_speed"] == 4.59
    assert data["data"]["workouts"][0]["descent"] == 23.4
    assert data["data"]["workouts"][0]["description"] is None
    assert data["data"]["workouts"][0]["distance"] == 0.3
    assert data["data"]["workouts"][0]["max_alt"] == 998.0
    assert data["data"]["workouts"][0]["max_speed"] == 5.25
    assert data["data"]["workouts"][0]["min_alt"] == 975.0
    assert data["data"]["workouts"][0]["moving"] == "0:03:55"
    assert data["data"]["workouts"][0]["pauses"] == "0:00:15"
    assert data["data"]["workouts"][0]["with_file"] is True
    assert data["data"]["workouts"][0]["map"] is not None
    assert data["data"]["workouts"][0]["weather_start"] is None
    assert data["data"]["workouts"][0]["weather_end"] is None
    assert data["data"]["workouts"][0]["notes"] is None
    assert len(data["data"]["workouts"][0]["segments"]) == 2

    segment = data["data"]["workouts"][0]["segments"][0]
    assert segment["workout_id"] == data["data"]["workouts"][0]["id"]
    assert segment["segment_id"] is not None
    assert segment["duration"] == "0:01:30"
    assert segment["ascent"] == 0
    assert segment["ave_speed"] == 4.53
    assert segment["descent"] == 11.0
    assert segment["distance"] == 0.113
    assert segment["max_alt"] == 998.0
    assert segment["max_speed"] == 5.25
    assert segment["min_alt"] == 987.0
    assert segment["moving"] == "0:01:30"
    assert segment["pauses"] is None

    segment = data["data"]["workouts"][0]["segments"][1]
    assert segment["workout_id"] == data["data"]["workouts"][0]["id"]
    assert segment["segment_id"] is not None
    assert segment["duration"] == "0:02:25"
    assert segment["ascent"] == 0.4
    assert segment["ave_speed"] == 4.62
    assert segment["descent"] == 12.4
    assert segment["distance"] == 0.186
    assert segment["max_alt"] == 987.0
    assert segment["max_speed"] == 5.12
    assert segment["min_alt"] == 975.0
    assert segment["moving"] == "0:02:25"
    assert segment["pauses"] is None

    records = data["data"]["workouts"][0]["records"]
    assert len(records) == 5
    assert records[0]["sport_id"] == 1
    assert records[0]["workout_id"] == data["data"]["workouts"][0]["id"]
    assert records[0]["record_type"] == "AS"
    assert records[0]["workout_date"] == "Tue, 13 Mar 2018 12:44:45 GMT"
    assert records[0]["value"] == 4.59
    assert records[1]["sport_id"] == 1
    assert records[1]["workout_id"] == data["data"]["workouts"][0]["id"]
    assert records[1]["record_type"] == "FD"
    assert records[1]["workout_date"] == "Tue, 13 Mar 2018 12:44:45 GMT"
    assert records[1]["value"] == 0.3
    assert records[2]["sport_id"] == 1
    assert records[2]["workout_id"] == data["data"]["workouts"][0]["id"]
    assert records[2]["record_type"] == "HA"
    assert records[2]["workout_date"] == "Tue, 13 Mar 2018 12:44:45 GMT"
    assert records[2]["value"] == 0.4
    assert records[3]["sport_id"] == 1
    assert records[3]["workout_id"] == data["data"]["workouts"][0]["id"]
    assert records[3]["record_type"] == "LD"
    assert records[3]["workout_date"] == "Tue, 13 Mar 2018 12:44:45 GMT"
    assert records[3]["value"] == "0:03:55"
    assert records[4]["sport_id"] == 1
    assert records[4]["workout_id"] == data["data"]["workouts"][0]["id"]
    assert records[4]["record_type"] == "MS"
    assert records[4]["workout_date"] == "Tue, 13 Mar 2018 12:44:45 GMT"
    assert records[4]["value"] == 5.25


def assert_workout_data_wo_gpx(data: Dict, user: User) -> None:
    assert "creation_date" in data["data"]["workouts"][0]
    assert (
        data["data"]["workouts"][0]["workout_date"]
        == "Tue, 15 May 2018 14:05:00 GMT"
    )
    assert data["data"]["workouts"][0]["user"] == jsonify_dict(
        user.serialize()
    )
    assert data["data"]["workouts"][0]["sport_id"] == 1
    assert data["data"]["workouts"][0]["duration"] == "1:00:00"
    assert (
        data["data"]["workouts"][0]["title"]
        == "Cycling (Sport) - 2018-05-15 14:05:00"
    )
    assert data["data"]["workouts"][0]["ascent"] is None
    assert data["data"]["workouts"][0]["ave_speed"] == 10.0
    assert data["data"]["workouts"][0]["descent"] is None
    assert data["data"]["workouts"][0]["description"] is None
    assert data["data"]["workouts"][0]["distance"] == 10.0
    assert data["data"]["workouts"][0]["max_alt"] is None
    assert data["data"]["workouts"][0]["max_speed"] == 10.0
    assert data["data"]["workouts"][0]["min_alt"] is None
    assert data["data"]["workouts"][0]["moving"] == "1:00:00"
    assert data["data"]["workouts"][0]["pauses"] is None
    assert data["data"]["workouts"][0]["with_file"] is False
    assert data["data"]["workouts"][0]["map"] is None
    assert data["data"]["workouts"][0]["weather_start"] is None
    assert data["data"]["workouts"][0]["weather_end"] is None
    assert data["data"]["workouts"][0]["notes"] is None

    assert len(data["data"]["workouts"][0]["segments"]) == 0

    records = data["data"]["workouts"][0]["records"]
    assert len(records) == 4
    assert records[0]["sport_id"] == 1
    assert records[0]["workout_id"] == data["data"]["workouts"][0]["id"]
    assert records[0]["record_type"] == "AS"
    assert records[0]["workout_date"] == "Tue, 15 May 2018 14:05:00 GMT"
    assert records[0]["value"] == 10.0
    assert records[1]["sport_id"] == 1
    assert records[1]["workout_id"] == data["data"]["workouts"][0]["id"]
    assert records[1]["record_type"] == "FD"
    assert records[1]["workout_date"] == "Tue, 15 May 2018 14:05:00 GMT"
    assert records[1]["value"] == 10.0
    assert records[2]["sport_id"] == 1
    assert records[2]["workout_id"] == data["data"]["workouts"][0]["id"]
    assert records[2]["record_type"] == "LD"
    assert records[2]["workout_date"] == "Tue, 15 May 2018 14:05:00 GMT"
    assert records[2]["value"] == "1:00:00"
    assert records[3]["sport_id"] == 1
    assert records[3]["workout_id"] == data["data"]["workouts"][0]["id"]
    assert records[3]["record_type"] == "MS"
    assert records[3]["workout_date"] == "Tue, 15 May 2018 14:05:00 GMT"
    assert records[3]["value"] == 10.0


def assert_files_are_deleted(
    app: "Flask", user: User, expected_count: Optional[int] = 0
) -> None:
    upload_directory = os.path.join(
        app.config["UPLOAD_FOLDER"], f"workouts/{user.id}"
    )
    assert (
        len(
            [
                name
                for name in os.listdir(upload_directory)
                if os.path.isfile(os.path.join(upload_directory, name))
            ]
        )
        == expected_count
    )


class TestPostWorkoutWithGpx(
    WorkoutGpxInfoMixin, WorkoutApiTestCaseMixin, MediaMixin
):
    def test_it_returns_error_if_user_is_not_authenticated(
        self, app: "Flask", sport_1_cycling: "Sport", gpx_file: str
    ) -> None:
        client = app.test_client()

        response = client.post(
            "/api/workouts",
            data=dict(
                file=(BytesIO(str.encode(gpx_file)), "example.gpx"),
                data='{"sport_id": 1}',
            ),
            headers=dict(content_type="multipart/form-data"),
        )

        self.assert_401(response)

    def test_it_returns_error_when_user_is_suspended(
        self,
        app: "Flask",
        suspended_user: "User",
        sport_1_cycling: "Sport",
        gpx_file: str,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, suspended_user.email
        )

        response = client.post(
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

        self.assert_403(response)

    def test_it_returns_500_if_gpx_has_invalid_xml(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        gpx_file_invalid_xml: str,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
            "/api/workouts",
            data=dict(
                file=(
                    BytesIO(str.encode(gpx_file_invalid_xml)),
                    "example.gpx",
                ),
                data='{"sport_id": 1}',
            ),
            headers=dict(
                content_type="multipart/form-data",
                Authorization=f"Bearer {auth_token}",
            ),
        )

        data = self.assert_500(response, "error when parsing gpx file")
        assert "data" not in data

    def test_it_returns_error_when_file_size_exceeds_limit(
        self,
        app_with_max_file_size: Flask,
        user_1: "User",
        sport_1_cycling: "Sport",
        gpx_file: str,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app_with_max_file_size, user_1.email
        )

        response = client.post(
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

        data = self.assert_413(
            response,
            match=(
                r"Error during workout upload, "
                r"file size \((.*)\) exceeds 1.0KB."
            ),
        )
        assert "data" not in data


class TestPostWorkoutWithKml(WorkoutApiTestCaseMixin):
    def test_it_adds_a_workout_with_kml_file(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        kml_2_3_with_one_track: str,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
            "/api/workouts",
            data=dict(
                file=(
                    BytesIO(str.encode(kml_2_3_with_one_track)),
                    "example.kml",
                ),
                data='{"sport_id": 1}',
            ),
            headers=dict(
                content_type="multipart/form-data",
                Authorization=f"Bearer {auth_token}",
            ),
        )

        data = assert_response(response, 201, contains={"status": "created"})
        assert len(data["data"]["workouts"]) == 1
        assert data["data"]["workouts"][0]["title"] == "just a workout"
        assert data["data"]["workouts"][0]["sport_id"] == 1
        assert data["data"]["workouts"][0]["duration"] == "0:04:10"
        assert data["data"]["workouts"][0]["ascent"] == 0.4
        assert data["data"]["workouts"][0]["ave_speed"] == 4.61
        assert data["data"]["workouts"][0]["descent"] == 23.4
        assert data["data"]["workouts"][0]["description"] == "some description"
        assert data["data"]["workouts"][0]["distance"] == 0.32
        assert data["data"]["workouts"][0]["max_alt"] == 998.0
        assert data["data"]["workouts"][0]["max_speed"] == 5.25
        assert data["data"]["workouts"][0]["min_alt"] == 975.0
        assert data["data"]["workouts"][0]["moving"] == "0:04:10"
        assert data["data"]["workouts"][0]["pauses"] is None
        assert data["data"]["workouts"][0]["with_file"] is True
        assert data["data"]["workouts"][0]["map"] is not None
        assert data["data"]["workouts"][0]["weather_start"] is None
        assert data["data"]["workouts"][0]["weather_end"] is None
        assert data["data"]["workouts"][0]["notes"] is None
        assert len(data["data"]["workouts"][0]["segments"]) == 1


class TestPostWorkoutWithKmz(WorkoutApiTestCaseMixin):
    def test_it_adds_a_workout_with_kmz_file(
        self, app: "Flask", user_1: "User", sport_1_cycling: "Sport"
    ) -> None:
        file_path = os.path.join(app.root_path, "tests/files/example.kmz")
        with open(file_path, "rb") as kmz_file:
            client, auth_token = self.get_test_client_and_auth_token(
                app, user_1.email
            )

            response = client.post(
                "/api/workouts",
                data=dict(
                    file=(kmz_file, "example.kmz"), data='{"sport_id": 1}'
                ),
                headers=dict(
                    content_type="multipart/form-data",
                    Authorization=f"Bearer {auth_token}",
                ),
            )

        data = assert_response(response, 201, contains={"status": "created"})
        assert len(data["data"]["workouts"]) == 1
        assert data["data"]["workouts"][0]["title"] == "just a workout"
        assert data["data"]["workouts"][0]["sport_id"] == 1
        assert data["data"]["workouts"][0]["duration"] == "0:04:10"
        assert data["data"]["workouts"][0]["ascent"] == 0.4
        assert data["data"]["workouts"][0]["ave_speed"] == 4.59
        assert data["data"]["workouts"][0]["descent"] == 23.4
        assert data["data"]["workouts"][0]["description"] == "some description"
        assert data["data"]["workouts"][0]["distance"] == 0.299
        assert data["data"]["workouts"][0]["max_alt"] == 998.0
        assert data["data"]["workouts"][0]["max_speed"] == 5.41
        assert data["data"]["workouts"][0]["min_alt"] == 975.0
        assert data["data"]["workouts"][0]["moving"] == "0:03:55"
        assert data["data"]["workouts"][0]["pauses"] == "0:00:15"
        assert data["data"]["workouts"][0]["with_file"] is True
        assert data["data"]["workouts"][0]["map"] is not None
        assert data["data"]["workouts"][0]["weather_start"] is None
        assert data["data"]["workouts"][0]["weather_end"] is None
        assert data["data"]["workouts"][0]["notes"] is None
        assert len(data["data"]["workouts"][0]["segments"]) == 2


class TestPostWorkoutWithTcx(WorkoutApiTestCaseMixin):
    def test_it_adds_a_workout_with_tcx_file(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        tcx_with_one_lap_and_one_track: str,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
            "/api/workouts",
            data=dict(
                file=(
                    BytesIO(str.encode(tcx_with_one_lap_and_one_track)),
                    "example.tcx",
                ),
                data='{"sport_id": 1}',
            ),
            headers=dict(
                content_type="multipart/form-data",
                Authorization=f"Bearer {auth_token}",
            ),
        )

        data = assert_response(response, 201, contains={"status": "created"})
        assert len(data["data"]["workouts"]) == 1
        assert data["data"]["workouts"][0]["title"] is not None
        assert data["data"]["workouts"][0]["sport_id"] == 1
        assert data["data"]["workouts"][0]["duration"] == "0:04:10"
        assert data["data"]["workouts"][0]["ascent"] == 0.0
        assert data["data"]["workouts"][0]["ave_speed"] == 4.58
        assert data["data"]["workouts"][0]["descent"] == 21.0
        assert data["data"]["workouts"][0]["description"] is None
        assert data["data"]["workouts"][0]["distance"] == 0.318
        assert data["data"]["workouts"][0]["max_alt"] == 997.0
        assert data["data"]["workouts"][0]["max_speed"] == 5.11
        assert data["data"]["workouts"][0]["min_alt"] == 976.0
        assert data["data"]["workouts"][0]["moving"] == "0:04:10"
        assert data["data"]["workouts"][0]["pauses"] is None
        assert data["data"]["workouts"][0]["with_file"] is True
        assert data["data"]["workouts"][0]["map"] is not None
        assert data["data"]["workouts"][0]["weather_start"] is None
        assert data["data"]["workouts"][0]["weather_end"] is None
        assert data["data"]["workouts"][0]["notes"] is None
        assert len(data["data"]["workouts"][0]["segments"]) == 1


class TestPostWorkoutWithFit(WorkoutApiTestCaseMixin, WorkoutFileMixin):
    def test_it_adds_a_workout_with_fit_file(
        self, app: "Flask", user_1: "User", sport_1_cycling: "Sport"
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
            "/api/workouts",
            data=dict(
                file=(
                    self.get_fit_file_content(app, "example.fit"),
                    "example.fit",
                ),
                data='{"sport_id": 1}',
            ),
            headers=dict(
                content_type="multipart/form-data",
                Authorization=f"Bearer {auth_token}",
            ),
        )

        data = assert_response(response, 201, contains={"status": "created"})
        assert len(data["data"]["workouts"]) == 1
        assert data["data"]["workouts"][0]["title"] is not None
        assert data["data"]["workouts"][0]["sport_id"] == 1
        assert data["data"]["workouts"][0]["duration"] == "0:04:10"
        assert data["data"]["workouts"][0]["ascent"] == 0.0
        assert data["data"]["workouts"][0]["ave_speed"] == 4.58
        assert data["data"]["workouts"][0]["descent"] == 21.0
        assert data["data"]["workouts"][0]["description"] is None
        assert data["data"]["workouts"][0]["distance"] == 0.318
        assert data["data"]["workouts"][0]["max_alt"] == 997.0
        assert data["data"]["workouts"][0]["max_speed"] == 5.11
        assert data["data"]["workouts"][0]["min_alt"] == 976.0
        assert data["data"]["workouts"][0]["moving"] == "0:04:10"
        assert data["data"]["workouts"][0]["pauses"] is None
        assert data["data"]["workouts"][0]["with_file"] is True
        assert data["data"]["workouts"][0]["map"] is not None
        assert data["data"]["workouts"][0]["weather_start"] is None
        assert data["data"]["workouts"][0]["weather_end"] is None
        assert data["data"]["workouts"][0]["notes"] is None
        assert len(data["data"]["workouts"][0]["segments"]) == 1

    def test_it_adds_a_workout_with_apple_watch_fit_file(
        self, app: "Flask", user_1: "User", sport_1_cycling: "Sport"
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
            "/api/workouts",
            data=dict(
                file=(
                    self.get_fit_file_content(app, "apple_watch.fit"),
                    "apple_watch.fit",
                ),
                data='{"sport_id": 1}',
            ),
            headers=dict(
                content_type="multipart/form-data",
                Authorization=f"Bearer {auth_token}",
            ),
        )

        data = assert_response(response, 201, contains={"status": "created"})
        assert len(data["data"]["workouts"]) == 1
        assert data["data"]["workouts"][0]["title"] is not None
        assert data["data"]["workouts"][0]["sport_id"] == 1
        assert data["data"]["workouts"][0]["duration"] == "0:05:35"
        assert data["data"]["workouts"][0]["with_file"] is True
        assert data["data"]["workouts"][0]["map"] is not None
        assert data["data"]["workouts"][0]["calories"] == 32


class TestPostWorkoutWithZipArchive(
    UserTaskMixin, WorkoutApiTestCaseMixin, MediaMixin
):
    def test_it_adds_workouts_synchronously_with_zip_archive(
        self, app: "Flask", user_1: "User", sport_1_cycling: "Sport"
    ) -> None:
        # 'gpx_test.zip' contains 3 gpx files (same data) and 1 non-gpx file
        file_path = os.path.join(app.root_path, "tests/files/gpx_test.zip")
        with open(file_path, "rb") as zip_file:
            client, auth_token = self.get_test_client_and_auth_token(
                app, user_1.email
            )

            response = client.post(
                "/api/workouts",
                data=dict(
                    file=(zip_file, "gpx_test.zip"), data='{"sport_id": 1}'
                ),
                headers=dict(
                    content_type="multipart/form-data",
                    Authorization=f"Bearer {auth_token}",
                ),
            )

            data = assert_response(
                response, 201, contains={"status": "created"}
            )
            assert len(data["data"]["workouts"]) == 3
            assert "creation_date" in data["data"]["workouts"][0]
            assert (
                "Tue, 13 Mar 2018 12:44:45 GMT"
                == data["data"]["workouts"][0]["workout_date"]
            )
            assert data["data"]["workouts"][0]["user"] == jsonify_dict(
                user_1.serialize()
            )
            assert 1 == data["data"]["workouts"][0]["sport_id"]
            assert "0:04:10" == data["data"]["workouts"][0]["duration"]
            assert data["data"]["workouts"][0]["ascent"] == 0.4
            assert data["data"]["workouts"][0]["ave_speed"] == 4.61
            assert data["data"]["workouts"][0]["descent"] == 23.4
            assert data["data"]["workouts"][0]["description"] is None
            assert data["data"]["workouts"][0]["distance"] == 0.32
            assert data["data"]["workouts"][0]["max_alt"] == 998.0
            assert data["data"]["workouts"][0]["max_speed"] == 5.12
            assert data["data"]["workouts"][0]["min_alt"] == 975.0
            assert data["data"]["workouts"][0]["moving"] == "0:04:10"
            assert data["data"]["workouts"][0]["pauses"] is None
            assert data["data"]["workouts"][0]["with_file"] is True
            assert data["data"]["workouts"][0]["map"] is not None
            assert data["data"]["workouts"][0]["weather_start"] is None
            assert data["data"]["workouts"][0]["weather_end"] is None
            assert data["data"]["workouts"][0]["notes"] is None
            assert len(data["data"]["workouts"][0]["segments"]) == 1

            segment = data["data"]["workouts"][0]["segments"][0]
            assert segment["workout_id"] == data["data"]["workouts"][0]["id"]
            assert segment["segment_id"] is not None
            assert segment["duration"] == "0:04:10"
            assert segment["ascent"] == 0.4
            assert segment["ave_speed"] == 4.61
            assert segment["descent"] == 23.4
            assert segment["distance"] == 0.32
            assert segment["max_alt"] == 998.0
            assert segment["max_speed"] == 5.12
            assert segment["min_alt"] == 975.0
            assert segment["moving"] == "0:04:10"
            assert segment["pauses"] is None

    def test_it_creates_task_to_add_workouts_asynchronously_when_files_exceed_limit(  # noqa
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        upload_workouts_archive_mock: "MagicMock",
    ) -> None:
        app.config.update(
            {"file_limit_import": 3, "file_sync_limit_import": 2}
        )
        # 'gpx_test.zip' contains 3 gpx files (same data) and 1 non-gpx file
        file_path = os.path.join(app.root_path, "tests/files/gpx_test.zip")
        with open(file_path, "rb") as zip_file:
            client, auth_token = self.get_test_client_and_auth_token(
                app, user_1.email
            )

            response = client.post(
                "/api/workouts",
                data=dict(
                    file=(zip_file, "gpx_test.zip"), data='{"sport_id": 1}'
                ),
                headers=dict(
                    content_type="multipart/form-data",
                    Authorization=f"Bearer {auth_token}",
                ),
            )

            data = assert_response(
                response, 200, contains={"status": "in_progress"}
            )
            upload_task = UserTask.query.filter_by(
                user_id=user_1.id, task_type="workouts_archive_upload"
            ).one()
            upload_workouts_archive_mock.send.assert_called_once_with(
                task_id=upload_task.id
            )
            assert data["data"] == {"task_id": upload_task.short_id}

    def test_it_returns_400_when_files_in_archive_exceed_limit(
        self,
        app_with_max_workouts: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
    ) -> None:
        file_path = os.path.join(
            app_with_max_workouts.root_path, "tests/files/gpx_test.zip"
        )
        # 'gpx_test.zip' contains 3 gpx files (same data) and 1 non-gpx file
        with open(file_path, "rb") as zip_file:
            client, auth_token = self.get_test_client_and_auth_token(
                app_with_max_workouts, user_1.email
            )

            response = client.post(
                "/api/workouts",
                data=dict(
                    file=(zip_file, "gpx_test.zip"), data='{"sport_id": 1}'
                ),
                headers=dict(
                    content_type="multipart/form-data",
                    Authorization=f"Bearer {auth_token}",
                ),
            )

            self.assert_400(
                response,
                "the number of files in the archive exceeds the limit",
                "fail",
            )

    def test_it_returns_413_if_archive_size_exceeds_limit(
        self,
        app_with_max_zip_file_size: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
    ) -> None:
        # 'gpx_test.zip' contains 3 gpx files (same data) and 1 non-gpx file
        file_path = os.path.join(
            app_with_max_zip_file_size.root_path, "tests/files/gpx_test.zip"
        )
        with open(file_path, "rb") as zip_file:
            client, auth_token = self.get_test_client_and_auth_token(
                app_with_max_zip_file_size, user_1.email
            )

            response = client.post(
                "/api/workouts",
                data=dict(
                    file=(zip_file, "gpx_test.zip"), data='{"sport_id": 1}'
                ),
                headers=dict(
                    content_type="multipart/form-data",
                    Authorization=f"Bearer {auth_token}",
                ),
            )

            data = self.assert_413(
                response,
                "Error during workout upload, "
                "file size (2.5KB) exceeds 1.0KB.",
            )
            assert "data" not in data


class TestPostAndGetWorkoutWithFile(WorkoutApiTestCaseMixin):
    def workout_assertion(
        self, app: "Flask", user_1: "User", gpx_file: str, with_segments: bool
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )
        response = client.post(
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

        data = json.loads(response.data.decode())
        assert response.status_code == 201
        assert "created" in data["status"]
        assert len(data["data"]["workouts"]) == 1
        assert "just a workout" == data["data"]["workouts"][0]["title"]
        if with_segments:
            assert_workout_data_with_gpx_segments(data, user_1)
        else:
            assert_workout_data_with_gpx(data, user_1)
        map_id = data["data"]["workouts"][0]["map"]
        workout_short_id = data["data"]["workouts"][0]["id"]
        segment_short_id = data["data"]["workouts"][0]["segments"][0][
            "segment_id"
        ]

        response = client.get(
            f"/api/workouts/{workout_short_id}/geojson",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert response.status_code == 200
        assert "success" in data["status"]
        assert "" in data["message"]
        assert isinstance(data["data"]["geojson"], dict)

        response = client.get(
            f"/api/workouts/{workout_short_id}/geojson/segment/{segment_short_id}",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )
        data = json.loads(response.data.decode())

        assert response.status_code == 200
        assert "success" in data["status"]
        assert "" in data["message"]
        assert isinstance(data["data"]["geojson"], dict)

        response = client.get(
            f"/api/workouts/map/{map_id}",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )
        assert response.status_code == 200

    def test_it_gets_a_workout_created_with_gpx(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        gpx_file: str,
    ) -> None:
        return self.workout_assertion(app, user_1, gpx_file, False)

    def test_it_gets_a_workout_created_with_gpx_with_segments(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        gpx_file_with_segments: str,
    ) -> None:
        return self.workout_assertion(
            app, user_1, gpx_file_with_segments, True
        )

    def test_it_gets_chart_data_for_a_workout_created_with_gpx(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        gpx_file: str,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
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
        data = json.loads(response.data.decode())
        workout_short_id = data["data"]["workouts"][0]["id"]
        response = client.get(
            f"/api/workouts/{workout_short_id}/chart_data",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert response.status_code == 200
        assert "success" in data["status"]
        assert data["message"] == ""
        assert len(data["data"]["chart_data"]) == gpx_file.count("</trkpt>")
        assert data["data"]["chart_data"][0] == {
            "distance": 0.0,
            "duration": 0,
            "elevation": 998.0,
            "latitude": 44.68095,
            "longitude": 6.07367,
            "speed": 0.0,
            "time": "2018-03-13 12:44:45+00:00",
        }

    def test_it_gets_chart_data_for_a_workout_created_with_gpx_without_elevation(  # noqa
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        gpx_file_without_elevation: str,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
            "/api/workouts",
            data=dict(
                file=(
                    BytesIO(str.encode(gpx_file_without_elevation)),
                    "example.gpx",
                ),
                data='{"sport_id": 1}',
            ),
            headers=dict(
                content_type="multipart/form-data",
                Authorization=f"Bearer {auth_token}",
            ),
        )
        data = json.loads(response.data.decode())
        workout_short_id = data["data"]["workouts"][0]["id"]
        response = client.get(
            f"/api/workouts/{workout_short_id}/chart_data",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert response.status_code == 200
        assert "success" in data["status"]
        assert data["message"] == ""
        assert len(
            data["data"]["chart_data"]
        ) == gpx_file_without_elevation.count("</trkpt>")
        # no 'elevation' key in data
        assert data["data"]["chart_data"][0] == {
            "distance": 0.0,
            "duration": 0,
            "latitude": 44.68095,
            "longitude": 6.07367,
            "speed": 0.0,
            "time": "2018-03-13 12:44:45+00:00",
        }

    def test_it_gets_segment_chart_data_for_a_workout_created_with_gpx(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        gpx_file: str,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
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
        data = json.loads(response.data.decode())
        workout_short_id = data["data"]["workouts"][0]["id"]
        segment_short_id = data["data"]["workouts"][0]["segments"][0][
            "segment_id"
        ]
        response = client.get(
            f"/api/workouts/{workout_short_id}/chart_data/segment/{segment_short_id}",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert response.status_code == 200
        assert "success" in data["status"]
        assert data["message"] == ""
        assert data["data"]["chart_data"] != ""
        assert len(data["data"]["chart_data"]) == gpx_file.count("</trkpt>")
        assert data["data"]["chart_data"][0] == {
            "distance": 0.0,
            "duration": 0,
            "elevation": 998.0,
            "latitude": 44.68095,
            "longitude": 6.07367,
            "speed": 0.0,
            "time": "2018-03-13 12:44:45+00:00",
        }

    def test_it_returns_404_on_getting_chart_data_if_workout_belongs_to_another_user(  # noqa
        self,
        app: "Flask",
        user_1: "User",
        user_2: User,
        sport_1_cycling: "Sport",
        gpx_file: str,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )
        response = client.post(
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
        data = json.loads(response.data.decode())
        workout_short_id = data["data"]["workouts"][0]["id"]
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_2.email
        )

        response = client.get(
            f"/api/workouts/{workout_short_id}/chart_data",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        self.assert_404(response)

    def test_it_returns_404_if_segment_id_does_not_exist(
        self,
        app: "Flask",
        user_1: "User",
        sport_1_cycling: "Sport",
        gpx_file: str,
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
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
        data = json.loads(response.data.decode())
        workout_short_id = data["data"]["workouts"][0]["id"]
        response = client.get(
            f"/api/workouts/{workout_short_id}/chart_data/segment/999999",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = self.assert_404_with_message(
            response, "No segment with id '999999'"
        )
        assert "data" not in data


class TestPostAndGetWorkoutWithoutFile(WorkoutApiTestCaseMixin):
    def test_it_add_and_gets_a_workout_wo_gpx(
        self, app: "Flask", user_1: "User", sport_1_cycling: "Sport"
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
            "/api/workouts/no_gpx",
            content_type="application/json",
            data=json.dumps(
                dict(
                    sport_id=1,
                    duration=3600,
                    workout_date="2018-05-15 14:05",
                    distance=10,
                )
            ),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )
        data = json.loads(response.data.decode())
        workout_short_id = data["data"]["workouts"][0]["id"]
        response = client.get(
            f"/api/workouts/{workout_short_id}",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert response.status_code == 200
        assert "success" in data["status"]
        assert len(data["data"]["workouts"]) == 1
        assert_workout_data_wo_gpx(data, user_1)

    def test_it_adds_and_gets_a_workout_wo_gpx_notes(
        self, app: "Flask", user_1: "User", sport_1_cycling: "Sport"
    ) -> None:
        client, auth_token = self.get_test_client_and_auth_token(
            app, user_1.email
        )

        response = client.post(
            "/api/workouts/no_gpx",
            content_type="application/json",
            data=json.dumps(
                dict(
                    sport_id=1,
                    duration=3600,
                    workout_date="2018-05-15 14:05",
                    distance=10,
                    notes="new test with notes",
                )
            ),
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )
        data = json.loads(response.data.decode())
        workout_short_id = data["data"]["workouts"][0]["id"]
        response = client.get(
            f"/api/workouts/{workout_short_id}",
            headers=dict(Authorization=f"Bearer {auth_token}"),
        )

        data = json.loads(response.data.decode())
        assert response.status_code == 200
        assert "success" in data["status"]
        assert len(data["data"]["workouts"]) == 1
        assert "new test with notes" == data["data"]["workouts"][0]["notes"]
