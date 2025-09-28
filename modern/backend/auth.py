import os
import time
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from passlib.hash import bcrypt
import jwt
import models
from db import get_db
from sqlalchemy.orm import Session
from config import settings
import secrets
from totp import generate_totp_secret, provisioning_uri, verify_totp, generate_recovery_codes, hash_recovery_codes, verify_and_consume_recovery_code
from schemas import LoginRequest, SignupRequest, TwoFAEnableRequest, TwoFADisableRequest
from security_monitor import log_login_failure, log_unauthorized_access

router = APIRouter()

# Secure JWT secret management - MUST be set in production
JWT_SECRET = os.getenv('LIFERPG_JWT_SECRET')
if not JWT_SECRET:
    if os.getenv('ENVIRONMENT') == 'production':
        raise RuntimeError("LIFERPG_JWT_SECRET environment variable is required in production")
    # Only allow fallback in development
    JWT_SECRET = secrets.token_urlsafe(64)
    print("WARNING: Using generated JWT secret for development. Set LIFERPG_JWT_SECRET in production!")

JWT_ALGO = 'HS256'
JWT_EXP_SECONDS = 60 * 60 * 24  # 1 day


def create_token(payload: dict) -> str:
    now = int(time.time())
    # Ensure 'sub' is a string (JWT libraries may expect string subject)
    if 'sub' in payload:
        payload = {**payload, 'sub': str(payload['sub'])}
    payload_out = {**payload, 'iat': now, 'exp': now + JWT_EXP_SECONDS}
    return jwt.encode(payload_out, JWT_SECRET, algorithm=JWT_ALGO)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except Exception:
        return {}


