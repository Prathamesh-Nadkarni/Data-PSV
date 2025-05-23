import json
import sqlite3
from DataSourcing.ReadData import read_json_file, read_sales_csv_file, read_social_media_csv_file
import bcrypt
from datetime import datetime
import pandas as pd
import os
import sqlite3

def connection(db_path):
    """Create a connection to the SQLite database"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.join(base_dir, '..', 'Data', 'sqllite-db')

    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    db_path = os.path.join(db_dir, db_path)
    conn = sqlite3.connect(db_path)

    return conn

def create_and_populate_user_db(json_data, db_path):

    # Connect to SQLite DB (creates if doesn't exist)
    conn = connection(db_path)
    cur = conn.cursor()

    # Create tables
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            account_id TEXT PRIMARY KEY,
            user_id TEXT,
            mask TEXT,
            name TEXT,
            official_name TEXT,
            type TEXT,
            subtype TEXT,
            holder_category TEXT,
            available REAL,
            current REAL,
            "limit" REAL,
            iso_currency_code TEXT,
            unofficial_currency_code TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            user_id TEXT,
            account_id TEXT,
            account_owner TEXT,
            amount REAL,
            authorized_date TEXT,
            date TEXT,
            iso_currency_code TEXT,
            merchant_name TEXT,
            name TEXT,
            payment_channel TEXT,
            pending INTEGER,
            transaction_type TEXT,
            category_id TEXT,
            category TEXT,
            FOREIGN KEY(account_id) REFERENCES accounts(account_id),
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')

    # Insert data
    for user in json_data:
        user_id = user['user_id']
        cur.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))

        # Accounts
        for acc in user['accounts']['accounts']:
            balances = acc.get('balances', {})
            cur.execute('''
                INSERT OR IGNORE INTO accounts (
                    account_id, user_id, mask, name, official_name, type, subtype, holder_category,
                    available, current, "limit", iso_currency_code, unofficial_currency_code
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                acc['account_id'],
                user_id,
                acc.get('mask'),
                acc.get('name'),
                acc.get('official_name'),
                acc.get('type'),
                acc.get('subtype'),
                acc.get('holder_category'),
                balances.get('available'),
                balances.get('current'),
                balances.get('limit'),
                balances.get('iso_currency_code'),
                balances.get('unofficial_currency_code')
            ))

        # Transactions
        for txn in user['transactions']['transactions']:
            cur.execute('''
                INSERT OR IGNORE INTO transactions (
                    transaction_id, user_id, account_id, account_owner, amount, authorized_date, date,
                    iso_currency_code, merchant_name, name, payment_channel, pending, transaction_type,
                    category_id, category
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                txn.get('transaction_id'),
                user_id,
                txn.get('account_id'),
                txn.get('account_owner'),
                txn.get('amount'),
                txn.get('authorized_date'),
                txn.get('date'),
                txn.get('iso_currency_code'),
                txn.get('merchant_name'),
                txn.get('name'),
                txn.get('payment_channel'),
                int(txn.get('pending', False)),
                txn.get('transaction_type'),
                txn.get('category_id'),
                ', '.join(txn.get('category', [])) if txn.get('category') else None
            ))

    conn.commit()
    conn.close()




def create_and_populate_sales_db(csvData, db_path):
    conn = connection(db_path)
    cur = conn.cursor()

    # Create sales table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT,
            category TEXT,
            product_name TEXT,
            sales REAL,
            quantity INTEGER
        )
    ''')

    for row in csvData:
        cur.execute('''
            INSERT INTO sales (
                country, category, product_name, sales, quantity
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            row['Country'],
            row['Category'],
            row['Product Name'],
            float(row['Sales']),
            int(row['Quantity'])
        ))
    
    conn.commit()
    conn.close()




def create_users_db(db_path):
    """Create secure user database with necessary security fields"""
    conn = connection(db_path)
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'user', 'company')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            failed_attempts INTEGER DEFAULT 0,
            is_locked INTEGER DEFAULT 0,
            lock_until TIMESTAMP,
            mfa_secret TEXT,
            UNIQUE(username, role)
        )
    ''')
    
    # Security-related indexes
    cur.execute('CREATE INDEX IF NOT EXISTS idx_username ON users(username)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_lock_status ON users(is_locked)')
    
    conn.commit()
    conn.close()

def register_user(username, password, role):
    
    try:
        db_path = 'users_login.db'
        conn = connection(db_path)
        cur = conn.cursor()
        
        # Check for existing username+role combo
        cur.execute('''
            SELECT 1 
            FROM users 
            WHERE username = ? AND role = ?
        ''', (username, role))
        
        if cur.fetchone():
            raise ValueError(f"Username '{username}' already registered as {role}")
        
        # Insert new user
        password_bytes = password.encode('utf-8')
    
        # Generate salt and hash
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        cur.execute('''
            INSERT INTO users 
            (username, password_hash, role) 
            VALUES (?, ?, ?)
        ''', (username, password_hash, role))
        
        conn.commit()
        
    except sqlite3.IntegrityError as e:
        error_msg = str(e)
        if "UNIQUE constraint failed: users.username, users.role" in error_msg:
            raise ValueError("Username already exists with this role")
        elif "UNIQUE constraint failed: users.username" in error_msg:
            raise ValueError("Username exists with different role (old schema)")
        else:
            raise ValueError(f"Database error: {error_msg}")
    finally:
        if conn:
            conn.close()




def authenticate_user(username, password):
    """Authenticate user with bcrypt and security checks. 
    Returns user's role if authenticated, else False."""
    db_path = 'users_login.db'
    conn = connection(db_path)
    cur = conn.cursor()
    
    cur.execute('''
        SELECT user_id, password_hash, role, failed_attempts, is_locked, lock_until 
        FROM users 
        WHERE username = ?
    ''', (username,))
    
    user = cur.fetchone()
    
    if not user:
        conn.close()
        return False
    
    user_id, pw_hash, role, attempts, is_locked, lock_until = user
    
    # Check if account is locked
    if is_locked or (lock_until and datetime.now() < datetime.fromisoformat(lock_until)):
        conn.close()
        return False
        
    # Check password.
    password_bytes = password.encode('utf-8')
    stored_hash_bytes = pw_hash.encode('utf-8')
    if bcrypt.checkpw(password_bytes, stored_hash_bytes):
        # Reset failed attempts on successful login
        cur.execute('''
            UPDATE users 
            SET failed_attempts = 0, 
                last_login = CURRENT_TIMESTAMP 
            WHERE user_id = ?
        ''', (user_id,))
        conn.commit()
        conn.close()
        return role
    else:
        new_attempts = attempts + 1
        lock_status = new_attempts >= 5  # Lock after 5 attempts
        
        cur.execute('''
            UPDATE users 
            SET failed_attempts = ?,
                is_locked = ?,
                lock_until = CASE WHEN ? THEN datetime('now', '+15 minutes') ELSE NULL END
            WHERE user_id = ?
        ''', (new_attempts, lock_status, lock_status, user_id))
        conn.commit()
        conn.close()
        return False


