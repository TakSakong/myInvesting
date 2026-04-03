import pytest
from flask import url_for, request, redirect
from app import app, get_db_connection

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.app_context():
        # Clear the database before testing
        conn = get_db_connection()
        conn.execute("DELETE FROM stocks")
        conn.commit()
        conn.close()
    
    with app.test_client() as client:
        yield client

def test_add_stock(client):
    # Simulate adding a stock
    response = client.post("/add", data={"symbol": "AAPL", "name": "Apple Inc.", "price": 150})

    # Check if the stock was added to the stocks db
    with app.app_context():
        conn = get_db_connection()
        stocks = conn.execute("SELECT * FROM stocks").fetchall()
        conn.close()

    assert len(stocks) == 1
    assert stocks[0]["symbol"] == "AAPL"
    assert stocks[0]["name"] == "Apple Inc."
    assert stocks[0]["price"] == 150.0

    # Check if the response renders the index page properly
    assert response.status_code == 200
    assert b"Apple Inc." in response.data

def test_add_multiple_stocks(client):
    # Add multiple stocks
    client.post("/add", data={"symbol": "AAPL", "name": "Apple Inc.", "price": 150})
    client.post("/add", data={"symbol": "MSFT", "name": "Microsoft Corp.",  "price": 250})

    # Check if both stocks were added
    with app.app_context():
        conn = get_db_connection()
        stocks = conn.execute("SELECT * FROM stocks ORDER BY symbol").fetchall()
        conn.close()

    assert len(stocks) == 2
    assert stocks[0]["symbol"] == "AAPL"
    assert stocks[0]["name"] == "Apple Inc."
    assert stocks[0]["price"] == 150.0

    assert stocks[1]["symbol"] == "MSFT"
    assert stocks[1]["name"] == "Microsoft Corp."
    assert stocks[1]["price"] == 250.0

def test_index_shows_stocks(client):
    # Add a stock directly via DB
    with app.app_context():
        conn = get_db_connection()
        conn.execute("INSERT INTO stocks (symbol, name, price) VALUES (?, ?, ?)", ("AAPL", "Apple Inc.", 150.0))
        conn.commit()
        conn.close()

    # Access the index page
    response = client.get("/")

    # Check if the stock information is displayed on the index page
    assert response.status_code == 200
    assert b"AAPL" in response.data
    assert b"Apple Inc." in response.data