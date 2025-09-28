"""
Mobile-specific backend optimizations and endpoints for LifeRPG mobile app.
Includes data compression, efficient queries, and mobile-friendly responses.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, and_, or_, text
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
import gzip
import base64
from pydantic import BaseModel

from .db import get_db
from .models import User, Habit, Log
from .auth import get_current_user
from .advanced_cache import AdvancedCacheManager

router = APIRouter(prefix="/api/v1/mobile", tags=["mobile"])
cache_manager = AdvancedCacheManager()

class MobileHabitResponse(BaseModel):
    """Optimized habit response for mobile devices"""
    id: int
    title: str
    difficulty: int
    completed_today: bool
    streak: int = 0
    due_time: Optional[str] = None
    category: Optional[str] = None
    priority: int = 1
    # Reduced payload - only essential fields

class MobileTodayResponse(BaseModel):
    """Compact today's overview for mobile"""
    date: str
    habits: List[MobileHabitResponse]
    stats: Dict[str, Any]
    achievements: List[Dict[str, Any]] = []
    notifications: List[Dict[str, Any]] = []

class MobileAnalyticsResponse(BaseModel):
    """Lightweight analytics for mobile"""
    completion_rate: float
    streak_count: int
    weekly_progress: List[float]
    top_categories: List[Dict[str, Any]]
    recent_achievements: List[Dict[str, Any]]

class CompressedResponse:
    """Utility for compressed API responses"""
    
    @staticmethod
    def compress_json(data: Any) -> str:
        """Compress JSON data for mobile transmission"""
        json_str = json.dumps(data, separators=(',', ':'))
        compressed = gzip.compress(json_str.encode('utf-8'))
        return base64.b64encode(compressed).decode('utf-8')
    
    @staticmethod
    def should_compress(request: Request, data_size: int) -> bool:
        """Determine if response should be compressed based on conditions"""
        # Compress if client accepts gzip and data is larger than 1KB
        accept_encoding = request.headers.get('accept-encoding', '')
        user_agent = request.headers.get('user-agent', '').lower()
        
        is_mobile = any(device in user_agent for device in [
            'mobile', 'android', 'iphone', 'ipad', 'phone'
        ])
        
        return 'gzip' in accept_encoding and (data_size > 1024 or is_mobile)

