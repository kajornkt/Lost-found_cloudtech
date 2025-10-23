from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
from database import init_db, get_db_connection

app = FastAPI()

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class SocialLink(BaseModel):
    type: str
    link: str

class UserSignUp(BaseModel):
    name: str
    faculty: str
    class_year: str
    phone: str
    email: str
    password: str
    confirm_password: str
    social_links: List[SocialLink] = []

class UserSignIn(BaseModel):
    email: str
    password: str

# Initialize database on startup
@app.on_event("startup")
def startup():
    init_db()

# Routes
@app.get("/")
def read_root():
    return {"message": "Lost&Found Backend is running with SQLite!"}

@app.post("/api/signup")
def signup(user: UserSignUp):
    # Check if passwords match
    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Insert new user
        cursor.execute('''
            INSERT INTO users (name, faculty, class_year, phone, email, password, social_links)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user.name,
            user.faculty, 
            user.class_year,
            user.phone,
            user.email,
            user.password,  # In production, hash this!
            json.dumps([link.dict() for link in user.social_links])
        ))
        
        conn.commit()
        user_id = cursor.lastrowid
        
        return {
            "message": "User created successfully", 
            "user": {
                "id": user_id,
                "name": user.name, 
                "email": user.email
            }
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/signin")
def signin(user: UserSignIn):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, name, email, faculty, password, social_links 
            FROM users WHERE email = ?
        ''', (user.email,))
        
        db_user = cursor.fetchone()
        
        if db_user and db_user['password'] == user.password:
            return {
                "message": "Login successful",
                "user": {
                    "id": db_user['id'],
                    "name": db_user['name'],
                    "email": db_user['email'],
                    "faculty": db_user['faculty']
                }
            }
        
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    finally:
        conn.close()

@app.get("/api/users")
def get_users():
    """Get all users (for testing)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, name, email, faculty, class_year, phone, created_at 
            FROM users
        ''')
        users = cursor.fetchall()
        return [dict(user) for user in users]
    finally:
        conn.close()

@app.get("/api/users/count")
def get_users_count():
    """Get total number of users"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) as count FROM users")
        result = cursor.fetchone()
        return {"total_users": result['count']}
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)