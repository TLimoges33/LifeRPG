import os
import time
from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from . import models
import requests
from typing import Optional

router = APIRouter()
oauth = OAuth()

# Load config from env at runtime
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
BASE_URL = os.getenv('BASE_URL', 'http://localhost:8000')

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile https://www.googleapis.com/auth/calendar.events'}
    )


@router.get('/oauth/google/login')
async def google_login(request: Request):
    if 'google' not in oauth:
        return {'error': 'google oauth not configured; set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET'}
    redirect_uri = BASE_URL + '/api/v1/oauth/google/callback'
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get('/oauth/google/callback')
async def google_callback(request: Request):
    """Handle Google's OAuth callback, persist Integration and OAuthToken records.

    This demo stores access/refresh tokens associated to a newly created `Integration` for
    the (demo) user. In a real app, you'd associate the integration with the authenticated
    user and secure storage for tokens.
    """
    if 'google' not in oauth:
        return {'error': 'google oauth not configured'}

    token = await oauth.google.authorize_access_token(request)
    # Try to get userinfo (sub/email) from id_token or userinfo endpoint
    userinfo = None
    try:
        userinfo = await oauth.google.parse_id_token(request, token)
    except Exception:
        # fallback: try userinfo endpoint
        try:
            resp = await oauth.google.get('userinfo', token=token)
            userinfo = resp.json()
        except Exception:
            userinfo = {}

    # Persist integration + token into DB (demo uses `user_id` query param or 1)
    db = models.SessionLocal()
    try:
        # For demo, allow passing ?user_id= to associate the integration
        qs = dict(request.query_params)
        user_id = int(qs.get('user_id')) if qs.get('user_id') else 1

        # Create or reuse an Integration row for this user+provider
        ext_id = userinfo.get('sub') or userinfo.get('id') or None
        integration = db.query(models.Integration).filter_by(user_id=user_id, provider='google').first()
        if not integration:
            integration = models.Integration(user_id=user_id, provider='google', external_id=ext_id, config='{}')
            db.add(integration)
            db.commit()
            db.refresh(integration)

            # Persist token (single latest token demo). Encrypt tokens at rest.
            from .crypto import encrypt_text

            expires_at = None
            if token.get('expires_in'):
                expires_at = int(time.time()) + int(token.get('expires_in'))

        oauth_token = models.OAuthToken(
                integration_id=integration.id,
                access_token=encrypt_text(token.get('access_token') or ''),
                refresh_token=encrypt_text(token.get('refresh_token') or ''),
                scope=token.get('scope'),
                expires_at=expires_at
            )
        db.add(oauth_token)
        db.commit()

        return {'ok': True, 'integration_id': integration.id, 'token_saved': bool(oauth_token.id)}
    finally:
        db.close()


def _decrypt_token(db_token_encrypted: str) -> str:
    from .crypto import decrypt_text
    return decrypt_text(db_token_encrypted)


def refresh_google_token_if_needed(oauth_token_row: models.OAuthToken) -> Optional[models.OAuthToken]:
    """Refresh Google's access token using refresh_token if expired or near expiry.

    Returns updated OAuthToken row (new DB row) or None on failure.
    """
    # If not expired, return the same
    now = int(time.time())
    if oauth_token_row.expires_at and oauth_token_row.expires_at > now + 30:
        return oauth_token_row

    refresh_token = _decrypt_token(oauth_token_row.refresh_token)
    if not refresh_token:
        return None

    # Use Google's token endpoint to refresh
    token_url = 'https://oauth2.googleapis.com/token'
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    if not client_id or not client_secret:
        return None

    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    try:
        resp = requests.post(token_url, data=data, timeout=10)
        if resp.status_code != 200:
            return None
        t = resp.json()
        # Persist new token
        from .crypto import encrypt_text
        db = models.SessionLocal()
        try:
            new_expires = None
            if t.get('expires_in'):
                new_expires = int(time.time()) + int(t.get('expires_in'))
            new_row = models.OAuthToken(
                integration_id=oauth_token_row.integration_id,
                access_token=encrypt_text(t.get('access_token') or ''),
                refresh_token=encrypt_text(t.get('refresh_token') or refresh_token),
                scope=t.get('scope') or oauth_token_row.scope,
                expires_at=new_expires
            )
            db.add(new_row)
            db.commit()
            db.refresh(new_row)
            return new_row
        finally:
            db.close()
    except Exception:
        return None
