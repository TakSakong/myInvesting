#app.py

from flask import Flask, render_template, request, redirect, url_for, abort, g, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import yfinance as yf
from datetime import datetime
import sqlite3
import logging
import time
import os
import secrets
from functools import wraps
from flasgger import Swagger
from .repository import UserRepository, StockRepository, FavoriteRepository, DiscussionRepository
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
Swagger(app)

def get_db_connection():
    """Establishes or retrieves the SQLite database connection.
    
    Returns:
        sqlite3.Connection: The active SQLite database connection for the current Flask app context.
    """
    if 'db' not in g:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if app.config.get("TESTING"):
            g.db = sqlite3.connect(os.path.join(base_dir, 'test_stocks.db'), check_same_thread=False)
        else:
            g.db = sqlite3.connect(os.path.join(base_dir, 'stocks.db'), check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db

def get_user_repo():
    return UserRepository(get_db_connection())

def get_stock_repo():
    """Retrieves an instance of StockRepository."""
    return StockRepository(get_db_connection())

def get_favorite_repo():
    return FavoriteRepository(get_db_connection())

def get_discussion_repo():
    return DiscussionRepository(get_db_connection())

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initializes the database by creating necessary tables."""
    conn = get_db_connection()
    UserRepository(conn).create_table()
    StockRepository(conn).create_table()
    FavoriteRepository(conn).create_table()
    DiscussionRepository(conn).create_table()

with app.app_context():
    init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def parse_date_strategy(pub_ts: str) -> str:
    """Parses a date string using the Strategy Pattern and Chain of Responsibility.
    
    Attempts to parse the publication date using several predefined formats. If all formatting 
    strategies fail, it gracefully degrades by returning the first 10 characters.
    
    Args:
        pub_ts (str): The raw publication timestamp string.
        
    Returns:
        str: A parsed and formatted date string (YYYY-MM-DD), or the truncated original string 
        if parsing is unresolvable.
    """
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
stock_cache = {}  # Proxy Pattern 인메모리 캐시

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            flash("아이디와 비밀번호를 모두 입력해주세요.", "error")
            return redirect(url_for('register'))
            
        hashed_pw = generate_password_hash(password)
        repo = get_user_repo()
        user_id = repo.add_user(username, hashed_pw)
        if user_id:
            session['user_id'] = user_id
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash("이미 존재하는 아이디입니다.", "error")
            return redirect(url_for('register'))
            
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        repo = get_user_repo()
        user = repo.get_user_by_username(username)
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            flash("아이디 혹은 비밀번호가 올바르지 않습니다.", "error")
            return redirect(url_for('login'))
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

def get_stock_data(symbol):
    """Fetches stock data using a Proxy Caching Pattern.
    
    Reduces synchronous load times and external API calls to Yahoo Finance 
    by caching results in-memory. Bypasses the cache entirely when in TESTING mode.
    
    Args:
        symbol (str): The stock ticker symbol.
        
    Returns:
        tuple: A tuple containing:
            - dict or None: The stock information dictionary.
            - list: A list of related news articles.
    """
    # 1. 테스트 환경일 경우 목(Mock) 주입이 깨지지 않게 캐시 바이패스(우회)
    if app.config.get("TESTING"):
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1mo")
        dates = hist.index.strftime('%Y-%m-%d').tolist() if not hist.empty else []
        prices = [round(p, 2) for p in hist['Close'].tolist()] if not hist.empty else []
        chart_data = {"dates": dates, "prices": prices}
        return stock.info, (stock.news or []), chart_data

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
        
        hist = stock.history(period="1mo")
        dates = hist.index.strftime('%Y-%m-%d').tolist() if not hist.empty else []
        prices = [round(p, 2) for p in hist['Close'].tolist()] if not hist.empty else []
        chart_data = {"dates": dates, "prices": prices}
        
        stock_cache[symbol] = ((info, raw_news, chart_data), now)
        return info, raw_news, chart_data
    except Exception as e:
        # 야후 서버 타임아웃 / 장애 방어용
        logging.error(f"야후 파이낸스 API 오류: {e}")
        return None, [], {}

@app.route("/")
@login_required
def index():
    """Renders the main dashboard page."""
    user_id = session['user_id']
    stocks = get_stock_repo().get_all_by_user(user_id)
    favorites = get_favorite_repo().get_all_by_user(user_id)
    return render_template("index.html", stocks=stocks, favorites=favorites)
@app.route("/search")
@login_required
def search():
    """Handles stock search and displays relevant news and information.
    
    Retrieves a stock ticker symbol from the query parameters, fetches its proxy-cached
    data from Yahoo Finance, parses related news dates using a Strategy pattern, 
    and renders the search results page.
    
    Returns:
        str: The rendered HTML content for the search page or an error message if the ticker is invalid.
    ---
    parameters:
      - name: q
        in: query
        type: string
        required: true
        description: The stock ticker symbol to search for
    responses:
      200:
        description: The search results page or an error text
    """
    symbol = request.args.get("q").strip().upper()

    # Proxy Pattern을 통해 정보를 받아옴 (동기식 대기 단축)
    info, raw_news, chart_data = get_stock_data(symbol)
    
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

    posts = get_discussion_repo().get_posts_by_symbol(symbol)

    return render_template('search.html',
                            name=info.get("longName"),
                            price=info.get("currentPrice"),
                            symbol=symbol,
                            news=news,
                            chart_data=chart_data,
                            posts=posts)


@app.route("/news")
def news_detail():
    """Redirects the user to an external news article URL.
    
    Args:
        url (str, optional): The URL parameter passed in the query string.
        
    Returns:
        werkzeug.wrappers.Response: A redirect response to the specified URL.
        
    Raises:
        werkzeug.exceptions.BadRequest: If the URL parameter is missing.
    ---
    parameters:
      - name: url
        in: query
        type: string
        required: true
        description: The URL string of the news article to redirect
    responses:
      302:
        description: Redirects to the target URL
      400:
        description: Bad Request if URL is missing
    """
    url = request.args.get("url", "")
    if not url:
        abort(400)
    return redirect(url)

@app.route("/discussion/post", methods=["POST"])
@login_required
def add_post():
    symbol = request.form.get("symbol")
    content = request.form.get("content")
    if symbol and content:
        get_discussion_repo().add_post(symbol, session['user_id'], content)
    return redirect(url_for('search', q=symbol))

@app.route("/discussion/comment", methods=["POST"])
@login_required
def add_comment():
    post_id = request.form.get("post_id")
    symbol = request.form.get("symbol")
    content = request.form.get("content")
    if post_id and symbol and content:
        get_discussion_repo().add_comment(post_id, session['user_id'], content)
    return redirect(url_for('search', q=symbol))

@app.route("/add", methods=["POST"])
@login_required
def add():
    """Adds a new stock to the database.
    
    Validates form submissions utilizing a Guard Clause pattern to ensure 
    no inputs are empty and that the parsed price is a valid numeric value.
    
    Returns:
        str: The updated index page HTML containing the new stock.
        
    Raises:
        werkzeug.exceptions.BadRequest: If there is a missing field or invalid price format.
    ---
    consumes:
      - application/x-www-form-urlencoded
    parameters:
      - name: symbol
        in: formData
        type: string
        required: true
        description: Ticker symbol.
      - name: name
        in: formData
        type: string
        required: true
        description: Company name.
      - name: price
        in: formData
        type: number
        required: true
        description: Numeric price string.
    responses:
      200:
        description: Updated dashboard HTML.
      400:
        description: Validation error.
    """
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
    repo.add(session['user_id'], symbol, name, parsed_price)
    return redirect(url_for('index'))

@app.route("/favorite/add", methods=["POST"])
@login_required
def favorite_add():
    """Adds a given news article to the global favorites list.
    
    Verifies that the article URL does not already exist in the favorites 
    list before appending it to prevent duplicates.
    
    Returns:
        str: The updated index page HTML incorporating the new favorite article.
    ---
    consumes:
      - application/x-www-form-urlencoded
    parameters:
      - name: url
        in: formData
        type: string
        required: true
      - name: title
        in: formData
        type: string
      - name: snippet
        in: formData
        type: string
      - name: date
        in: formData
        type: string
      - name: publisher
        in: formData
        type: string
    responses:
      200:
        description: Updated dashboard HTML.
    """
    url = request.form.get("url", "")
    title = request.form.get("title", "")
    snippet = request.form.get("snippet", "")
    date = request.form.get("date", "")
    publisher = request.form.get("publisher", "")
    
    get_favorite_repo().add(session['user_id'], url, title, snippet, date, publisher)
    return redirect(url_for('index'))

@app.route("/favorite/delete", methods=["POST"])
@login_required
def favorite_delete():
    """Deletes a news article from the global favorites list.
    
    Uses list comprehension to filter out the specified article based on its URL.
    
    Returns:
        str: The updated index page HTML after the article is removed.
    ---
    consumes:
      - application/x-www-form-urlencoded
    parameters:
      - name: url
        in: formData
        type: string
        required: true
    responses:
      200:
        description: Updated dashboard HTML.
    """
    url = request.form.get("url", "")
    get_favorite_repo().delete(session['user_id'], url)
    return redirect(url_for('index'))

@app.route("/delete", methods=["POST"])
@login_required
def delete():
    """Deletes a stock from the database using its symbol.
    
    Returns:
        str: The updated index page HTML after the deletion.
    ---
    consumes:
      - application/x-www-form-urlencoded
    parameters:
      - name: symbol
        in: formData
        type: string
        required: true
    responses:
      200:
        description: Updated dashboard HTML.
    """
    symbol = request.form.get("symbol")

    repo = get_stock_repo()
    repo.delete(session['user_id'], symbol)

    # index 페이지로 리디렉션
    return redirect(url_for('index'))
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)