from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import mysql.connector
import json
import os
from datetime import datetime, timedelta
import uuid

# Initialize app
app = FastAPI(title="Lost&Found API")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import database functions
from database import get_db, init_database

# Data models
class SocialLink(BaseModel):
    platform: str
    profile_url: str

class UserCreate(BaseModel):
    full_name: str
    faculty: str
    class_year: str
    phone: str
    email: str
    password: str
    confirm_password: str
    social_profiles: List[SocialLink] = []
    profile_photo_url: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    faculty: Optional[str] = None
    class_year: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    social_profiles: Optional[List[SocialLink]] = None
    profile_photo_url: Optional[str] = None

class PostCreate(BaseModel):
    item_name: str
    description: str
    item_status: str  # 'lost' or 'found'
    place: str
    images: List[str] = []

class PostUpdate(BaseModel):
    item_name: Optional[str] = None
    description: Optional[str] = None
    item_status: Optional[str] = None  # 'lost', 'found', 'returned', 'claimed', 'expired'
    place: Optional[str] = None
    images: Optional[List[str]] = None

# Initialize database on startup
@app.on_event("startup")
def startup():
    init_database()
    check_and_update_expired_posts()

# Create uploads directory
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

def check_and_update_expired_posts():
    """Check for expired posts and update their status"""
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('''
            UPDATE posts 
            SET item_status = 'expired' 
            WHERE expires_at < CURRENT_TIMESTAMP 
            AND item_status IN ('lost', 'found')
        ''')
        
        db.commit()
        expired_count = cursor.rowcount
        if expired_count > 0:
            print(f"✅ Marked {expired_count} posts as expired")
            
    except mysql.connector.Error as err:
        print(f"Error updating expired posts: {err}")
    finally:
        cursor.close()
        db.close()

# ========== AUTHENTICATION ROUTES ==========
@app.get("/")
def api_status():
    return {"status": "active", "service": "Lost&Found API", "database": "MySQL"}

