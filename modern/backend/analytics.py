"""
Analytics module for LifeRPG - habit tracking insights and visualizations.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import models
import json

def get_habit_heatmap(db: Session, user_id: int, days: int = 365) -> Dict:
    """Generate habit completion heatmap data for the last N days."""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Get all completions in the date range
    completions = db.query(
        func.date(models.Log.timestamp).label('date'),
        func.count(models.Log.id).label('count')
    ).filter(
        models.Log.user_id == user_id,
        models.Log.action == 'complete',
        models.Log.timestamp >= start_date
    ).group_by(
        func.date(models.Log.timestamp)
    ).all()
    
    # Create a map of date -> completion count
    completion_map = {str(comp.date): comp.count for comp in completions}
    
    # Generate full date range with completion counts
    heatmap_data = []
    current_date = start_date.date()
    end_date_only = end_date.date()
    
    while current_date <= end_date_only:
        date_str = current_date.isoformat()
        count = completion_map.get(date_str, 0)
        heatmap_data.append({
            'date': date_str,
            'count': count,
            'level': min(4, count)  # 0-4 intensity levels for visualization
        })
        current_date += timedelta(days=1)
    
    return {
        'data': heatmap_data,
        'total_days': days,
        'completion_days': len(completion_map),
        'total_completions': sum(completion_map.values()),
        'start_date': start_date.date().isoformat(),
        'end_date': end_date.date().isoformat()
    }

def get_habit_trends(db: Session, user_id: int, habit_id: Optional[int] = None, days: int = 30) -> Dict:
    """Get habit completion trends over time."""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Base query
    query = db.query(
        func.date(models.Log.timestamp).label('date'),
        func.count(models.Log.id).label('completions')
    ).filter(
        models.Log.user_id == user_id,
        models.Log.action == 'complete',
        models.Log.timestamp >= start_date
    )
    
    # Filter by specific habit if provided
    if habit_id:
        query = query.filter(models.Log.habit_id == habit_id)
    
    trends = query.group_by(
        func.date(models.Log.timestamp)
    ).order_by(
        func.date(models.Log.timestamp)
    ).all()
    
    # Fill in missing dates with 0
    trend_data = []
    current_date = start_date.date()
    trend_map = {str(trend.date): trend.completions for trend in trends}
    
    while current_date <= end_date.date():
        date_str = current_date.isoformat()
        trend_data.append({
            'date': date_str,
            'completions': trend_map.get(date_str, 0)
        })
        current_date += timedelta(days=1)
    
    # Calculate some basic stats
    total_completions = sum(trend_map.values())
    active_days = len([d for d in trend_data if d['completions'] > 0])
    avg_per_day = total_completions / days if days > 0 else 0
    
    return {
        'data': trend_data,
        'stats': {
            'total_completions': total_completions,
            'active_days': active_days,
            'average_per_day': round(avg_per_day, 2),
            'completion_rate': round((active_days / days) * 100, 1) if days > 0 else 0
        },
        'period': {
            'days': days,
            'start_date': start_date.date().isoformat(),
            'end_date': end_date.date().isoformat()
        }
    }

def get_habit_breakdown(db: Session, user_id: int, days: int = 30) -> Dict:
    """Get breakdown of completions by habit."""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Get completions by habit
    results = db.query(
        models.Habit.id,
        models.Habit.title,
        func.count(models.Log.id).label('completions')
    ).join(
        models.Log, models.Habit.id == models.Log.habit_id
    ).filter(
        models.Habit.user_id == user_id,
        models.Log.action == 'complete',
        models.Log.timestamp >= start_date
    ).group_by(
        models.Habit.id, models.Habit.title
    ).order_by(
        func.count(models.Log.id).desc()
    ).all()
    
    habit_data = []
    total_completions = 0
    
    for result in results:
        completions = result.completions
        total_completions += completions
        habit_data.append({
            'habit_id': result.id,
            'habit_title': result.title,
            'completions': completions
        })
    
    # Calculate percentages
    for habit in habit_data:
        habit['percentage'] = round((habit['completions'] / total_completions) * 100, 1) if total_completions > 0 else 0
    
    return {
        'habits': habit_data,
        'total_completions': total_completions,
        'period': {
            'days': days,
            'start_date': start_date.date().isoformat(),
            'end_date': end_date.date().isoformat()
        }
    }

def get_streak_history(db: Session, user_id: int, days: int = 90) -> Dict:
    """Calculate streak history over time."""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Get all completion dates
    completion_dates = db.query(
        func.date(models.Log.timestamp).label('date')
    ).filter(
        models.Log.user_id == user_id,
        models.Log.action == 'complete',
        models.Log.timestamp >= start_date
    ).group_by(
        func.date(models.Log.timestamp)
    ).order_by(
        func.date(models.Log.timestamp)
    ).all()
    
    # Convert to set for fast lookup
    completion_dates_set = {comp.date for comp in completion_dates}
    
    # Calculate streak for each day
    streak_data = []
    current_date = start_date.date()
    current_streak = 0
    
    while current_date <= end_date.date():
        if current_date in completion_dates_set:
            current_streak += 1
        else:
            current_streak = 0
        
        streak_data.append({
            'date': current_date.isoformat(),
            'streak': current_streak,
            'completed': current_date in completion_dates_set
        })
        
        current_date += timedelta(days=1)
    
    # Find longest streak in period
    max_streak = max((day['streak'] for day in streak_data), default=0)
    
    return {
        'data': streak_data,
        'max_streak': max_streak,
        'current_streak': streak_data[-1]['streak'] if streak_data else 0,
        'period': {
            'days': days,
            'start_date': start_date.date().isoformat(),
            'end_date': end_date.date().isoformat()
        }
    }

def get_weekly_summary(db: Session, user_id: int, weeks: int = 12) -> Dict:
    """Get weekly completion summary."""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(weeks=weeks)
    
    # Get completions grouped by week
    results = db.query(
        func.strftime('%Y-%W', models.Log.timestamp).label('week'),
        func.count(models.Log.id).label('completions')
    ).filter(
        models.Log.user_id == user_id,
        models.Log.action == 'complete',
        models.Log.timestamp >= start_date
    ).group_by(
        func.strftime('%Y-%W', models.Log.timestamp)
    ).order_by(
        func.strftime('%Y-%W', models.Log.timestamp)
    ).all()
    
    weekly_data = []
    for result in results:
        # Parse week string (YYYY-WW format)
        year_week = result.week
        completions = result.completions
        
        weekly_data.append({
            'week': year_week,
            'completions': completions
        })
    
    return {
        'data': weekly_data,
        'total_weeks': weeks,
        'period': {
            'weeks': weeks,
            'start_date': start_date.date().isoformat(),
            'end_date': end_date.date().isoformat()
        }
    }

def get_performance_insights(db: Session, user_id: int) -> Dict:
    """Generate performance insights and recommendations."""
    # Get basic stats
    total_habits = db.query(models.Habit).filter(models.Habit.user_id == user_id).count()
    active_habits = db.query(models.Habit).filter(
        models.Habit.user_id == user_id,
        models.Habit.status == 'active'
    ).count()
    
    # Get completion data for last 30 days
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent_completions = db.query(models.Log).filter(
        models.Log.user_id == user_id,
        models.Log.action == 'complete',
        models.Log.timestamp >= thirty_days_ago
    ).count()
    
    # Calculate completion rate
    expected_completions = active_habits * 30  # Assuming daily habits
    completion_rate = (recent_completions / expected_completions) * 100 if expected_completions > 0 else 0
    
    # Get streak info
    from . import gamification
    current_streak = gamification.calculate_current_streak(db, user_id)
    longest_streak = gamification.calculate_longest_streak(db, user_id)
    
    # Generate insights
    insights = []
    
    if completion_rate < 50:
        insights.append({
            'type': 'warning',
            'title': 'Low Completion Rate',
            'message': f'Your completion rate is {completion_rate:.1f}%. Consider reducing the number of active habits or adjusting your routine.',
            'action': 'Review your habits and focus on the most important ones.'
        })
    elif completion_rate > 80:
        insights.append({
            'type': 'success',
            'title': 'Excellent Performance',
            'message': f'Great job! You have a {completion_rate:.1f}% completion rate.',
            'action': 'Consider adding new challenges or increasing habit difficulty.'
        })
    
    if current_streak == 0 and longest_streak > 0:
        insights.append({
            'type': 'motivation',
            'title': 'Get Back on Track',
            'message': f'You had a {longest_streak}-day streak before. You can do it again!',
            'action': 'Start with one small habit to rebuild momentum.'
        })
    
    if current_streak >= 7:
        insights.append({
            'type': 'celebration',
            'title': 'Great Streak!',
            'message': f'You\'re on a {current_streak}-day streak. Keep it up!',
            'action': 'Maintain consistency to reach the next milestone.'
        })
    
    return {
        'stats': {
            'total_habits': total_habits,
            'active_habits': active_habits,
            'completion_rate': round(completion_rate, 1),
            'recent_completions': recent_completions,
            'current_streak': current_streak,
            'longest_streak': longest_streak
        },
        'insights': insights
    }
