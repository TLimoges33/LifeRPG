from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from . import models
from .oauth import router as oauth_router
import os

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
