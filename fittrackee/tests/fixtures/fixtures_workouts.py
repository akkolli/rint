from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import TYPE_CHECKING, Dict, Generator, Iterator, List, Union
from unittest.mock import MagicMock, Mock, patch

import pytest
from PIL import Image

from fittrackee import db
from fittrackee.constants import PaceSpeedDisplay
from fittrackee.workouts.models import (
    Sport,
    Workout,
    WorkoutSegment,
)
from fittrackee.workouts.services.workout_from_file.base_workout_with_segment_service import (
    StaticMap,
)
from fittrackee.workouts.utils.convert import convert_speed_into_pace_duration

if TYPE_CHECKING:
    from fittrackee.users.models import User

byte_io = BytesIO()
Image.new("RGB", (256, 256)).save(byte_io, "PNG")
byte_image = byte_io.getvalue()


@dataclass
class DramatiqMessage:
    message_id: str


MESSAGE_ID = "e7640357-3b8d-47be-885d-68104cdfe4b2"
message = DramatiqMessage(message_id=MESSAGE_ID)


@pytest.fixture(autouse=True)
def update_records_patch(request: pytest.FixtureRequest) -> Iterator[None]:
    # allows to disable record creation/update on tests where
    # records are not needed
    if "disable_autouse_update_records_patch" in request.keywords:
        yield
    else:
        with patch(
            "fittrackee.workouts.models.update_records", return_value=None
        ):
            yield


@pytest.fixture(scope="session", autouse=True)
def static_map_get_mock() -> Generator:
    # to avoid unnecessary requests calls through staticmap
    m = Mock(return_value=(200, byte_image))
    with patch.object(StaticMap, "get", m) as _fixture:
        yield _fixture


@pytest.fixture()
def sport_1_cycling() -> Sport:
    sport = Sport(label="Cycling (Sport)")
    db.session.add(sport)
    db.session.commit()
    return sport


@pytest.fixture()
def sport_2_running() -> Sport:
    sport = Sport(label="Running")
    sport.stopped_speed_threshold = 0.1
    sport.pace_speed_display = PaceSpeedDisplay.PACE
    db.session.add(sport)
    db.session.commit()
    return sport


def update_workout(target: Union[Workout, WorkoutSegment]) -> None:
    distance = target.distance if target.distance else 0
    target.ave_speed = float(distance) / (target.duration.seconds / 3600)
    target.max_speed = target.ave_speed
    target.moving = target.duration
    target.ave_pace = convert_speed_into_pace_duration(target.ave_speed)
    target.best_pace = convert_speed_into_pace_duration(target.max_speed)


@pytest.fixture()
def workout_cycling_user_1(
    user_1: "User", sport_1_cycling: "Sport"
) -> Workout:
    workout = Workout(
        user_id=user_1.id,
        sport_id=sport_1_cycling.id,
        # workout_date: 'Mon, 01 Jan 2018 00:00:00 GMT'
        workout_date=datetime(2018, 1, 1, tzinfo=timezone.utc),
        distance=10,
        duration=timedelta(seconds=3600),
    )
    update_workout(workout)
    db.session.add(workout)
    db.session.commit()
    return workout


@pytest.fixture()
def workout_cycling_user_1_segment(
    workout_cycling_user_1: Workout,
) -> WorkoutSegment:
    workout_segment = WorkoutSegment(
        workout_id=workout_cycling_user_1.id,
        workout_uuid=workout_cycling_user_1.uuid,
    )
    workout_segment.start_date = workout_cycling_user_1.workout_date
    workout_segment.duration = workout_cycling_user_1.duration
    workout_segment.distance = workout_cycling_user_1.distance
    update_workout(workout_segment)
    db.session.add(workout_segment)
    workout_cycling_user_1.original_file = "workouts/1/example.tcx"
    db.session.commit()
    return workout_segment


@pytest.fixture()
def workout_cycling_user_1_with_coordinates(
    user_1: "User", sport_1_cycling: "Sport"
) -> Workout:
    workout = Workout(
        user_id=user_1.id,
        sport_id=sport_1_cycling.id,
        # workout_date: 'Tue, 13 Mar 2018 00:00:00 GMT'
        workout_date=datetime(2018, 3, 13, tzinfo=timezone.utc),
        distance=0.300,
        duration=timedelta(seconds=3600),
    )
    update_workout(workout)
    workout.bounds = [44.67822, 6.07355, 44.68095, 6.07442]
    db.session.add(workout)
    workout.original_file = "workouts/1/example.tcx"
    workout.store_start_point_geometry([6.07367, 44.68095])
    db.session.commit()
    return workout


@pytest.fixture()
def workout_cycling_user_1_segment_0_coordinates() -> List[List]:
    return [
        [6.07367, 44.68095],
        [6.07367, 44.68091],
        [6.07364, 44.6808],
        [6.07364, 44.68075],
        [6.07364, 44.68071],
        [6.07361, 44.68049],
        [6.07356, 44.68019],
        [6.07355, 44.68014],
        [6.07358, 44.67995],
    ]