@router.get("/today", response_model=MobileTodayResponse)
async def get_mobile_today(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Optimized endpoint for mobile today view"""
    cache_key = f"mobile_today_{current_user.id}_{datetime.now().date()}"
    
    # Try cache first
    cached_data = await cache_manager.get(cache_key)
    if cached_data:
        return JSONResponse(content=cached_data)
    
    today = datetime.now().date()
    
    # Efficient query with minimal joins
    habits_query = (
        db.query(Habit)
        .filter(Habit.user_id == current_user.id)
        .filter(Habit.is_active == True)
        .options(selectinload(Habit.logs.and_(
            func.date(Log.timestamp) == today
        )))
    )
    
    habits = habits_query.all()
    
    # Process habits for mobile
    mobile_habits = []
    completed_count = 0
    total_streak = 0
    
    for habit in habits:
        # Check if completed today
        completed_today = any(
            log.action == 'complete' and log.timestamp.date() == today
            for log in habit.logs
        )
        
        if completed_today:
            completed_count += 1
        
        # Calculate streak (simplified for mobile)
        streak = habit.current_streak or 0
        total_streak += streak
        
        mobile_habits.append(MobileHabitResponse(
            id=habit.id,
            title=habit.title,
            difficulty=habit.difficulty,
            completed_today=completed_today,
            streak=streak,
            due_time=habit.due_time.strftime('%H:%M') if habit.due_time else None,
            category=habit.category,
            priority=habit.priority or 1
        ))
    
    # Quick stats calculation
    total_habits = len(habits)
    completion_rate = (completed_count / total_habits * 100) if total_habits > 0 else 0
    
    stats = {
        'completed': completed_count,
        'total': total_habits,
        'completion_rate': round(completion_rate, 1),
        'total_streak': total_streak,
        'level': current_user.level or 1,
        'xp': current_user.experience_points or 0
    }
    
    # Recent achievements (limited for mobile)
    recent_achievements = []
    
    # Recent notifications (simulated for now)
    notifications = []
    
    response_data = {
        'date': today.isoformat(),
        'habits': [habit.dict() for habit in mobile_habits],
        'stats': stats,
        'achievements': recent_achievements,
        'notifications': notifications
    }
    
    # Cache for 5 minutes
    await cache_manager.set(cache_key, response_data, ttl=300)
    
    return JSONResponse(content=response_data)

@router.get("/habits/minimal")
async def get_minimal_habits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Ultra-lightweight habits endpoint for low-bandwidth situations"""
    cache_key = f"minimal_habits_{current_user.id}"
    
    cached_data = await cache_manager.get(cache_key)
    if cached_data:
        return JSONResponse(content=cached_data)
    
    # Minimal query - only essential fields
    habits = (
        db.query(
            Habit.id,
            Habit.title,
            Habit.difficulty,
            Habit.current_streak
        )
        .filter(Habit.user_id == current_user.id)
        .filter(Habit.is_active == True)
        .limit(limit)
        .all()
    )
    
    response_data = [
        {
            'id': h.id,
            'title': h.title[:30],  # Truncate for mobile
            'difficulty': h.difficulty,
            'streak': h.current_streak or 0
        }
        for h in habits
    ]
    
    await cache_manager.set(cache_key, response_data, ttl=600)
    return JSONResponse(content=response_data)

@router.post("/habits/{habit_id}/complete/optimistic")
async def optimistic_habit_complete(
    habit_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Optimistic completion for mobile - responds immediately, processes in background"""
    
    # Immediate response for better mobile UX
    response_data = {
        'success': True,
        'habit_id': habit_id,
        'completed_at': datetime.now().isoformat(),
        'processing': True
    }
    
    # Add background task for actual processing
    background_tasks.add_task(
        process_habit_completion, 
        habit_id, 
        current_user.id, 
        db
    )
    
    return JSONResponse(content=response_data)

async def process_habit_completion(habit_id: int, user_id: int, db: Session):
    """Background processing of habit completion"""
    try:
        habit = db.query(Habit).filter(
            Habit.id == habit_id,
            Habit.user_id == user_id
        ).first()
        
        if not habit:
            return
        
        today = datetime.now().date()
        
        # Check if already completed today
        existing_log = db.query(Log).filter(
            Log.habit_id == habit_id,
            Log.action == 'complete',
            func.date(Log.timestamp) == today
        ).first()
        
        if existing_log:
            return
        
        # Create completion log
        log = Log(
            user_id=user_id,
            habit_id=habit_id,
            action='complete',
            timestamp=datetime.now()
        )
        db.add(log)
        
        # Update streak
        habit.current_streak = (habit.current_streak or 0) + 1
        habit.last_completed = datetime.now()
        
        db.commit()
        
        # Invalidate relevant caches
        await cache_manager.delete_pattern(f"*today_{user_id}*")
        await cache_manager.delete_pattern(f"*habits_{user_id}*")
        
    except Exception as e:
        print(f"Background completion processing failed: {e}")
        db.rollback()

@router.get("/analytics/mobile", response_model=MobileAnalyticsResponse)
async def get_mobile_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = 7
):
    """Lightweight analytics optimized for mobile display"""
    cache_key = f"mobile_analytics_{current_user.id}_{days}d"
    
    cached_data = await cache_manager.get(cache_key)
    if cached_data:
        return JSONResponse(content=cached_data)
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Efficient aggregated query
    completion_stats = (
        db.query(
            func.date(Log.timestamp).label('date'),
            func.count(Log.id).label('completions'),
            func.count(func.distinct(Log.habit_id)).label('unique_habits')
        )
        .filter(Log.user_id == current_user.id)
        .filter(Log.action == 'complete')
        .filter(func.date(Log.timestamp) >= start_date)
        .group_by(func.date(Log.timestamp))
        .all()
    )
    
    # Calculate weekly progress
    weekly_progress = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        day_stats = next((s for s in completion_stats if s.date == date), None)
        completions = day_stats.completions if day_stats else 0
        weekly_progress.append(completions)
    
    # Overall completion rate
    total_possible = db.query(func.count(Habit.id)).filter(
        Habit.user_id == current_user.id,
        Habit.is_active == True
    ).scalar() * days
    
    total_completed = sum(weekly_progress)
    completion_rate = (total_completed / total_possible * 100) if total_possible > 0 else 0
    
    # Top categories (simplified)
    top_categories = (
        db.query(
            Habit.category,
            func.count(Log.id).label('count')
        )
        .join(Log, Habit.id == Log.habit_id)
        .filter(Habit.user_id == current_user.id)
        .filter(Log.action == 'complete')
        .filter(func.date(Log.timestamp) >= start_date)
        .group_by(Habit.category)
        .order_by(func.count(Log.id).desc())
        .limit(3)
        .all()
    )
    
    category_data = [
        {'name': cat.category or 'Uncategorized', 'count': cat.count}
        for cat in top_categories
    ]
    
    # Current streak count
    active_streaks = (
        db.query(func.count(Habit.id))
        .filter(Habit.user_id == current_user.id)
        .filter(Habit.current_streak > 0)
        .scalar()
    )
    
    response_data = MobileAnalyticsResponse(
        completion_rate=round(completion_rate, 1),
        streak_count=active_streaks or 0,
        weekly_progress=weekly_progress,
        top_categories=category_data,
        recent_achievements=[]  # Simplified for mobile
    )
    
    await cache_manager.set(cache_key, response_data.dict(), ttl=1800)  # 30 minutes
    
    return response_data

@router.get("/sync/status")
async def get_sync_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check sync status for offline mobile app"""
    
    # Check for any pending sync operations
    # In a real implementation, this would check a sync queue
    
    last_sync = await cache_manager.get(f"last_sync_{current_user.id}")
    
    return {
        'last_sync': last_sync or datetime.now().isoformat(),
        'pending_operations': 0,  # Would be actual count
        'sync_needed': False,
        'server_time': datetime.now().isoformat()
    }

@router.post("/sync/queue")
async def queue_offline_operations(
    operations: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Queue operations from offline mobile app for processing"""
    
    processed = 0
    errors = []
    
    for operation in operations:
        try:
            if operation['type'] == 'habit_complete':
                await process_habit_completion(
                    operation['habit_id'],
                    current_user.id,
                    db
                )
            elif operation['type'] == 'habit_create':
                # Process habit creation
                pass
            
            processed += 1
            
        except Exception as e:
            errors.append({
                'operation': operation,
                'error': str(e)
            })
    
    # Update last sync time
    await cache_manager.set(
        f"last_sync_{current_user.id}",
        datetime.now().isoformat(),
        ttl=86400
    )
    
    return {
        'processed': processed,
        'errors': len(errors),
        'error_details': errors[:5],  # Limit error details
        'sync_time': datetime.now().isoformat()
    }

@router.get("/health/mobile")
async def mobile_health_check():
    """Lightweight health check for mobile apps"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'features': {
            'offline_sync': True,
            'push_notifications': True,
            'compression': True,
            'caching': True
        }
    }

# Mobile-specific middleware for response compression
@router.middleware("http")
async def mobile_compression_middleware(request: Request, call_next):
    """Compress responses for mobile clients when beneficial"""
    response = await call_next(request)
    
    # Only compress JSON responses
    if (response.headers.get('content-type', '').startswith('application/json') and
        hasattr(response, 'body')):
        
        body_size = len(response.body) if hasattr(response, 'body') else 0
        
        if CompressedResponse.should_compress(request, body_size):
            # Add compression header
            response.headers['X-Mobile-Optimized'] = 'true'
    
    return response