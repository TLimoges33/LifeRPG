"""
Telemetry collection for LifeRPG - opt-in anonymous usage analytics.
"""
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from sqlalchemy.orm import Session
import models
import json
import os

def is_telemetry_enabled() -> bool:
    """Check if telemetry is enabled globally."""
    return os.getenv('TELEMETRY_ENABLED', 'true').lower() in ('true', '1', 'yes', 'on')

def has_user_consented(db: Session, user_id: int) -> bool:
    """Check if user has consented to telemetry."""
    if not is_telemetry_enabled():
        return False
    
    consent = db.query(models.Profile).filter(
        models.Profile.user_id == user_id,
        models.Profile.key == 'telemetry_consent'
    ).first()
    
    return consent and consent.value == 'true'

def set_user_consent(db: Session, user_id: int, consent: bool) -> None:
    """Set user's telemetry consent."""
    existing = db.query(models.Profile).filter(
        models.Profile.user_id == user_id,
        models.Profile.key == 'telemetry_consent'
    ).first()
    
    if existing:
        existing.value = 'true' if consent else 'false'
    else:
        profile = models.Profile(
            user_id=user_id,
            key='telemetry_consent',
            value='true' if consent else 'false'
        )
        db.add(profile)
    
    db.commit()

def record_event(db: Session, user_id: Optional[int], event_name: str, properties: Optional[Dict[str, Any]] = None) -> bool:
    """Record a telemetry event if user has consented."""
    # Check if telemetry is enabled globally
    if not is_telemetry_enabled():
        return False
    
    # For anonymous events (user_id = None), always record if globally enabled
    if user_id is not None and not has_user_consented(db, user_id):
        return False
    
    # Sanitize properties to remove PII
    safe_properties = sanitize_properties(properties or {})
    
    event = models.TelemetryEvent(
        user_id=user_id,
        name=event_name,
        payload=json.dumps(safe_properties)
    )
    
    db.add(event)
    
    try:
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False

def sanitize_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
    """Remove or hash any potentially identifying information."""
    safe_props = {}
    
    # List of allowed property keys that are safe to collect
    allowed_keys = {
        'action', 'category', 'label', 'value', 'duration', 'count',
        'habit_difficulty', 'habit_cadence', 'achievement_type',
        'integration_provider', 'feature_used', 'error_type',
        'platform', 'version', 'browser', 'screen_resolution',
        'habit_count', 'completion_count', 'streak_length'
    }
    
    for key, value in properties.items():
        if key in allowed_keys:
            # Further sanitize the value
            if isinstance(value, str) and len(value) > 100:
                # Truncate long strings
                safe_props[key] = value[:100]
            elif isinstance(value, (int, float, bool)):
                safe_props[key] = value
            elif isinstance(value, str):
                safe_props[key] = value
    
    return safe_props

# Pre-defined event helpers
def record_habit_completion(db: Session, user_id: int, habit_difficulty: int, xp_awarded: int) -> bool:
    """Record a habit completion event."""
    return record_event(db, user_id, 'habit_completed', {
        'habit_difficulty': habit_difficulty,
        'xp_awarded': xp_awarded
    })

def record_achievement_earned(db: Session, user_id: int, achievement_type: str, xp_awarded: int) -> bool:
    """Record an achievement earned event."""
    return record_event(db, user_id, 'achievement_earned', {
        'achievement_type': achievement_type,
        'xp_awarded': xp_awarded
    })

def record_level_up(db: Session, user_id: int, old_level: int, new_level: int) -> bool:
    """Record a level up event."""
    return record_event(db, user_id, 'level_up', {
        'old_level': old_level,
        'new_level': new_level
    })

def record_habit_created(db: Session, user_id: int, habit_difficulty: int, habit_cadence: str) -> bool:
    """Record a habit creation event."""
    return record_event(db, user_id, 'habit_created', {
        'habit_difficulty': habit_difficulty,
        'habit_cadence': habit_cadence
    })

def record_integration_sync(db: Session, user_id: int, provider: str, items_synced: int, success: bool) -> bool:
    """Record an integration sync event."""
    return record_event(db, user_id, 'integration_sync', {
        'integration_provider': provider,
        'items_synced': items_synced,
        'success': success
    })

def record_feature_usage(db: Session, user_id: int, feature: str, duration_seconds: Optional[int] = None) -> bool:
    """Record a feature usage event."""
    properties = {'feature_used': feature}
    if duration_seconds is not None:
        properties['duration'] = duration_seconds
    
    return record_event(db, user_id, 'feature_used', properties)

def record_error(db: Session, user_id: Optional[int], error_type: str, context: Optional[str] = None) -> bool:
    """Record an error event (can be anonymous)."""
    properties = {'error_type': error_type}
    if context:
        properties['context'] = context[:50]  # Truncate context
    
    return record_event(db, user_id, 'error_occurred', properties)

def get_telemetry_stats(db: Session, days: int = 30) -> Dict:
    """Get aggregated telemetry statistics for admin purposes."""
    from datetime import timedelta
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Count events by type
    event_counts = db.query(
        models.TelemetryEvent.name,
        db.func.count(models.TelemetryEvent.id).label('count')
    ).filter(
        models.TelemetryEvent.created_at >= cutoff
    ).group_by(
        models.TelemetryEvent.name
    ).all()
    
    # Count unique users (approximate)
    unique_users = db.query(models.TelemetryEvent.user_id).filter(
        models.TelemetryEvent.created_at >= cutoff,
        models.TelemetryEvent.user_id.isnot(None)
    ).distinct().count()
    
    # Total events
    total_events = db.query(models.TelemetryEvent).filter(
        models.TelemetryEvent.created_at >= cutoff
    ).count()
    
    return {
        'period_days': days,
        'total_events': total_events,
        'unique_users': unique_users,
        'events_by_type': {event.name: event.count for event in event_counts},
        'telemetry_enabled': is_telemetry_enabled()
    }
