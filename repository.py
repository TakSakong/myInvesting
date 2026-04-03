import sqlite3

class StockRepository:
    def __init__(self, db_connection):
        self.conn = db_connection

    def create_table(self):
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
        stocks = self.conn.execute('SELECT * FROM stocks').fetchall()
        return [dict(row) for row in stocks]

    def add(self, symbol, name, price):
        try:
            self.conn.execute('INSERT INTO stocks (symbol, name, price) VALUES (?, ?, ?)',
                              (symbol, name, float(price)))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def delete(self, symbol):
        self.conn.execute('DELETE FROM stocks WHERE symbol = ?', (symbol,))
        self.conn.commit()