@pytest.fixture()
def workout_cycling_user_1_segment_0_with_coordinates(
    workout_cycling_user_1_with_coordinates: Workout,
    workout_cycling_user_1_segment_0_coordinates: List[List],
) -> WorkoutSegment:
    workout_segment = WorkoutSegment(
        workout_id=workout_cycling_user_1_with_coordinates.id,
        workout_uuid=workout_cycling_user_1_with_coordinates.uuid,
    )
    workout_segment.start_date = (
        workout_cycling_user_1_with_coordinates.workout_date
    )
    workout_segment.duration = timedelta(minutes=1, seconds=30)
    workout_segment.moving = workout_segment.duration
    workout_segment.distance = 0.113
    db.session.add(workout_segment)
    workout_segment.store_geometry(
        workout_cycling_user_1_segment_0_coordinates
    )
    workout_segment.points = [
        {
            "cadence": 0,
            "distance": 0.0,
            "duration": 0,
            "elevation": 998.0,
            "heart_rate": 92,
            "latitude": 44.68095,
            "longitude": 6.07367,
            "pace": None,
            "power": 0,
            "speed": 0,
            "time": "2018-03-13 12:44:45+00:00",
        },
        {
            "cadence": 50,
            "distance": 4.4527796323533435,
            "duration": 5,
            "elevation": 998.0,
            "heart_rate": 87,
            "latitude": 44.68091,
            "longitude": 6.07367,
            "pace": 0.9090909091,
            "power": 305,
            "speed": 3.96,
            "time": "2018-03-13 12:44:50+00:00",
        },
        {
            "cadence": 51,
            "distance": 17.551714568218248,
            "duration": 15,
            "elevation": 994.0,
            "heart_rate": 88,
            "latitude": 44.6808,
            "longitude": 6.07364,
            "pace": 0.8256880734,
            "power": 326,
            "speed": 4.36,
            "time": "2018-03-13 12:45:00+00:00",
        },
        {
            "cadence": 54,
            "distance": 23.117689107275726,
            "duration": 20,
            "elevation": 994.0,
            "heart_rate": 90,
            "latitude": 44.68075,
            "longitude": 6.07364,
            "pace": 0.9972299169,
            "power": 287,
            "speed": 3.61,
            "time": "2018-03-13 12:45:05+00:00",
        },
        {
            "cadence": 53,
            "distance": 27.57046873962907,
            "duration": 25,
            "elevation": 994.0,
            "heart_rate": 87,
            "latitude": 44.68071,
            "longitude": 6.07364,
            "pace": 0.942408377,
            "power": 251,
            "speed": 3.82,
            "time": "2018-03-13 12:45:10+00:00",
        },
        {
            "cadence": 54,
            "distance": 52.19591920442389,
            "duration": 45,
            "elevation": 993.0,
            "heart_rate": 85,
            "latitude": 44.68049,
            "longitude": 6.07361,
            "pace": 0.775862069,
            "power": 248,
            "speed": 4.64,
            "time": "2018-03-13 12:45:30+00:00",
        },
        {
            "cadence": 54,
            "distance": 85.84031796618186,
            "duration": 70,
            "elevation": 992.0,
            "heart_rate": 86,
            "latitude": 44.68019,
            "longitude": 6.07356,
            "pace": 0.808988764,
            "power": 246,
            "speed": 4.45,
            "time": "2018-03-13 12:45:55+00:00",
        },
        {
            "cadence": 55,
            "distance": 91.46229198539272,
            "duration": 75,
            "elevation": 992.0,
            "heart_rate": 84,
            "latitude": 44.68014,
            "longitude": 6.07355,
            "pace": 0.7741935484,
            "power": 216,
            "speed": 4.65,
            "time": "2018-03-13 12:46:00+00:00",
        },
        {
            "cadence": 53,
            "distance": 113.32529632259636,
            "duration": 90,
            "elevation": 987.0,
            "heart_rate": 86,
            "latitude": 44.67995,
            "longitude": 6.07358,
            "pace": 0.6857142857,
            "power": 243,
            "speed": 5.25,
            "time": "2018-03-13 12:46:15+00:00",
        },
    ]
    db.session.commit()
    return workout_segment


@pytest.fixture()
def workout_cycling_user_1_segment_0_chart_data() -> List[Dict]:
    return [
        {
            "distance": 0.0,
            "duration": 0,
            "elevation": 998.0,
            "hr": 92,
            "latitude": 44.68095,
            "longitude": 6.07367,
            "power": 0,
            "speed": 0,
            "time": "2018-03-13 12:44:45+00:00",
        },
        {
            "distance": 0.0,
            "duration": 5,
            "elevation": 998.0,
            "hr": 87,
            "latitude": 44.68091,
            "longitude": 6.07367,
            "power": 305,
            "speed": 3.96,
            "time": "2018-03-13 12:44:50+00:00",
        },
        {
            "distance": 0.02,
            "duration": 15,
            "elevation": 994.0,
            "hr": 88,
            "latitude": 44.6808,
            "longitude": 6.07364,
            "power": 326,
            "speed": 4.36,
            "time": "2018-03-13 12:45:00+00:00",
        },
        {
            "distance": 0.02,
            "duration": 20,
            "elevation": 994.0,
            "hr": 90,
            "latitude": 44.68075,
            "longitude": 6.07364,
            "power": 287,
            "speed": 3.61,
            "time": "2018-03-13 12:45:05+00:00",
        },
        {
            "distance": 0.03,
            "duration": 25,
            "elevation": 994.0,
            "hr": 87,
            "latitude": 44.68071,
            "longitude": 6.07364,
            "power": 251,
            "speed": 3.82,
            "time": "2018-03-13 12:45:10+00:00",
        },
        {
            "distance": 0.05,
            "duration": 45,
            "elevation": 993.0,
            "hr": 85,
            "latitude": 44.68049,
            "longitude": 6.07361,
            "power": 248,
            "speed": 4.64,
            "time": "2018-03-13 12:45:30+00:00",
        },
        {
            "distance": 0.09,
            "duration": 70,
            "elevation": 992.0,
            "hr": 86,
            "latitude": 44.68019,
            "longitude": 6.07356,
            "power": 246,
            "speed": 4.45,
            "time": "2018-03-13 12:45:55+00:00",
        },
        {
            "distance": 0.09,
            "duration": 75,
            "elevation": 992.0,
            "hr": 84,
            "latitude": 44.68014,
            "longitude": 6.07355,
            "power": 216,
            "speed": 4.65,
            "time": "2018-03-13 12:46:00+00:00",
        },
        {
            "distance": 0.11,
            "duration": 90,
            "elevation": 987.0,
            "hr": 86,
            "latitude": 44.67995,
            "longitude": 6.07358,
            "power": 243,
            "speed": 5.25,
            "time": "2018-03-13 12:46:15+00:00",
        },
    ]


@pytest.fixture()
def workout_cycling_user_1_segment_0_chart_data_wo_hr(
    workout_cycling_user_1_segment_0_chart_data: List[Dict],
) -> List[Dict]:
    return [
        {
            "distance": data["distance"],
            "duration": data["duration"],
            "elevation": data["elevation"],
            "latitude": data["latitude"],
            "longitude": data["longitude"],
            "power": data["power"],
            "speed": data["speed"],
            "time": data["time"],
        }
        for data in workout_cycling_user_1_segment_0_chart_data
    ]


@pytest.fixture()
def workout_cycling_user_1_segment_0_chart_data_wo_hr_and_wo_coords(
    workout_cycling_user_1_segment_0_chart_data: List[Dict],
) -> List[Dict]:
    return [
        {
            "distance": data["distance"],
            "duration": data["duration"],
            "elevation": data["elevation"],
            "power": data["power"],
            "speed": data["speed"],
            "time": data["time"],
        }
        for data in workout_cycling_user_1_segment_0_chart_data
    ]


