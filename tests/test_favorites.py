# tests/test_favorites.py
# /favorite/add, /favorite/delete 라우트 및 메인페이지 표시 전용 테스트
#
# 시나리오:
#   S1 – search.html의 뉴스 항목마다 즐겨찾기 버튼이 존재한다
#   S2 – 즐겨찾기 버튼을 누르면 기사가 즐겨찾기 목록에 추가된다
#   S3 – 즐겨찾기한 기사는 메인페이지(index.html)에서 한 눈에 볼 수 있다
#   S4 – 같은 기사를 중복 즐겨찾기해도 한 번만 등록된다
#   S5 – 즐겨찾기를 취소(삭제)하면 목록에서 제거된다

import pytest
from unittest.mock import MagicMock, patch
from app import app, favorites

# ---------------------------------------------------------------------------
# Shared mock data
# ---------------------------------------------------------------------------

ARTICLE = {
    "url":       "https://example.com/news/apple-record-high",
    "title":     "Apple Hits Record High Amid AI Boom",
    "snippet":   "Apple Inc. shares soared to a record high.",
    "date":      "2026-03-19",
    "publisher": "한국경제",
}

MOCK_INFO = {"currency": "USD", "longName": "Apple Inc.", "currentPrice": 175.0}

MOCK_NEWS = [
    {
        "content": {
            "id": "uuid-001",
            "title": ARTICLE["title"],
            "summary": ARTICLE["snippet"],
            "pubDate": "2026-03-19T09:00:00Z",
            "provider": {"displayName": ARTICLE["publisher"]},
            "canonicalUrl": {"url": ARTICLE["url"]},
        }
    }
]


@pytest.fixture(autouse=True)
def clear_favorites():
    """각 테스트 전에 즐겨찾기 목록을 초기화한다."""
    favorites.clear()
    yield
    favorites.clear()


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def _make_mock_ticker():
    mock = MagicMock()
    mock.info = MOCK_INFO
    mock.news = MOCK_NEWS
    return mock


# ---------------------------------------------------------------------------
# S1 – search.html의 뉴스 항목마다 즐겨찾기 버튼이 존재한다
# ---------------------------------------------------------------------------

class TestScenario1_FavoriteButtonOnSearchPage:
    """search.html에 즐겨찾기 버튼(/favorite/add 로 POST)이 렌더링된다."""

    def test_favorite_button_rendered(self, client):
        """뉴스 목록에 /favorite/add 로 POST하는 버튼이 있어야 한다."""
        with patch("yfinance.Ticker", return_value=_make_mock_ticker()):
            response = client.get("/search?q=AAPL")
        assert b"/favorite/add" in response.data

    def test_favorite_button_contains_article_url(self, client):
        """즐겨찾기 버튼의 hidden input에 기사 URL이 포함되어야 한다."""
        with patch("yfinance.Ticker", return_value=_make_mock_ticker()):
            response = client.get("/search?q=AAPL")
        assert ARTICLE["url"].encode() in response.data


# ---------------------------------------------------------------------------
# S2 – 즐겨찾기 버튼을 누르면 기사가 즐겨찾기 목록에 추가된다
# ---------------------------------------------------------------------------

class TestScenario2_AddFavorite:
    """POST /favorite/add 가 기사를 favorites 목록에 추가한다."""

    def test_add_favorite_returns_200(self, client):
        """즐겨찾기 추가 후 200 OK를 반환해야 한다."""
        response = client.post("/favorite/add", data=ARTICLE)
        assert response.status_code == 200

    def test_add_favorite_stores_article(self, client):
        """즐겨찾기 추가 후 favorites 목록에 기사가 저장되어야 한다."""
        client.post("/favorite/add", data=ARTICLE)
        assert len(favorites) == 1
        assert favorites[0]["url"] == ARTICLE["url"]
        assert favorites[0]["title"] == ARTICLE["title"]

    def test_add_favorite_stores_all_fields(self, client):
        """도메인 정보(title·snippet·date·publisher)가 모두 저장되어야 한다."""
        client.post("/favorite/add", data=ARTICLE)
        saved = favorites[0]
        assert saved["snippet"]   == ARTICLE["snippet"]
        assert saved["date"]      == ARTICLE["date"]
        assert saved["publisher"] == ARTICLE["publisher"]


# ---------------------------------------------------------------------------
# S3 – 즐겨찾기한 기사는 메인페이지(index.html)에서 한 눈에 볼 수 있다
# ---------------------------------------------------------------------------

class TestScenario3_FavoritesVisibleOnMainPage:
    """index.html에 즐겨찾기된 기사들이 표시된다."""

    def test_main_page_shows_favorite_title(self, client):
        """메인 페이지에 즐겨찾기된 기사의 제목이 표시되어야 한다."""
        client.post("/favorite/add", data=ARTICLE)
        response = client.get("/")
        assert ARTICLE["title"].encode() in response.data

    def test_main_page_shows_favorite_publisher(self, client):
        """메인 페이지에 즐겨찾기된 기사의 뉴스사가 표시되어야 한다."""
        client.post("/favorite/add", data=ARTICLE)
        response = client.get("/")
        assert ARTICLE["publisher"].encode("utf-8") in response.data

    def test_main_page_shows_favorite_date(self, client):
        """메인 페이지에 즐겨찾기된 기사의 날짜가 표시되어야 한다."""
        client.post("/favorite/add", data=ARTICLE)
        response = client.get("/")
        assert ARTICLE["date"].encode() in response.data

    def test_main_page_no_favorites_shows_message(self, client):
        """즐겨찾기가 없을 때 안내 메시지가 표시되어야 한다."""
        response = client.get("/")
        assert "즐겨찾기한 기사가 없습니다".encode("utf-8") in response.data


# ---------------------------------------------------------------------------
# S4 – 같은 기사를 중복 즐겨찾기해도 한 번만 등록된다
# ---------------------------------------------------------------------------

class TestScenario4_NoDuplicateFavorites:
    """URL이 같은 기사는 중복 추가되지 않는다."""

    def test_duplicate_favorite_not_added(self, client):
        """같은 URL로 두 번 즐겨찾기해도 목록에 한 개만 있어야 한다."""
        client.post("/favorite/add", data=ARTICLE)
        client.post("/favorite/add", data=ARTICLE)
        assert len(favorites) == 1


# ---------------------------------------------------------------------------
# S5 – 즐겨찾기를 취소(삭제)하면 목록에서 제거된다
# ---------------------------------------------------------------------------

class TestScenario5_RemoveFavorite:
    """POST /favorite/delete 가 기사를 favorites 목록에서 제거한다."""

    def test_delete_favorite_removes_article(self, client):
        """즐겨찾기 취소 후 favorites 목록이 비어 있어야 한다."""
        client.post("/favorite/add", data=ARTICLE)
        client.post("/favorite/delete", data={"url": ARTICLE["url"]})
        assert len(favorites) == 0

    def test_delete_favorite_returns_200(self, client):
        """즐겨찾기 취소 후 200 OK를 반환해야 한다."""
        client.post("/favorite/add", data=ARTICLE)
        response = client.post("/favorite/delete", data={"url": ARTICLE["url"]})
        assert response.status_code == 200

    def test_delete_nonexistent_favorite_is_safe(self, client):
        """존재하지 않는 즐겨찾기를 삭제해도 에러 없이 200 OK를 반환해야 한다."""
        response = client.post("/favorite/delete", data={"url": ARTICLE["url"]})
        assert response.status_code == 200
        assert len(favorites) == 0
