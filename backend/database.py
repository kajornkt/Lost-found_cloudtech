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
                student_id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(255) NOT NULL,
                faculty ENUM('School of Engineering',
                       'School of Architecture, Art, and Design',
                       'School of Industrial Education and Technology',
                       'School of Agricultural Technology',
                       'School of Science',
                       'School of Food Industry',
                       'School of Information Technology',
                       'International College',
                       'College of Materials Innovation and Technology',
                       'College of Advanced Manufacturing Innovation',
                       'KMITL Business School',
                       'International Academy of Aviation Industry',
                       'School of Liberal Arts',
                       'Faculty of Medicine',
                       'College of Innovation and Industrial Management',
                       'Institute of Music Science and Engineering',
                       'School of Dentistry',
                       'School of Nursing Science',
                       'School of Integrated Innovative Technology') NOT NULL,
                class_year ENUM('1', '2', '3', '4', '5', '6') NOT NULL,
                phone VARCHAR(20) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                profile_photo_url VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')
        
        # Create social_profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_profiles (
                contact_id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT,
                platform VARCHAR(100) ENUM('Facebook', 'Twitter / X', 'Instagram', 'Line', 'Discord')) NOT NULL,
                profile_url VARCHAR(255) NOT NULL,
                FOREIGN KEY (student_id) REFERENCES users(student_id)
            )
        ''')

        # Create post table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS post (
                post_id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT,
                item_name VARCHAR(50) NOT NULL,
                item_status ENUM('lost', 'found') DEFAULT 'lost',
                place VARCHAR(100) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                expires_at DATE 
                    GENERATED ALWAYS AS (DATE_ADD(created_at, INTERVAL 30 DAY)) STORED,
                FOREIGN KEY (student_id) REFERENCES users(student_id)
            )
        ''')

        # Create post_images table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS post_images (
                post_image_id INT AUTO_INCREMENT PRIMARY KEY,
                post_id INT,
                image_url VARCHAR(255) NOT NULL,
                image_order INT NOT NULL,
                FOREIGN KEY (post_id) REFERENCES post(post_id) # <-- This Foreign Key must reference the 'post' table
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