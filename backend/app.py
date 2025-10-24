from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import mysql.connector
import json

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
    url: str

class UserCreate(BaseModel):
    full_name: str
    faculty: str
    class_year: str
    phone: str
    email: str
    password: str
    confirm_password: str
    social_profiles: List[SocialLink] = []

class UserLogin(BaseModel):
    email: str
    password: str

# Initialize database on startup
@app.on_event("startup")
def startup():
    init_database()

# API Routes
@app.get("/")
def api_status():
    return {"status": "active", "service": "Lost&Found API", "database": "MySQL"}

@app.post("/auth/register")
async def register_user(user: UserCreate):
    # Validate passwords match
    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Password confirmation does not match")
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email address already registered")
        
        # Create new user
        cursor.execute('''
            INSERT INTO users (full_name, faculty, class_year, phone, email, password, social_profiles)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (
            user.full_name,
            user.faculty,
            user.class_year,
            user.phone,
            user.email,
            user.password,  # In production, hash this!
            json.dumps([profile.dict() for profile in user.social_profiles])
        ))
        
        db.commit()
        return {"success": True, "message": "Account created successfully", "user_email": user.email}
        
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
            SELECT id, full_name, email, faculty, password 
            FROM users WHERE email = %s
        ''', (credentials.email,))
        
        user = cursor.fetchone()
        
        if user and user['password'] == credentials.password:
            return {
                "success": True,
                "message": "Login successful",
                "user_data": {
                    "user_id": user['id'],
                    "name": user['full_name'],
                    "email": user['email'],
                    "faculty": user['faculty']
                }
            }
        
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    finally:
        cursor.close()
        db.close()

@app.get("/users")
async def get_all_users():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id, full_name, email, faculty, class_year FROM users")
        users = cursor.fetchall()
        return {"users": users, "count": len(users)}
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)