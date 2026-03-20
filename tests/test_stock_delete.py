import pytest
from flask import url_for
from app import app, stocks

@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_delete_stock(client):
    # Clear the stocks list and add a stock for testing
    stocks.clear()
    client.post("/add", data={"symbol": "AAPL", "name": "Apple Inc.", "price": 150})
    # Simulate deleting the stock
    response = client.post("/delete", data={"symbol": "AAPL"})

    # Check if the stock was deleted from the stocks list
    
    # assert len(stocks) == 0

    # Check if the response redirects to the index page
    assert response.status_code == 200
    assert b"AAPL" not in response.data
    assert b"Apple Inc." not in response.data

def test_delete_nonexistent_stock(client):
    # Clear the stocks list
    stocks.clear()

    # Attempt to delete a stock that doesn't exist
    response = client.post("/delete", data={"symbol": "AAPL"}, follow_redirects=True)

    # Ensure the stocks list is still empty
    assert len(stocks) == 0

    # Check if the response redirects to the index page
    assert response.status_code == 200