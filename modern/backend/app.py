from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from . import models
from .oauth import router as oauth_router
from .auth import router as auth_router, get_current_user
import os
import requests
import time
from fastapi import Body

app = FastAPI(title='LifeRPG Modern Backend')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv('FRONTEND_ORIGIN', 'http://localhost:5173')],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# HTTPS enforcement middleware (for production behind a proxy, check X-Forwarded-Proto)
@app.middleware('http')
async def https_redirect(request, call_next):
    if os.getenv('FORCE_HTTPS', 'false').lower() == 'true':
        proto = request.headers.get('x-forwarded-proto', request.url.scheme)
        if proto != 'https':
            from starlette.responses import RedirectResponse
            url = request.url.replace(scheme='https')
            return RedirectResponse(str(url))
    return await call_next(request)

@app.on_event('startup')
def startup_event():
    models.init_db()

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.get('/api/v1/hello')
def hello():
    return {'message': 'Hello from LifeRPG modern backend (FastAPI)'}

app.include_router(oauth_router, prefix='/api/v1')
app.include_router(auth_router, prefix='/api/v1/auth')


from .rbac import require_admin


@app.get('/api/v1/admin/users')
def admin_list_users(admin_user=Depends(require_admin)):
    # placeholder; will be replaced with require_admin dependency
    db = models.SessionLocal()
    try:
        rows = db.query(models.User).all()
        return [{'id': r.id, 'email': r.email, 'role': r.role} for r in rows]
    finally:
        db.close()


@app.post('/api/v1/admin/users/{user_id}/role')
def admin_set_role(user_id: int, payload: dict, admin_user=Depends(require_admin)):
    role = payload.get('role')
    if role not in ['user', 'moderator', 'admin']:
        raise HTTPException(status_code=400, detail='invalid role')
    db = models.SessionLocal()
    try:
        user = db.query(models.User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail='user not found')
        user.role = role
        db.commit()
        return {'id': user.id, 'role': user.role}
    finally:
        db.close()

# Basic user routes (demo)
@app.post('/api/v1/users')
def create_user(payload: dict):
    db = models.SessionLocal()
    email = payload.get('email')
    if not email:
        raise HTTPException(status_code=400, detail='email required')
    user = models.User(email=email, display_name=payload.get('display_name'))
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return {'id': user.id, 'email': user.email}


@app.get('/api/v1/integrations/{integration_id}/google/events')
def google_events(integration_id: int):
    """Demo endpoint: fetch upcoming Google Calendar events using stored access token.

    Note: For production you must handle token refresh, errors, and rate limits. This is a demo.
    """
    db = models.SessionLocal()
    try:
        token = db.query(models.OAuthToken).filter_by(integration_id=integration_id).order_by(models.OAuthToken.id.desc()).first()
        if not token or not token.access_token:
            raise HTTPException(status_code=404, detail='no token found for integration')
        # Try to refresh token if needed (refresh flow is in oauth module)
        from .oauth import refresh_google_token_if_needed
        refreshed = refresh_google_token_if_needed(token)
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
    finally:
        db.close()


@app.get('/api/v1/integrations/{integration_id}/events_preview')
def events_preview(integration_id: int):
    db = models.SessionLocal()
    try:
        integration = db.query(models.Integration).filter_by(id=integration_id).first()
        if not integration:
            raise HTTPException(status_code=404, detail='integration not found')
        token_row = db.query(models.OAuthToken).filter_by(integration_id=integration_id).order_by(models.OAuthToken.id.desc()).first()
        if not token_row:
            raise HTTPException(status_code=404, detail='no token')
        from .oauth import refresh_google_token_if_needed
        refreshed = refresh_google_token_if_needed(token_row)
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
    finally:
        db.close()


@app.post('/api/v1/guilds')
def create_guild(payload: dict = Body({})):
    name = payload.get('name')
    owner_id = payload.get('owner_id', 1)
    if not name:
        raise HTTPException(status_code=400, detail='name required')
    db = models.SessionLocal()
    try:
        g = models.Guild(name=name, description=payload.get('description'), owner_id=owner_id)
        db.add(g)
        db.commit()
        db.refresh(g)
        return {'id': g.id, 'name': g.name}
    finally:
        db.close()


