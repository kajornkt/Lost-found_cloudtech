import sqlite3
import json

def init_db():
    conn = sqlite3.connect('lost_found.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            faculty TEXT NOT NULL,
            class_year TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            social_links TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

def get_db_connection():
    conn = sqlite3.connect('lost_found.db')
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn