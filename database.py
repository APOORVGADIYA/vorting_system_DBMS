import sqlite3
from werkzeug.security import generate_password_hash

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Create users table (already in 3NF)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create elections table (3NF)
    c.execute('''
        CREATE TABLE IF NOT EXISTS elections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            election_type TEXT NOT NULL,
            created_by INTEGER,
            election_date DATE NOT NULL,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Create parties table (3NF)
    c.execute('''
        CREATE TABLE IF NOT EXISTS parties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            tagline TEXT
        )
    ''')
    
    # Create candidates table (3NF)
    c.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id INTEGER,
            party_id INTEGER,
            name TEXT NOT NULL,
            UNIQUE(election_id, name),
            FOREIGN KEY (election_id) REFERENCES elections (id),
            FOREIGN KEY (party_id) REFERENCES parties (id)
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()