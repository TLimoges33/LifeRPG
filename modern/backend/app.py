from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from . import models
from .oauth import router as oauth_router
import os
import requests
import time

app = FastAPI(title='LifeRPG Modern Backend')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv('FRONTEND_ORIGIN', 'http://localhost:5173')],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

        headers = {'Authorization': f'Bearer {token.access_token}'}
        params = {'maxResults': 10, 'singleEvents': True, 'orderBy': 'startTime', 'timeMin': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
        resp = requests.get('https://www.googleapis.com/calendar/v3/calendars/primary/events', headers=headers, params=params, timeout=10)
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f'google api error: {resp.status_code}')
        return resp.json()
    finally:
        db.close()
