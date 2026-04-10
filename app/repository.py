import sqlite3

class UserRepository:
    """A repository for handling user authentication operations.
    """
    def __init__(self, db_connection):
        self.conn = db_connection

    def create_table(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def add_user(self, username, password_hash):
        try:
            cursor = self.conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                                       (username, password_hash))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_user_by_username(self, username):
        user = self.conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        return dict(user) if user else None
        
    def get_user_by_id(self, user_id):
        user = self.conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        return dict(user) if user else None


class StockRepository:
    """A repository for handling database operations related to user's stocks.
    """
    def __init__(self, db_connection):
        self.conn = db_connection

    def create_table(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, symbol)
            )
        ''')
        self.conn.commit()

    def get_all_by_user(self, user_id):
        stocks = self.conn.execute('SELECT * FROM stocks WHERE user_id = ?', (user_id,)).fetchall()
        return [dict(row) for row in stocks]

    def add(self, user_id, symbol, name, price):
        try:
            self.conn.execute('INSERT INTO stocks (user_id, symbol, name, price) VALUES (?, ?, ?, ?)',
                              (user_id, symbol, name, float(price)))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def delete(self, user_id, symbol):
        self.conn.execute('DELETE FROM stocks WHERE user_id = ? AND symbol = ?', (user_id, symbol))
        self.conn.commit()


class FavoriteRepository:
    """A repository for handling database operations related to user's news favorites.
    """
    def __init__(self, db_connection):
        self.conn = db_connection

    def create_table(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                snippet TEXT,
                date TEXT,
                publisher TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, url)
            )
        ''')
        self.conn.commit()

    def get_all_by_user(self, user_id):
        favorites = self.conn.execute('SELECT * FROM favorites WHERE user_id = ?', (user_id,)).fetchall()
        return [dict(row) for row in favorites]

    def add(self, user_id, url, title, snippet, date, publisher):
        try:
            self.conn.execute('''
                INSERT INTO favorites (user_id, url, title, snippet, date, publisher) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, url, title, snippet, date, publisher))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def delete(self, user_id, url):
        self.conn.execute('DELETE FROM favorites WHERE user_id = ? AND url = ?', (user_id, url))
        self.conn.commit()

class DiscussionRepository:
    """A repository for handling discussion posts and comments."""
    def __init__(self, db_connection):
        self.conn = db_connection

    def create_table(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_symbol TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        self.conn.commit()

    def add_post(self, stock_symbol, user_id, content):
        self.conn.execute('''
            INSERT INTO posts (stock_symbol, user_id, content) 
            VALUES (?, ?, ?)
        ''', (stock_symbol.strip().upper(), user_id, content))
        self.conn.commit()

    def add_comment(self, post_id, user_id, content):
        self.conn.execute('''
            INSERT INTO comments (post_id, user_id, content) 
            VALUES (?, ?, ?)
        ''', (post_id, user_id, content))
        self.conn.commit()

    def get_posts_by_symbol(self, stock_symbol):
        # Join posts with users
        posts_rows = self.conn.execute('''
            SELECT p.id, p.content, p.created_at, u.username 
            FROM posts p
            JOIN users u ON p.user_id = u.id
            WHERE p.stock_symbol = ?
            ORDER BY p.created_at DESC
        ''', (stock_symbol.strip().upper(),)).fetchall()
        
        posts = [dict(row) for row in posts_rows]
        
        # Populate comments for each post
        for post in posts:
            comments_rows = self.conn.execute('''
                SELECT c.id, c.content, c.created_at, u.username 
                FROM comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.post_id = ?
                ORDER BY c.created_at ASC
            ''', (post['id'],)).fetchall()
            post['comments'] = [dict(crow) for crow in comments_rows]
            
        return posts