def get_user_security_status(username):
    """Get security-related user info"""
    db_path = 'users_login.db'
    conn = connection(db_path)
    cur = conn.cursor()
    
    cur.execute('''
        SELECT username, role, created_at, last_login, failed_attempts, is_locked
        FROM users
        WHERE username = ?
    ''', (username,))
    
    return cur.fetchone()



def create_social_media_db(data, db_path='social_media.db'):
    """
    Creates SQLite database from social media CSV data
    """
    # Read CSV into DataFrame
    df = pd.DataFrame(data)
    
    # Connect to SQLite database
    conn = connection(db_path)
    
    # Write to SQLite table
    df.to_sql('usage_metrics', conn, if_exists='replace', index=False)
    
    # Create indexes for common queries
    with conn:
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_platform 
            ON usage_metrics(Platform)
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_userid 
            ON usage_metrics(UserID)
        ''')

    
    conn.close()

def createDB(dbname):
    if dbname == 'sales_data.db':
        create_and_populate_sales_db(read_sales_csv_file(), 'sales_data.db')
    if dbname == 'user_data.db':
        create_and_populate_user_db(read_json_file(), 'user_data.db')
    if dbname == 'social_media.db':
        create_social_media_db(read_social_media_csv_file(), 'social_media.db')
    if dbname == 'users_login.db':
        create_users_db('users_login.db')
    if dbname == 'createall':
        create_and_populate_sales_db(read_sales_csv_file(), 'sales_data.db')
        create_and_populate_user_db(read_json_file(), 'user_data.db')
        create_social_media_db(read_social_media_csv_file(), 'social_media.db')
        create_users_db('users_login.db')




'''
register_user("alice", "SecurePassw0rd!")

# Authenticate
if authenticate_user("alice", "SecurePassw0rd!"):
    print("Login successful")
else:
    print("Invalid credentials")

# Check security status
print(get_user_security_status("alice"))
'''