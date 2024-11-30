import sqlite3
import logging


logging.basicConfig(level=logging.INFO)

def init_db():
    conn = sqlite3.connect('app_db.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 0,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            is_registered INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quadcopters (
            id INTEGER PRIMARY KEY,
            name TEXT,
            price REAL,
            flight_time INTEGER,
            range INTEGER,
            camera_quality TEXT,
            portability TEXT,
            description TEXT
        )
    ''')
    conn.commit()
    conn.close()
    # populate_quadcopters()

def add_user(user_id, username):
    conn = sqlite3.connect('app_db.db')
    try:
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
        conn.commit()
        logging.info(f"Added user {username} with ID {user_id} to the database.")
    except Exception as e:
        logging.error(f"Error adding user {user_id}: {e}")
    finally:
        conn.close()

def get_user_balance(user_id):
    conn = sqlite3.connect('app_db.db')
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 0
    except Exception as e:
        logging.error(f"Error getting balance for user {user_id}: {e}")
        return 0
    finally:
        conn.close()

def update_user_balance(user_id, amount):
    conn = sqlite3.connect('app_db.db')
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        conn.commit()
    except Exception as e:
        logging.error(f"Error updating balance for user {user_id}: {e}")
    finally:
        conn.close()

def complete_registration(user_id, full_name, email, phone):
    conn = sqlite3.connect('app_db.db')
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET full_name = ?, email = ?, phone = ?, is_registered = 1 
            WHERE user_id = ?
        ''', (full_name, email, phone, user_id))
        conn.commit()
        logging.info(f"Completed registration for user ID {user_id} with name {full_name}.")
    except Exception as e:
        logging.error(f"Error completing registration for user {user_id}: {e}")
    finally:
        conn.close()

def is_user_registered(user_id):
    conn = sqlite3.connect('app_db.db')
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT is_registered FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] == 1 if result else False
    except Exception as e:
        logging.error(f"Error checking registration for user {user_id}: {e}")
        return False
    finally:
        conn.close()
def get_quadcopters(budget, flight_time, range_):
    conn = sqlite3.connect('app_db.db')
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM quadcopters
            WHERE price <= ? AND flight_time >= ? AND range >= ?
        ''', (budget, flight_time, range_))
        quadcopters = cursor.fetchall()
        return quadcopters
    except Exception as e:
        logging.error(f"Error getting quadcopters: {e}")
        return []
    finally:
        conn.close()
