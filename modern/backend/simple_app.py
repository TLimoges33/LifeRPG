from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import json
import models
import gamification
import analytics
import telemetry

# Initialize database
models.init_db()

# Create FastAPI app
app = FastAPI(title="The Wizard's Grimoire API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple dependency to get database session
def get_db() -> Session:
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Mock user for demo (in real app this would come from authentication)
mock_user = {
    "id": 1,
    "email": "wizard@grimoire.com",
    "display_name": "Master Wizard",
    "role": "admin"
}

# Health check
@app.get("/health")
def health_check():
    return {"status": "The magical energies are flowing strong! ✨"}

# Authentication endpoints
@app.post("/api/v1/register")
def register(email: str = Body(...), password: str = Body(...), db: Session = Depends(get_db)):
    # Create user in database (simplified for demo)
    user = models.User(email=email, display_name=email.split('@')[0])
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": "user"
        },
        "token": "demo_token_12345"
    }

@app.post("/api/v1/login")
def login(email: str = Body(...), password: str = Body(...)):
    return {
        "user": mock_user,
        "token": "demo_token_12345"
    }

@app.get("/api/v1/me")
def get_current_user():
    return mock_user

# Habits endpoints
@app.get("/api/v1/habits")
def get_habits(db: Session = Depends(get_db)):
    habits = db.query(models.Habit).filter(models.Habit.user_id == mock_user["id"]).all()
    return [
        {
            "id": habit.id,
            "title": habit.title,
            "notes": habit.notes,
            "cadence": habit.cadence,
            "difficulty": habit.difficulty,
            "xp_reward": habit.xp_reward,
            "status": habit.status,
            "created_at": habit.created_at.isoformat() if habit.created_at else None
        }
        for habit in habits
    ]

@app.post("/api/v1/habits")
def create_habit(
    title: str = Body(...),
    notes: str = Body(""),
    cadence: str = Body("daily"),
    difficulty: int = Body(1),
    xp_reward: int = Body(10),
    db: Session = Depends(get_db)
):
    habit = models.Habit(
        user_id=mock_user["id"],
        title=title,
        notes=notes,
        cadence=cadence,
        difficulty=difficulty,
        xp_reward=xp_reward
    )
    db.add(habit)
    db.commit()
    db.refresh(habit)
    
    # Check for achievements
    achievements = gamification.check_achievements(db, mock_user["id"])
    
    return {
        "habit": {
            "id": habit.id,
            "title": habit.title,
            "notes": habit.notes,
            "cadence": habit.cadence,
            "difficulty": habit.difficulty,
            "xp_reward": habit.xp_reward,
            "status": habit.status,
            "created_at": habit.created_at.isoformat() if habit.created_at else None
        },
        "achievements": achievements
    }

@app.post("/api/v1/habits/{habit_id}/complete")
def complete_habit(habit_id: int, db: Session = Depends(get_db)):
    habit = db.query(models.Habit).filter(models.Habit.id == habit_id).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Spell not found in grimoire")
    
    # Create completion log
    log = models.HabitLog(
        habit_id=habit_id,
        user_id=mock_user["id"],
        notes="Spell cast successfully! ✨"
    )
    db.add(log)
    
    # Award XP
    gamification.award_xp(db, mock_user["id"], habit.xp_reward)
    
    # Track telemetry
    telemetry.track_habit_completion(db, mock_user["id"], habit_id)
    
    db.commit()
    
    # Check for achievements
    achievements = gamification.check_achievements(db, mock_user["id"])
    
    return {
        "message": "Spell cast successfully! Mystical energy gathered.",
        "xp_awarded": habit.xp_reward,
        "achievements": achievements
    }

@app.delete("/api/v1/habits/{habit_id}")
def delete_habit(habit_id: int, db: Session = Depends(get_db)):
    habit = db.query(models.Habit).filter(models.Habit.id == habit_id).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Spell not found in grimoire")
    
    db.delete(habit)
    db.commit()
    
    return {"message": "Spell removed from grimoire"}

# Gamification endpoints
@app.get("/api/v1/gamification/stats")
def get_gamification_stats(db: Session = Depends(get_db)):
    return gamification.get_user_stats(db, mock_user["id"])

@app.get("/api/v1/gamification/achievements")
def get_achievements(db: Session = Depends(get_db)):
    return gamification.get_user_achievements(db, mock_user["id"])

@app.get("/api/v1/gamification/leaderboard")
def get_leaderboard(db: Session = Depends(get_db)):
    return gamification.get_leaderboard(db)

# Analytics endpoints
@app.get("/api/v1/analytics/overview")
def get_analytics_overview(db: Session = Depends(get_db)):
    return analytics.get_user_analytics(db, mock_user["id"])

@app.get("/api/v1/analytics/habits/heatmap")
def get_habits_heatmap(db: Session = Depends(get_db)):
    return analytics.get_habits_heatmap(db, mock_user["id"])

@app.get("/api/v1/analytics/habits/trends")
def get_habits_trends(db: Session = Depends(get_db)):
    return analytics.get_habits_trends(db, mock_user["id"])

@app.get("/api/v1/analytics/streaks")
def get_streaks(db: Session = Depends(get_db)):
    return analytics.get_streak_data(db, mock_user["id"])

# Telemetry endpoints
@app.get("/api/v1/telemetry/consent")
def get_telemetry_consent():
    return {"consent": True}

@app.post("/api/v1/telemetry/consent")
def set_telemetry_consent(consent: bool = Body(...)):
    return {"consent": consent, "message": "Scrying preferences updated"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
