import os
from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth

router = APIRouter()

oauth = OAuth()

# Register provider with placeholders; read from env at runtime
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
    if 'google' not in oauth:
        return {'error': 'google oauth not configured'}
    token = await oauth.google.authorize_access_token(request)
    user = await oauth.google.parse_id_token(request, token)
    # token contains access_token and refresh_token; persist securely
    # For demo, return token info
    return {'token': token, 'user': user}