@pytest.fixture()
def workout_cycling_user_1_segment_1_coordinates() -> List[List]:
    return [
        [6.07364, 44.67977],
        [6.07367, 44.67972],
        [6.07368, 44.67966],
        [6.0737, 44.67961],
        [6.07377, 44.67938],
        [6.07381, 44.67933],
        [6.07385, 44.67922],
        [6.0739, 44.67911],
        [6.07399, 44.679],
        [6.07402, 44.67896],
        [6.07408, 44.67884],
        [6.07423, 44.67863],
        [6.07425, 44.67858],
        [6.07434, 44.67842],
        [6.07435, 44.67837],
        [6.07442, 44.67822],
    ]


@pytest.fixture()
def workout_cycling_user_1_segment_1_with_coordinates(
    workout_cycling_user_1_with_coordinates: Workout,
    workout_cycling_user_1_segment_1_coordinates: List[List],
) -> WorkoutSegment:
    workout_segment = WorkoutSegment(
        workout_id=workout_cycling_user_1_with_coordinates.id,
        workout_uuid=workout_cycling_user_1_with_coordinates.uuid,
    )
    workout_segment.start_date = datetime(
        year=2018,
        month=3,
        day=13,
        hour=12,
        minute=46,
        second=30,
        tzinfo=timezone.utc,
    )
    workout_segment.duration = timedelta(minutes=2, seconds=25)
    workout_segment.moving = workout_segment.duration
    workout_segment.distance = 0.186
    db.session.add(workout_segment)
    workout_segment.store_geometry(
        workout_cycling_user_1_segment_1_coordinates
    )
    workout_segment.points = [
        {
            "cadence": 56,
            "distance": 0.0,
            "duration": 105,
            "elevation": 987.0,
            "heart_rate": 88,
            "latitude": 44.67977,
            "longitude": 6.07364,
            "pace": None,
            "power": 267,
            "speed": 0,
            "time": "2018-03-13 12:46:30+00:00",
        },
        {
            "cadence": 56,
            "distance": 6.051349268478878,
            "duration": 110,
            "elevation": 987.0,
            "heart_rate": 86,
            "latitude": 44.67972,
            "longitude": 6.07367,
            "pace": 0.7826086957,
            "power": 278,
            "speed": 4.6,
            "time": "2018-03-13 12:46:35+00:00",
        },
        {
            "cadence": 55,
            "distance": 12.77725695386378,
            "duration": 115,
            "elevation": 987.0,
            "heart_rate": 83,
            "latitude": 44.67966,
            "longitude": 6.07368,
            "pace": 0.7929515419,
            "power": 290,
            "speed": 4.54,
            "time": "2018-03-13 12:46:40+00:00",
        },
        {
            "cadence": 56,
            "distance": 18.649751790376072,
            "duration": 120,
            "elevation": 986.0,
            "heart_rate": 83,
            "latitude": 44.67961,
            "longitude": 6.0737,
            "pace": 0.8053691275,
            "power": 228,
            "speed": 4.47,
            "time": "2018-03-13 12:46:45+00:00",
        },
        {
            "cadence": 54,
            "distance": 44.84590773920506,
            "duration": 140,
            "elevation": 986.0,
            "heart_rate": 85,
            "latitude": 44.67938,
            "longitude": 6.07377,
            "pace": 0.7725321888,
            "power": 280,
            "speed": 4.66,
            "time": "2018-03-13 12:47:05+00:00",
        },
        {
            "cadence": 56,
            "distance": 51.24939597404716,
            "duration": 145,
            "elevation": 986.0,
            "heart_rate": 86,
            "latitude": 44.67933,
            "longitude": 6.07381,
            "pace": 0.7843137255,
            "power": 269,
            "speed": 4.59,
            "time": "2018-03-13 12:47:10+00:00",
        },
        {
            "cadence": 53,
            "distance": 63.93671950289988,
            "duration": 155,
            "elevation": 985.0,
            "heart_rate": 85,
            "latitude": 44.67922,
            "longitude": 6.07385,
            "pace": 0.7547169811,
            "power": 280,
            "speed": 4.77,
            "time": "2018-03-13 12:47:20+00:00",
        },
        {
            "cadence": 56,
            "distance": 77.74277217988791,
            "duration": 165,
            "elevation": 980.0,
            "heart_rate": 84,
            "latitude": 44.67911,
            "longitude": 6.0739,
            "pace": 0.7142857143,
            "power": 256,
            "speed": 5.04,
            "time": "2018-03-13 12:47:30+00:00",
        },
        {
            "cadence": 55,
            "distance": 91.90940943581896,
            "duration": 175,
            "elevation": 980.0,
            "heart_rate": 86,
            "latitude": 44.679,
            "longitude": 6.07399,
            "pace": 0.823798627,
            "power": 234,
            "speed": 4.37,
            "time": "2018-03-13 12:47:40+00:00",
        },
        {
            "cadence": 55,
            "distance": 96.9558091208821,
            "duration": 180,
            "elevation": 980.0,
            "heart_rate": 83,
            "latitude": 44.67896,
            "longitude": 6.07402,
            "pace": 0.823798627,
            "power": 241,
            "speed": 4.37,
            "time": "2018-03-13 12:47:45+00:00",
        },
        {
            "cadence": 55,
            "distance": 111.16851205741831,
            "duration": 190,
            "elevation": 979.0,
            "heart_rate": 83,
            "latitude": 44.67884,
            "longitude": 6.07408,
            "pace": 0.7317073171,
            "power": 264,
            "speed": 4.92,
            "time": "2018-03-13 12:47:55+00:00",
        },
        {
            "cadence": 54,
            "distance": 137.46418982445846,
            "duration": 210,
            "elevation": 981.0,
            "heart_rate": 82,
            "latitude": 44.67863,
            "longitude": 6.07423,
            "pace": 0.8035714286,
            "power": 256,
            "speed": 4.48,
            "time": "2018-03-13 12:48:15+00:00",
        },
        {
            "cadence": 57,
            "distance": 143.33669224740893,
            "duration": 215,
            "elevation": 980.0,
            "heart_rate": 85,
            "latitude": 44.67858,
            "longitude": 6.07425,
            "pace": 0.814479638,
            "power": 267,
            "speed": 4.42,
            "time": "2018-03-13 12:48:20+00:00",
        },
        {
            "cadence": 57,
            "distance": 162.5457270763049,
            "duration": 230,
            "elevation": 979.0,
            "heart_rate": 84,
            "latitude": 44.67842,
            "longitude": 6.07434,
            "pace": 0.831408776,
            "power": 234,
            "speed": 4.33,
            "time": "2018-03-13 12:48:35+00:00",
        },
        {
            "cadence": 52,
            "distance": 168.16770449996508,
            "duration": 235,
            "elevation": 979.0,
            "heart_rate": 84,
            "latitude": 44.67837,
            "longitude": 6.07435,
            "pace": 0.8591885442,
            "power": 225,
            "speed": 4.19,
            "time": "2018-03-13 12:48:40+00:00",
        },
        {
            "cadence": 50,
            "distance": 186.2099364366852,
            "duration": 250,
            "elevation": 975.0,
            "heart_rate": 81,
            "latitude": 44.67822,
            "longitude": 6.07442,
            "pace": 0.831408776,
            "power": 218,
            "speed": 4.33,
            "time": "2018-03-13 12:48:55+00:00",
        },
    ]
    db.session.commit()
    return workout_segment


