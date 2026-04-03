# tests/test_news.py
# /news 라우트 전용 테스트
#
# 시나리오:
#   S3 – user는 뉴스를 클릭하여 뉴스 세부 정보들을 볼 수 있다
#        (search.html에 뉴스 링크가 포함되어 있고, 클릭 시 외부 기사 URL로 리디렉션된다)

import pytest
from unittest.mock import MagicMock, patch
from app import app

# ---------------------------------------------------------------------------
# Shared mock data (search.html에 링크가 렌더링됐는지 확인하기 위해 필요)
# ---------------------------------------------------------------------------

MOCK_INFO = {
    "currency": "USD",
    "longName": "Apple Inc.",
    "currentPrice": 175.0,
}

MOCK_NEWS = [
    {
        "content": {
            "id": "uuid-001",
            "title": "Apple Hits Record High Amid AI Boom",
            "summary": "Apple Inc. shares soared to a record high.",
            "pubDate": "2026-03-19T09:00:00Z",
            "provider": {"displayName": "한국경제"},
            "canonicalUrl": {"url": "https://example.com/news/apple-record-high"},
        }
    },
]


@pytest.fixture
def client():
    app.config["TESTING"] = True
    from app import init_db, get_db_connection
    with app.app_context():
        init_db()
        conn = get_db_connection()
        conn.execute("DELETE FROM stocks")
        conn.commit()
        conn.close()
    with app.test_client() as client:
        yield client


def _make_mock_ticker(info=MOCK_INFO, news=MOCK_NEWS):
    """Return a MagicMock that mimics a yfinance.Ticker object."""
    mock_ticker = MagicMock()
    mock_ticker.info = info
    mock_ticker.news = news
    return mock_ticker


# ---------------------------------------------------------------------------
# S3 – user는 뉴스를 클릭하여 뉴스 세부 정보들을 볼 수 있다
# ---------------------------------------------------------------------------

class TestScenario3_NewsDetailNavigation:
    """뉴스 클릭 시 외부 기사 URL로 이동한다."""

    def test_news_link_present_in_search_results(self, client):
        """search.html의 뉴스 항목에 /news?url=... 형식의 링크가 포함되어야 한다."""
        with patch("yfinance.Ticker", return_value=_make_mock_ticker()):
            response = client.get("/search?q=AAPL")
        assert b"/news?url=" in response.data

    def test_news_detail_route_redirects_to_article(self, client):
        """GET /news?url=<기사URL> 은 해당 URL로 302 리디렉션해야 한다."""
        article_url = "https://example.com/news/apple-record-high"
        response = client.get(f"/news?url={article_url}")
        assert response.status_code == 302
        assert response.headers["Location"] == article_url

    def test_news_detail_without_url_returns_400(self, client):
        """url 파라미터 없이 /news에 접근하면 400 Bad Request를 반환해야 한다."""
        response = client.get("/news")
        assert response.status_code == 400
