import sqlite3

class StockRepository:
    """A repository for handling database operations related to stocks.
    
    Attributes:
        conn (sqlite3.Connection): The SQLite database connection object.
    """
    def __init__(self, db_connection):
        """Initializes the StockRepository.
        
        Args:
            db_connection (sqlite3.Connection): The SQLite database connection to be used.
        """
        self.conn = db_connection

    def create_table(self):
        """Creates the 'stocks' table if it does not already exist.
        
        This sets up the schema required for storing stock symbols, names, and prices.
        """
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')
        self.conn.commit()

    def get_all(self):
        """Retrieves all stored stocks from the database.
        
        Returns:
            list[dict]: A list of dictionaries, where each dictionary contains stock data 
            (id, symbol, name, price).
        """
        stocks = self.conn.execute('SELECT * FROM stocks').fetchall()
        return [dict(row) for row in stocks]

    def add(self, symbol, name, price):
        """Adds a new stock entry into the database.
        
        Args:
            symbol (str): The ticker symbol of the stock (e.g., 'AAPL').
            name (str): The full name of the company or asset.
            price (float): The current price of the stock.
            
        Returns:
            bool: True if the stock was successfully added, False if the symbol already exists.
        """
        try:
            self.conn.execute('INSERT INTO stocks (symbol, name, price) VALUES (?, ?, ?)',
                              (symbol, name, float(price)))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def delete(self, symbol):
        """Deletes a stock entry from the database by its symbol.
        
        Args:
            symbol (str): The ticker symbol of the stock to delete.
        """
        self.conn.execute('DELETE FROM stocks WHERE symbol = ?', (symbol,))
        self.conn.commit()
