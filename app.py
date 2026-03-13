#app.py

from flask import Flask, render_template, request
import yfinance as yf

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/search") 
def search():
    symbol = request.args.get("q")

    stock = yf.Ticker(symbol)
    info = stock.info

    price = info.get("currentPrice")
    name = info.get("longName")

    return f"{name} 현재 가격: {price}"
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)