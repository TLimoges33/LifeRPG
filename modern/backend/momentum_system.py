"""
Enhanced Momentum System - Matching AHK's time-decay momentum mechanics

This module implements the momentum system that matches the legacy AutoHotkey
version, including daily decay and completion-based momentum boosts.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
import models
import logging

logger = logging.getLogger(__name__)


class MomentumService:
    """Service for managing user momentum with time-based decay and boosts."""
    
    # Constants matching AHK version
    DAILY_DECAY_RATE = 15  # 15% daily decay
    COMPLETION_BOOST = 5   # 5 points per completion
    MAX_MOMENTUM = 100     # Maximum momentum level
    MIN_MOMENTUM = 0       # Minimum momentum level
    
    def __init__(self, db: Session):
        self.db = db

    def get_user_momentum(self, user_id: int) -> Dict:
        """Get current user momentum with calculation if needed."""
        user = (self.db.query(models.User)
                .filter(models.User.id == user_id).first())
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Get or create momentum record
        momentum_record = self._get_or_create_momentum_record(user_id)
        
        # Calculate current momentum with decay
        current_momentum = self._calculate_current_momentum(momentum_record)
        
        # Update if changed
        if current_momentum != momentum_record.momentum:
            momentum_record.momentum = current_momentum
            momentum_record.last_updated = datetime.utcnow()
            self.db.commit()
        
        return {
            'user_id': user_id,
            'momentum': current_momentum,
            'last_updated': momentum_record.last_updated.isoformat(),
            'momentum_color': self._get_momentum_color(current_momentum),
            'momentum_level': self._get_momentum_level(current_momentum),
            'days_since_update': (
                datetime.utcnow() - momentum_record.last_updated
            ).days
        }

    def update_momentum_for_completion(
        self, user_id: int, habit_difficulty: int = 1
    ) -> Dict:
        """Update momentum when a habit is completed."""
        momentum_record = self._get_or_create_momentum_record(user_id)
        
        # First apply any pending decay
        current_momentum = self._calculate_current_momentum(momentum_record)
        
        # Apply completion boost (scaled by difficulty)
        boost = self.COMPLETION_BOOST * habit_difficulty
        new_momentum = min(self.MAX_MOMENTUM, current_momentum + boost)
        
        # Update record
        momentum_record.momentum = new_momentum
        momentum_record.last_updated = datetime.utcnow()
        self.db.commit()
        
        logger.info(
            f"Momentum updated for user {user_id}: "
            f"{current_momentum} -> {new_momentum} (+{boost})"
        )
        
        return {
            'previous_momentum': current_momentum,
            'new_momentum': new_momentum,
            'boost_applied': boost,
            'momentum_color': self._get_momentum_color(new_momentum),
            'momentum_level': self._get_momentum_level(new_momentum)
        }

    def apply_daily_momentum_decay(
        self, user_id: Optional[int] = None
    ) -> List[Dict]:
        """Apply daily momentum decay. If user_id is None, applies to all."""
        if user_id:
            users = [
                self.db.query(models.User)
                .filter(models.User.id == user_id).first()
            ]
        else:
            users = self.db.query(models.User).all()
        
        results = []
        
        for user in users:
            if not user:
                continue
                
            momentum_record = self._get_or_create_momentum_record(user.id)
            old_momentum = momentum_record.momentum
            new_momentum = self._calculate_current_momentum(momentum_record)
            
            if new_momentum != old_momentum:
                momentum_record.momentum = new_momentum
                momentum_record.last_updated = datetime.utcnow()
                
                results.append({
                    'user_id': user.id,
                    'old_momentum': old_momentum,
                    'new_momentum': new_momentum,
                    'decay_applied': old_momentum - new_momentum
                })
        
        self.db.commit()
        return results

    def get_momentum_history(self, user_id: int, days: int = 30) -> Dict:
        """Get momentum history for visualization."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get habit completions for the period
        completions = self.db.query(models.Log).filter(
            and_(
                models.Log.user_id == user_id,
                models.Log.action == 'completed',
                models.Log.created_at >= start_date
            )
        ).order_by(models.Log.created_at).all()
        
        # Simulate momentum over time
        momentum_history = []
        current_momentum = self._get_or_create_momentum_record(user_id).momentum
        
        # Work backwards from current momentum
        completion_dates = [c.created_at.date() for c in completions]
        
        for i in range(days):
            date = (end_date - timedelta(days=i)).date()
            
            # Count completions on this date
            completions_count = completion_dates.count(date)
            
            # Estimate momentum for this date
            if i == 0:
                momentum = current_momentum
            else:
                # Apply reverse decay and subtract completion boosts
                momentum = momentum_history[i-1]['momentum']
                momentum += self.DAILY_DECAY_RATE  # Add back the decay
                momentum -= completions_count * self.COMPLETION_BOOST  # Subtract the boost
                momentum = max(self.MIN_MOMENTUM, min(self.MAX_MOMENTUM, momentum))
            
            momentum_history.append({
                'date': date.isoformat(),
                'momentum': max(0, momentum),
                'completions': completions_count,
                'momentum_level': self._get_momentum_level(momentum)
            })
        
        # Reverse to get chronological order
        momentum_history.reverse()
        
        return {
            'user_id': user_id,
            'period_days': days,
            'history': momentum_history,
            'average_momentum': sum(h['momentum'] for h in momentum_history) / len(momentum_history),
            'total_completions': sum(h['completions'] for h in momentum_history)
        }

    def get_momentum_insights(self, user_id: int) -> Dict:
        """Get momentum insights and recommendations."""
        current_data = self.get_user_momentum(user_id)
        history = self.get_momentum_history(user_id, 7)  # Last week
        
        insights = []
        recommendations = []
        
        # Analyze current momentum level
        momentum = current_data['momentum']
        if momentum >= 80:
            insights.append("🔥 You're on fire! Your momentum is excellent.")
            recommendations.append("Keep up the great work and maintain consistency.")
        elif momentum >= 60:
            insights.append("💪 Strong momentum! You're building good habits.")
            recommendations.append("Try to complete habits daily to maintain this level.")
        elif momentum >= 40:
            insights.append("⚡ Moderate momentum. Room for improvement.")
            recommendations.append("Focus on completing at least one habit daily.")
        elif momentum >= 20:
            insights.append("📈 Low momentum. Time to get back on track.")
            recommendations.append("Start with easier habits to rebuild momentum.")
        else:
            insights.append("🎯 Fresh start! Let's build momentum together.")
            recommendations.append("Begin with one simple habit and complete it daily.")
        
        # Analyze recent trend
        recent_momentum = [h['momentum'] for h in history['history'][-3:]]
        if len(recent_momentum) >= 2:
            trend = recent_momentum[-1] - recent_momentum[0]
            if trend > 10:
                insights.append("📈 Your momentum is trending upward!")
            elif trend < -10:
                insights.append("📉 Your momentum has been declining recently.")
        
        # Days without decay
        days_since_update = current_data['days_since_update']
        if days_since_update >= 3:
            recommendations.append(f"It's been {days_since_update} days since your last activity. Complete a habit to prevent further momentum decay.")
        
        return {
            'user_id': user_id,
            'current_momentum': momentum,
            'momentum_level': current_data['momentum_level'],
            'insights': insights,
            'recommendations': recommendations,
            'days_since_update': days_since_update,
            'weekly_average': history['average_momentum']
        }

    def _get_or_create_momentum_record(self, user_id: int) -> models.UserMomentum:
        """Get or create momentum record for user."""
        momentum_record = self.db.query(models.UserMomentum).filter(
            models.UserMomentum.user_id == user_id
        ).first()
        
        if not momentum_record:
            momentum_record = models.UserMomentum(
                user_id=user_id,
                momentum=50,  # Start with moderate momentum
                last_updated=datetime.utcnow()
            )
            self.db.add(momentum_record)
            self.db.commit()
        
        return momentum_record

    def _calculate_current_momentum(self, momentum_record: models.UserMomentum) -> float:
        """Calculate current momentum with time-based decay."""
        if not momentum_record.last_updated:
            return momentum_record.momentum
        
        # Calculate days since last update
        now = datetime.utcnow()
        days_elapsed = (now - momentum_record.last_updated).days
        
        if days_elapsed == 0:
            return momentum_record.momentum
        
        # Apply daily decay (15% per day, matching AHK)
        current_momentum = momentum_record.momentum
        for _ in range(days_elapsed):
            decay = current_momentum * (self.DAILY_DECAY_RATE / 100)
            current_momentum = max(self.MIN_MOMENTUM, current_momentum - decay)
        
        return round(current_momentum, 2)

    def _get_momentum_color(self, momentum: float) -> str:
        """Get color code for momentum level (matching AHK HUD colors)."""
        if momentum >= 70:
            return 'green'
        elif momentum >= 40:
            return 'yellow'
        else:
            return 'red'

    def _get_momentum_level(self, momentum: float) -> str:
        """Get descriptive level for momentum."""
        if momentum >= 90:
            return 'Legendary'
        elif momentum >= 80:
            return 'Excellent'
        elif momentum >= 70:
            return 'Great'
        elif momentum >= 60:
            return 'Good'
        elif momentum >= 50:
            return 'Fair'
        elif momentum >= 40:
            return 'Moderate'
        elif momentum >= 30:
            return 'Low'
        elif momentum >= 20:
            return 'Poor'
        else:
            return 'Critical'


