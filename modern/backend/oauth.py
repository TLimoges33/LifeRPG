import os
import time
from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from . import models

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
