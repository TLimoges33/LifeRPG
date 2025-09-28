import os
import time
from typing import Optional

import os
import time
from typing import Optional

from fastapi import APIRouter, Request, Depends, HTTPException
from authlib.integrations.starlette_client import OAuth
from sqlalchemy.orm import Session
import requests

import models
from db import get_db
from transaction import transactional

router = APIRouter()
oauth = OAuth()

# Load config from env at runtime
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
BASE_URL = os.getenv('BASE_URL', 'http://localhost:8000')
OIDC_STATE_MODE = os.getenv('OIDC_STATE_MODE', 'db').strip().lower()  # 'db' | 'jwt'
OIDC_STATE_SECRET = os.getenv('OIDC_STATE_SECRET')  # fallback to JWT secret below if not set
OIDC_VALIDATE_CLAIMS = os.getenv('OIDC_VALIDATE_CLAIMS', 'false').strip().lower() in ('1','true','yes','on')

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known-openid-configuration',
        client_kwargs={'scope': 'openid email profile https://www.googleapis.com/auth/calendar.events'},
    )


@router.get('/oauth/google/login')
async def google_login(request: Request):
    if 'google' not in oauth:
        return {'error': 'google oauth not configured; set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET'}
    redirect_uri = BASE_URL + '/api/v1/oauth/google/callback'
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get('/oauth/google/callback')
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google's OAuth callback and persist Integration + OAuthToken rows.

    Associates integration with `user_id` query param (or 1) and stores encrypted tokens.
    """
    if 'google' not in oauth:
        return {'error': 'google oauth not configured'}

    token = await oauth.google.authorize_access_token(request)
    userinfo = None
    try:
        userinfo = await oauth.google.parse_id_token(request, token)
    except Exception:
        try:
            resp = await oauth.google.get('userinfo', token=token)
            userinfo = resp.json()
        except Exception:
            userinfo = {}

    qs = dict(request.query_params)
    user_id = int(qs.get('user_id')) if qs.get('user_id') else 1

    ext_id = userinfo.get('sub') or userinfo.get('id') or None

    from .crypto import encrypt_text

    expires_at = None
    if token.get('expires_in'):
        expires_at = int(time.time()) + int(token.get('expires_in'))

    # persist integration + token in a transaction so audit logs can participate
    with transactional(db):
        integration = db.query(models.Integration).filter_by(user_id=user_id, provider='google').first()
        if not integration:
            integration = models.Integration(user_id=user_id, provider='google', external_id=ext_id, config='{}')
            db.add(integration)
            db.flush()
            db.refresh(integration)

        oauth_token = models.OAuthToken(
            integration_id=integration.id,
            access_token=encrypt_text(token.get('access_token') or ''),
            refresh_token=encrypt_text(token.get('refresh_token') or ''),
            scope=token.get('scope'),
            expires_at=expires_at,
        )
        db.add(oauth_token)
        db.flush()
        db.refresh(oauth_token)

    return {'ok': True, 'integration_id': integration.id, 'token_saved': bool(oauth_token.id)}


# --- Generic OIDC with PKCE (multi-provider) ---
BASE_URL = os.getenv('BASE_URL', 'http://localhost:8000')

def _load_provider_configs():
    """Load provider configs from env JSON OIDC_PROVIDERS or legacy single-provider vars."""
    import json
    raw = os.getenv('OIDC_PROVIDERS')
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    # Legacy single provider
    issuer = os.getenv('OIDC_ISSUER')
    client_id = os.getenv('OIDC_CLIENT_ID')
    client_secret = os.getenv('OIDC_CLIENT_SECRET')
    scope = os.getenv('OIDC_SCOPE', 'openid email profile')
    if issuer and client_id:
        return {'oidc': {'issuer': issuer, 'client_id': client_id, 'client_secret': client_secret, 'scope': scope}}
    return {}


def _ensure_registered(provider: str):
    cfgs = _load_provider_configs()
    # Already registered as an attribute on the OAuth registry
    if hasattr(oauth, provider):
        return provider in cfgs or provider == 'google'
    if provider in cfgs:
        info = cfgs[provider]
        oauth.register(
            name=provider,
            client_id=info.get('client_id'),
            client_secret=info.get('client_secret'),
            server_metadata_url=f"{info.get('issuer').rstrip('/')}/.well-known/openid-configuration",
            client_kwargs={'scope': info.get('scope', 'openid email profile')},
            code_challenge_method='S256',
        )
        return True
    return False


@router.get('/auth/oidc/providers')
def list_oidc_providers():
    return {'providers': list(_load_provider_configs().keys())}


@router.get('/auth/oidc/{provider}/login')
async def oidc_login_provider(provider: str, request: Request, db: Session = Depends(get_db)):
    if not _ensure_registered(provider):
        raise HTTPException(status_code=400, detail='OIDC provider not configured')
    redirect_uri = BASE_URL + '/api/v1/auth/oidc/callback'
    # Create PKCE params; Authlib can generate code_verifier if not provided; we'll track state+verifier
    from authlib.oauth2.rfc7636 import create_s256_code_challenge
    import secrets
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = create_s256_code_challenge(code_verifier)
    # generate state
    state = secrets.token_urlsafe(32)
    exp = int(time.time()) + 600
    # Two modes: DB-backed or signed JWT state
    if OIDC_STATE_MODE == 'db':
        exp_dt = __import__('datetime').datetime.fromtimestamp(exp, __import__('datetime').timezone.utc)
        s = models.OIDCLoginState(state=state, provider=provider, code_verifier=code_verifier, expires_at=exp_dt)
        db.add(s)
        db.commit()
        state_out = state
    else:
        import jwt as pyjwt
        from .auth import JWT_SECRET as DEFAULT_SECRET
        secret = OIDC_STATE_SECRET or DEFAULT_SECRET
        payload = {'pv': provider, 'cv': code_verifier, 'exp': exp, 'iat': int(time.time())}
        state_out = pyjwt.encode(payload, secret, algorithm='HS256')
    # Use authorize_redirect with extra PKCE params
    client = getattr(oauth, provider)
    return await client.authorize_redirect(
        request,
        redirect_uri,
        code_challenge=code_challenge,
        code_challenge_method='S256',
        state=state_out,
    )


@router.get('/auth/oidc/callback')
async def oidc_callback(request: Request, db: Session = Depends(get_db)):
    params = dict(request.query_params)
    state = params.get('state')
    if not state:
        raise HTTPException(status_code=400, detail='missing state')
    rec = None
    provider = None
    code_verifier = None
    # Try DB mode first (back-compat)
    if OIDC_STATE_MODE == 'db':
        rec = db.query(models.OIDCLoginState).filter_by(state=state).first()
        if not rec:
            raise HTTPException(status_code=400, detail='invalid state')
        provider = rec.provider
        code_verifier = rec.code_verifier
    else:
        # JWT state
        import jwt as pyjwt
        from .auth import JWT_SECRET as DEFAULT_SECRET
        secret = OIDC_STATE_SECRET or DEFAULT_SECRET
        try:
            data = pyjwt.decode(state, secret, algorithms=['HS256'])
            provider = data.get('pv')
            code_verifier = data.get('cv')
            if not provider or not code_verifier:
                raise Exception('invalid')
        except Exception:
            raise HTTPException(status_code=400, detail='invalid state')
    # Optional expiration check (handle naive vs aware datetimes)
    from datetime import datetime, timezone
    if rec.expires_at:
        exp_at = rec.expires_at
        if getattr(exp_at, 'tzinfo', None) is None:
            exp_at = exp_at.replace(tzinfo=timezone.utc)
        if exp_at < datetime.now(timezone.utc):
            # Cleanup stale state and reject
            try:
                db.delete(rec)
                db.commit()
            except Exception:
                pass
            raise HTTPException(status_code=400, detail='state expired')

    # Exchange code for tokens using stored code_verifier
    # Ensure client is registered for the stored provider
    if not _ensure_registered(provider):
        raise HTTPException(status_code=400, detail='OIDC provider not configured')
    client = getattr(oauth, provider)
    try:
        token = await client.authorize_access_token(request, code_verifier=code_verifier)
    except Exception:
        raise HTTPException(status_code=401, detail='token exchange failed')

    # Get userinfo via ID token or userinfo endpoint
    userinfo = None
    try:
        userinfo = await client.parse_id_token(request, token)
    except Exception:
        try:
            resp = await client.get('userinfo', token=token)
            userinfo = resp.json()
        except Exception:
            userinfo = {}

    # Optional audience/issuer extra validation
    if OIDC_VALIDATE_CLAIMS:
        try:
            # claims may be in parsed userinfo or in raw id_token
            claims = userinfo or {}
            idt = token.get('id_token') if isinstance(token, dict) else None
            iss_expected = None
            aud_expected = None
            cfgs = _load_provider_configs()
            info = cfgs.get(provider) or {}
            iss_expected = info.get('issuer')
            aud_expected = info.get('client_id')
            if idt:
                import jwt as pyjwt
                # don't verify signature again here; Authlib already did. We just parse claims.
                try:
                    claims = pyjwt.decode(idt, options={'verify_signature': False})
                except Exception:
                    claims = claims or {}
            if iss_expected and claims.get('iss') and claims.get('iss') != iss_expected:
                raise HTTPException(status_code=401, detail='issuer mismatch')
            aud = claims.get('aud')
            if aud_expected and aud:
                if isinstance(aud, str) and aud != aud_expected:
                    raise HTTPException(status_code=401, detail='audience mismatch')
                if isinstance(aud, (list, tuple)) and aud_expected not in aud:
                    raise HTTPException(status_code=401, detail='audience mismatch')
        except HTTPException:
            raise
        except Exception:
            # be conservative: if validation requested but we cannot evaluate, reject
            raise HTTPException(status_code=401, detail='claim validation failed')

    email = userinfo.get('email') or userinfo.get('preferred_username')
    if not email:
        raise HTTPException(status_code=400, detail='email not provided by provider')

    # Upsert user and create app session
    user = db.query(models.User).filter_by(email=email).first()
    if not user:
        user = models.User(email=email, display_name=userinfo.get('name'))
        db.add(user)
        db.flush()
        db.refresh(user)

    # cleanup state
    if rec is not None:
        try:
            db.delete(rec)
            db.commit()
        except Exception:
            pass

    # Issue app session cookie
    from .auth import create_token
    app_token = create_token({'sub': user.id})
    from fastapi.responses import JSONResponse
    resp = JSONResponse({'id': user.id, 'email': user.email})
    from .config import settings as cfg
    # set cookies
    resp.set_cookie('session', app_token, httponly=True, secure=cfg.COOKIE_SECURE, samesite=cfg.COOKIE_SAMESITE)
    import secrets as _secrets
    csrf = _secrets.token_urlsafe(32)
    resp.set_cookie(cfg.CSRF_COOKIE_NAME, csrf, httponly=False, secure=cfg.COOKIE_SECURE, samesite=cfg.COOKIE_SAMESITE)
    # store provider and id_token for RP-initiated logout
    id_token = token.get('id_token') if isinstance(token, dict) else None
    if id_token:
        resp.set_cookie('oidc_id_token', id_token, httponly=True, secure=cfg.COOKIE_SECURE, samesite=cfg.COOKIE_SAMESITE)
    resp.set_cookie('oidc_provider', provider, httponly=True, secure=cfg.COOKIE_SECURE, samesite=cfg.COOKIE_SAMESITE)
    return resp


@router.post('/auth/oidc/logout')
async def oidc_logout(request: Request):
    """Logout locally and, if supported, redirect to the IdP end_session endpoint (RP-initiated logout)."""
    from fastapi.responses import JSONResponse, RedirectResponse
    provider = request.cookies.get('oidc_provider')
    id_token = request.cookies.get('oidc_id_token')
    # Clear local cookies
    from .config import settings as cfg
    resp: JSONResponse | RedirectResponse
    end_session = None
    if provider and _ensure_registered(provider):
        client = getattr(oauth, provider)
        try:
            # ensure metadata loaded
            meta = await client.load_server_metadata()
        except Exception:
            meta = getattr(client, 'server_metadata', {}) or {}
        end_session = (meta or {}).get('end_session_endpoint') or (meta or {}).get('end_session_endpoint_url')
    if end_session and id_token:
        post_logout = BASE_URL + '/api/v1/auth/oidc/logout/callback'
        url = f"{end_session}?id_token_hint={id_token}&post_logout_redirect_uri={post_logout}"
        resp = RedirectResponse(url, status_code=307)
    else:
        resp = JSONResponse({'ok': True, 'logged_out': True})
    # clear cookies
    resp.delete_cookie('session')
    resp.delete_cookie('oidc_id_token')
    resp.delete_cookie('oidc_provider')
    try:
        # also clear csrf cookie if present
        from .config import settings as cfg2
        resp.delete_cookie(cfg2.CSRF_COOKIE_NAME)
    except Exception:
        pass
    return resp


@router.get('/auth/oidc/logout/callback')
def oidc_logout_callback():
    return {'ok': True, 'logout': 'complete'}


def _decrypt_token(db_token_encrypted: str) -> str:
    from .crypto import decrypt_text

    return decrypt_text(db_token_encrypted)


def refresh_google_token_if_needed(token_row: models.OAuthToken, db: Session) -> Optional[models.OAuthToken]:
    """Refresh Google's access token using refresh_token; return new OAuthToken row or None.

    This helper requires an active SQLAlchemy `db` Session so it can participate in
    the caller's transaction. It no longer creates or commits its own session.
    """
    # still valid
    if token_row.expires_at and token_row.expires_at > int(time.time()):
        return None
    if not token_row.refresh_token:
        return None

    token_url = 'https://oauth2.googleapis.com/token'
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    if not client_id or not client_secret:
        return None

    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': _decrypt_token(token_row.refresh_token),
    }

    try:
        resp = requests.post(token_url, data=data, timeout=10)
        if resp.status_code != 200:
            return None
        t = resp.json()
        from .crypto import encrypt_text

        new_expires = None
        if t.get('expires_in'):
            new_expires = int(time.time()) + int(t.get('expires_in'))

        new_row = models.OAuthToken(
            integration_id=token_row.integration_id,
            access_token=encrypt_text(t.get('access_token') or ''),
            refresh_token=encrypt_text(t.get('refresh_token') or _decrypt_token(token_row.refresh_token)),
            scope=t.get('scope') or token_row.scope,
            expires_at=new_expires,
        )
        db.add(new_row)
        # caller controls commit/flush/refresh; flush so caller can see id if needed
        db.flush()
        db.refresh(new_row)
        return new_row
    except Exception:
        return None


oauth_router = router