@pytest.fixture()
def workout_running_user_1(
    user_1: "User", sport_2_running: "Sport"
) -> Workout:
    workout = Workout(
        user_id=user_1.id,
        sport_id=sport_2_running.id,
        # workout_date: 'Mon, 02 Apr 2018 00:00:00 GMT'
        workout_date=datetime(2018, 4, 2, tzinfo=timezone.utc),
        distance=12,
        duration=timedelta(seconds=6000),
    )
    update_workout(workout)
    db.session.add(workout)
    db.session.commit()
    return workout


@pytest.fixture()
def workout_cycling_user_2(
    user_2: "User", sport_1_cycling: "Sport"
) -> Workout:
    workout = Workout(
        user_id=user_2.id,
        sport_id=sport_1_cycling.id,
        # workout_date: 'Tue, 23 Jan 2018 00:00:00 GMT'
        workout_date=datetime(2018, 1, 23, tzinfo=timezone.utc),
        distance=15,
        duration=timedelta(seconds=3600),
    )
    update_workout(workout)
    db.session.add(workout)
    db.session.commit()
    return workout


track_points_part_1_coordinates = [
    (6.07367, 44.68095),
    (6.07367, 44.68091),
    (6.07364, 44.6808),
    (6.07364, 44.68075),
    (6.07364, 44.68071),
    (6.07361, 44.68049),
    (6.07356, 44.68019),
    (6.07355, 44.68014),
    (6.07358, 44.67995),
]
track_points_part_2_coordinates = [
    (6.07364, 44.67977),
    (6.07367, 44.67972),
    (6.07368, 44.67966),
    (6.0737, 44.67961),
    (6.07377, 44.67938),
    (6.07381, 44.67933),
    (6.07385, 44.67922),
    (6.0739, 44.67911),
    (6.07399, 44.679),
    (6.07402, 44.67896),
    (6.07408, 44.67884),
    (6.07423, 44.67863),
    (6.07425, 44.67858),
    (6.07434, 44.67842),
    (6.07435, 44.67837),
    (6.07442, 44.67822),
]


track_points_part_1 = """
           <trkpt lat="44.68095" lon="6.07367">
             <ele>998</ele>
             <time>2018-03-13T12:44:45Z</time>
           </trkpt>
           <trkpt lat="44.68091" lon="6.07367">
             <ele>998</ele>
             <time>2018-03-13T12:44:50Z</time>
           </trkpt>
           <trkpt lat="44.6808" lon="6.07364">
             <ele>994</ele>
             <time>2018-03-13T12:45:00Z</time>
           </trkpt>
           <trkpt lat="44.68075" lon="6.07364">
             <ele>994</ele>
             <time>2018-03-13T12:45:05Z</time>
           </trkpt>
           <trkpt lat="44.68071" lon="6.07364">
             <ele>994</ele>
             <time>2018-03-13T12:45:10Z</time>
           </trkpt>
           <trkpt lat="44.68049" lon="6.07361">
             <ele>993</ele>
             <time>2018-03-13T12:45:30Z</time>
           </trkpt>
           <trkpt lat="44.68019" lon="6.07356">
             <ele>992</ele>
             <time>2018-03-13T12:45:55Z</time>
           </trkpt>
           <trkpt lat="44.68014" lon="6.07355">
             <ele>992</ele>
             <time>2018-03-13T12:46:00Z</time>
           </trkpt>
           <trkpt lat="44.67995" lon="6.07358">
             <ele>987</ele>
             <time>2018-03-13T12:46:15Z</time>
           </trkpt>
"""
track_points_part_2 = """
           <trkpt lat="44.67977" lon="6.07364">
             <ele>987</ele>
             <time>2018-03-13T12:46:30Z</time>
           </trkpt>
           <trkpt lat="44.67972" lon="6.07367">
             <ele>987</ele>
             <time>2018-03-13T12:46:35Z</time>
           </trkpt>
           <trkpt lat="44.67966" lon="6.07368">
             <ele>987</ele>
             <time>2018-03-13T12:46:40Z</time>
           </trkpt>
           <trkpt lat="44.67961" lon="6.0737">
             <ele>986</ele>
             <time>2018-03-13T12:46:45Z</time>
           </trkpt>
           <trkpt lat="44.67938" lon="6.07377">
             <ele>986</ele>
             <time>2018-03-13T12:47:05Z</time>
           </trkpt>
           <trkpt lat="44.67933" lon="6.07381">
             <ele>986</ele>
             <time>2018-03-13T12:47:10Z</time>
           </trkpt>
           <trkpt lat="44.67922" lon="6.07385">
             <ele>985</ele>
             <time>2018-03-13T12:47:20Z</time>
           </trkpt>
           <trkpt lat="44.67911" lon="6.0739">
             <ele>980</ele>
             <time>2018-03-13T12:47:30Z</time>
           </trkpt>
           <trkpt lat="44.679" lon="6.07399">
             <ele>980</ele>
             <time>2018-03-13T12:47:40Z</time>
           </trkpt>
           <trkpt lat="44.67896" lon="6.07402">
             <ele>980</ele>
             <time>2018-03-13T12:47:45Z</time>
           </trkpt>
           <trkpt lat="44.67884" lon="6.07408">
             <ele>979</ele>
             <time>2018-03-13T12:47:55Z</time>
           </trkpt>
           <trkpt lat="44.67863" lon="6.07423">
             <ele>981</ele>
             <time>2018-03-13T12:48:15Z</time>
           </trkpt>
           <trkpt lat="44.67858" lon="6.07425">
             <ele>980</ele>
             <time>2018-03-13T12:48:20Z</time>
           </trkpt>
           <trkpt lat="44.67842" lon="6.07434">
             <ele>979</ele>
             <time>2018-03-13T12:48:35Z</time>
           </trkpt>
           <trkpt lat="44.67837" lon="6.07435">
             <ele>979</ele>
             <time>2018-03-13T12:48:40Z</time>
           </trkpt>
           <trkpt lat="44.67822" lon="6.07442">
             <ele>975</ele>
             <time>2018-03-13T12:48:55Z</time>
           </trkpt>
"""


