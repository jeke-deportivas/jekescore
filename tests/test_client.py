"""Tests para el cliente HTTP."""


from jekescore.client import JekeScoreClient, USER_AGENTS


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