@router.post('/signup')
def signup(payload: SignupRequest, request: Request = None, db: Session = Depends(get_db)):
    email = payload.email
    password = payload.password
    existing = db.query(models.User).filter_by(email=email).first()
    if existing:
        raise HTTPException(status_code=400, detail='email exists')
    user = models.User(email=email, password_hash=bcrypt.hash(password), display_name=payload.display_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token({'sub': user.id})
    resp = JSONResponse({'id': user.id, 'email': user.email})
    # Default behavior: set main session cookie when no prior session
    if not request or (not request.cookies.get('session') and not request.headers.get('authorization')):
        resp.set_cookie('session', token, httponly=True, secure=settings.COOKIE_SECURE, samesite=settings.COOKIE_SAMESITE)
        # CSRF token cookie for double-submit pattern (non-HttpOnly so client JS can mirror header)
        csrf = secrets.token_urlsafe(32)
        resp.set_cookie(settings.CSRF_COOKIE_NAME, csrf, httponly=False, secure=settings.COOKIE_SECURE, samesite=settings.COOKIE_SAMESITE)
    else:
        # If a session already exists (e.g., admin creating a user), also emit an alternate session cookie
        # so follow-up flows (like 2FA setup) can target the newly created user without overwriting admin session.
        resp.set_cookie('session_alt', token, httponly=True, secure=settings.COOKIE_SECURE, samesite=settings.COOKIE_SAMESITE)
    return resp


@router.post('/login')
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email
    password = payload.password
    totp_code = payload.totp_code
    recovery_code = payload.recovery_code
    
    user = db.query(models.User).filter_by(email=email).first()
    if not user or not user.password_hash or not bcrypt.verify(password, user.password_hash):
        # Log failed login attempt
        log_login_failure(
            user_id=email,
            ip_address=request.client.host if request and request.client else "unknown",
            user_agent=request.headers.get("user-agent") if request else None
        )
        raise HTTPException(status_code=401, detail='invalid credentials')
    # If TOTP is enabled, require totp_code or recovery_code
    if getattr(user, 'totp_enabled', 0):
        ok = False
        if totp_code and user.totp_secret:
            ok = verify_totp(user.totp_secret, str(totp_code))
        if not ok and recovery_code and user.recovery_codes:
            # consume recovery code
            hashes = [h for h in (user.recovery_codes or '').split('\n') if h.strip()]
            used, remaining = verify_and_consume_recovery_code(hashes, str(recovery_code))
            if used:
                user.recovery_codes = '\n'.join(remaining)
                db.commit()
                ok = True
        if not ok:
            raise HTTPException(status_code=401, detail='2fa required')
    token = create_token({'sub': user.id})
    resp = JSONResponse({'id': user.id, 'email': user.email})
    resp.set_cookie('session', token, httponly=True, secure=settings.COOKIE_SECURE, samesite=settings.COOKIE_SAMESITE)
    csrf = secrets.token_urlsafe(32)
    resp.set_cookie(settings.CSRF_COOKIE_NAME, csrf, httponly=False, secure=settings.COOKIE_SECURE, samesite=settings.COOKIE_SAMESITE)
    return resp


@router.post('/2fa/setup')
def totp_setup(payload: dict = None, request: Request = None, db: Session = Depends(get_db)):
    """Begin TOTP setup, returning otpauth URI and recovery codes. Requires logged-in user.
    The caller must store the plaintext recovery codes client-side; only hashes are stored server-side.
    """
    user = get_current_user(request, db, prefer_alt_session=True)
    if getattr(user, 'totp_enabled', 0):
        raise HTTPException(status_code=400, detail='2fa already enabled')
    secret = generate_totp_secret()
    uri = provisioning_uri(secret, user.email)
    codes = generate_recovery_codes()
    hashes = hash_recovery_codes(codes)
    user.totp_secret = secret
    user.recovery_codes = '\n'.join(hashes)
    db.commit()
    return {'otpauth_uri': uri, 'recovery_codes': codes}


@router.get('/2fa/qr')
def totp_qr(request: Request = None, db: Session = Depends(get_db)):
    """Generate QR code for TOTP setup securely on server"""
    import qrcode
    import io
    import base64
    
    user = get_current_user(request, db, prefer_alt_session=True)
    
    # Check if user has a TOTP secret (setup in progress)
    if not user.totp_secret:
        raise HTTPException(status_code=400, detail='No TOTP setup in progress')
    
    otpauth_uri = provisioning_uri(user.totp_secret, user.email)
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(otpauth_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for JSON response
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    
    return {'qr_code': f'data:image/png;base64,{img_base64}'}


@router.post('/2fa/enable')
def totp_enable(payload: dict, request: Request = None, db: Session = Depends(get_db)):
    user = get_current_user(request, db, prefer_alt_session=True)
    code = (payload or {}).get('code')
    if not user.totp_secret:
        raise HTTPException(status_code=400, detail='no 2fa setup in progress')
    if not code or not verify_totp(user.totp_secret, str(code)):
        raise HTTPException(status_code=400, detail='invalid code')
    user.totp_enabled = 1
    db.commit()
    return {'ok': True}


@router.post('/2fa/disable')
def totp_disable(payload: dict, request: Request = None, db: Session = Depends(get_db)):
    user = get_current_user(request, db, prefer_alt_session=True)
    # Require current password and optionally a TOTP to disable
    password = (payload or {}).get('password')
    code = (payload or {}).get('code')
    if not password or not user.password_hash or not bcrypt.verify(password, user.password_hash):
        raise HTTPException(status_code=401, detail='invalid credentials')
    if user.totp_enabled and user.totp_secret and code and not verify_totp(user.totp_secret, str(code)):
        raise HTTPException(status_code=400, detail='invalid code')
    user.totp_enabled = 0
    user.totp_secret = None
    user.recovery_codes = None
    db.commit()
    return {'ok': True}


@router.post('/logout')
def logout():
    resp = JSONResponse({'ok': True})
    resp.delete_cookie('session')
    resp.delete_cookie('session_alt')
    resp.delete_cookie(settings.CSRF_COOKIE_NAME)
    return resp


def get_current_user(request: Request, db: Session = Depends(get_db), prefer_alt_session: bool = False):
    """Return the current user. Requires an injected DB session via Depends(get_db).

    This function intentionally does NOT create a temporary session. Callers must
    pass an active Session (via FastAPI dependency injection) to avoid accidental
    ad-hoc sessions.
    """
    # Support session cookie or Authorization: Bearer <token>
    token = None
    # Some flows (like signup-then-2FA) may provide an alternate session cookie for the newly created user.
    if prefer_alt_session:
        token = request.cookies.get('session_alt')
    if not token:
        token = request.cookies.get('session')
    if not token:
        auth_hdr = request.headers.get('authorization') or request.headers.get('Authorization')
        if auth_hdr and auth_hdr.lower().startswith('bearer '):
            token = auth_hdr.split(' ', 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail='not authenticated')
    data = decode_token(token)
    uid = data.get('sub')
    if not uid:
        raise HTTPException(status_code=401, detail='invalid token')
    # cast subject to int id
    try:
        uid = int(uid)
    except Exception:
        raise HTTPException(status_code=401, detail='invalid token')
    user = db.query(models.User).filter_by(id=uid).first()
    if not user:
        raise HTTPException(status_code=401, detail='user not found')
    return user


@router.get('/me')
def me(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return { 'id': user.id, 'email': user.email, 'role': user.role, 'display_name': user.display_name }


auth_router = router