@pytest.fixture()
def gpx_file() -> str:
    return (
        """<?xml version='1.0' encoding='UTF-8'?>
<gpx
  xmlns:gpxdata="http://www.cluetrust.com/XML/GPXDATA/1/0"
  xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
  xmlns:gpxext="http://www.garmin.com/xmlschemas/GpxExtensions/v3"
  xmlns="http://www.topografix.com/GPX/1/1"
>
  <metadata/>
  <trk>
    <name>just a workout</name>
    <trkseg>
"""
        + track_points_part_1
        + track_points_part_2
        + """
    </trkseg>
  </trk>
</gpx>
"""
    )


@pytest.fixture()
def osmand_gpx_file() -> str:
    return (
        """<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<gpx 
  version="1.1"
  creator="OsmAnd+ 5.2.13"
  xmlns="http://www.topografix.com/GPX/1/1"
  xmlns:osmand="https://osmand.net/docs/technical/osmand-file-formats/osmand-gpx"
  xmlns:gpxtpx="https://www8.garmin.com/xmlschemas/TrackPointExtensionv1.xsd"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://www.topografix.com/GPX/1/1 https://www.topografix.com/GPX/1/1/gpx.xsd"
>
  <metadata>
    <name>2018-03-13_13-12_Tue</name>
    <time>2018-03-13T12:44:45Z</time>
    <extensions>
      <osmand:activity>hiking</osmand:activity>
    </extensions>
  </metadata>
  <trk>
    <name>just a workout</name>
    <trkseg>
"""
        + track_points_part_1
        + track_points_part_2
        + """
    </trkseg>
  </trk>
  <extensions>
    <osmand:show_arrows>false</osmand:show_arrows>
    <osmand:show_start_finish>true</osmand:show_start_finish>
    <osmand:split_interval>0.0</osmand:split_interval>
    <osmand:split_type>no_split</osmand:split_type>
    <osmand:line_3d_visualization_by_type>none</osmand:line_3d_visualization_by_type>
    <osmand:line_3d_visualization_wall_color_type>none</osmand:line_3d_visualization_wall_color_type>
    <osmand:line_3d_visualization_position_type>top</osmand:line_3d_visualization_position_type>
    <osmand:vertical_exaggeration_scale>1.0</osmand:vertical_exaggeration_scale>
    <osmand:elevation_meters>1000.0</osmand:elevation_meters>
    <osmand:width></osmand:width>
    <osmand:coloring_type>solid</osmand:coloring_type>
  </extensions>
</gpx>
"""
    )


@pytest.fixture()
def gpx_file_without_elevation() -> str:
    return """<?xml version='1.0' encoding='UTF-8'?>
<gpx
  xmlns:gpxdata="http://www.cluetrust.com/XML/GPXDATA/1/0"
  xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
  xmlns:gpxext="http://www.garmin.com/xmlschemas/GpxExtensions/v3"
  xmlns="http://www.topografix.com/GPX/1/1"
>
  <metadata/>
  <trk>
    <name>just a workout</name>
    <trkseg>
      <trkpt lat="44.68095" lon="6.07367">
        <time>2018-03-13T12:44:45Z</time>
      </trkpt>
      <trkpt lat="44.68091" lon="6.07367">
        <time>2018-03-13T12:44:50Z</time>
      </trkpt>
      <trkpt lat="44.6808" lon="6.07364">
        <time>2018-03-13T12:45:00Z</time>
      </trkpt>
      <trkpt lat="44.68075" lon="6.07364">
        <time>2018-03-13T12:45:05Z</time>
      </trkpt>
      <trkpt lat="44.68071" lon="6.07364">
        <time>2018-03-13T12:45:10Z</time>
      </trkpt>
      <trkpt lat="44.68049" lon="6.07361">
        <time>2018-03-13T12:45:30Z</time>
      </trkpt>
      <trkpt lat="44.68019" lon="6.07356">
        <time>2018-03-13T12:45:55Z</time>
      </trkpt>
      <trkpt lat="44.68014" lon="6.07355">
        <time>2018-03-13T12:46:00Z</time>
      </trkpt>
      <trkpt lat="44.67995" lon="6.07358">
        <time>2018-03-13T12:46:15Z</time>
      </trkpt>
      <trkpt lat="44.67977" lon="6.07364">
        <time>2018-03-13T12:46:30Z</time>
      </trkpt>
      <trkpt lat="44.67972" lon="6.07367">
        <time>2018-03-13T12:46:35Z</time>
      </trkpt>
      <trkpt lat="44.67966" lon="6.07368">
        <time>2018-03-13T12:46:40Z</time>
      </trkpt>
      <trkpt lat="44.67961" lon="6.0737">
        <time>2018-03-13T12:46:45Z</time>
      </trkpt>
      <trkpt lat="44.67938" lon="6.07377">
        <time>2018-03-13T12:47:05Z</time>
      </trkpt>
      <trkpt lat="44.67933" lon="6.07381">
        <time>2018-03-13T12:47:10Z</time>
      </trkpt>
      <trkpt lat="44.67922" lon="6.07385">
        <time>2018-03-13T12:47:20Z</time>
      </trkpt>
      <trkpt lat="44.67911" lon="6.0739">
        <time>2018-03-13T12:47:30Z</time>
      </trkpt>
      <trkpt lat="44.679" lon="6.07399">
        <time>2018-03-13T12:47:40Z</time>
      </trkpt>
      <trkpt lat="44.67896" lon="6.07402">
        <time>2018-03-13T12:47:45Z</time>
      </trkpt>
      <trkpt lat="44.67884" lon="6.07408">
        <time>2018-03-13T12:47:55Z</time>
      </trkpt>
      <trkpt lat="44.67863" lon="6.07423">
        <time>2018-03-13T12:48:15Z</time>
      </trkpt>
      <trkpt lat="44.67858" lon="6.07425">
        <time>2018-03-13T12:48:20Z</time>
      </trkpt>
      <trkpt lat="44.67842" lon="6.07434">
        <time>2018-03-13T12:48:35Z</time>
      </trkpt>
      <trkpt lat="44.67837" lon="6.07435">
        <time>2018-03-13T12:48:40Z</time>
      </trkpt>
      <trkpt lat="44.67822" lon="6.07442">
        <time>2018-03-13T12:48:55Z</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
"""


