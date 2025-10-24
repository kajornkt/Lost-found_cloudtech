import mysql.connector
from mysql.connector import Error

def get_db():
    """Create a database connection for standard API operations."""
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
    """Initialize database and tables."""
    # Initialize conn and cursor to None to prevent UnboundLocalError 
    # if the initial connection fails. (FIXED PYTHON ERROR)
    conn = None
    cursor = None
    
    try:
        # First connect without specifying the database to create it
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conn.cursor()
        
        # Create database if not exists
        cursor.execute("CREATE DATABASE IF NOT EXISTS lost_found_system")
        cursor.execute("USE lost_found_system")
        
        # --- Create 'users' table (Must be created before 'user_social_profiles') ---
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
            ) ENGINE=InnoDB
        ''')
        
        # --- Create 'social_profiles' table (Must be created before 'user_social_profiles') ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_profiles (
                contact_id INT AUTO_INCREMENT PRIMARY KEY,
                platform ENUM('Facebook', 'Instagram', 'LINE', 'Twitter / X', 'Discord', 'Other') NOT NULL,
                profile_url VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
        ''')
        
        # --- Create 'user_social_profiles' junction table (Many-to-Many link) ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_social_profiles (
                user_social_id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                contact_id INT NOT NULL,
                -- Ensures a user can't have the same link defined twice
                UNIQUE KEY unique_user_contact (student_id, contact_id), 
                FOREIGN KEY (student_id) REFERENCES users(student_id) ON DELETE CASCADE,
                FOREIGN KEY (contact_id) REFERENCES social_profiles(contact_id) ON DELETE CASCADE
            ) ENGINE=InnoDB
        ''')

        # --- Create 'posts' table ---
        # FIXED: expires_at is now a Generated Column for reliability (MySQL 5.7+ required)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                post_id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                item_name VARCHAR(100) NOT NULL,
                item_status ENUM('lost', 'found', 'returned', 'claimed', 'expired') DEFAULT 'lost',
                place VARCHAR(100) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                -- Corrected to use GENERATED ALWAYS AS for calculation-based columns
                expires_at DATETIME GENERATED ALWAYS AS (DATE_ADD(created_at, INTERVAL 30 DAY)) STORED,
                FOREIGN KEY (student_id) REFERENCES users(student_id) ON DELETE CASCADE
            ) ENGINE=InnoDB
        ''')

        # --- Create 'post_images' table ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS post_images (
                post_image_id INT AUTO_INCREMENT PRIMARY KEY,
                post_id INT NOT NULL,
                image_url VARCHAR(255) NOT NULL,
                image_order INT NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
            ) ENGINE=InnoDB
        ''')
        
        # --- Create event to automatically handle expired posts ---
        # NOTE: This requires the MySQL Event Scheduler to be enabled on your server.
        # Check if the event scheduler is enabled.
        cursor.execute("SET GLOBAL event_scheduler = ON") 
        
        cursor.execute('''
            CREATE EVENT IF NOT EXISTS auto_handle_expired_posts
            ON SCHEDULE EVERY 1 DAY
            DO
            BEGIN
                -- 1. Mark posts as 'expired' when the expiration date has passed
                UPDATE posts 
                SET item_status = 'expired' 
                WHERE expires_at < NOW() 
                AND item_status IN ('lost', 'found');
                
                -- 2. Delete posts marked 'expired' that have been expired for an additional 30 days
                -- (This keeps expired posts visible for 30 days after the initial expiration)
                DELETE FROM posts 
                WHERE item_status = 'expired' 
                AND expires_at < (NOW() - INTERVAL 30 DAY);
            END
        ''')
        
        conn.commit()
        print("✅ Database 'lost_found_system' initialized successfully!")
        print("✅ All tables created with proper relationships!")
        print("✅ Auto-expiration event created and enabled!")
        
    except Error as e:
        print(f"Database initialization failed: {e}")
    finally:
        # Safely close cursor and connection 
        if conn and conn.is_connected():
            if cursor:
                cursor.close()
            conn.close()