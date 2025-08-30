"""
Gamification engine for LifeRPG - XP, levels, achievements, and streaks.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
import models
import json

# XP and Level Configuration
XP_BASE = 100  # Base XP needed for level 2
XP_MULTIPLIER = 1.2  # Each level requires 20% more XP
MAX_LEVEL = 100

# Achievement Definitions
ACHIEVEMENT_DEFINITIONS = {
    "first_habit": {
        "name": "First Steps",
        "description": "Complete your first habit",
        "xp_reward": 50,
        "icon": "🌱"
    },
    "streak_7": {
        "name": "Week Warrior",
        "description": "Maintain a 7-day streak",
        "xp_reward": 100,
        "icon": "🔥"
    },
    "streak_30": {
        "name": "Monthly Master",
        "description": "Maintain a 30-day streak",
        "xp_reward": 500,
        "icon": "💪"
    },
    "streak_100": {
        "name": "Century Champion",
        "description": "Maintain a 100-day streak",
        "xp_reward": 2000,
        "icon": "👑"
    },
    "habit_count_10": {
        "name": "Habit Builder",
        "description": "Create 10 habits",
        "xp_reward": 200,
        "icon": "🏗️"
    },
    "habit_count_50": {
        "name": "Routine Master",
        "description": "Create 50 habits",
        "xp_reward": 1000,
        "icon": "⚡"
    },
    "xp_1000": {
        "name": "Experience Gained",
        "description": "Earn 1,000 XP",
        "xp_reward": 0,
        "icon": "⭐"
    },
    "level_10": {
        "name": "Rising Star",
        "description": "Reach level 10",
        "xp_reward": 500,
        "icon": "🌟"
    },
    "level_25": {
        "name": "Veteran Player",
        "description": "Reach level 25",
        "xp_reward": 1500,
        "icon": "🎖️"
    },
    "perfect_week": {
        "name": "Perfect Week",
        "description": "Complete all active habits for 7 consecutive days",
        "xp_reward": 300,
        "icon": "💎"
    }
}

def calculate_level_from_xp(total_xp: int) -> int:
    """Calculate level based on total XP."""
    if total_xp < XP_BASE:
        return 1
    
    level = 1
    xp_needed = XP_BASE
    remaining_xp = total_xp
    
    while remaining_xp >= xp_needed and level < MAX_LEVEL:
        remaining_xp -= xp_needed
        level += 1
        xp_needed = int(xp_needed * XP_MULTIPLIER)
    
    return level

def calculate_xp_for_level(level: int) -> int:
    """Calculate total XP needed to reach a given level."""
    if level <= 1:
        return 0
    
    total_xp = 0
    xp_needed = XP_BASE
    
    for _ in range(2, level + 1):
        total_xp += xp_needed
        xp_needed = int(xp_needed * XP_MULTIPLIER)
    
    return total_xp

def calculate_xp_for_next_level(current_xp: int) -> int:
    """Calculate XP needed for the next level."""
    current_level = calculate_level_from_xp(current_xp)
    if current_level >= MAX_LEVEL:
        return 0
    
    next_level_xp = calculate_xp_for_level(current_level + 1)
    return next_level_xp - current_xp

def get_user_stats(db: Session, user_id: int) -> Dict:
    """Get comprehensive user gamification stats."""
    # Get user's total XP from profile
    xp_profile = db.query(models.Profile).filter(
        models.Profile.user_id == user_id,
        models.Profile.key == "total_xp"
    ).first()
    
    total_xp = int(xp_profile.value) if xp_profile and xp_profile.value else 0
    current_level = calculate_level_from_xp(total_xp)
    xp_for_current_level = calculate_xp_for_level(current_level)
    xp_for_next_level = calculate_xp_for_level(current_level + 1) if current_level < MAX_LEVEL else 0
    xp_progress = total_xp - xp_for_current_level
    xp_needed = xp_for_next_level - xp_for_current_level if current_level < MAX_LEVEL else 0
    
    # Get habit stats
    total_habits = db.query(models.Habit).filter(models.Habit.user_id == user_id).count()
    active_habits = db.query(models.Habit).filter(
        models.Habit.user_id == user_id,
        models.Habit.status == "active"
    ).count()
    
    # Get total completions
    total_completions = db.query(models.Log).filter(
        models.Log.user_id == user_id,
        models.Log.action == "complete"
    ).count()
    
    # Calculate current streak (simplified - longest consecutive days with any habit completion)
    current_streak = calculate_current_streak(db, user_id)
    longest_streak = calculate_longest_streak(db, user_id)
    
    # Get achievements
    achievements = db.query(models.Achievement).filter(
        models.Achievement.user_id == user_id
    ).all()
    
    return {
        "total_xp": total_xp,
        "current_level": current_level,
        "xp_progress": xp_progress,
        "xp_needed": xp_needed,
        "xp_percentage": int((xp_progress / xp_needed * 100)) if xp_needed > 0 else 100,
        "total_habits": total_habits,
        "active_habits": active_habits,
        "total_completions": total_completions,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "achievements_count": len(achievements),
        "achievements": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "earned_at": a.earned_at.isoformat() if a.earned_at else None
            }
            for a in achievements
        ]
    }

def calculate_current_streak(db: Session, user_id: int) -> int:
    """Calculate user's current consecutive day streak."""
    # Get recent completions, grouped by date
    recent_logs = db.query(
        func.date(models.Log.timestamp).label('log_date')
    ).filter(
        models.Log.user_id == user_id,
        models.Log.action == "complete",
        models.Log.timestamp >= datetime.now() - timedelta(days=365)
    ).group_by(
        func.date(models.Log.timestamp)
    ).order_by(
        func.date(models.Log.timestamp).desc()
    ).all()
    
    if not recent_logs:
        return 0
    
    # Check for consecutive days starting from today
    today = datetime.now().date()
    current_streak = 0
    check_date = today
    
    for log in recent_logs:
        if log.log_date == check_date:
            current_streak += 1
            check_date = check_date - timedelta(days=1)
        elif log.log_date == check_date - timedelta(days=1):
            # Allow for today not having completions yet
            current_streak += 1
            check_date = log.log_date - timedelta(days=1)
        else:
            break
    
    return current_streak

