import os
import time
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from passlib.hash import bcrypt
import jwt
from . import models

router = APIRouter()

JWT_SECRET = os.getenv('LIFERPG_JWT_SECRET', 'dev_jwt_secret_change')
JWT_ALGO = 'HS256'
JWT_EXP_SECONDS = 60 * 60 * 24  # 1 day


def create_token(payload: dict) -> str:
    now = int(time.time())
    payload_out = {**payload, 'iat': now, 'exp': now + JWT_EXP_SECONDS}
    return jwt.encode(payload_out, JWT_SECRET, algorithm=JWT_ALGO)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except Exception:
        return {}


@router.post('/signup')
def signup(payload: dict):
    email = payload.get('email')
    password = payload.get('password')
    if not email or not password:
        raise HTTPException(status_code=400, detail='email and password required')
    db = models.SessionLocal()
    try:
        existing = db.query(models.User).filter_by(email=email).first()
        if existing:
            raise HTTPException(status_code=400, detail='email exists')
        user = models.User(email=email, password_hash=bcrypt.hash(password), display_name=payload.get('display_name'))
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_token({'sub': user.id})
        resp = JSONResponse({'id': user.id, 'email': user.email})
        resp.set_cookie('session', token, httponly=True, secure=False, samesite='lax')
        return resp
    finally:
        db.close()


@router.post('/login')
def login(payload: dict):
    email = payload.get('email')
    password = payload.get('password')
    if not email or not password:
        raise HTTPException(status_code=400, detail='email and password required')
    db = models.SessionLocal()
    try:
        user = db.query(models.User).filter_by(email=email).first()
        if not user or not user.password_hash or not bcrypt.verify(password, user.password_hash):
            raise HTTPException(status_code=401, detail='invalid credentials')
        token = create_token({'sub': user.id})
        resp = JSONResponse({'id': user.id, 'email': user.email})
        resp.set_cookie('session', token, httponly=True, secure=False, samesite='lax')
        return resp
    finally:
        db.close()


@router.post('/logout')
def logout():
    resp = JSONResponse({'ok': True})
    resp.delete_cookie('session')
    return resp


def get_current_user(request: Request):
    token = request.cookies.get('session')
    if not token:
        raise HTTPException(status_code=401, detail='not authenticated')
    data = decode_token(token)
    uid = data.get('sub')
    if not uid:
        raise HTTPException(status_code=401, detail='invalid token')
    db = models.SessionLocal()
    try:
        user = db.query(models.User).filter_by(id=uid).first()
        if not user:
            raise HTTPException(status_code=401, detail='user not found')
        return user
    finally:
        db.close()