@app.get('/api/v1/guilds')
def list_guilds():
    db = models.SessionLocal()
    try:
        rows = db.query(models.Guild).all()
        return [{'id': r.id, 'name': r.name, 'owner_id': r.owner_id} for r in rows]
    finally:
        db.close()


@app.post('/api/v1/guilds/{guild_id}/members')
def add_guild_member(guild_id: int, payload: dict = Body({})):
    user_id = payload.get('user_id')
    role = payload.get('role', 'member')
    if not user_id:
        raise HTTPException(status_code=400, detail='user_id required')
    db = models.SessionLocal()
    try:
        gm = models.GuildMember(guild_id=guild_id, user_id=user_id, role=role)
        db.add(gm)
        db.commit()
        db.refresh(gm)
        return {'id': gm.id, 'guild_id': gm.guild_id, 'user_id': gm.user_id}
    finally:
        db.close()


@app.get('/api/v1/guilds/{guild_id}/members')
def list_guild_members(guild_id: int):
    db = models.SessionLocal()
    try:
        rows = db.query(models.GuildMember).filter_by(guild_id=guild_id).all()
        return [{'id': r.id, 'user_id': r.user_id, 'role': r.role} for r in rows]
    finally:
        db.close()


@app.get('/api/v1/users/{user_id}/integrations')
def list_user_integrations(user_id: int):
    db = models.SessionLocal()
    try:
        rows = db.query(models.Integration).filter_by(user_id=user_id).all()
        out = [
            {"id": r.id, "provider": r.provider, "external_id": r.external_id, "created_at": r.created_at.isoformat() if r.created_at else None}
            for r in rows
        ]
        return out
    finally:
        db.close()


@app.get('/api/v1/integrations')
def list_integrations():
    db = models.SessionLocal()
    try:
        rows = db.query(models.Integration).all()
        out = [
            {"id": r.id, "user_id": r.user_id, "provider": r.provider, "external_id": r.external_id, "created_at": r.created_at.isoformat() if r.created_at else None}
            for r in rows
        ]
        return out
    finally:
        db.close()


@app.delete('/api/v1/integrations/{integration_id}')
def delete_integration(integration_id: int, request=None):
    db = models.SessionLocal()
    try:
        row = db.query(models.Integration).filter_by(id=integration_id).first()
        if not row:
            raise HTTPException(status_code=404, detail='integration not found')
    # require owner or admin
    from .rbac import require_owner_or_admin
    require_owner_or_admin(row.user_id)(request)
    db.delete(row)
        db.commit()
        return {'ok': True}
    finally:
        db.close()


@app.post('/api/v1/integrations/{integration_id}/sync_to_habits')
def sync_integration_to_habits(integration_id: int, payload: dict = Body({})):
    """Fetch events from the integration and create Habit + Log entries.

    Demo mapping: create a Habit per event with title 'Event: <summary>' and a Log entry.
    """
    db = models.SessionLocal()
    try:
        integration = db.query(models.Integration).filter_by(id=integration_id).first()
        if not integration:
            raise HTTPException(status_code=404, detail='integration not found')

    # require owner or admin
    from .rbac import require_owner_or_admin
    require_owner_or_admin(integration.user_id)(None)
    # Fetch events via existing events endpoint logic
        # Reuse token refresh + decrypt logic from oauth module
        token_row = db.query(models.OAuthToken).filter_by(integration_id=integration_id).order_by(models.OAuthToken.id.desc()).first()
        if not token_row:
            raise HTTPException(status_code=404, detail='no token found for integration')

        from .oauth import refresh_google_token_if_needed
        refreshed = refresh_google_token_if_needed(token_row)
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
        for ev in events:
            title = ev.get('summary') or 'Untitled Event'
            # Create habit and log
            habit = models.Habit(project_id=None, user_id=integration.user_id, title=f'Event: {title}', notes=str(ev), cadence='once')
            db.add(habit)
            db.commit()
            db.refresh(habit)

            log = models.Log(habit_id=habit.id, user_id=integration.user_id, action='imported_event')
            db.add(log)
            db.commit()
            created.append({'habit_id': habit.id, 'title': habit.title})

        return {'created': created, 'count': len(created)}
    finally:
        db.close()