@pytest.fixture()
def gpx_file_invalid_xml() -> str:
    return """<?xml version='1.0' encoding='UTF-8'?>
<gpx
  xmlns:gpxdata="http://www.cluetrust.com/XML/GPXDATA/1/0"
  xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
  xmlns:gpxext="http://www.garmin.com/xmlschemas/GpxExtensions/v3"
  xmlns="http://www.topografix.com/GPX/1/1"
>
  <metadata/>
  <trk>
    <name>just a workout</name>
"""


@pytest.fixture()
def gpx_file_with_segments() -> str:
    return (
        """<?xml version='1.0' encoding='UTF-8'?>
<gpx
  xmlns:gpxdata="http://www.cluetrust.com/XML/GPXDATA/1/0"
  xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
  xmlns:gpxext="http://www.garmin.com/xmlschemas/GpxExtensions/v3"
  xmlns="http://www.topografix.com/GPX/1/1"
>
  <metadata/>
  <trk>
    <name>just a workout</name>
    <trkseg>
"""
        + track_points_part_1
        + """
    </trkseg>
    <trkseg>
"""
        + track_points_part_2
        + """
    </trkseg>
  </trk>
</gpx>
"""
    )


segment_0_coordinates = [
    (6.07367, 44.68095),
    (6.07367, 44.68091),
    (6.07364, 44.6808),
]
segment_1_coordinates = [
    (6.07367, 44.67972),
    (6.07368, 44.67966),
    (6.0737, 44.67961),
]
segment_2_coordinates = [
    (6.07425, 44.67858),
    (6.07434, 44.67842),
    (6.07435, 44.67837),
]


@pytest.fixture()
def upload_workouts_archive_mock() -> Iterator[MagicMock]:
    with patch("fittrackee.workouts.tasks.upload_workouts_archive") as mock:
        mock.send = MagicMock()
        mock.send.return_value = message
        yield mock


kml_track_points_part_1 = """
          <when>2018-03-13T13:43:45+01:00</when>
          <gx:coord/>
          <when>2018-03-13T13:44:45+01:00</when>
          <gx:coord>6.07367 44.68095 998</gx:coord>
          <when>2018-03-13T13:44:50+01:00</when>
          <gx:coord>6.07367 44.68091 998</gx:coord>
          <when>2018-03-13T13:45:00+01:00</when>
          <gx:coord>6.07364 44.6808 994</gx:coord>
          <when>2018-03-13T13:45:05+01:00</when>
          <gx:coord>6.07364 44.68075 994</gx:coord>
          <when>2018-03-13T13:45:10+01:00</when>
          <gx:coord>6.07364 44.68071 994</gx:coord>
          <when>2018-03-13T13:45:30+01:00</when>
          <gx:coord>6.07361 44.68049 993</gx:coord>
          <when>2018-03-13T13:45:55+01:00</when>
          <gx:coord>6.07356 44.68019 992</gx:coord>
          <when>2018-03-13T13:46:00+01:00</when>
          <gx:coord>6.07355 44.68014 992</gx:coord>
          <when>2018-03-13T13:46:15+01:00</when>
          <gx:coord>6.07358 44.67995 987</gx:coord>
"""
kml_track_points_part_2 = """
          <when>2018-03-13T13:46:30+01:00</when>
          <gx:coord>6.07364 44.67977 987</gx:coord>
          <when>2018-03-13T13:46:35+01:00</when>
          <gx:coord>6.07367 44.67972 987</gx:coord>
          <when>2018-03-13T13:46:40+01:00</when>
          <gx:coord>6.07368 44.67966 987</gx:coord>
          <when>2018-03-13T13:46:45+01:00</when>
          <gx:coord>6.0737 44.67961 986</gx:coord>
          <when>2018-03-13T13:47:05+01:00</when>
          <gx:coord>6.07377 44.67938 986</gx:coord>
          <when>2018-03-13T13:47:10+01:00</when>
          <gx:coord>6.07381 44.67933 986</gx:coord>
          <when>2018-03-13T13:47:20+01:00</when>
          <gx:coord>6.07385 44.67922 985</gx:coord>
          <when>2018-03-13T13:47:30+01:00</when>
          <gx:coord>6.0739 44.67911 985</gx:coord>
          <when>2018-03-13T13:47:40+01:00</when>
          <gx:coord>6.07399 44.679 980</gx:coord>
          <when>2018-03-13T13:47:45+01:00</when>
          <gx:coord>6.07402 44.67896 980</gx:coord>
          <when>2018-03-13T13:47:55+01:00</when>
          <gx:coord>6.07408 44.67884 979</gx:coord>
          <when>2018-03-13T13:48:15+01:00</when>
          <gx:coord>6.07423 44.67863 981</gx:coord>
          <when>2018-03-13T13:48:20+01:00</when>
          <gx:coord>6.07425 44.67858 980</gx:coord>
          <when>2018-03-13T13:48:35+01:00</when>
          <gx:coord>6.07434 44.67842 979</gx:coord>
          <when>2018-03-13T13:48:40+01:00</when>
          <gx:coord>6.07435 44.67837 979</gx:coord>
          <when>2018-03-13T13:48:55+01:00</when>
          <gx:coord>6.07442 44.67822 975</gx:coord>
"""


