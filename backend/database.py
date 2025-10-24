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
        
        # Create social_profiles table FIRST (due to foreign key)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_profiles (
                contact_id INT AUTO_INCREMENT PRIMARY KEY,
                platform ENUM('Facebook', 'Instagram', 'LINE', 'Twitter', 'Discord', 'Other') NOT NULL,
                profile_url VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                student_id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(255) NOT NULL,
                faculty ENUM(
                    'School of Engineering',
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
                    'School of Integrated Innovative Technology'
                ) NOT NULL,
                class_year ENUM('1', '2', '3', '4', '5', '6') NOT NULL,
                phone VARCHAR(20) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                profile_photo_url VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        ''')
        
        # Create user_social_profiles junction table (many-to-many)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_social_profiles (
                user_social_id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT,
                contact_id INT,
                FOREIGN KEY (student_id) REFERENCES users(student_id) ON DELETE CASCADE,
                FOREIGN KEY (contact_id) REFERENCES social_profiles(contact_id) ON DELETE CASCADE
            )
        ''')

        # Create posts table (renamed from 'post')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                post_id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT,
                item_name VARCHAR(100) NOT NULL,
                item_status ENUM('lost', 'found', 'returned', 'claimed', 'expired') DEFAULT 'lost',
                place VARCHAR(100) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL 30 DAY),
                FOREIGN KEY (student_id) REFERENCES users(student_id) ON DELETE CASCADE
            )
        ''')

        # Create post_images table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS post_images (
                post_image_id INT AUTO_INCREMENT PRIMARY KEY,
                post_id INT,
                image_url VARCHAR(255) NOT NULL,
                image_order INT NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
            )
        ''')
        
        # Create event to automatically handle expired posts
        cursor.execute('''
            CREATE EVENT IF NOT EXISTS auto_handle_expired_posts
            ON SCHEDULE EVERY 1 DAY
            DO
            BEGIN
                -- Mark posts as expired when they pass expiration date
                UPDATE posts 
                SET item_status = 'expired' 
                WHERE expires_at < CURRENT_TIMESTAMP 
                AND item_status IN ('lost', 'found');
                
                -- Delete expired posts that are older than 60 days total
                DELETE FROM posts 
                WHERE item_status = 'expired' 
                AND expires_at < (CURRENT_TIMESTAMP - INTERVAL 30 DAY);
            END
        ''')
        
        # Enable event scheduler
        cursor.execute("SET GLOBAL event_scheduler = ON")
        
        conn.commit()
        print("✅ Database 'lost_found_system' initialized successfully!")
        print("✅ All tables created with proper relationships!")
        print("✅ Auto-expiration event enabled!")
        
    except Error as e:
        print(f"Database initialization failed: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()