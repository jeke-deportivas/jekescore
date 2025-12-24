"""Tests para el cliente HTTP."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jekescore.client import JekeScoreClient, USER_AGENTS, get_shotmap


class TestJekeScoreClient:
    def test_default_platform_windows(self):
        client = JekeScoreClient()
        ua = str(client.session.headers["User-Agent"])
        assert USER_AGENTS["windows"] in ua

    def test_platform_macos(self):
        client = JekeScoreClient(platform="macos")
        ua = str(client.session.headers["User-Agent"])
        assert "Macintosh" in ua

    def test_platform_linux(self):
        client = JekeScoreClient(platform="linux")
        ua = str(client.session.headers["User-Agent"])
        assert "Linux" in ua

    def test_custom_user_agent(self):
        custom_ua = "CustomBot/1.0"
        client = JekeScoreClient(user_agent=custom_ua)
        assert str(client.session.headers["User-Agent"]) == custom_ua

    def test_cookies_dict(self):
        cookies = {"session": "abc123", "token": "xyz"}
        client = JekeScoreClient(cookies=cookies)
        assert client.session.cookies.get("session") == "abc123"
        assert client.session.cookies.get("token") == "xyz"

    def test_cookies_file_dict_format(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"session": "file123", "auth": "token456"}, f)
            f.flush()
            client = JekeScoreClient(cookies_file=f.name)
            assert client.session.cookies.get("session") == "file123"
            assert client.session.cookies.get("auth") == "token456"
            Path(f.name).unlink()

    def test_cookies_file_list_format(self):
        cookies_list = [
            {"name": "session", "value": "list123"},
            {"name": "token", "value": "listtoken"},
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(cookies_list, f)
            f.flush()
            client = JekeScoreClient(cookies_file=f.name)
            assert client.session.cookies.get("session") == "list123"
            assert client.session.cookies.get("token") == "listtoken"
            Path(f.name).unlink()

    def test_cookies_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            JekeScoreClient(cookies_file="/nonexistent/path/cookies.json")

    def test_unknown_platform_fallback_to_windows(self):
        client = JekeScoreClient(platform="android")
        ua = str(client.session.headers["User-Agent"])
        assert USER_AGENTS["windows"] in ua


class TestGetMatchIdFromUrl:
    def test_extract_from_hash_format(self):
        url = "https://www.sofascore.com/football/match/barcelona-atalanta/OgbsKgb#id:12557619"
        match_id = JekeScoreClient.get_match_id_from_url(url)
        assert match_id == 12557619

    def test_extract_from_hash_with_tab(self):
        url = "https://www.sofascore.com/es/football/match/eibar-racing/KgbsOgb#id:12557619,tab:statistics"
        match_id = JekeScoreClient.get_match_id_from_url(url)
        assert match_id == 12557619

    def test_extract_from_event_format(self):
        url = "https://www.sofascore.com/api/v1/event/12345678/shotmap"
        match_id = JekeScoreClient.get_match_id_from_url(url)
        assert match_id == 12345678

    def test_no_match_id(self):
        url = "https://www.sofascore.com/football"
        match_id = JekeScoreClient.get_match_id_from_url(url)
        assert match_id is None


class TestParseShot:
    @pytest.fixture
    def client(self):
        return JekeScoreClient()

    def test_parse_basic_shot(self, client):
        shot_data = {
            "id": 12345,
            "time": 35,
            "timeSeconds": 2100,
            "isHome": True,
            "shotType": "goal",
            "situation": "assisted",
            "bodyPart": "right-foot",
            "player": {"id": 100, "name": "Test Player", "shortName": "T. Player"},
            "playerCoordinates": {"x": 18.5, "y": 45.0, "z": 0},
            "goalMouthLocation": "low-left",
            "goalMouthCoordinates": {"x": 0, "y": 50.0, "z": 5.0},
        }
        shot = client._parse_shot(shot_data)
        assert shot.id == 12345
        assert shot.time == 35
        assert shot.is_home is True
        assert shot.shot_type == "goal"
        assert shot.player.name == "Test Player"
        assert shot.x == 18.5
        assert shot.y == 45.0

    def test_parse_shot_with_goalkeeper(self, client):
        shot_data = {
            "id": 12346,
            "time": 50,
            "timeSeconds": 3000,
            "isHome": False,
            "shotType": "save",
            "situation": "regular",
            "bodyPart": "left-foot",
            "player": {"id": 200, "name": "Striker"},
            "playerCoordinates": {"x": 15.0, "y": 50.0},
            "goalMouthLocation": "high-centre",
            "goalMouthCoordinates": {"x": 0, "y": 50.0, "z": 25.0},
            "goalkeeper": {"id": 300, "name": "Goalie", "position": "G"},
        }
        shot = client._parse_shot(shot_data)
        assert shot.goalkeeper is not None
        assert shot.goalkeeper.name == "Goalie"
        assert shot.goalkeeper.position == "G"

    def test_parse_shot_with_draw_coordinates(self, client):
        shot_data = {
            "id": 12347,
            "time": 60,
            "timeSeconds": 3600,
            "isHome": True,
            "shotType": "miss",
            "situation": "corner",
            "bodyPart": "head",
            "player": {"id": 400, "name": "Header"},
            "playerCoordinates": {"x": 5.0, "y": 45.0},
            "goalMouthLocation": "high-right",
            "goalMouthCoordinates": {"x": 0, "y": 40.0, "z": 30.0},
            "draw": {
                "start": {"x": 5.0, "y": 45.0, "z": 0},
                "end": {"x": 0, "y": 40.0, "z": 30.0},
                "goal": {"x": 0, "y": 40.0, "z": 30.0},
            },
        }
        shot = client._parse_shot(shot_data)
        assert shot.draw is not None
        assert shot.draw.start.x == 5.0
        assert shot.draw.end.y == 40.0

    def test_parse_shot_with_block(self, client):
        shot_data = {
            "id": 12348,
            "time": 70,
            "timeSeconds": 4200,
            "isHome": False,
            "shotType": "block",
            "situation": "regular",
            "bodyPart": "right-foot",
            "player": {"id": 500, "name": "Shooter"},
            "playerCoordinates": {"x": 20.0, "y": 50.0},
            "goalMouthLocation": "low-centre",
            "goalMouthCoordinates": {"x": 0, "y": 50.0, "z": 10.0},
            "blockCoordinates": {"x": 10.0, "y": 50.0, "z": 5.0},
            "draw": {
                "start": {"x": 20.0, "y": 50.0},
                "end": {"x": 10.0, "y": 50.0},
                "goal": {"x": 0, "y": 50.0},
                "block": {"x": 10.0, "y": 50.0, "z": 5.0},
            },
        }
        shot = client._parse_shot(shot_data)
        assert shot.block_coordinates is not None
        assert shot.block_coordinates.x == 10.0
        assert shot.draw is not None
        assert shot.draw.block is not None
        assert shot.draw.block.x == 10.0

    def test_parse_shot_with_goal_type(self, client):
        shot_data = {
            "id": 12349,
            "time": 90,
            "timeSeconds": 5400,
            "isHome": True,
            "shotType": "goal",
            "situation": "set-piece",
            "bodyPart": "right-foot",
            "player": {"id": 600, "name": "Penalty Taker"},
            "playerCoordinates": {"x": 11.0, "y": 50.0},
            "goalMouthLocation": "low-right",
            "goalMouthCoordinates": {"x": 0, "y": 45.0, "z": 5.0},
            "goalType": "penalty",
        }
        shot = client._parse_shot(shot_data)
        assert shot.goal_type == "penalty"


class TestGetShotmap:
    @pytest.fixture
    def mock_response_data(self):
        return {
            "shotmap": [
                {
                    "id": 1001,
                    "time": 25,
                    "timeSeconds": 1500,
                    "isHome": True,
                    "shotType": "goal",
                    "situation": "assisted",
                    "bodyPart": "right-foot",
                    "player": {"id": 10, "name": "Scorer"},
                    "playerCoordinates": {"x": 15.0, "y": 45.0},
                    "goalMouthLocation": "low-left",
                    "goalMouthCoordinates": {"x": 0, "y": 50.0, "z": 5.0},
                },
                {
                    "id": 1002,
                    "time": 55,
                    "timeSeconds": 3300,
                    "isHome": False,
                    "shotType": "miss",
                    "situation": "regular",
                    "bodyPart": "left-foot",
                    "player": {"id": 20, "name": "Shooter"},
                    "playerCoordinates": {"x": 22.0, "y": 60.0},
                    "goalMouthLocation": "high-right",
                    "goalMouthCoordinates": {"x": 0, "y": 40.0, "z": 30.0},
                },
            ]
        }

    def test_get_shotmap(self, mock_response_data):
        client = JekeScoreClient()
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_response_data
        mock_resp.raise_for_status = MagicMock()

        with patch.object(client.session, "get", return_value=mock_resp):
            shotmap = client.get_shotmap(12345678)
            assert shotmap.match_id == 12345678
            assert len(shotmap) == 2
            assert shotmap.shots[0].id == 1001
            assert shotmap.shots[1].id == 1002

    def test_get_shotmap_with_referer(self, mock_response_data):
        client = JekeScoreClient()
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_response_data
        mock_resp.raise_for_status = MagicMock()

        with patch.object(client.session, "get", return_value=mock_resp) as mock_get:
            referer = "https://www.sofascore.com/match/test#id:12345678"
            client.get_shotmap(12345678, referer_url=referer)
            call_args = mock_get.call_args
            assert call_args[1]["headers"]["Referer"] == referer

    def test_get_shotmap_with_string_id(self, mock_response_data):
        client = JekeScoreClient()
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_response_data
        mock_resp.raise_for_status = MagicMock()

        with patch.object(client.session, "get", return_value=mock_resp):
            shotmap = client.get_shotmap("12345678")
            assert shotmap.match_id == 12345678


class TestConvenienceFunction:
    def test_get_shotmap_function(self):
        with patch("jekescore.client.JekeScoreClient") as MockClient:
            mock_instance = MagicMock()
            MockClient.return_value = mock_instance
            mock_instance.get_shotmap.return_value = MagicMock(match_id=99999)

            result = get_shotmap(99999, platform="macos")
            MockClient.assert_called_once_with(cookies=None, cookies_file=None, platform="macos")
            mock_instance.get_shotmap.assert_called_once_with(99999)
            assert result.match_id == 99999