@pytest.fixture()
def kml_2_2_with_one_track() -> str:
    return (
        """<?xml version="1.0" encoding="UTF-8"?>
<kml
  xmlns="http://www.opengis.net/kml/2.2"
  xmlns:gx="http://www.google.com/kml/ext/2.2"
  xmlns:atom="http://www.w3.org/2005/Atom"
  xmlns:opentracks="http://opentracksapp.com/xmlschemas/v1"
>
  <Document>
    <open>1</open>
    <visibility>1</visibility>
    <name><![CDATA[just a workout]]></name>
    <atom:generator><![CDATA[OpenTracks]]></atom:generator>
    <Style id="track">
      <LineStyle>
        <color>7f0000ff</color>
        <width>4</width>
      </LineStyle>
      <IconStyle>
        <scale>1.3</scale>
        <Icon/>
      </IconStyle>
    </Style>
    <Style id="waypoint">
      <IconStyle>
        <Icon/>
      </IconStyle>
    </Style>
    <Schema id="schema">
      <gx:SimpleArrayField name="speed" type="float">
        <displayName><![CDATA[Vitesse (m/s)]]></displayName>
      </gx:SimpleArrayField>
      <gx:SimpleArrayField name="power" type="float">
        <displayName><![CDATA[Puissance (W)]]></displayName>
      </gx:SimpleArrayField>
      <gx:SimpleArrayField name="cadence" type="float">
        <displayName><![CDATA[Cadence (tr/min)]]></displayName>
      </gx:SimpleArrayField>
      <gx:SimpleArrayField name="heart_rate" type="float">
        <displayName><![CDATA[Fréquence cardiaque (bpm)]]></displayName>
      </gx:SimpleArrayField>
    </Schema>
    <Placemark>
      <name><![CDATA[just a workout]]></name>
      <description><![CDATA[some description]]></description>
      <icon><![CDATA[WALK]]></icon>
      <opentracks:trackid>7ab3bdbd-6941-47be-9cbd-865b5cfe4f74 "
       </opentracks:trackid>
      <styleUrl>#track</styleUrl>
      <ExtendedData>
        <Data name="type">
          <value><![CDATA[marche]]></value>
        </Data>
      </ExtendedData>
      <gx:MultiTrack>
        <altitudeMode>absolute</altitudeMode>
        <gx:interpolate>1</gx:interpolate>
        <gx:Track>
"""
        + kml_track_points_part_1
        + kml_track_points_part_2
        + """
        </gx:Track>
      </gx:MultiTrack>
    </Placemark>
  </Document>
</kml>
"""
    )


def kml_2_2_to_kml_2_3(kml_content: str) -> str:
    return kml_content.replace('/2.2"', '/2.3"').replace("gx:", "")


@pytest.fixture()
def kml_2_3_with_one_track(kml_2_2_with_one_track: str) -> str:
    return kml_2_2_to_kml_2_3(kml_2_2_with_one_track)


tcx_track_points_part_1 = """        <Trackpoint>
          <Time>2018-03-13T12:44:45Z</Time>
          <Position>
            <LatitudeDegrees>44.68095000</LatitudeDegrees>
            <LongitudeDegrees>6.073670000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>997.00000</AltitudeMeters>
          <DistanceMeters>0.000</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:44:50Z</Time>
          <Position>
            <LatitudeDegrees>44.68091000</LatitudeDegrees>
            <LongitudeDegrees>6.073670000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>996.00000</AltitudeMeters>
          <DistanceMeters>4.449</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:45:00Z</Time>
          <Position>
            <LatitudeDegrees>44.68080000</LatitudeDegrees>
            <LongitudeDegrees>6.073640000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>996.00000</AltitudeMeters>
          <DistanceMeters>16.908</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:45:05Z</Time>
          <Position>
            <LatitudeDegrees>44.68075000</LatitudeDegrees>
            <LongitudeDegrees>6.073640000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>996.00000</AltitudeMeters>
          <DistanceMeters>22.467</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:45:10Z</Time>
          <Position>
            <LatitudeDegrees>44.68071000</LatitudeDegrees>
            <LongitudeDegrees>6.073640000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>996.00000</AltitudeMeters>
          <DistanceMeters>26.914</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:45:30Z</Time>
          <Position>
            <LatitudeDegrees>44.68049000</LatitudeDegrees>
            <LongitudeDegrees>6.073610000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>995.00000</AltitudeMeters>
          <DistanceMeters>51.492</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:45:55Z</Time>
          <Position>
            <LatitudeDegrees>44.68019000</LatitudeDegrees>
            <LongitudeDegrees>6.073560000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>993.00000</AltitudeMeters>
          <DistanceMeters>85.083</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:46:00Z</Time>
          <Position>
            <LatitudeDegrees>44.68014000</LatitudeDegrees>
            <LongitudeDegrees>6.073550000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>992.00000</AltitudeMeters>
          <DistanceMeters>90.698</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:46:15Z</Time>
          <Position>
            <LatitudeDegrees>44.67995000</LatitudeDegrees>
            <LongitudeDegrees>6.073580000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>991.00000</AltitudeMeters>
          <DistanceMeters>111.958</DistanceMeters>
        </Trackpoint>"""


