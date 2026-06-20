import sqlite3

dbName = "testbet.db"
def create_db():
    conn = sqlite3.connect(dbName)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  money REAL NOT NULL);''')
    conn.commit()
    c.execute('''CREATE TABLE IF NOT EXISTS bets
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  amount REAL NOT NULL,
                  outcome TEXT NOT NULL,
                  FOREIGN KEY(user_id) REFERENCES users(id));''')
    conn.close()