from fastapi import FastAPI, Depends, HTTPException
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
import models
import oauth
from oauth import oauth_router
import auth
from auth import auth_router
import os
import requests
import time
from fastapi import Body
import json
from typing import Optional

from contextlib import asynccontextmanager
from starlette.responses import Response

import config
from config import settings
import middleware
from middleware import BodySizeLimitMiddleware, RateLimitMiddleware, CSRFMiddleware
import metrics
from metrics import setup_metrics
import plugins

import adapters
from adapters import ADAPTERS


@asynccontextmanager
async def lifespan(app: FastAPI):
    # initialize DB on startup
    models.init_db()
    # optional: enqueue due integrations on startup if enabled
    try:
        if os.getenv('STARTUP_SCHEDULER_ENABLE', 'false').lower() in ('1','true','yes','on'):
            from .worker import schedule_periodic_syncs
            try:
                schedule_periodic_syncs()
            except Exception:
                pass
    except Exception:
        pass
    yield


app = FastAPI(title="The Wizard's Grimoire API", lifespan=lifespan)

# CORS: allow configured origins and credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["authorization", "content-type", "accept"],
    expose_headers=["set-cookie"],
)

# Request size limit
app.add_middleware(BodySizeLimitMiddleware, max_body_bytes=int(os.getenv('MAX_BODY_BYTES', '1048576')))  # 1 MiB default

# Basic per-IP rate-limit
app.add_middleware(RateLimitMiddleware, requests_per_minute=int(os.getenv('REQUESTS_PER_MINUTE', '120')))

# CSRF (disabled by default; enable via CSRF_ENABLE=true)
app.add_middleware(CSRFMiddleware)

# Prometheus metrics
setup_metrics(app)


# HTTPS enforcement middleware (for production behind a proxy, check X-Forwarded-Proto)
@app.middleware('http')
async def security_headers(request, call_next):
    # Optional HTTPS redirect when behind a reverse proxy
    if settings.FORCE_HTTPS:
        proto = request.headers.get('x-forwarded-proto', request.url.scheme)
        if proto != 'https':
            from starlette.responses import RedirectResponse
            url = request.url.replace(scheme='https')
            return RedirectResponse(str(url))

    response: Response = await call_next(request)

    # Security headers
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('Referrer-Policy', 'no-referrer')
    response.headers.setdefault('Permissions-Policy', 'geolocation=()')
    response.headers.setdefault('Content-Security-Policy', settings.csp_header())
    if settings.HSTS_ENABLE:
        response.headers.setdefault('Strict-Transport-Security', 'max-age=63072000; includeSubDomains; preload')
    return response

# startup behavior is handled by the `lifespan` context manager above

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.get('/api/v1/hello')
def hello():
    return {'message': 'Hello from LifeRPG modern backend (FastAPI)'}

app.include_router(oauth_router, prefix='/api/v1')
app.include_router(auth_router, prefix='/api/v1/auth')

# Include mobile API for mobile-optimized endpoints
try:
    import mobile_api
    app.include_router(mobile_api.router)
    print("✅ Mobile API endpoints registered successfully")
except ImportError as e:
    print(f"⚠️  Mobile API not available: {e}")

# Include AI Assistant API for Phase 3 features
try:
    import ai_assistant
    app.include_router(ai_assistant.router)
    print("✅ AI Assistant API endpoints registered successfully")
except ImportError as e:
    print(f"⚠️  AI Assistant API not available: {e}")

# Initialize plugin system
plugins.setup_plugin_system(app)


import rbac
from rbac import require_admin


import db
from db import get_db
from transaction import transactional
from sqlalchemy.orm import Session
import worker
from worker import get_queue, example_job, enqueue_adapter_sync, run_adapter_sync
import hmac, hashlib, base64
from auth import get_current_user


# Public API tokens (create/list/delete) for read-only widgets
@app.post('/api/v1/tokens')
def create_token(payload: dict = Body(...), user=Depends(get_current_user), db: Session = Depends(get_db)):
    name = (payload or {}).get('name') or 'public-token'
    scope = (payload or {}).get('scope') or 'read:widgets'
    from .tokens import create_public_token
    token = create_public_token(db, user.id, name=name, scope=scope)
    # Commit so the token row is visible to subsequent requests (new sessions)
    db.commit()
    return {'ok': True, 'token': token, 'name': name, 'scope': scope}


@app.get('/api/v1/tokens')
def list_tokens(user=Depends(get_current_user), db: Session = Depends(get_db)):
    from .models import PublicToken
    rows = db.query(PublicToken).filter_by(user_id=user.id).all()
    return [
        {
            'id': r.id,
            'name': r.name,
            'scope': r.scope,
            'created_at': r.created_at,
            'last_used_at': r.last_used_at,
        }
        for r in rows
    ]