tcx_track_points_part_2 = """<Trackpoint>
          <Time>2018-03-13T12:46:30Z</Time>
          <Position>
            <LatitudeDegrees>44.67977000</LatitudeDegrees>
            <LongitudeDegrees>6.073640000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>989.00000</AltitudeMeters>
          <DistanceMeters>132.527</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:46:35Z</Time>
          <Position>
            <LatitudeDegrees>44.67972000</LatitudeDegrees>
            <LongitudeDegrees>6.073670000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>988.00000</AltitudeMeters>
          <DistanceMeters>138.572</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:46:40Z</Time>
          <Position>
            <LatitudeDegrees>44.67966000</LatitudeDegrees>
            <LongitudeDegrees>6.073680000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>988.00000</AltitudeMeters>
          <DistanceMeters>145.290</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:46:45Z</Time>
          <Position>
            <LatitudeDegrees>44.67961000</LatitudeDegrees>
            <LongitudeDegrees>6.073700000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>987.00000</AltitudeMeters>
          <DistanceMeters>151.071</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:47:05Z</Time>
          <Position>
            <LatitudeDegrees>44.67938000</LatitudeDegrees>
            <LongitudeDegrees>6.073770000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>985.00000</AltitudeMeters>
          <DistanceMeters>177.238</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:47:10Z</Time>
          <Position>
            <LatitudeDegrees>44.67933000</LatitudeDegrees>
            <LongitudeDegrees>6.073810000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>985.00000</AltitudeMeters>
          <DistanceMeters>183.635</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:47:20Z</Time>
          <Position>
            <LatitudeDegrees>44.67922000</LatitudeDegrees>
            <LongitudeDegrees>6.073850000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>985.00000</AltitudeMeters>
          <DistanceMeters>196.269</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:47:30Z</Time>
          <Position>
            <LatitudeDegrees>44.67911000</LatitudeDegrees>
            <LongitudeDegrees>6.073900000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>984.00000</AltitudeMeters>
          <DistanceMeters>209.123</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:47:40Z</Time>
          <Position>
            <LatitudeDegrees>44.67900000</LatitudeDegrees>
            <LongitudeDegrees>6.073990000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>983.00000</AltitudeMeters>
          <DistanceMeters>223.274</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:47:45Z</Time>
          <Position>
            <LatitudeDegrees>44.67896000</LatitudeDegrees>
            <LongitudeDegrees>6.074020000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>983.00000</AltitudeMeters>
          <DistanceMeters>228.315</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:47:55Z</Time>
          <Position>
            <LatitudeDegrees>44.67884000</LatitudeDegrees>
            <LongitudeDegrees>6.074080000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>982.00000</AltitudeMeters>
          <DistanceMeters>242.477</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:48:15Z</Time>
          <Position>
            <LatitudeDegrees>44.67863000</LatitudeDegrees>
            <LongitudeDegrees>6.074230000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>979.00000</AltitudeMeters>
          <DistanceMeters>268.667</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:48:20Z</Time>
          <Position>
            <LatitudeDegrees>44.67858000</LatitudeDegrees>
            <LongitudeDegrees>6.074250000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>979.00000</AltitudeMeters>
          <DistanceMeters>274.448</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:48:35Z</Time>
          <Position>
            <LatitudeDegrees>44.67842000</LatitudeDegrees>
            <LongitudeDegrees>6.074340000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>978.00000</AltitudeMeters>
          <DistanceMeters>293.610</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:48:40Z</Time>
          <Position>
            <LatitudeDegrees>44.67837000</LatitudeDegrees>
            <LongitudeDegrees>6.074350000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>978.00000</AltitudeMeters>
          <DistanceMeters>299.225</DistanceMeters>
        </Trackpoint>
        <Trackpoint>
          <Time>2018-03-13T12:48:55Z</Time>
          <Position>
            <LatitudeDegrees>44.67822000</LatitudeDegrees>
            <LongitudeDegrees>6.074420000</LongitudeDegrees>
          </Position>
          <AltitudeMeters>976.00000</AltitudeMeters>
          <DistanceMeters>316.798</DistanceMeters>
        </Trackpoint>"""


@pytest.fixture()
def tcx_with_one_lap_and_one_track() -> str:
    return (
        """<?xml version="1.0" encoding="UTF-8"?>
<TrainingCenterDatabase
    xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd"
>
    <Activities>
        <Activity Sport="Other">
            <Id>2018-03-13T12:44:45Z</Id>
            <Lap StartTime="2018-03-13T12:44:45Z">
                <Track>
"""
        + tcx_track_points_part_1
        + tcx_track_points_part_2
        + """
                </Track>
            </Lap>
          <Creator xsi:type="Device_t">
            <Name>vívoactive</Name>
          </Creator>
        </Activity>
    </Activities>
    <Author xsi:type="Application_t">
      <Name>Garmin Connect API</Name>
    </Author>
</TrainingCenterDatabase>
"""
    )


OPEN_ELEVATION_RESPONSE = {
    "results": [
        {"elevation": 998.0, "latitude": 44.68095, "longitude": 6.07367},
        {"elevation": 998.0, "latitude": 44.68091, "longitude": 6.07367},
        {"elevation": 994.0, "latitude": 44.6808, "longitude": 6.07364},
        {"elevation": 994.0, "latitude": 44.68075, "longitude": 6.07364},
        {"elevation": 994.0, "latitude": 44.68071, "longitude": 6.07364},
        {"elevation": 993.0, "latitude": 44.68049, "longitude": 6.07361},
        {"elevation": 992.0, "latitude": 44.68019, "longitude": 6.07356},
        {"elevation": 992.0, "latitude": 44.68014, "longitude": 6.07355},
        {"elevation": 987.0, "latitude": 44.67995, "longitude": 6.07358},
        {"elevation": 987.0, "latitude": 44.67977, "longitude": 6.07364},
        {"elevation": 987.0, "latitude": 44.67972, "longitude": 6.07367},
        {"elevation": 987.0, "latitude": 44.67966, "longitude": 6.07368},
        {"elevation": 986.0, "latitude": 44.67961, "longitude": 6.0737},
        {"elevation": 986.0, "latitude": 44.67938, "longitude": 6.07377},
        {"elevation": 986.0, "latitude": 44.67933, "longitude": 6.07381},
        {"elevation": 985.0, "latitude": 44.67922, "longitude": 6.07385},
        {"elevation": 980.0, "latitude": 44.67911, "longitude": 6.0739},
        {"elevation": 980.0, "latitude": 44.679, "longitude": 6.07399},
        {"elevation": 980.0, "latitude": 44.67896, "longitude": 6.07402},
        {"elevation": 979.0, "latitude": 44.67884, "longitude": 6.07408},
        {"elevation": 981.0, "latitude": 44.67863, "longitude": 6.07423},
        {"elevation": 980.0, "latitude": 44.67858, "longitude": 6.07425},
        {"elevation": 979.0, "latitude": 44.67842, "longitude": 6.07434},
        {"elevation": 979.0, "latitude": 44.67837, "longitude": 6.07435},
        {"elevation": 975.0, "latitude": 44.67822, "longitude": 6.07442},
    ]
}
VALHALLA_VALUES = [
    1998.0,
    1998.0,
    1994.0,
    1994.0,
    1994.0,
    1993.0,
    1992.0,
    1992.0,
    1987.0,
    1987.0,
    1987.0,
    1987.0,
    1986.0,
    1986.0,
    1986.0,
    1985.0,
    1980.0,
    1980.0,
    1980.0,
    1979.0,
    1981.0,
    1980.0,
    1979.0,
    1979.0,
    1975.0,
]
VALHALLA_RESPONSE = {"height": VALHALLA_VALUES}
