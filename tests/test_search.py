# tests/test_search.py
# /search 라우트 전용 테스트
#
# 시나리오:
#   S1 – 사용자가 티커로 주식을 검색하면 search.html로 이동한다
#   S2 – search.html에 최신 뉴스 목록(제목·내용 앞부분·날짜·뉴스사)이 표시된다

import pytest
from unittest.mock import MagicMock, patch
from app import app

# ---------------------------------------------------------------------------
# Shared mock data
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
            "summary": (
                "Apple Inc. shares soared to a record high on Thursday as investors "
                "cheered the company's latest artificial-intelligence announcements. "
                "Analysts raised price targets across the board."
            ),
            "pubDate": "2026-03-19T09:00:00Z",
            "provider": {"displayName": "한국경제"},
            "canonicalUrl": {"url": "https://example.com/news/apple-record-high"},
        }
    },
    {
        "content": {
            "id": "uuid-002",
            "title": "AAPL Q2 Earnings Preview",
            "summary": "Wall Street expects Apple to beat consensus estimates for the second quarter.",
            "pubDate": "2026-03-18T06:30:00Z",
            "provider": {"displayName": "연합뉴스"},
            "canonicalUrl": {"url": "https://example.com/news/aapl-earnings-preview"},
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
# S1 – 사용자가 티커로 주식을 검색하면 search.html로 이동한다
# ---------------------------------------------------------------------------

class TestScenario1_SearchRendersSearchPage:
    """유효한 티커를 검색하면 search.html이 200 OK로 렌더링된다."""

    def test_valid_ticker_returns_200(self, client):
        """GET /search?q=AAPL 는 200 OK를 반환해야 한다."""
        with patch("yfinance.Ticker", return_value=_make_mock_ticker()):
            response = client.get("/search?q=AAPL")
        assert response.status_code == 200

    def test_valid_ticker_renders_stock_info(self, client):
        """search.html에 종목명·현재가·심볼이 렌더링되어야 한다."""
        with patch("yfinance.Ticker", return_value=_make_mock_ticker()):
            response = client.get("/search?q=AAPL")
        assert b"Apple Inc." in response.data
        assert b"175.0" in response.data
        assert b"AAPL" in response.data

    def test_invalid_ticker_returns_error_message(self, client):
        """USD가 아닌 통화(KRW)의 티커는 에러 메시지를 반환해야 한다."""
        mock_ticker = _make_mock_ticker(info={"currency": "KRW"}, news=[])
        with patch("yfinance.Ticker", return_value=mock_ticker):
            response = client.get("/search?q=005930")
        assert "유효한 미국 주식 티커를 입력해주세요".encode("utf-8") in response.data

    def test_lowercase_ticker_is_uppercased(self, client):
        """소문자 티커(aapl)는 자동으로 대문자(AAPL)로 변환되어야 한다."""
        with patch("yfinance.Ticker", return_value=_make_mock_ticker()) as mock_cls:
            client.get("/search?q=aapl")
        mock_cls.assert_called_once_with("AAPL")


# ---------------------------------------------------------------------------
# S2 – search.html에 최신 뉴스 목록(제목·내용 앞부분·날짜·뉴스사)이 표시된다
# ---------------------------------------------------------------------------

class TestScenario2_NewsDisplayedOnSearchPage:
    """search.html에 뉴스 제목·내용 앞부분·날짜·뉴스사가 올바르게 표시된다."""

    def _get_response(self, client):
        with patch("yfinance.Ticker", return_value=_make_mock_ticker()):
            return client.get("/search?q=AAPL")

    def test_news_title_is_displayed(self, client):
        """각 뉴스의 제목이 search.html에 표시되어야 한다."""
        response = self._get_response(client)
        assert b"Apple Hits Record High Amid AI Boom" in response.data
        assert b"AAPL Q2 Earnings Preview" in response.data

    def test_news_snippet_is_displayed(self, client):
        """150자를 초과하는 뉴스 내용은 앞부분 150자 + '...'로 잘려야 한다."""
        response = self._get_response(client)
        assert b"Apple Inc. shares soared" in response.data
        assert b"..." in response.data

    def test_news_date_is_displayed(self, client):
        """뉴스 작성일자가 YYYY-MM-DD 형식으로 표시되어야 한다."""
        response = self._get_response(client)
        assert b"2026-03-19" in response.data
        assert b"2026-03-18" in response.data

    def test_news_publisher_is_displayed(self, client):
        """뉴스 회사 정보(한국경제, 연합뉴스 등)가 표시되어야 한다."""
        response = self._get_response(client)
        assert "한국경제".encode("utf-8") in response.data
        assert "연합뉴스".encode("utf-8") in response.data

    def test_no_news_shows_fallback_message(self, client):
        """뉴스가 없을 때 '관련 뉴스가 없습니다' 메시지가 표시되어야 한다."""
        mock_ticker = _make_mock_ticker(news=[])
        with patch("yfinance.Ticker", return_value=mock_ticker):
            response = client.get("/search?q=AAPL")
        assert "관련 뉴스가 없습니다".encode("utf-8") in response.data