@app.delete('/api/v1/tokens/{token_id}')
def delete_token(token_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    from .models import PublicToken
    row = db.query(PublicToken).filter_by(id=token_id, user_id=user.id).first()
    if not row:
        raise HTTPException(status_code=404, detail='not found')
    db.delete(row)
    db.flush()
    db.commit()
    return {'ok': True}


# Habits CRUD endpoints
@app.get('/api/v1/habits')
def list_habits(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """List user's habits."""
    habits = db.query(models.Habit).filter(models.Habit.user_id == user.id).all()
    return [
        {
            'id': h.id,
            'project_id': h.project_id,
            'title': h.title,
            'notes': h.notes,
            'cadence': h.cadence,
            'difficulty': h.difficulty,
            'xp_reward': h.xp_reward,
            'status': h.status,
            'due_date': h.due_date.isoformat() if h.due_date else None,
            'labels': json.loads(h.labels) if h.labels else [],
            'created_at': h.created_at.isoformat() if h.created_at else None
        }
        for h in habits
    ]


@app.post('/api/v1/habits')
def create_habit(payload: dict = Body(...), user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new habit."""
    from . import gamification
    
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
    from . import telemetry
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
    for field in ['title', 'notes', 'cadence', 'difficulty', 'xp_reward', 'status', 'project_id']:
        if field in payload:
            setattr(habit, field, payload[field])
    
    if 'labels' in payload:
        habit.labels = json.dumps(payload['labels'])
    
    db.commit()
    
    return {'ok': True}


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
    
    return {'ok': True}


@app.post('/api/v1/habits/{habit_id}/complete')
def complete_habit(habit_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Mark a habit as completed and award XP."""
    from . import gamification
    
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
    from . import telemetry
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
    from . import gamification
    return gamification.get_user_stats(db, user.id)


@app.get('/api/v1/gamification/achievements')
def list_achievements(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """List all available achievements and user's progress."""
    from . import gamification
    
    # Get user's earned achievements
    earned = db.query(models.Achievement).filter(models.Achievement.user_id == user.id).all()
    earned_keys = {a.name for a in earned}
    
    # Return all possible achievements with earned status
    achievements = []
    for key, definition in gamification.ACHIEVEMENT_DEFINITIONS.items():
        achievements.append({
            'key': key,
            'name': definition['name'],
            'description': definition['description'],
            'xp_reward': definition['xp_reward'],
            'icon': definition['icon'],
            'earned': key in earned_keys,
            'earned_at': next((a.earned_at.isoformat() for a in earned if a.name == key), None)
        })
    
    return achievements


@app.get('/api/v1/gamification/leaderboard')
def get_leaderboard(limit: int = 10, db: Session = Depends(get_db)):
    """Get leaderboard of top users by XP (anonymous)."""
    from . import gamification
    
    # Get top users by XP
    xp_profiles = db.query(models.Profile).filter(
        models.Profile.key == 'total_xp'
    ).order_by(
        models.Profile.value.desc()
    ).limit(limit).all()
    
    leaderboard = []
    for i, profile in enumerate(xp_profiles):
        total_xp = int(profile.value) if profile.value else 0
        level = gamification.calculate_level_from_xp(total_xp)
        
        # Get user display name (anonymous option)
        user = db.query(models.User).filter(models.User.id == profile.user_id).first()
        display_name = user.display_name if user and user.display_name else f"Player {user.id}" if user else "Anonymous"
        
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
    from . import analytics, telemetry
    
    # Record feature usage
    telemetry.record_feature_usage(db, user.id, 'analytics_heatmap')
    
    return analytics.get_habit_heatmap(db, user.id, days)


@app.get('/api/v1/analytics/trends')
def get_habit_trends(habit_id: Optional[int] = None, days: int = 30, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get habit completion trends over time."""
    from . import analytics, telemetry
    
    # Record feature usage
    telemetry.record_feature_usage(db, user.id, 'analytics_trends')
    
    return analytics.get_habit_trends(db, user.id, habit_id, days)


@app.get('/api/v1/analytics/breakdown')
def get_habit_breakdown(days: int = 30, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get breakdown of completions by habit."""
    from . import analytics, telemetry
    
    # Record feature usage
    telemetry.record_feature_usage(db, user.id, 'analytics_breakdown')
    
    return analytics.get_habit_breakdown(db, user.id, days)


@app.get('/api/v1/analytics/streaks')
def get_streak_history(days: int = 90, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get streak history over time."""
    from . import analytics, telemetry
    
    # Record feature usage
    telemetry.record_feature_usage(db, user.id, 'analytics_streaks')
    
    return analytics.get_streak_history(db, user.id, days)


@app.get('/api/v1/analytics/weekly')
def get_weekly_summary(weeks: int = 12, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get weekly completion summary."""
    from . import analytics, telemetry
    
    # Record feature usage
    telemetry.record_feature_usage(db, user.id, 'analytics_weekly')
    
    return analytics.get_weekly_summary(db, user.id, weeks)


@app.get('/api/v1/analytics/insights')
def get_performance_insights(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get performance insights and recommendations."""
    from . import analytics, telemetry
    
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
    from . import telemetry
    telemetry.set_user_consent(db, user.id, consent)
    return {'consent': consent}


@app.get('/api/v1/telemetry/consent')
def get_telemetry_consent(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's current telemetry consent status."""
    from . import telemetry
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
    from . import telemetry
    success = telemetry.record_event(db, user.id, event_name, properties)
    return {'recorded': success}


@app.get('/api/v1/admin/telemetry/stats')
def get_telemetry_statistics(
    days: Optional[int] = 30,
    admin_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get aggregated telemetry statistics (admin only)."""
    from . import telemetry
    return telemetry.get_telemetry_stats(db, days)


@app.get('/api/v1/public/widgets/status')
def public_status(token: str, db: Session = Depends(get_db)):
    """Return a minimal read-only status for embedding: active habits, completions in last 7 days, and streak estimate.
    Auth via lightweight public token.
    """
    from .tokens import verify_public_token
    uid = verify_public_token(db, token)
    if not uid:
        raise HTTPException(status_code=401, detail='invalid token')
    # Compute a tiny summary
    from .models import Habit, Log
    from datetime import datetime, timedelta, timezone
    active = db.query(Habit).filter_by(user_id=uid, status='active').count()
    since = datetime.now(timezone.utc) - timedelta(days=7)
    completed = db.query(Log).filter(Log.user_id == uid, Log.action == 'completed', Log.timestamp >= since).count()
    # naive streak: count consecutive days with at least one completion
    days = set()
    rows = db.query(Log).filter(Log.user_id == uid, Log.action == 'completed', Log.timestamp >= (datetime.now(timezone.utc) - timedelta(days=90))).all()
    for r in rows:
        try:
            d = (r.timestamp.date() if hasattr(r.timestamp, 'date') else None)
            if d:
                days.add(d)
        except Exception:
            continue
    # compute current streak
    today = datetime.now(timezone.utc).date()
    streak = 0
    cur = today
    while cur in days:
        streak += 1
        cur = cur - timedelta(days=1)
    return {'active_habits': active, 'completed_last_7_days': completed, 'current_streak_days': streak}


@app.get('/api/v1/admin/users')
def admin_list_users(admin_user=Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(models.User).all()
    return [{'id': r.id, 'email': r.email, 'role': r.role} for r in rows]


@app.get('/api/v1/admin/settings')
def get_admin_settings(admin_user=Depends(require_admin)):
    from .config import settings
    return {
        'integration_close_mode': settings.INTEGRATION_CLOSE_MODE,
    'default_sync_interval_seconds': int(os.getenv('DEFAULT_SYNC_INTERVAL_SECONDS', '900'))
    }


@app.post('/api/v1/admin/settings')
def update_admin_settings(payload: dict, admin_user=Depends(require_admin)):
    # For simplicity, apply only to process env and global settings; persist per-integration via integration.config
    close_mode = payload.get('integration_close_mode')
    if close_mode in ('archive', 'delete'):
        from .config import settings as _s
        _s.INTEGRATION_CLOSE_MODE = close_mode
    if 'default_sync_interval_seconds' in payload:
        os.environ['DEFAULT_SYNC_INTERVAL_SECONDS'] = str(int(payload['default_sync_interval_seconds']))
    return {'ok': True}


@app.get('/api/v1/admin/provider_caps')
def get_provider_caps(admin_user=Depends(require_admin)):
    """Return current provider caps from env, settings, and DB overrides (min across integrations)."""
    from .config import settings
    from .models import SessionLocal, Integration
    caps = dict(settings.PROVIDER_CAPS)
    default_cap = settings.DEFAULT_PROVIDER_CAP
    # incorporate DB overrides (min across integrations per provider)
    s = SessionLocal()
    try:
        import json as _json
        for row in s.query(Integration).all():
            prov = row.provider
            if not prov or not row.config:
                continue
            try:
                cfg = _json.loads(row.config)
            except Exception:
                continue
            v = cfg.get('sync_max_concurrency')
            if isinstance(v, int) and v > 0:
                if prov not in caps:
                    caps[prov] = min(default_cap, v)
                else:
                    caps[prov] = min(caps[prov], v)
        # Global admin settings integration (provider caps persistence)
        admin_row = (
            s.query(Integration)
            .filter_by(provider='admin', external_id='settings')
            .order_by(Integration.id.desc())
            .first()
        )
        if admin_row and admin_row.config:
            try:
                acfg = _json.loads(admin_row.config) or {}
                pc = acfg.get('provider_caps') or {}
                if isinstance(pc, dict):
                    for k, v in pc.items():
                        try:
                            iv = int(v)
                            if iv > 0:
                                caps[k] = iv if k not in caps else min(caps[k], iv)
                        except Exception:
                            continue
                    # Also update in-process settings so other components see it
                    settings.PROVIDER_CAPS.update({k: int(v) for k, v in pc.items() if str(v).isdigit() and int(v) > 0})
            except Exception:
                pass
    finally:
        s.close()
    return {'default': default_cap, 'caps': caps}


@app.post('/api/v1/admin/provider_caps')
def set_provider_caps(payload: dict = Body(...), admin_user=Depends(require_admin)):
    """Set global per-provider cap overrides (in-process only via settings.PROVIDER_CAPS)."""
    # Accept dict of provider->cap ints
    data = payload.get('caps') or {}
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail='caps must be an object')
    # update settings in-process; also update env JSON for persistence across restarts if desired
    from .config import settings
    cleaned = {}
    for k, v in data.items():
        try:
            iv = int(v)
            if iv > 0:
                cleaned[str(k)] = iv
        except Exception:
            continue
    settings.PROVIDER_CAPS = cleaned
    import json as _json
    os.environ['SYNC_PROVIDER_CAPS'] = _json.dumps(cleaned)
    # Persist to DB in a special admin settings integration for durability
    from .models import SessionLocal, Integration
    s = SessionLocal()
    try:
        row = (
            s.query(Integration)
            .filter_by(provider='admin', external_id='settings')
            .order_by(Integration.id.desc())
            .first()
        )
        data = {'provider_caps': cleaned}
        if not row:
            # create owned by the calling admin user
            uid = getattr(admin_user, 'id', None) or 1
            row = Integration(user_id=uid, provider='admin', external_id='settings', config=_json.dumps(data))
            s.add(row)
        else:
            row.config = _json.dumps(data)
        s.commit()
    except Exception:
        try:
            s.rollback()
        except Exception:
            pass
    finally:
        s.close()
    return {'ok': True, 'caps': cleaned}
@app.get('/api/v1/admin/orchestration')
def get_orchestration_summary(admin_user=Depends(require_admin)):
    """Summarize provider orchestration: inflight, queue depth, and effective cap."""
    # Read Redis keys for inflight and queue depth
    try:
        from redis import Redis
    except Exception:
        Redis = None
    inflight = {}
    qdepth = {}
    if Redis:
        try:
            r = Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
            for key in r.scan_iter(match='sync_provider_inflight:*'):
                try:
                    prov = key.decode().split(':',1)[1]
                    inflight[prov] = int(r.get(key) or 0)
                except Exception:
                    continue
            for key in r.scan_iter(match='sync_queue_depth:*'):
                try:
                    prov = key.decode().split(':',1)[1]
                    qdepth[prov] = int(r.get(key) or 0)
                except Exception:
                    continue
        except Exception:
            pass
    # Compute effective caps similar to metrics module
    caps = {}
    try:
        from .models import SessionLocal, Integration
        from .config import settings
        s = SessionLocal()
        try:
            import json as _json
            per_integ = {}
            for row in s.query(Integration).all():
                if not row.provider or not row.config:
                    continue
                try:
                    cfg = _json.loads(row.config)
                    v = cfg.get('sync_max_concurrency')
                except Exception:
                    v = None
                if isinstance(v, int) and v > 0:
                    per_integ[row.provider] = min(per_integ.get(row.provider, v), v)
            admin_row = (
                s.query(Integration)
                .filter_by(provider='admin', external_id='settings')
                .order_by(Integration.id.desc())
                .first()
            )
            admin_caps = {}
            if admin_row and admin_row.config:
                try:
                    acfg = _json.loads(admin_row.config) or {}
                    if isinstance(acfg.get('provider_caps'), dict):
                        admin_caps = acfg.get('provider_caps')
                except Exception:
                    pass
            default_cap = settings.DEFAULT_PROVIDER_CAP
            proc_caps = getattr(settings, 'PROVIDER_CAPS', {}) or {}
            providers = set().union(inflight.keys(), qdepth.keys(), per_integ.keys(), proc_caps.keys(), admin_caps.keys())
            for prov in providers:
                base = default_cap
                if prov in proc_caps:
                    try:
                        base = min(base, int(proc_caps[prov]))
                    except Exception:
                        pass
                if prov in admin_caps:
                    try:
                        base = min(base, int(admin_caps[prov]))
                    except Exception:
                        pass
                if prov in per_integ:
                    base = min(base, int(per_integ[prov]))
                caps[prov] = base
        finally:
            s.close()
    except Exception:
        pass
    out = []
    for prov in sorted(set().union(inflight.keys(), qdepth.keys(), caps.keys())):
        out.append({'provider': prov, 'inflight': inflight.get(prov, 0), 'queue_depth': qdepth.get(prov, 0), 'cap': caps.get(prov)})
    # Also add RQ queue length if available
    try:
        from rq import Queue
        if Redis:
            q = Queue('default', connection=Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0')))
            out.append({'queue': 'default', 'rq_length': len(q)})
    except Exception:
        pass
    return {'providers': out}


@app.get('/api/v1/admin/email/health')
def email_health(admin_user=Depends(require_admin)):
    from .config import settings
    from .metrics import log_job_event
    info = {
        'transport': settings.EMAIL_TRANSPORT,
        'smtp_host': bool(settings.SMTP_HOST),
        'smtp_port': settings.SMTP_PORT,
        'smtp_user': bool(settings.SMTP_USERNAME),
        'smtp_tls': settings.SMTP_USE_TLS,
        'from': settings.SMTP_FROM or settings.SMTP_USERNAME,
    }
    # Best-effort connectivity check for SMTP
    ok = True
    err = None
    if settings.EMAIL_TRANSPORT == 'smtp' and settings.SMTP_HOST:
        import smtplib
        try:
            s = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=5)
            if settings.SMTP_USE_TLS:
                s.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                s.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            try:
                s.quit()
            except Exception:
                pass
        except Exception as e:
            ok = False
            err = str(e)
    return {'ok': ok, 'info': info, 'error': err}


@app.post('/api/v1/admin/email/test')
def email_test(payload: dict = Body({}), admin_user=Depends(require_admin)):
    to = payload.get('to') or admin_user.email if hasattr(admin_user, 'email') else None
    if not to:
        raise HTTPException(status_code=400, detail='to is required')
    from .notifier import send_email
    try:
        send_email(to, 'LifeRPG test email', 'This is a test email from LifeRPG.')
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


# Hooks schema/examples and validation (admin)
@app.get('/api/v1/admin/hooks/schema')
def get_hooks_schema(admin_user=Depends(require_admin)):
    """Return a simple schema and examples for hooks configuration to aid UI validation."""
    schema = {
        'type': 'object',
        'properties': {
            'pre_sync': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'type': {'type': 'string', 'enum': ['slack', 'webhook', 'email']},
                        'text': {'type': 'string'},
                        'url': {'type': 'string'},
                        'template': {'type': 'string'},
                        'headers': {'type': 'object'},
                        'to': {'type': 'string'},
                        'subject': {'type': 'string'},
                        'body': {'type': 'string'},
                        'on': {'type': 'string', 'enum': ['success', 'fail', 'always']},
                    }
                }
            },
            'post_sync': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'type': {'type': 'string', 'enum': ['slack', 'webhook', 'email']},
                        'text': {'type': 'string'},
                        'url': {'type': 'string'},
                        'template': {'type': 'string'},
                        'headers': {'type': 'object'},
                        'to': {'type': 'string'},
                        'subject': {'type': 'string'},
                        'body': {'type': 'string'},
                        'on': {'type': 'string', 'enum': ['success', 'fail', 'always']},
                    }
                }
            }
        },
        'additionalProperties': False
    }
    examples = [
        {
            'hooks': {
                'pre_sync': [
                    {'type': 'slack', 'text': 'Sync starting for {provider}'},
                    {'type': 'webhook', 'url': 'https://example.com/hook', 'template': '{provider} sync started'}
                ],
                'post_sync': [
                    {'type': 'slack', 'on': 'success'},
                    {'type': 'email', 'to': 'ops@example.com', 'subject': 'Sync {provider}', 'body': 'count={count}', 'on': 'success'},
                    {'type': 'webhook', 'url': 'https://example.com/notify', 'headers': {'X-Token': 'abc'}, 'template': '{provider} done: {count}'}
                ]
            }
        }
    ]
    return {'schema': schema, 'examples': examples}


@app.post('/api/v1/admin/hooks/validate')
def validate_hooks(payload: dict = Body(...), admin_user=Depends(require_admin)):
    """Validate a hooks object for basic structure without external dependencies."""
    hooks = payload.get('hooks')
    errors = []
    if not isinstance(hooks, dict):
        return {'ok': False, 'errors': ['hooks must be an object']}
    pre = hooks.get('pre_sync', [])
    post = hooks.get('post_sync', [])
    if not isinstance(pre, list):
        errors.append('pre_sync must be an array')
    if not isinstance(post, list):
        errors.append('post_sync must be an array')

    def _validate_items(items, where: str):
        if not isinstance(items, list):
            return
        for idx, it in enumerate(items):
            if not isinstance(it, dict):
                errors.append(f'{where}[{idx}] must be an object')
                continue
            typ = str(it.get('type') or '').lower()
            if typ not in ('slack', 'webhook', 'email'):
                errors.append(f'{where}[{idx}].type must be one of slack|webhook|email')
                continue
            if 'on' in it:
                on = str(it.get('on') or '').lower()
                if on not in ('success', 'fail', 'always'):
                    errors.append(f'{where}[{idx}].on must be one of success|fail|always')
            if typ == 'webhook':
                if not it.get('url'):
                    errors.append(f'{where}[{idx}].url is required for webhook')
                if 'headers' in it and not isinstance(it.get('headers'), dict):
                    errors.append(f'{where}[{idx}].headers must be an object')
            if typ == 'email':
                for key in ('to', 'subject', 'body'):
                    if not it.get(key):
                        errors.append(f'{where}[{idx}].{key} is required for email')

    _validate_items(pre, 'pre_sync')
    _validate_items(post, 'post_sync')
    return {'ok': len(errors) == 0, 'errors': errors}


@app.post('/api/v1/admin/users/{user_id}/role')
def admin_set_role(user_id: int, payload: dict, admin_user=Depends(require_admin), db: Session = Depends(get_db)):
    role = payload.get('role')
    if role not in ['user', 'moderator', 'admin']:
        raise HTTPException(status_code=400, detail='invalid role')
    with transactional(db):
        user = db.query(models.User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail='user not found')
        user.role = role
        # include audit log in same transaction
        _log_change(admin_user.id if hasattr(admin_user, 'id') else None, 'user', user.id, 'set_role', {'role': role}, db=db)
        db.flush()
        return {'id': user.id, 'role': user.role}


def _log_change(actor_user_id, entity, entity_id, action, payload=None, *, db: Session):
    """
    Insert a ChangeLog record into the provided SQLAlchemy `db` session.

    This function requires the caller to pass an active Session (via
    FastAPI's `Depends(get_db)`) so that changelogs are written as part of the
    caller's transaction. It no longer creates its own SessionLocal.
    """
    cl = models.ChangeLog(user_id=actor_user_id, entity=entity, entity_id=entity_id, action=action, payload=json.dumps(payload or {}))
    db.add(cl)
    # caller is responsible for committing/refreshing
    return cl


# Testing-only endpoint: intentionally create-then-fail to assert transactional rollback in tests
@app.post('/api/v1/_test/create_then_fail')
def create_then_fail(payload: dict, db: Session = Depends(get_db)):
    """Create a user and then raise an error to ensure rollback occurs."""
    email = payload.get('email')
    if not email:
        raise HTTPException(status_code=400, detail='email required')
    try:
        with transactional(db, nested=False):
            u = models.User(email=email, display_name=payload.get('display_name'))
            db.add(u)
            db.flush()
            # write audit log in same transaction
            _log_change(None, 'user', None, 'create', {'email': email}, db=db)
            # simulate unexpected error but raise as HTTPException so TestClient returns 500
            raise HTTPException(status_code=500, detail='intentional failure for rollback test')
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        raise

# Basic user routes (demo)
@app.post('/api/v1/users')
def create_user(payload: dict, db: Session = Depends(get_db)):
    email = payload.get('email')
    if not email:
        raise HTTPException(status_code=400, detail='email required')
    with transactional(db, nested=False):
        user = models.User(email=email, display_name=payload.get('display_name'))
        db.add(user)
        db.flush()
        _log_change(None, 'user', None, 'create', {'email': email}, db=db)
        db.refresh(user)
        return {'id': user.id, 'email': user.email}


@app.get('/api/v1/integrations/{integration_id}/google/events')
def google_events(integration_id: int, db: Session = Depends(get_db)):
    """Demo endpoint: fetch upcoming Google Calendar events using stored access token.

    Note: For production you must handle token refresh, errors, and rate limits. This is a demo.
    """
    token = db.query(models.OAuthToken).filter_by(integration_id=integration_id).order_by(models.OAuthToken.id.desc()).first()
    if not token or not token.access_token:
        raise HTTPException(status_code=404, detail='no token found for integration')
    # Try to refresh token if needed (refresh flow is in oauth module)
    from .oauth import refresh_google_token_if_needed
    refreshed = refresh_google_token_if_needed(token, db=db)
    if refreshed:
        token = refreshed

    from .crypto import decrypt_text
    decrypted_access = decrypt_text(token.access_token)
    if not decrypted_access:
        raise HTTPException(status_code=500, detail='unable to decrypt access token')
    headers = {'Authorization': f'Bearer {decrypted_access}'}
    params = {'maxResults': 10, 'singleEvents': True, 'orderBy': 'startTime', 'timeMin': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    resp = requests.get('https://www.googleapis.com/calendar/v3/calendars/primary/events', headers=headers, params=params, timeout=10)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f'google api error: {resp.status_code}')
    return resp.json()


@app.get('/api/v1/integrations/{integration_id}/events_preview')
def events_preview(integration_id: int, db: Session = Depends(get_db)):
    integration = db.query(models.Integration).filter_by(id=integration_id).first()
    if not integration:
        raise HTTPException(status_code=404, detail='integration not found')
    token_row = db.query(models.OAuthToken).filter_by(integration_id=integration_id).order_by(models.OAuthToken.id.desc()).first()
    if not token_row:
        raise HTTPException(status_code=404, detail='no token')
    from .oauth import refresh_google_token_if_needed
    refreshed = refresh_google_token_if_needed(token_row, db=db)
    if refreshed:
        token_row = refreshed
    from .crypto import decrypt_text
    access = decrypt_text(token_row.access_token)
    if not access:
        raise HTTPException(status_code=500, detail='unable to decrypt')
    headers = {'Authorization': f'Bearer {access}'}
    params = {'maxResults': 50, 'singleEvents': True, 'orderBy': 'startTime', 'timeMin': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    resp = requests.get('https://www.googleapis.com/calendar/v3/calendars/primary/events', headers=headers, params=params, timeout=10)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail='google api error')
    items = resp.json().get('items', [])
    # Return light preview objects
    preview = [{
        'id': it.get('id'),
        'summary': it.get('summary'),
        'start': it.get('start'),
        'end': it.get('end')
    } for it in items]
    return {'preview': preview}


@app.post('/api/v1/guilds')
def create_guild(payload: dict = Body({}), db: Session = Depends(get_db)):
    name = payload.get('name')
    owner_id = payload.get('owner_id', 1)
    if not name:
        raise HTTPException(status_code=400, detail='name required')
    with transactional(db):
        g = models.Guild(name=name, description=payload.get('description'), owner_id=owner_id)
        db.add(g)
        db.flush()
        _log_change(owner_id, 'guild', None, 'create', {'name': name}, db=db)
        db.refresh(g)
        return {'id': g.id, 'name': g.name}


@app.get('/api/v1/guilds')
def list_guilds(db: Session = Depends(get_db)):
    rows = db.query(models.Guild).all()
    return [{'id': r.id, 'name': r.name, 'owner_id': r.owner_id} for r in rows]


@app.post('/api/v1/guilds/{guild_id}/members')
def add_guild_member(guild_id: int, payload: dict = Body({}), db: Session = Depends(get_db)):
    user_id = payload.get('user_id')
    role = payload.get('role', 'member')
    if not user_id:
        raise HTTPException(status_code=400, detail='user_id required')
    with transactional(db):
        gm = models.GuildMember(guild_id=guild_id, user_id=user_id, role=role)
        db.add(gm)
        db.flush()
        _log_change(user_id, 'guild_member', gm.id if getattr(gm, 'id', None) else None, 'add', {'guild_id': guild_id}, db=db)
        db.refresh(gm)
        return {'id': gm.id, 'guild_id': gm.guild_id, 'user_id': gm.user_id}


@app.get('/api/v1/guilds/{guild_id}/members')
def list_guild_members(guild_id: int, db: Session = Depends(get_db)):
    rows = db.query(models.GuildMember).filter_by(guild_id=guild_id).all()
    return [{'id': r.id, 'user_id': r.user_id, 'role': r.role} for r in rows]


@app.get('/api/v1/users/{user_id}/integrations')
def list_user_integrations(user_id: int, db: Session = Depends(get_db)):
    rows = db.query(models.Integration).filter_by(user_id=user_id).all()
    out = [
        {"id": r.id, "provider": r.provider, "external_id": r.external_id, "created_at": r.created_at.isoformat() if r.created_at else None}
        for r in rows
    ]
    return out


@app.get('/api/v1/integrations')
def list_integrations(db: Session = Depends(get_db)):
    rows = db.query(models.Integration).all()
    out = [
        {"id": r.id, "user_id": r.user_id, "provider": r.provider, "external_id": r.external_id, "created_at": r.created_at.isoformat() if r.created_at else None}
        for r in rows
    ]
    return out


@app.get('/api/v1/integrations/{integration_id}')
def get_integration(integration_id: int, request: Request = None, db: Session = Depends(get_db)):
    integ = db.query(models.Integration).filter_by(id=integration_id).first()
    if not integ:
        raise HTTPException(status_code=404, detail='integration not found')
    # require owner/admin
    from .rbac import require_owner_or_admin
    _ = require_owner_or_admin(integ.user_id)(request, db)
    return {
        'id': integ.id,
        'user_id': integ.user_id,
        'provider': integ.provider,
        'external_id': integ.external_id,
        'config': integ.config,
        'created_at': integ.created_at.isoformat() if integ.created_at else None
    }


@app.patch('/api/v1/integrations/{integration_id}')
def patch_integration(integration_id: int, payload: dict = Body(...), request: Request = None, db: Session = Depends(get_db)):
    integ = db.query(models.Integration).filter_by(id=integration_id).first()
    if not integ:
        raise HTTPException(status_code=404, detail='integration not found')
    from .rbac import require_owner_or_admin
    actor = require_owner_or_admin(integ.user_id)(request, db)
    cfg_patch = payload.get('config') or {}
    if not isinstance(cfg_patch, dict):
        raise HTTPException(status_code=400, detail='config must be an object')
    import json as _json
    cur = {}
    if integ.config:
        try:
            cur = _json.loads(integ.config)
        except Exception:
            cur = {}
    cur.update(cfg_patch)
    with transactional(db):
        integ.config = _json.dumps(cur)
        _log_change(actor.id if actor else None, 'integration', integ.id, 'update_config', cfg_patch, db=db)
        db.flush()
    return {'ok': True}


@app.delete('/api/v1/integrations/{integration_id}')
def delete_integration(integration_id: int, request: Request = None, db: Session = Depends(get_db)):
    row = db.query(models.Integration).filter_by(id=integration_id).first()
    if not row:
        raise HTTPException(status_code=404, detail='integration not found')

    # require owner or admin and capture actor
    from .rbac import require_owner_or_admin
    # call the returned dependency with request and injected db so get_current_user uses the same session
    actor = require_owner_or_admin(row.user_id)(request, db)

    with transactional(db):
        actor_id = actor.id if actor and hasattr(actor, 'id') else None
        # delete related oauth tokens first (if cascade isn't set)
        db.query(models.OAuthToken).filter_by(integration_id=row.id).delete(synchronize_session=False)
        db.delete(row)
        _log_change(actor_id, 'integration', row.id, 'delete', {}, db=db)
    return {'ok': True}


# Encrypted export/import (admin)
@app.get('/api/v1/admin/export')
def admin_export(admin_user=Depends(require_admin), db: Session = Depends(get_db)):
    data = {
        'users': [
            {'id': u.id, 'email': u.email, 'role': u.role, 'display_name': u.display_name}
            for u in db.query(models.User).all()
        ],
        'projects': [
            {'id': p.id, 'user_id': p.user_id, 'title': p.title, 'description': p.description}
            for p in db.query(models.Project).all()
        ],
        'habits': [
            {'id': h.id, 'user_id': h.user_id, 'project_id': h.project_id, 'title': h.title, 'notes': h.notes, 'cadence': h.cadence}
            for h in db.query(models.Habit).all()
        ],
        'logs': [
            {'id': l.id, 'habit_id': l.habit_id, 'user_id': l.user_id, 'action': l.action}
            for l in db.query(models.Log).all()
        ],
        'achievements': [
            {'id': a.id, 'user_id': a.user_id, 'name': a.name, 'description': a.description}
            for a in db.query(models.Achievement).all()
        ],
        'integrations': [
            {'id': i.id, 'user_id': i.user_id, 'provider': i.provider, 'external_id': i.external_id, 'config': i.config}
            for i in db.query(models.Integration).all()
        ],
        'oauth_tokens': [
            {'id': t.id, 'integration_id': t.integration_id, 'access_token': t.access_token, 'refresh_token': t.refresh_token, 'scope': t.scope, 'expires_at': t.expires_at}
            for t in db.query(models.OAuthToken).all()
        ],
        'integration_item_map': [
            {'id': m.id, 'integration_id': m.integration_id, 'external_id': m.external_id, 'entity_type': m.entity_type, 'entity_id': m.entity_id}
            for m in db.query(models.IntegrationItemMap).all()
        ],
    }
    from .crypto import encrypt_text
    blob = encrypt_text(json.dumps(data))
    return {'ciphertext': blob}


@app.post('/api/v1/admin/import')
def admin_import(payload: dict = Body(...), request: Request = None, db: Session = Depends(get_db)):
    # If the DB is empty (no users), allow bootstrap import without auth
    users_exist = db.query(models.User).count() > 0
    if users_exist:
        # Enforce admin when there are users present
        _ = require_admin(request, db)
    from .crypto import decrypt_text
    ciphertext = payload.get('ciphertext')
    if not ciphertext:
        raise HTTPException(status_code=400, detail='ciphertext required')
    try:
        data = json.loads(decrypt_text(ciphertext))
    except Exception:
        raise HTTPException(status_code=400, detail='invalid ciphertext')
    with transactional(db):
        # naive import: does not handle ID conflicts robustly; for demo purposes only
        for u in data.get('users', []):
            if not db.query(models.User).filter_by(id=u['id']).first():
                db.add(models.User(id=u['id'], email=u['email'], role=u.get('role'), display_name=u.get('display_name')))
        for p in data.get('projects', []):
            if not db.query(models.Project).filter_by(id=p['id']).first():
                db.add(models.Project(id=p['id'], user_id=p['user_id'], title=p['title'], description=p.get('description')))
        for h in data.get('habits', []):
            if not db.query(models.Habit).filter_by(id=h['id']).first():
                db.add(models.Habit(id=h['id'], user_id=h['user_id'], project_id=h.get('project_id'), title=h['title'], notes=h.get('notes'), cadence=h.get('cadence')))
        for l in data.get('logs', []):
            if not db.query(models.Log).filter_by(id=l['id']).first():
                db.add(models.Log(id=l['id'], habit_id=l.get('habit_id'), user_id=l['user_id'], action=l.get('action')))
        for a in data.get('achievements', []):
            if not db.query(models.Achievement).filter_by(id=a['id']).first():
                db.add(models.Achievement(id=a['id'], user_id=a['user_id'], name=a['name'], description=a.get('description')))
        for i in data.get('integrations', []):
            if not db.query(models.Integration).filter_by(id=i['id']).first():
                db.add(models.Integration(id=i['id'], user_id=i['user_id'], provider=i['provider'], external_id=i.get('external_id'), config=i.get('config')))
        for t in data.get('oauth_tokens', []):
            if not db.query(models.OAuthToken).filter_by(id=t['id']).first():
                db.add(models.OAuthToken(id=t['id'], integration_id=t['integration_id'], access_token=t.get('access_token'), refresh_token=t.get('refresh_token'), scope=t.get('scope'), expires_at=t.get('expires_at')))
        for m in data.get('integration_item_map', []):
            if not db.query(models.IntegrationItemMap).filter_by(id=m['id']).first():
                db.add(models.IntegrationItemMap(id=m['id'], integration_id=m['integration_id'], external_id=m['external_id'], entity_type=m['entity_type'], entity_id=m['entity_id']))
    return {'ok': True}


@app.post('/api/v1/integrations/{integration_id}/sync_to_habits')
def sync_integration_to_habits(integration_id: int, payload: dict = Body({}), request: Request = None, db: Session = Depends(get_db)):
    """Fetch events from the integration and create Habit + Log entries.

    Demo mapping: create a Habit per event with title 'Event: <summary>' and a Log entry.
    """
    # Use injected session `db` (FastAPI dependency) and participate in transaction.
    integration = db.query(models.Integration).filter_by(id=integration_id).first()
    if not integration:
        raise HTTPException(status_code=404, detail='integration not found')

    # require owner or admin and capture actor
    from .rbac import require_owner_or_admin
    # pass the injected `db` so get_current_user is called with a real Session
    actor = require_owner_or_admin(integration.user_id)(request, db)

    # Reuse token refresh + decrypt logic from oauth module; pass db so refresh participates in transaction
    token_row = db.query(models.OAuthToken).filter_by(integration_id=integration_id).order_by(models.OAuthToken.id.desc()).first()
    if not token_row:
        raise HTTPException(status_code=404, detail='no token found for integration')

    from .oauth import refresh_google_token_if_needed
    refreshed = refresh_google_token_if_needed(token_row, db=db)
    if refreshed:
        token_row = refreshed

    from .crypto import decrypt_text
    access = decrypt_text(token_row.access_token)
    if not access:
        raise HTTPException(status_code=500, detail='unable to decrypt access token')

    headers = {'Authorization': f'Bearer {access}'}
    params = {'maxResults': 25, 'singleEvents': True, 'orderBy': 'startTime', 'timeMin': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    resp = requests.get('https://www.googleapis.com/calendar/v3/calendars/primary/events', headers=headers, params=params, timeout=10)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail='google api error')
    events = resp.json().get('items', [])

    created = []
    with transactional(db):
        for ev in events:
            title = ev.get('summary') or 'Untitled Event'
            # Create habit and log within single transaction
            habit = models.Habit(project_id=None, user_id=integration.user_id, title=f'Event: {title}', notes=str(ev), cadence='once')
            db.add(habit)
            db.flush()  # ensure habit.id is available

            log = models.Log(habit_id=habit.id, user_id=integration.user_id, action='imported_event')
            db.add(log)
            created.append({'habit_id': habit.id, 'title': habit.title})

        # Audit log in same transaction
        actor_id = actor.id if actor and hasattr(actor, 'id') else None
        _log_change(actor_id, 'integration', integration.id, 'sync_to_habits', {'count': len(created)}, db=db)

    try:
        record_integration_sync(integration.provider or 'unknown', 'success')
    except Exception:
        pass
    return {'created': created, 'count': len(created)}


# Provider-specific webhook: Todoist with HMAC-SHA256 signature
@app.post('/api/v1/webhooks/todoist')
async def todoist_webhook(request: Request):
    secret = os.getenv('TODOIST_WEBHOOK_SECRET')
    if not secret:
        # If not configured, accept but mark as unverified
        q = get_queue()
        body = await request.body()
        if q:
            job = q.enqueue(example_job, {'provider': 'todoist', 'payload': body.decode('utf-8', 'ignore')})
            try:
                record_webhook('todoist', False)
            except Exception:
                pass
            return {'ok': True, 'queued': True, 'job_id': job.id, 'verified': False}
        try:
            record_webhook('todoist', False)
        except Exception:
            pass
        return {'ok': True, 'queued': False, 'verified': False}
    body = await request.body()
    hdr = request.headers.get('X-Todoist-Hmac-SHA256') or request.headers.get('x-todoist-hmac-sha256')
    if not hdr:
        raise HTTPException(status_code=403, detail='missing signature')
    digest = hmac.new(secret.encode('utf-8'), body, hashlib.sha256).digest()
    hexsig = digest.hex()
    b64sig = base64.b64encode(digest).decode('ascii')
    if hdr != hexsig and hdr != b64sig:
        raise HTTPException(status_code=403, detail='invalid signature')
    q = get_queue()
    if q:
        job = q.enqueue(example_job, {'provider': 'todoist', 'payload': body.decode('utf-8', 'ignore')})
        try:
            record_webhook('todoist', True)
        except Exception:
            pass
        return {'ok': True, 'queued': True, 'job_id': job.id, 'verified': True}
    try:
        record_webhook('todoist', True)
    except Exception:
        pass
    return {'ok': True, 'queued': False, 'verified': True}


# Minimal Todoist connect endpoint: store personal API token under integration
@app.post('/api/v1/integrations/todoist/connect')
def todoist_connect(payload: dict = Body(...), request: Request = None, db: Session = Depends(get_db)):
    user_id = payload.get('user_id')
    api_token = payload.get('api_token')
    if not user_id or not api_token:
        raise HTTPException(status_code=400, detail='user_id and api_token required')
    # Require current user matches or admin
    from .rbac import require_owner_or_admin
    actor = require_owner_or_admin(user_id)(request, db)
    with transactional(db):
        integ = models.Integration(user_id=user_id, provider='todoist', external_id=None, config=None)
        db.add(integ)
        db.flush()
        from .crypto import encrypt_text
        tok = models.OAuthToken(integration_id=integ.id, access_token=encrypt_text(api_token))
        db.add(tok)
        _log_change(actor.id if actor else None, 'integration', integ.id, 'connect_todoist', {}, db=db)
        db.refresh(integ)
        return {'id': integ.id, 'provider': integ.provider}


# Minimal GitHub connect endpoint: store PAT token under integration
@app.post('/api/v1/integrations/github/connect')
def github_connect(payload: dict = Body(...), request: Request = None, db: Session = Depends(get_db)):
    user_id = payload.get('user_id')
    pat_token = payload.get('token')
    if not user_id or not pat_token:
        raise HTTPException(status_code=400, detail='user_id and token required')
    from .rbac import require_owner_or_admin
    actor = require_owner_or_admin(user_id)(request, db)
    with transactional(db):
        integ = models.Integration(user_id=user_id, provider='github', external_id=None, config=None)
        db.add(integ)
        db.flush()
        from .crypto import encrypt_text
        tok = models.OAuthToken(integration_id=integ.id, access_token=encrypt_text(pat_token))
        db.add(tok)
        _log_change(actor.id if actor else None, 'integration', integ.id, 'connect_github', {}, db=db)
        db.refresh(integ)
        return {'id': integ.id, 'provider': integ.provider}


@app.post('/api/v1/integrations/{integration_id}/sync')
def trigger_integration_sync(integration_id: int, request: Request = None, db: Session = Depends(get_db)):
    integ = db.query(models.Integration).filter_by(id=integration_id).first()
    if not integ:
        raise HTTPException(status_code=404, detail='integration not found')
    # require owner/admin
    from .rbac import require_owner_or_admin
    _ = require_owner_or_admin(integ.user_id)(request, db)
    provider = integ.provider
    # enqueue background sync with retry/backoff
    job = enqueue_adapter_sync(provider, integration_id)
    if job:
        try:
            record_integration_sync(provider, 'queued')
            record_integration_sync_by_id(integration_id, 'queued')
        except Exception:
            pass
        try:
            log_job_event('enqueued', provider=provider, integration_id=integration_id, job_id=job.id)
        except Exception:
            pass
        return {'queued': True, 'job_id': job.id}
    # no queue -> run inline
    try:
        res = run_adapter_sync(provider, integration_id)
        try:
            record_integration_sync(provider, 'inline')
            record_integration_sync_by_id(integration_id, 'inline')
        except Exception:
            pass
        try:
            log_job_event('inline_done', provider=provider, integration_id=integration_id, result=res)
        except Exception:
            pass
        return {'queued': False, 'result': res}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post('/api/v1/webhooks/{provider}')
def webhook_receiver(provider: str, payload: dict = Body({}), request: Request = None):
    # Verify signatures per provider (omitted for brevity in demo)
    # Enqueue processing job or handle minimally
    q = get_queue()
    if q:
        job = q.enqueue(example_job, {'provider': provider, 'payload': payload})
        return {'ok': True, 'queued': True, 'job_id': job.id}
    return {'ok': True, 'queued': False}


# Slack integration: connect via incoming webhook
@app.post('/api/v1/integrations/slack/connect')
def slack_connect(payload: dict = Body(...), request: Request = None, db: Session = Depends(get_db)):
    user_id = payload.get('user_id')
    webhook_url = payload.get('webhook_url')
    if not user_id or not webhook_url:
        raise HTTPException(status_code=400, detail='user_id and webhook_url required')
    from .rbac import require_owner_or_admin
    actor = require_owner_or_admin(user_id)(request, db)
    with transactional(db):
        integ = models.Integration(user_id=user_id, provider='slack', external_id=None, config=None)
        db.add(integ)
        db.flush()
        from .crypto import encrypt_text
        tok = models.OAuthToken(integration_id=integ.id, access_token=encrypt_text(webhook_url))
        db.add(tok)
        _log_change(actor.id if actor else None, 'integration', integ.id, 'connect_slack', {}, db=db)
        db.refresh(integ)
        return {'id': integ.id, 'provider': integ.provider}


@app.post('/api/v1/integrations/{integration_id}/slack/test')
def slack_test_message(integration_id: int, request: Request = None, db: Session = Depends(get_db)):
    integ = db.query(models.Integration).filter_by(id=integration_id).first()
    if not integ or integ.provider != 'slack':
        raise HTTPException(status_code=404, detail='slack integration not found')
    from .rbac import require_owner_or_admin
    _ = require_owner_or_admin(integ.user_id)(request, db)
    # Use adapter to send a test message
    res = ADAPTERS['slack'].sync(db=db, integration_id=integration_id)
    return {'ok': True, 'result': res}