def calculate_longest_streak(db: Session, user_id: int) -> int:
    """Calculate user's longest ever consecutive day streak."""
    # Get all completion dates
    logs = db.query(
        func.date(models.Log.timestamp).label('log_date')
    ).filter(
        models.Log.user_id == user_id,
        models.Log.action == "complete"
    ).group_by(
        func.date(models.Log.timestamp)
    ).order_by(
        func.date(models.Log.timestamp)
    ).all()
    
    if not logs:
        return 0
    
    max_streak = 1
    current_streak = 1
    
    for i in range(1, len(logs)):
        prev_date = logs[i-1].log_date
        curr_date = logs[i].log_date
        
        if curr_date == prev_date + timedelta(days=1):
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 1
    
    return max_streak

def award_xp(db: Session, user_id: int, xp_amount: int, source: str = "habit_completion") -> Dict:
    """Award XP to a user and check for level-ups and achievements."""
    # Get current XP
    xp_profile = db.query(models.Profile).filter(
        models.Profile.user_id == user_id,
        models.Profile.key == "total_xp"
    ).first()
    
    old_xp = int(xp_profile.value) if xp_profile and xp_profile.value else 0
    new_xp = old_xp + xp_amount
    old_level = calculate_level_from_xp(old_xp)
    new_level = calculate_level_from_xp(new_xp)
    
    # Update XP in profile
    if xp_profile:
        xp_profile.value = str(new_xp)
    else:
        xp_profile = models.Profile(user_id=user_id, key="total_xp", value=str(new_xp))
        db.add(xp_profile)
    
    # Check for level-up achievements
    level_up = new_level > old_level
    new_achievements = []
    
    if level_up:
        # Check level-based achievements
        for achievement_key in ["level_10", "level_25"]:
            if achievement_key not in [a["name"] for a in new_achievements]:
                required_level = int(achievement_key.split("_")[1])
                if new_level >= required_level and old_level < required_level:
                    achievement = award_achievement(db, user_id, achievement_key)
                    if achievement:
                        new_achievements.append(achievement)
    
    # Check XP-based achievements
    if new_xp >= 1000 and old_xp < 1000:
        achievement = award_achievement(db, user_id, "xp_1000")
        if achievement:
            new_achievements.append(achievement)
    
    db.commit()
    
    return {
        "xp_awarded": xp_amount,
        "total_xp": new_xp,
        "old_level": old_level,
        "new_level": new_level,
        "level_up": level_up,
        "new_achievements": new_achievements,
        "source": source
    }

