import math
import sqlite3

INITIAL_MONEY = 5000
DAILY_BONUS = 1000

dbName = "testbet.db"
conn = sqlite3.connect(dbName, check_same_thread=False)  # Allow access from multiple threads
conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key support
conn.execute("PRAGMA journal_mode = WAL")  # Enable Write-Ahead Logging for better concurrency

EVENT_PAYOUT_SUBSIDY = 1000 # A flat amount added to the total payout pool to ensure winners get a minimum payout

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
    c.execute('''CREATE TABLE IF NOT EXISTS bets
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  event_id INTEGER NOT NULL,
                  user_id INTEGER NOT NULL,
                  amount REAL NOT NULL,
                  outcome TEXT NOT NULL,
                  FOREIGN KEY(user_id) REFERENCES users(id));''')
    conn.commit()

def add_user_or_daily_bonus(username):
    c = conn.cursor()
    c.execute("SELECT id, money FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    if user:
        user_id, money = user
        c.execute("SELECT last_daily_bonus < datetime('now', '-1 day') FROM users WHERE id = ?", (user_id,))
        eligible_for_bonus = c.fetchone()[0]
        if eligible_for_bonus:
            c.execute("UPDATE users SET money = money + ?, last_daily_bonus = CURRENT_TIMESTAMP WHERE id = ?", (DAILY_BONUS, user_id))
        else:
            if money < 50:
                c.execute("UPDATE users SET money = 50 WHERE id = ?", (user_id,))
        return user_id
    else:
        return add_user(username, INITIAL_MONEY)
    conn.commit()

def add_user(username, initial_money):
    c = conn.cursor()
    c.execute("INSERT INTO users (username, money) VALUES (?, ?)", (username, initial_money))
    conn.commit()
    return c.lastrowid  # Return the ID of the newly created user

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

def place_bet(username, amount, event, outcome):
    add_user_or_daily_bonus(username)  # Ensure the user exists and apply daily bonus if applicable
    c = conn.cursor()
    result = {
        "money_bet": 0,
        "all_in": False,
    }
    with conn:
        c = conn.cursor()
        
        # 1. Fetch data 
        c.execute("SELECT money, id FROM users WHERE username = ?", (username,))
        money, user_id = c.fetchone()
        
        if amount > money:
            amount = money  # ALL IN
            result["all_in"] = True
        result["money_bet"] = amount

        print(f"User {username} (ID: {user_id}) is placing a bet of {amount} on event {event} for outcome {outcome}. Current money: {money}")
            
        # 3. Insert the bet
        c.execute(
            "INSERT INTO bets (event_id, user_id, amount, outcome) VALUES (?, ?, ?, ?)", 
            (event, user_id, amount, outcome)
        )
        c.execute("UPDATE users SET money = money - ? WHERE id = ?", (amount, user_id))
    return result

def cancel_bets(event):
    c = conn.cursor()
    with conn:
        c.execute("SELECT user_id, amount FROM bets WHERE event_id = ?", (event,))
        for row in c:
            user_id, amount = row
            c.execute("UPDATE users SET money = money + ? WHERE id = ?", (amount, user_id))
        c.execute("DELETE FROM bets WHERE event_id = ?", (event,))

def payout_bets(event, winning_outcome):
    c = conn.cursor()
    with conn:
        # 1. Calculate total amount bet and total amount bet on the winning outcome
        c.execute("SELECT SUM(amount) FROM bets WHERE event_id = ?", (event,))
        total_bet = c.fetchone()[0] or 0
        print(f"Total bet for event {event}: {total_bet}")
        
        c.execute("SELECT SUM(amount) FROM bets WHERE event_id = ? AND outcome = ?", (event, winning_outcome))
        total_winning_bet = c.fetchone()[0] or 0
        print(f"Total winning bet for event {event} on outcome {winning_outcome}: {total_winning_bet}")
        
        # 2. Calculate payout for each winner
        c.execute("SELECT user_id, amount FROM bets WHERE event_id = ? AND outcome = ?", (event, winning_outcome))
        for row in c:
            user_id, amount = row
            print(f"Calculating payout for user ID {user_id} who bet {amount} on winning outcome {winning_outcome}.")
            payout = math.ceil((amount / total_winning_bet) * (total_bet + EVENT_PAYOUT_SUBSIDY))
            print(f"User ID {user_id} had {amount / total_winning_bet} of the total winning bet.")
            print(f"User ID {user_id} will receive a payout of {payout}.")
            c.execute("UPDATE users SET money = money + ? WHERE id = ?", (payout, user_id))
        
        # 3. Clear all bets for the event
        c.execute("DELETE FROM bets WHERE event_id = ?", (event,))
        return {
            "Total": total_bet,
            "Winning": total_winning_bet,
        }
    
def events_with_bets():
    c = conn.cursor()
    c.execute("SELECT DISTINCT event_id FROM bets")
    return [row[0] for row in c.fetchall()]

create_db()