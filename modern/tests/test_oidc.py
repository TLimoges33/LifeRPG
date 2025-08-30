import os
import json
import time
import importlib
import pytest

# These tests simulate OIDC flows by overriding environment and mocking the Authlib client methods

@pytest.fixture
def oidc_app_client(monkeypatch):
    # Minimal env for one provider "testidp"
    os.environ['OIDC_PROVIDERS'] = json.dumps({
        'testidp': {
            'issuer': 'https://example-idp.test',
            'client_id': 'cid',
            'client_secret': 'csec',
            'scope': 'openid email profile'
        }
    })
    os.environ['BASE_URL'] = 'http://test'

    # Import app fresh
    import modern.backend.models as models
    importlib.reload(models)
    models.init_db()
    import modern.backend.app as app
    importlib.reload(app)

    client = app.app.test_client() if hasattr(app.app, 'test_client') else None
    if client is None:
        from fastapi.testclient import TestClient
        client = TestClient(app.app)

    return client


def test_oidc_state_expiry(monkeypatch, oidc_app_client):
    client = oidc_app_client

    # Mock out OAuth client to avoid real redirects and code exchange
    from modern.backend import oauth as oauth_mod

    class DummyClient:
        async def authorize_redirect(self, request, redirect_uri, **kwargs):
            # Simulate redirect: return a dummy response
            from starlette.responses import JSONResponse
            return JSONResponse({'redirect': redirect_uri, 'state': kwargs.get('state')})

        async def authorize_access_token(self, request, code_verifier=None):
            raise Exception('should not be called in expiry test')

    oauth_mod._ensure_registered('testidp')
    setattr(oauth_mod.oauth, 'testidp', DummyClient())

    # Start login to create state
    r = client.get('/api/v1/auth/oidc/testidp/login')
    assert r.status_code == 200
    data = r.json()
    state = data['state']

    # Expire the state by directly updating DB
    import modern.backend.models as models
    db = models.SessionLocal()
    rec = db.query(models.OIDCLoginState).filter_by(state=state).first()
    from datetime import datetime, timedelta, timezone
    rec.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()

    # Callback with expired state should 400
    r2 = client.get(f'/api/v1/auth/oidc/callback?state={state}&code=abc')
    assert r2.status_code == 400


def test_oidc_callback_flow(monkeypatch, oidc_app_client):
    client = oidc_app_client

    from modern.backend import oauth as oauth_mod

    class DummyClient:
        async def authorize_redirect(self, request, redirect_uri, **kwargs):
            from starlette.responses import JSONResponse
            return JSONResponse({'redirect': redirect_uri, 'state': kwargs.get('state')})

        async def authorize_access_token(self, request, code_verifier=None):
            return {'access_token': 'at', 'id_token': 'idt'}

        async def parse_id_token(self, request, token):
            return {'email': 'oidcuser@example.com', 'name': 'OIDC User'}

    oauth_mod._ensure_registered('testidp')
    setattr(oauth_mod.oauth, 'testidp', DummyClient())

    # Start login, capture state
    r = client.get('/api/v1/auth/oidc/testidp/login')
    assert r.status_code == 200
    state = r.json()['state']

    # Callback simulating IdP
    r2 = client.get(f'/api/v1/auth/oidc/callback?state={state}&code=abc')
    assert r2.status_code == 200
    # Should set session cookie
    assert 'session=' in r2.headers.get('set-cookie', '')

    # Logout should clear cookies and attempt RP logout URL (will fallback to JSON)
    r3 = client.post('/api/v1/auth/oidc/logout')
    assert r3.status_code in (200, 307)