def award_achievement(db: Session, user_id: int, achievement_key: str) -> Optional[Dict]:
    """Award an achievement to a user if they don't already have it."""
    # Check if user already has this achievement
    existing = db.query(models.Achievement).filter(
        models.Achievement.user_id == user_id,
        models.Achievement.name == achievement_key
    ).first()
    
    if existing:
        return None
    
    # Get achievement definition
    achievement_def = ACHIEVEMENT_DEFINITIONS.get(achievement_key)
    if not achievement_def:
        return None
    
    # Create achievement
    achievement = models.Achievement(
        user_id=user_id,
        name=achievement_key,
        description=f"{achievement_def['name']}: {achievement_def['description']}",
        earned_at=datetime.now()
    )
    
    db.add(achievement)
    
    # Award XP bonus if specified
    if achievement_def.get("xp_reward", 0) > 0:
        award_xp(db, user_id, achievement_def["xp_reward"], f"achievement_{achievement_key}")
    
    return {
        "key": achievement_key,
        "name": achievement_def["name"],
        "description": achievement_def["description"],
        "xp_reward": achievement_def.get("xp_reward", 0),
        "icon": achievement_def.get("icon", "🏆")
    }

def check_habit_achievements(db: Session, user_id: int) -> List[Dict]:
    """Check and award habit-related achievements."""
    new_achievements = []
    
    # Check habit count achievements
    total_habits = db.query(models.Habit).filter(models.Habit.user_id == user_id).count()
    
    if total_habits >= 10:
        achievement = award_achievement(db, user_id, "habit_count_10")
        if achievement:
            new_achievements.append(achievement)
    
    if total_habits >= 50:
        achievement = award_achievement(db, user_id, "habit_count_50")
        if achievement:
            new_achievements.append(achievement)
    
    # Check first habit achievement
    if total_habits >= 1:
        achievement = award_achievement(db, user_id, "first_habit")
        if achievement:
            new_achievements.append(achievement)
    
    # Check streak achievements
    current_streak = calculate_current_streak(db, user_id)
    
    if current_streak >= 7:
        achievement = award_achievement(db, user_id, "streak_7")
        if achievement:
            new_achievements.append(achievement)
    
    if current_streak >= 30:
        achievement = award_achievement(db, user_id, "streak_30")
        if achievement:
            new_achievements.append(achievement)
    
    if current_streak >= 100:
        achievement = award_achievement(db, user_id, "streak_100")
        if achievement:
            new_achievements.append(achievement)
    
    return new_achievements

def process_habit_completion(db: Session, user_id: int, habit_id: int) -> Dict:
    """Process a habit completion - award XP and check achievements."""
    habit = db.query(models.Habit).filter(
        models.Habit.id == habit_id,
        models.Habit.user_id == user_id
    ).first()
    
    if not habit:
        raise ValueError("Habit not found")
    
    # Award XP based on habit difficulty/reward
    xp_amount = habit.xp_reward or 10
    xp_result = award_xp(db, user_id, xp_amount, "habit_completion")
    
    # Check for new achievements
    habit_achievements = check_habit_achievements(db, user_id)
    
    # Combine achievement lists
    all_achievements = xp_result.get("new_achievements", []) + habit_achievements
    xp_result["new_achievements"] = all_achievements
    
    return xp_result
