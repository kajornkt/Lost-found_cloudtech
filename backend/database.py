import mysql.connector
from mysql.connector import Error

def get_db():
    """Create database connection"""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # Empty for XAMPP
            database="lost_found_system"
        )
        return connection
    except Error as e:
        print(f"Database connection failed: {e}")
        return None

def init_database():
    """Initialize database and tables"""
    try:
        # First connect without database to create it
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conn.cursor()
        
        # Create database if not exists
        cursor.execute("CREATE DATABASE IF NOT EXISTS lost_found_system")
        cursor.execute("USE lost_found_system")
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(255) NOT NULL,
                faculty VARCHAR(255) NOT NULL,
                class_year VARCHAR(10) NOT NULL,
                phone VARCHAR(20) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                social_profiles TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("✅ Database 'lost_found_system' initialized successfully!")
        
    except Error as e:
        print(f"Database initialization failed: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()