# Add momentum model if it doesn't exist
def add_momentum_model_if_needed():
    """Helper to add momentum model to models.py if not present."""
    momentum_model = '''
class UserMomentum(Base):
    __tablename__ = 'user_momentum'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    momentum = Column(Float, default=50.0)  # Current momentum level (0-100)
    last_updated = Column(DateTime, server_default=func.current_timestamp())
    
    user = relationship("User", back_populates="momentum")
    
    __table_args__ = (
        Index('idx_user_momentum_user_id', 'user_id'),
    )
'''
    return momentum_model


# FastAPI endpoints for momentum system
def get_momentum_endpoints():
    """Return FastAPI endpoints for momentum system."""
    endpoints = '''
@app.get('/api/v1/momentum/{user_id}')
def get_user_momentum_endpoint(
    user_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user momentum."""
    if user.id != user_id and not user.is_admin:
        raise HTTPException(403, "Access denied")
    
    momentum_service = MomentumService(db)
    return momentum_service.get_user_momentum(user_id)

@app.post('/api/v1/momentum/{user_id}/boost')
def boost_momentum_endpoint(
    user_id: int,
    difficulty: int = 1,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Boost momentum for habit completion."""
    if user.id != user_id:
        raise HTTPException(403, "Access denied")
    
    momentum_service = MomentumService(db)
    return momentum_service.update_momentum_for_completion(user_id, difficulty)

@app.get('/api/v1/momentum/{user_id}/history')
def get_momentum_history_endpoint(
    user_id: int,
    days: int = 30,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get momentum history for visualization."""
    if user.id != user_id and not user.is_admin:
        raise HTTPException(403, "Access denied")
    
    momentum_service = MomentumService(db)
    return momentum_service.get_momentum_history(user_id, days)

@app.get('/api/v1/momentum/{user_id}/insights')
def get_momentum_insights_endpoint(
    user_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get momentum insights and recommendations."""
    if user.id != user_id and not user.is_admin:
        raise HTTPException(403, "Access denied")
    
    momentum_service = MomentumService(db)
    return momentum_service.get_momentum_insights(user_id)

@app.post('/api/v1/admin/momentum/decay')
def apply_momentum_decay_endpoint(
    admin_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Apply momentum decay to all users (admin only)."""
    momentum_service = MomentumService(db)
    results = momentum_service.apply_daily_momentum_decay()
    return {"updated_users": len(results), "results": results}
'''
    return endpoints