#app.py

from flask import Flask, render_template, request, redirect, url_for, abort, g
import yfinance as yf
from datetime import datetime
import sqlite3
import logging
import time
from repository import StockRepository
app = Flask(__name__)

def get_db_connection():
    if 'db' not in g:
        if app.config.get("TESTING"):
            g.db = sqlite3.connect('test_stocks.db', check_same_thread=False)
        else:
            g.db = sqlite3.connect('stocks.db', check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db

def get_stock_repo():
    return StockRepository(get_db_connection())

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    get_stock_repo().create_table()

with app.app_context():
    init_db()

def parse_date_strategy(pub_ts: str) -> str:
    """Strategy Pattern(전략 패턴) 및 Chain of Responsibility를 활용한 날짜 파싱 로직"""
    if not pub_ts:
        return ""
    
    # 처리 가능한 날짜 파싱 전략(Strategy) 목록
    # 새로운 포맷이 생기면 이 리스트에 lambda 함수 하나만 추가하면 됩니다 (OCP 준수)
    parsers = [
        # 전략 1: ISO 8601 (예: "2026-03-19T09:00:00Z")
        lambda t: datetime.fromisoformat(t.replace("Z", "+00:00")).strftime("%Y-%m-%d"),
        # 전략 2: 영문 텍스트 포맷 (예: "Mar 19, 2026")
        lambda t: datetime.strptime(t, "%b %d, %Y").strftime("%Y-%m-%d"),
        # 전략 3: 슬래시 포맷 (예: "2026/03/19")
        lambda t: datetime.strptime(t, "%Y/%m/%d").strftime("%Y-%m-%d"),
        # Fallback 전략: 최소 10자 이상이면 단순히 맨 앞 10자리(YYYY-MM-DD 형식일 확률이 높음) 반환
        lambda t: t[:10] if len(t) >= 10 else t
    ]

    for parse_func in parsers:
        try:
            return parse_func(pub_ts)
        except (ValueError, TypeError):  # 구체적인 에러만 포착 (Fail-Fast)
            continue
            
    # 모든 전략이 실패했을 경우 로깅 후 원본 텍스트 앞부분을 강제로 응답 (장애를 삼키지 않음)
    logging.warning(f"알 수 없는 날짜 포맷이 발견되었습니다: {pub_ts}")
    return pub_ts[:10]

# 전역 변수
favorites = []  # 즐겨찾기한 뉴스 기사 목록
stock_cache = {}  # Proxy Pattern 인메모리 캐시

def get_stock_data(symbol):
    """Proxy Caching Pattern: 야후 파이낸스 동기 병목을 줄이기 위한 10분 내부 캐싱 래퍼"""
    # 1. 테스트 환경일 경우 목(Mock) 주입이 깨지지 않게 캐시 바이패스(우회)
    if app.config.get("TESTING"):
        stock = yf.Ticker(symbol)
        return stock.info, (stock.news or [])

    now = time.time()
    CACHE_TIMEOUT = 600  # 10분 (600초)

    # 2. 캐시 조회 (Hit)
    if symbol in stock_cache:
        cached_data, timestamp = stock_cache[symbol]
        if now - timestamp < CACHE_TIMEOUT:
            logging.info(f"캐시 적중(Cache Hit) - {symbol}")
            return cached_data

    # 3. 캐시 없음/만료 (Miss) -> 원본 서버 왕복 후 캐시에 담기
    logging.info(f"캐시 미스(Cache Miss) - 외부 서버 연동 {symbol}")
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        raw_news = stock.news or []
        stock_cache[symbol] = ((info, raw_news), now)
        return info, raw_news
    except Exception as e:
        # 야후 서버 타임아웃 / 장애 방어용
        logging.error(f"야후 파이낸스 API 오류: {e}")
        return None, []

@app.route("/")
def index():
    stocks = get_stock_repo().get_all()
    return render_template("index.html", stocks=stocks, favorites=favorites)
@app.route("/search") 
def search():
    symbol = request.args.get("q").strip().upper()

    # Proxy Pattern을 통해 정보를 받아옴 (동기식 대기 단축)
    info, raw_news = get_stock_data(symbol)
    
    if not info or info.get("currency") != "USD":
        return "유효한 미국 주식 티커를 입력해주세요."

    news = []
    for article in raw_news:
        content = article.get("content", {})
        pub_ts = content.get("pubDate") or content.get("displayTime", "")
        # 전략 패턴을 활용하여 날짜 파싱
        pub_date = parse_date_strategy(pub_ts)

        summary_raw = content.get("summary", "")
        snippet = summary_raw[:150] + "..." if len(summary_raw) > 150 else summary_raw

        provider = content.get("provider", {}).get("displayName", "")

        news.append({
            "title":     content.get("title", ""),
            "snippet":   snippet,
            "date":      pub_date,
            "publisher": provider,
            "url":       content.get("canonicalUrl", {}).get("url", ""),
            "uuid":      content.get("id", ""),
        })

    return render_template('search.html',
                            name=info.get("longName"),
                            price=info.get("currentPrice"),
                            symbol=symbol,
                            news=news)


@app.route("/news")
def news_detail():
    """Redirect the user to an external news article URL."""
    url = request.args.get("url", "")
    if not url:
        abort(400)
    return redirect(url)

@app.route("/add", methods=["POST"])
def add():
    symbol = request.form.get("symbol")
    name   = request.form.get("name")
    price  = request.form.get("price")
    
    # Guard Clause (방어막 패턴): 서버 측 입력값 이중 검증
    if not symbol or not name or not price:
        abort(400, "필수 항목(symbol, name, price)이 누락되었습니다.")
        
    try:
        parsed_price = float(price)
    except (ValueError, TypeError):
        abort(400, "잘못된 가격 형식입니다. 숫자를 입력해야 합니다.")
    
    repo = get_stock_repo()
    repo.add(symbol, name, parsed_price)
        
    stocks = repo.get_all()
    return render_template("index.html", stocks=stocks, favorites=favorites)

@app.route("/favorite/add", methods=["POST"])
def favorite_add():
    """기사를 즐겨찾기 목록에 추가한다. URL 기준 중복은 무시한다."""
    url = request.form.get("url", "")
    # 중복 방지
    if not any(f["url"] == url for f in favorites):
        favorites.append({
            "url":       url,
            "title":     request.form.get("title", ""),
            "snippet":   request.form.get("snippet", ""),
            "date":      request.form.get("date", ""),
            "publisher": request.form.get("publisher", ""),
        })
    stocks = get_stock_repo().get_all()
    return render_template("index.html", stocks=stocks, favorites=favorites)


@app.route("/favorite/delete", methods=["POST"])
def favorite_delete():
    """기사를 즐겨찾기 목록에서 제거한다."""
    url = request.form.get("url", "")
    favorites[:] = [f for f in favorites if f["url"] != url]
    stocks = get_stock_repo().get_all()
    return render_template("index.html", stocks=stocks, favorites=favorites)

@app.route("/delete", methods=["POST"])
def delete():
    symbol = request.form.get("symbol")

    repo = get_stock_repo()
    repo.delete(symbol)

    stocks = repo.get_all()
    # index 페이지로 리디렉션
    return render_template("index.html", stocks=stocks, favorites=favorites)
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)