@app.post("/auth/register")
async def register_user(user: UserCreate):
    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Password confirmation does not match")
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Check if email already exists
        cursor.execute("SELECT student_id FROM users WHERE email = %s", (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email address already registered")
        
        # Insert user
        cursor.execute('''
            INSERT INTO users (full_name, faculty, class_year, phone, email, password, profile_photo_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (
            user.full_name,
            user.faculty,
            user.class_year,
            user.phone,
            user.email,
            user.password,
            user.profile_photo_url
        ))
        
        student_id = cursor.lastrowid
        
        # Insert social profiles if any
        if user.social_profiles:
            for social in user.social_profiles:
                # Insert into social_profiles table
                cursor.execute('''
                    INSERT INTO social_profiles (platform, profile_url)
                    VALUES (%s, %s)
                ''', (social.platform, social.profile_url))
                
                contact_id = cursor.lastrowid
                
                # Link to user in junction table
                cursor.execute('''
                    INSERT INTO user_social_profiles (student_id, contact_id)
                    VALUES (%s, %s)
                ''', (student_id, contact_id))
        
        db.commit()
        
        return {
            "success": True, 
            "message": "Account created successfully", 
            "student_id": student_id,
            "user_email": user.email
        }
        
    except mysql.connector.Error as err:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        db.close()

@app.post("/auth/login")
async def login_user(credentials: UserLogin):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('''
            SELECT student_id, full_name, email, faculty, class_year, phone, profile_photo_url
            FROM users WHERE email = %s AND password = %s
        ''', (credentials.email, credentials.password))
        
        user = cursor.fetchone()
        
        if user:
            # Get social profiles
            cursor.execute('''
                SELECT sp.platform, sp.profile_url
                FROM social_profiles sp
                JOIN user_social_profiles usp ON sp.contact_id = usp.contact_id
                WHERE usp.student_id = %s
            ''', (user['student_id'],))
            
            social_profiles = cursor.fetchall()
            
            return {
                "success": True,
                "message": "Login successful",
                "user_data": {
                    "student_id": user['student_id'],
                    "name": user['full_name'],
                    "email": user['email'],
                    "faculty": user['faculty'],
                    "class_year": user['class_year'],
                    "phone": user['phone'],
                    "profile_photo_url": user['profile_photo_url'],
                    "social_profiles": social_profiles
                }
            }
        
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    finally:
        cursor.close()
        db.close()

# ========== PROFILE ROUTES ==========
@app.get("/users/{student_id}")
async def get_user_profile(student_id: int):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('''
            SELECT student_id, full_name, email, faculty, class_year, phone, profile_photo_url
            FROM users WHERE student_id = %s
        ''', (student_id,))
        
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get social profiles
        cursor.execute('''
            SELECT sp.platform, sp.profile_url
            FROM social_profiles sp
            JOIN user_social_profiles usp ON sp.contact_id = usp.contact_id
            WHERE usp.student_id = %s
        ''', (student_id,))
        
        user['social_profiles'] = cursor.fetchall()
        
        return user
        
    finally:
        cursor.close()
        db.close()

# ========== POSTS ROUTES ==========
@app.post("/posts")
async def create_post(post: PostCreate, student_id: int = Form(...)):
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Calculate expiration date (30 days from now)
        expires_at = datetime.now() + timedelta(days=30)
        
        # Insert post
        cursor.execute('''
            INSERT INTO posts (student_id, item_name, description, item_status, place, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            student_id,
            post.item_name,
            post.description,
            post.item_status,
            post.place,
            expires_at
        ))
        
        post_id = cursor.lastrowid
        
        # Insert images if any
        if post.images:
            for order, image_url in enumerate(post.images):
                cursor.execute('''
                    INSERT INTO post_images (post_id, image_url, image_order)
                    VALUES (%s, %s, %s)
                ''', (post_id, image_url, order))
        
        db.commit()
        
        return {
            "success": True, 
            "message": "Post created successfully",
            "post_id": post_id,
            "expires_at": expires_at.isoformat()
        }
        
    except mysql.connector.Error as err:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        db.close()

@app.get("/posts/user/{student_id}")
async def get_user_posts(student_id: int):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('''
            SELECT p.*, u.full_name, u.phone, u.email, u.profile_photo_url
            FROM posts p 
            JOIN users u ON p.student_id = u.student_id 
            WHERE p.student_id = %s
            ORDER BY 
                CASE 
                    WHEN p.item_status IN ('lost', 'found') AND p.expires_at > CURRENT_TIMESTAMP THEN 1
                    ELSE 2
                END,
                p.created_at DESC
        ''', (student_id,))
        
        posts = cursor.fetchall()
        
        # Get images for each post
        for post in posts:
            cursor.execute('''
                SELECT image_url, image_order
                FROM post_images 
                WHERE post_id = %s 
                ORDER BY image_order
            ''', (post['post_id'],))
            
            post['images'] = [img['image_url'] for img in cursor.fetchall()]
            
            # Add expiration info
            if post['item_status'] in ['lost', 'found'] and post['expires_at']:
                expires_date = post['expires_at']
                if isinstance(expires_date, str):
                    expires_date = datetime.fromisoformat(expires_date.replace('Z', '+00:00'))
                days_left = (expires_date - datetime.now()).days
                post['days_until_expiration'] = max(0, days_left)
                post['is_expiring_soon'] = days_left <= 7
        
        return {"posts": posts}
        
    finally:
        cursor.close()
        db.close()

@app.get("/posts/{post_id}")
async def get_post_details(post_id: int):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute('''
            SELECT p.*, u.full_name, u.phone, u.email, u.faculty, u.profile_photo_url
            FROM posts p 
            JOIN users u ON p.student_id = u.student_id 
            WHERE p.post_id = %s
        ''', (post_id,))
        
        post = cursor.fetchone()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Get images
        cursor.execute('''
            SELECT image_url, image_order
            FROM post_images 
            WHERE post_id = %s 
            ORDER BY image_order
        ''', (post_id,))
        
        post['images'] = [img['image_url'] for img in cursor.fetchall()]
        
        # Get social profiles
        cursor.execute('''
            SELECT sp.platform, sp.profile_url
            FROM social_profiles sp
            JOIN user_social_profiles usp ON sp.contact_id = usp.contact_id
            WHERE usp.student_id = %s
        ''', (post['student_id'],))
        
        post['social_profiles'] = cursor.fetchall()
        
        return post
        
    finally:
        cursor.close()
        db.close()

# ========== FILE UPLOAD ROUTE ==========
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Generate unique filename
        file_extension = file.filename.split('.')[-1]
        filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = f"uploads/{filename}"
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "success": True,
            "filename": filename,
            "url": f"/uploads/{filename}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

# ========== PUBLIC POSTS ROUTES ==========
@app.get("/posts")
async def get_all_posts(item_status: Optional[str] = None, search: Optional[str] = None):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        query = '''
            SELECT p.*, u.full_name, u.faculty, u.profile_photo_url
            FROM posts p 
            JOIN users u ON p.student_id = u.student_id 
            WHERE p.item_status IN ('lost', 'found')
            AND p.expires_at > CURRENT_TIMESTAMP
        '''
        params = []
        
        if item_status:
            query += " AND p.item_status = %s"
            params.append(item_status)
        
        if search:
            query += " AND (p.item_name LIKE %s OR p.description LIKE %s OR u.full_name LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        
        query += " ORDER BY p.created_at DESC"
        
        cursor.execute(query, params)
        posts = cursor.fetchall()
        
        # Get images for each post
        for post in posts:
            cursor.execute('''
                SELECT image_url, image_order
                FROM post_images 
                WHERE post_id = %s 
                ORDER BY image_order
            ''', (post['post_id'],))
            
            post['images'] = [img['image_url'] for img in cursor.fetchall()]
        
        return {"posts": posts}
        
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)