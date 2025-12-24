"""Tests para los modelos de datos."""

import pytest

from jekescore.models import Coordinates, Player, Shot, ShotMap


class TestCoordinates:
    def test_create_coordinates(self):
        coords = Coordinates(x=10.5, y=20.3, z=0)
        assert coords.x == 10.5
        assert coords.y == 20.3
        assert coords.z == 0

    def test_coordinates_default_z(self):
        coords = Coordinates(x=10, y=20)
        assert coords.z == 0


class TestPlayer:
    def test_create_player(self):
        player = Player(id=123, name="Lionel Messi", position="F")
        assert player.id == 123
        assert player.name == "Lionel Messi"
        assert player.position == "F"


class TestShot:
    @pytest.fixture
    def sample_shot(self):
        return Shot(
            id=6273548,
            time=36,
            time_seconds=2131,
            is_home=True,
            shot_type="goal",
            situation="assisted",
            body_part="right-foot",
            player=Player(id=605674, name="Iñigo Vicente", position="M"),
            player_coordinates=Coordinates(x=18.8, y=47.8, z=0),
            goal_mouth_location="low-left",
            goal_mouth_coordinates=Coordinates(x=0, y=53.9, z=1.9),
            goal_type="regular",
        )

    def test_shot_is_goal(self, sample_shot):
        assert sample_shot.is_goal is True

    def test_shot_coordinates(self, sample_shot):
        assert sample_shot.x == 18.8
        assert sample_shot.y == 47.8

    def test_shot_not_goal(self):
        shot = Shot(
            id=1,
            time=10,
            time_seconds=600,
            is_home=False,
            shot_type="miss",
            situation="regular",
            body_part="left-foot",
            player=Player(id=1, name="Test Player"),
            player_coordinates=Coordinates(x=10, y=20),
            goal_mouth_location="high-right",
            goal_mouth_coordinates=Coordinates(x=0, y=40, z=30),
        )
        assert shot.is_goal is False


class TestShotMap:
    @pytest.fixture
    def sample_shotmap(self):
        shots = [
            Shot(
                id=1,
                time=10,
                time_seconds=600,
                is_home=True,
                shot_type="goal",
                situation="assisted",
                body_part="right-foot",
                player=Player(id=1, name="Player 1"),
                player_coordinates=Coordinates(x=10, y=20),
                goal_mouth_location="low-left",
                goal_mouth_coordinates=Coordinates(x=0, y=50, z=10),
            ),
            Shot(
                id=2,
                time=25,
                time_seconds=1500,
                is_home=False,
                shot_type="save",
                situation="corner",
                body_part="head",
                player=Player(id=2, name="Player 2"),
                player_coordinates=Coordinates(x=5, y=40),
                goal_mouth_location="high-centre",
                goal_mouth_coordinates=Coordinates(x=0, y=50, z=20),
            ),
            Shot(
                id=3,
                time=78,
                time_seconds=4680,
                is_home=True,
                shot_type="miss",
                situation="regular",
                body_part="left-foot",
                player=Player(id=3, name="Player 3"),
                player_coordinates=Coordinates(x=20, y=60),
                goal_mouth_location="right",
                goal_mouth_coordinates=Coordinates(x=0, y=40, z=15),
            ),
        ]
        return ShotMap(match_id=12345, shots=shots)

    def test_shotmap_len(self, sample_shotmap):
        assert len(sample_shotmap) == 3

    def test_shotmap_goals(self, sample_shotmap):
        goals = sample_shotmap.goals
        assert len(goals) == 1
        assert goals[0].id == 1

    def test_shotmap_home_shots(self, sample_shotmap):
        home = sample_shotmap.home_shots
        assert len(home) == 2

    def test_shotmap_away_shots(self, sample_shotmap):
        away = sample_shotmap.away_shots
        assert len(away) == 1

    def test_shotmap_iteration(self, sample_shotmap):
        shot_ids = [s.id for s in sample_shotmap.shots]
        assert shot_ids == [1, 2, 3]
