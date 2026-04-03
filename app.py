#app.py

from flask import Flask, render_template, request, redirect, url_for, abort
import yfinance as yf
from datetime import datetime
import sqlite3

app = Flask(__name__)

def get_db_connection():
    if app.config.get("TESTING"):
        conn = sqlite3.connect('test_stocks.db', check_same_thread=False)
    else:
        conn = sqlite3.connect('stocks.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

with app.app_context():
    init_db()

def get_all_stocks():
    conn = get_db_connection()
    stocks = conn.execute('SELECT * FROM stocks').fetchall()
    conn.close()
    return [dict(row) for row in stocks]

# 전역 변수
favorites = []  # 즐겨찾기한 뉴스 기사 목록

@app.route("/")
def index():
    stocks = get_all_stocks()
    return render_template("index.html", stocks=stocks, favorites=favorites)
@app.route("/search") 
def search():
    symbol = request.args.get("q").strip().upper()

    stock = yf.Ticker(symbol)
    info = stock.info
    if not info or info.get("currency") != "USD":
        return "유효한 미국 주식 티커를 입력해주세요."

    # Fetch latest news articles for this ticker
    raw_news = stock.news or []
    news = []
    for article in raw_news:
        content = article.get("content", {})
        pub_ts = content.get("pubDate") or content.get("displayTime", "")
        # pubDate may be an ISO string; fall back gracefully
        try:
            pub_date = datetime.fromisoformat(pub_ts.replace("Z", "+00:00")).strftime("%Y-%m-%d")
        except Exception:
            pub_date = pub_ts[:10] if pub_ts else ""

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
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO stocks (symbol, name, price) VALUES (?, ?, ?)',
                     (symbol, name, float(price)))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # ignore duplicates
    finally:
        conn.close()
        
    stocks = get_all_stocks()
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
    stocks = get_all_stocks()
    return render_template("index.html", stocks=stocks, favorites=favorites)


@app.route("/favorite/delete", methods=["POST"])
def favorite_delete():
    """기사를 즐겨찾기 목록에서 제거한다."""
    url = request.form.get("url", "")
    favorites[:] = [f for f in favorites if f["url"] != url]
    stocks = get_all_stocks()
    return render_template("index.html", stocks=stocks, favorites=favorites)

@app.route("/delete", methods=["POST"])
def delete():
    symbol = request.form.get("symbol")

    conn = get_db_connection()
    conn.execute('DELETE FROM stocks WHERE symbol = ?', (symbol,))
    conn.commit()
    conn.close()

    stocks = get_all_stocks()
    # index 페이지로 리디렉션
    return render_template("index.html", stocks=stocks, favorites=favorites)
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)