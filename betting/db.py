import sqlite3

INITIAL_MONEY = 5000
DAILY_BONUS = 1000

dbName = "testbet.db"
conn = sqlite3.connect(dbName, check_same_thread=False)  # Allow access from multiple threads

def create_db():
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  money REAL NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  last_daily_bonus TIMESTAMP DEFAULT CURRENT_TIMESTAMP
              );''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_username ON users(username);")
    conn.commit()
    c.execute('''CREATE TABLE IF NOT EXISTS events
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    final_outcome TEXT
              );''')
    c.execute('''CREATE TABLE IF NOT EXISTS bets
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  event_id INTEGER NOT NULL,
                  user_id INTEGER NOT NULL,
                  amount REAL NOT NULL,
                  outcome TEXT NOT NULL,
                  FOREIGN KEY(event_id) REFERENCES events(id),
                  FOREIGN KEY(user_id) REFERENCES users(id));''')
    conn.commit()

def add_user_or_daily_bonus(username):
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    if user:
        user_id = user[0]
        c.execute("SELECT (last_daily_bonus < datetime('now', '-1 day')) FROM users WHERE id = ?", (user_id,))
        eligible_for_bonus = c.fetchone()[0]
        if eligible_for_bonus:
            c.execute("UPDATE users SET money = money + ?, last_daily_bonus = CURRENT_TIMESTAMP WHERE id = ?", (DAILY_BONUS, user_id))
    else:
        add_user(username, INITIAL_MONEY)
    conn.commit()

def add_user(username, initial_money):
    c = conn.cursor()
    c.execute("INSERT INTO users (username, money) VALUES (?, ?)", (username, initial_money))
    conn.commit()

def get_user_money(username):
    add_user_or_daily_bonus(username)  # Ensure the user exists and apply daily bonus if applicable
    print(f"Getting money for user: {username}")
    c = conn.cursor()
    c.execute("SELECT money FROM users WHERE username = ?", (username,))
    money = c.fetchone()
    return money[0] if money else None

def add_money(username, amount):
    add_user_or_daily_bonus(username)  # Ensure the user exists and apply daily bonus if applicable
    c = conn.cursor()
    c.execute("UPDATE users SET money = money + ? WHERE username = ?", (amount, username))
    conn.commit()

create_db()