import pytest
from flask import url_for
from app import app, get_db_connection

@pytest.fixture()
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

def test_delete_stock(client):
    # Add a stock for testing
    client.post("/add", data={"symbol": "AAPL", "name": "Apple Inc.", "price": 150})
    # Simulate deleting the stock
    response = client.post("/delete", data={"symbol": "AAPL"})

    # Check if the stock was deleted from the db
    with app.app_context():
        conn = get_db_connection()
        stocks = conn.execute("SELECT * FROM stocks").fetchall()
        conn.close()
        
    assert len(stocks) == 0

    # Check if the response renders the index page properly
    assert response.status_code == 200
    assert b"AAPL" not in response.data
    assert b"Apple Inc." not in response.data

def test_delete_nonexistent_stock(client):
    # Attempt to delete a stock that doesn't exist
    response = client.post("/delete", data={"symbol": "AAPL"}, follow_redirects=True)

    # Ensure the db is still empty
    with app.app_context():
        conn = get_db_connection()
        stocks = conn.execute("SELECT * FROM stocks").fetchall()
        conn.close()
        
    assert len(stocks) == 0

    # Check if the response renders the index page properly
    assert response.status_code == 200