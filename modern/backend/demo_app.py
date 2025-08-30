from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import json
import models
import gamification
import analytics
import telemetry
import plugins

# Initialize database
models.init_db()

# Create FastAPI app
app = FastAPI(title="LifeRPG API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize plugin system
plugins.setup_plugin_system(app)

# Simple dependency to get database session
def get_db():
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Simple auth dependency (for demo purposes)
def get_current_user(db: Session = Depends(get_db)):
    # For demo, return a hardcoded user - replace with real auth
    user = db.query(models.User).first()
    if not user:
        # Create a demo user
        user = models.User(
            email="demo@liferpg.com",
            display_name="Demo User",
            role="admin"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def require_admin(user=Depends(get_current_user)):
    if user.role != 'admin':
        raise HTTPException(status_code=403, detail='Admin access required')
    return user

# Auth endpoints (simplified for demo)
@app.post('/api/v1/auth/register')
@app.post('/api/v1/auth/login')
def auth_demo(payload: dict = Body(...)):
    return {
        "token": "demo-token",
        "user": {
            "id": 1,
            "email": payload.get("email", "demo@liferpg.com"),
            "display_name": payload.get("email", "demo@liferpg.com").split("@")[0],
            "role": "admin"
        }
    }

@app.get('/api/v1/me')
def get_me(user=Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role
    }

# Habits endpoints
@app.get('/api/v1/habits')
def list_habits(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """List all habits for the current user."""
    habits = db.query(models.Habit).filter(models.Habit.user_id == user.id).all()
    
    return [{
        'id': habit.id,
        'project_id': habit.project_id,
        'title': habit.title,
        'notes': habit.notes,
        'cadence': habit.cadence,
        'difficulty': habit.difficulty,
        'xp_reward': habit.xp_reward,
        'status': habit.status,
        'due_date': habit.due_date.isoformat() if habit.due_date else None,
        'labels': json.loads(habit.labels) if habit.labels else [],
        'created_at': habit.created_at.isoformat() if habit.created_at else None
    } for habit in habits]

@app.post('/api/v1/habits')
def create_habit(payload: dict = Body(...), user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new habit."""
    
    habit = models.Habit(
        user_id=user.id,
        project_id=payload.get('project_id'),
        title=payload.get('title', '').strip(),
        notes=payload.get('notes', '').strip(),
        cadence=payload.get('cadence', 'daily'),
        difficulty=payload.get('difficulty', 1),
        xp_reward=payload.get('xp_reward', 10),
        status=payload.get('status', 'active'),
        labels=json.dumps(payload.get('labels', []))
    )
    
    if not habit.title:
        raise HTTPException(status_code=400, detail='title is required')
    
    db.add(habit)
    db.flush()  # Get the ID
    
    # Check for achievements
    achievements = gamification.check_habit_achievements(db, user.id)
    
    # Record telemetry for habit creation
    telemetry.record_habit_created(db, user.id, habit.difficulty, habit.cadence)
    
    db.commit()
    
    return {
        'id': habit.id,
        'title': habit.title,
        'achievements': achievements
    }

@app.get('/api/v1/habits/{habit_id}')
def get_habit(habit_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get a specific habit."""
    habit = db.query(models.Habit).filter(
        models.Habit.id == habit_id,
        models.Habit.user_id == user.id
    ).first()
    
    if not habit:
        raise HTTPException(status_code=404, detail='Habit not found')
    
    return {
        'id': habit.id,
        'project_id': habit.project_id,
        'title': habit.title,
        'notes': habit.notes,
        'cadence': habit.cadence,
        'difficulty': habit.difficulty,
        'xp_reward': habit.xp_reward,
        'status': habit.status,
        'due_date': habit.due_date.isoformat() if habit.due_date else None,
        'labels': json.loads(habit.labels) if habit.labels else [],
        'created_at': habit.created_at.isoformat() if habit.created_at else None
    }

@app.put('/api/v1/habits/{habit_id}')
def update_habit(habit_id: int, payload: dict = Body(...), user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Update a habit."""
    habit = db.query(models.Habit).filter(
        models.Habit.id == habit_id,
        models.Habit.user_id == user.id
    ).first()
    
    if not habit:
        raise HTTPException(status_code=404, detail='Habit not found')
    
    # Update fields
    if 'title' in payload:
        habit.title = payload['title'].strip()
    if 'notes' in payload:
        habit.notes = payload['notes'].strip()
    if 'cadence' in payload:
        habit.cadence = payload['cadence']
    if 'difficulty' in payload:
        habit.difficulty = payload['difficulty']
    if 'xp_reward' in payload:
        habit.xp_reward = payload['xp_reward']
    if 'status' in payload:
        habit.status = payload['status']
    if 'labels' in payload:
        habit.labels = json.dumps(payload['labels'])
    
    db.commit()
    
    return {'id': habit.id, 'title': habit.title}

@app.delete('/api/v1/habits/{habit_id}')
def delete_habit(habit_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a habit."""
    habit = db.query(models.Habit).filter(
        models.Habit.id == habit_id,
        models.Habit.user_id == user.id
    ).first()
    
    if not habit:
        raise HTTPException(status_code=404, detail='Habit not found')
    
    db.delete(habit)
    db.commit()
    
    return {'message': 'Habit deleted successfully'}

@app.post('/api/v1/habits/{habit_id}/complete')
def complete_habit(habit_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Mark a habit as completed and process gamification."""
    
    habit = db.query(models.Habit).filter(
        models.Habit.id == habit_id,
        models.Habit.user_id == user.id
    ).first()
    
    if not habit:
        raise HTTPException(status_code=404, detail='Habit not found')
    
    # Create completion log
    log = models.Log(
        habit_id=habit_id,
        user_id=user.id,
        action='complete'
    )
    db.add(log)
    
    # Process gamification
    result = gamification.process_habit_completion(db, user.id, habit_id)
    
    # Record telemetry
    telemetry.record_habit_completion(db, user.id, habit.difficulty, result.get('xp_awarded', 0))
    
    # Record achievement telemetry if any were earned
    for achievement in result.get('new_achievements', []):
        telemetry.record_achievement_earned(db, user.id, achievement['name'], achievement.get('xp_reward', 0))
    
    # Record level up telemetry if applicable
    if result.get('level_up'):
        telemetry.record_level_up(db, user.id, result['old_level'], result['new_level'])
    
    db.commit()
    
    return result

# Gamification endpoints
@app.get('/api/v1/gamification/stats')
def get_gamification_stats(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's gamification stats including XP, level, achievements, and streaks."""
    return gamification.get_user_stats(db, user.id)

@app.get('/api/v1/gamification/achievements')
def get_achievements(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all achievements with earned status."""
    
    # Get user's earned achievements
    earned_achievements = db.query(models.Achievement).filter(models.Achievement.user_id == user.id).all()
    earned_dict = {achievement.name: achievement for achievement in earned_achievements}
    
    achievements = []
    for key, definition in gamification.ACHIEVEMENT_DEFINITIONS.items():
        achievement = {
            'key': key,
            'definition': definition,
            'earned': key in earned_dict,
            'earned_at': earned_dict[key].earned_at.isoformat() if key in earned_dict and earned_dict[key].earned_at else None
        }
        achievements.append(achievement)
    
    return achievements

@app.get('/api/v1/gamification/leaderboard')
def get_leaderboard(limit: int = 10, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get the XP leaderboard."""
    
    # Get top users by XP
    xp_profiles = db.query(models.Profile).filter(models.Profile.key == "total_xp").all()
    
    leaderboard = []
    for i, profile in enumerate(sorted(xp_profiles, key=lambda x: int(x.value or 0), reverse=True)[:limit]):
        total_xp = int(profile.value or 0)
        level = gamification.calculate_level_from_xp(total_xp)
        
        # Get user display name (anonymous option)
        user_obj = db.query(models.User).filter(models.User.id == profile.user_id).first()
        display_name = user_obj.display_name if user_obj and user_obj.display_name else f"Player {user_obj.id}" if user_obj else "Anonymous"
        
        leaderboard.append({
            'rank': i + 1,
            'display_name': display_name,
            'total_xp': total_xp,
            'level': level
        })
    
    return leaderboard

# Analytics endpoints
@app.get('/api/v1/analytics/heatmap')
def get_habit_heatmap(days: int = 365, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get habit completion heatmap data."""
    # Record feature usage
    telemetry.record_feature_usage(db, user.id, 'analytics_heatmap')
    
    return analytics.get_habit_heatmap(db, user.id, days)

@app.get('/api/v1/analytics/trends')
def get_habit_trends(habit_id: Optional[int] = None, days: int = 30, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get habit completion trends over time."""
    # Record feature usage
    telemetry.record_feature_usage(db, user.id, 'analytics_trends')
    
    return analytics.get_habit_trends(db, user.id, habit_id, days)

@app.get('/api/v1/analytics/breakdown')
def get_habit_breakdown(days: int = 30, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get breakdown of completions by habit."""
    # Record feature usage
    telemetry.record_feature_usage(db, user.id, 'analytics_breakdown')
    
    return analytics.get_habit_breakdown(db, user.id, days)

@app.get('/api/v1/analytics/streaks')
def get_streak_history(days: int = 90, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get streak history over time."""
    # Record feature usage
    telemetry.record_feature_usage(db, user.id, 'analytics_streaks')
    
    return analytics.get_streak_history(db, user.id, days)

@app.get('/api/v1/analytics/weekly')
def get_weekly_summary(weeks: int = 12, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get weekly completion summary."""
    # Record feature usage
    telemetry.record_feature_usage(db, user.id, 'analytics_weekly')
    
    return analytics.get_weekly_summary(db, user.id, weeks)

@app.get('/api/v1/analytics/insights')
def get_performance_insights(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get performance insights and recommendations."""
    # Record feature usage
    telemetry.record_feature_usage(db, user.id, 'analytics_insights')
    
    return analytics.get_performance_insights(db, user.id)

# Telemetry endpoints
@app.post('/api/v1/telemetry/consent')
def set_telemetry_consent(
    consent: bool = Body(..., embed=True),
    user=Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Set user's telemetry consent preference."""
    telemetry.set_user_consent(db, user.id, consent)
    return {'consent': consent}

@app.get('/api/v1/telemetry/consent')
def get_telemetry_consent(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's current telemetry consent status."""
    return {
        'consent': telemetry.has_user_consented(db, user.id),
        'enabled_globally': telemetry.is_telemetry_enabled()
    }

@app.post('/api/v1/telemetry/event')
def record_telemetry_event(
    event_name: str = Body(...),
    properties: Optional[dict] = Body(None),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record a custom telemetry event."""
    success = telemetry.record_event(db, user.id, event_name, properties)
    return {'recorded': success}

@app.get('/api/v1/admin/telemetry/stats')
def get_telemetry_statistics(
    days: Optional[int] = 30,
    admin_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get aggregated telemetry statistics (admin only)."""
    return telemetry.get_telemetry_stats(db, days)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
