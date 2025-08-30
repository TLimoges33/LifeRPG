#!/usr/bin/env python3
"""
Simple FastAPI backend for The Wizard's Grimoire demo
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from datetime import datetime, timedelta
import uuid

app = FastAPI(title="The Wizard's Grimoire API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Data models
class User(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime

class Habit(BaseModel):
    id: str
    user_id: str
    name: str
    description: str
    category: str
    target_frequency: int
    current_streak: int = 0
    total_completions: int = 0
    created_at: datetime
    updated_at: datetime

class HabitCompletion(BaseModel):
    id: str
    habit_id: str
    completed_at: datetime
    notes: Optional[str] = None

# In-memory data store
users_db = {}
habits_db = {}
completions_db = {}

# Demo data
demo_user = User(
    id="demo-user",
    email="wizard@grimoire.app",
    name="Demo Wizard",
    created_at=datetime.now()
)
users_db["demo-user"] = demo_user

demo_habits = [
    Habit(
        id="habit-1",
        user_id="demo-user",
        name="Morning Meditation",
        description="Start each day with mindful reflection",
        category="🧘‍♂️ Mindfulness",
        target_frequency=7,
        current_streak=5,
        total_completions=15,
        created_at=datetime.now() - timedelta(days=10),
        updated_at=datetime.now()
    ),
    Habit(
        id="habit-2",
        user_id="demo-user",
        name="Read Magical Texts",
        description="Study ancient wisdom for 30 minutes",
        category="📚 Learning",
        target_frequency=5,
        current_streak=3,
        total_completions=8,
        created_at=datetime.now() - timedelta(days=8),
        updated_at=datetime.now()
    ),
    Habit(
        id="habit-3",
        user_id="demo-user",
        name="Practice Spell Casting",
        description="Perfect your magical techniques",
        category="✨ Magic",
        target_frequency=3,
        current_streak=2,
        total_completions=6,
        created_at=datetime.now() - timedelta(days=5),
        updated_at=datetime.now()
    )
]

for habit in demo_habits:
    habits_db[habit.id] = habit

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Demo: accept any token or no token
    return demo_user

@app.get("/")
async def root():
    return {"message": "Welcome to The Wizard's Grimoire API"}

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/api/v1/me")
async def get_current_user_info(user: User = Depends(get_current_user)):
    return user

@app.post("/api/v1/auth/login")
async def login(credentials: dict):
    # Demo: accept any credentials
    return {
        "access_token": "demo-token",
        "token_type": "bearer",
        "user": demo_user
    }

@app.get("/api/v1/habits", response_model=List[Habit])
async def get_habits(user: User = Depends(get_current_user)):
    user_habits = [habit for habit in habits_db.values() if habit.user_id == user.id]
    return user_habits

@app.post("/api/v1/habits", response_model=Habit)
async def create_habit(habit_data: dict, user: User = Depends(get_current_user)):
    habit_id = str(uuid.uuid4())
    new_habit = Habit(
        id=habit_id,
        user_id=user.id,
        name=habit_data["name"],
        description=habit_data.get("description", ""),
        category=habit_data.get("category", "General"),
        target_frequency=habit_data.get("target_frequency", 7),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    habits_db[habit_id] = new_habit
    return new_habit

@app.post("/api/v1/habits/{habit_id}/complete")
async def complete_habit(habit_id: str, user: User = Depends(get_current_user)):
    if habit_id not in habits_db:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    habit = habits_db[habit_id]
    if habit.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Create completion record
    completion_id = str(uuid.uuid4())
    completion = HabitCompletion(
        id=completion_id,
        habit_id=habit_id,
        completed_at=datetime.now()
    )
    completions_db[completion_id] = completion
    
    # Update habit stats
    habit.total_completions += 1
    habit.current_streak += 1
    habit.updated_at = datetime.now()
    
    return {"message": "Habit completed successfully", "completion": completion}

@app.get("/api/v1/analytics/overview")
async def get_analytics_overview(user: User = Depends(get_current_user)):
    user_habits = [habit for habit in habits_db.values() if habit.user_id == user.id]
    total_completions = sum(habit.total_completions for habit in user_habits)
    avg_streak = sum(habit.current_streak for habit in user_habits) / len(user_habits) if user_habits else 0
    
    return {
        "total_habits": len(user_habits),
        "total_completions": total_completions,
        "average_streak": round(avg_streak, 1),
        "active_streaks": len([h for h in user_habits if h.current_streak > 0])
    }

@app.get("/api/v1/analytics/progress")
async def get_progress_data(user: User = Depends(get_current_user)):
    # Generate mock progress data for the last 30 days
    days = []
    for i in range(30):
        date = datetime.now() - timedelta(days=29-i)
        days.append({
            "date": date.strftime("%Y-%m-%d"),
            "completions": max(0, 3 + (i % 7) - 2)  # Mock varying completions
        })
    return {"progress": days}

@app.get("/api/v1/analytics/categories")
async def get_category_data(user: User = Depends(get_current_user)):
    user_habits = [habit for habit in habits_db.values() if habit.user_id == user.id]
    categories = {}
    for habit in user_habits:
        category = habit.category
        if category not in categories:
            categories[category] = 0
        categories[category] += habit.total_completions
    
    return {"categories": [{"name": k, "value": v} for k, v in categories.items()]}

@app.get("/api/v1/social/friends")
async def get_friends(user: User = Depends(get_current_user)):
    # Mock friends data
    return {
        "friends": [
            {"id": "friend-1", "name": "Merlin the Wise", "level": 12, "avatar": "🧙‍♂️"},
            {"id": "friend-2", "name": "Luna Spellweaver", "level": 8, "avatar": "🧙‍♀️"},
            {"id": "friend-3", "name": "Gandalf Grey", "level": 15, "avatar": "🧙"}
        ]
    }

@app.get("/api/v1/social/leaderboard")
async def get_leaderboard(user: User = Depends(get_current_user)):
    # Mock leaderboard data
    return {
        "leaderboard": [
            {"rank": 1, "name": "Gandalf Grey", "score": 1250, "avatar": "🧙"},
            {"rank": 2, "name": "Merlin the Wise", "score": 980, "avatar": "🧙‍♂️"},
            {"rank": 3, "name": "Demo Wizard", "score": 750, "avatar": "🧙‍♂️"},
            {"rank": 4, "name": "Luna Spellweaver", "score": 650, "avatar": "🧙‍♀️"}
        ]
    }

@app.get("/api/v1/user/notification-settings")
async def get_notification_settings(user: User = Depends(get_current_user)):
    return {
        "dailyReminders": True,
        "reminderTime": "09:00",
        "weeklyReports": True,
        "achievementAlerts": True,
        "friendActivity": True,
        "pushNotifications": False,
        "emailNotifications": True
    }

@app.put("/api/v1/user/notification-settings")
async def update_notification_settings(settings: dict, user: User = Depends(get_current_user)):
    # In a real app, save to database
    return settings

@app.get("/api/v1/user/performance-settings")
async def get_performance_settings(user: User = Depends(get_current_user)):
    return {
        "imageCompression": True,
        "lazyLoading": True,
        "caching": True,
        "preloading": True,
        "offlineMode": False
    }

@app.put("/api/v1/user/performance-settings")
async def update_performance_settings(settings: dict, user: User = Depends(get_current_user)):
    # In a real app, save to database
    return settings

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
