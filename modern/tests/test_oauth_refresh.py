import time
import pytest
import importlib

# Do not import models or oauth at module level; tests must reload them after
# the `client` fixture sets DATABASE_URL so engines bind to the temp DB.


class DummyResp:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data


# Note: DB is initialized by the `client` fixture in tests/conftest.py


def test_refresh_with_temp_session(client, monkeypatch):
    # ensure we use the test DB created by the `client` fixture
    import modern.backend.models as models
    importlib.reload(models)
    import modern.backend.oauth as oauth
    importlib.reload(oauth)
    refresh_google_token_if_needed = oauth.refresh_google_token_if_needed

    db = models.SessionLocal()
    try:
        integration = models.Integration(user_id=1, provider='google', external_id='ext1', config='{}')
        db.add(integration)
        db.commit()
        db.refresh(integration)

        token_row = models.OAuthToken(integration_id=integration.id, access_token='old', refresh_token='enc_refresh', scope='read', expires_at=1)
        db.add(token_row)
        db.commit()
        db.refresh(token_row)

        def fake_post(url, data=None, timeout=10):
            return DummyResp(200, {'access_token': 'new_access', 'refresh_token': 'new_refresh', 'expires_in': 3600, 'scope': 'read'})

        monkeypatch.setattr('modern.backend.oauth.requests.post', fake_post)
        # ensure client id/secret are set so helper proceeds
        monkeypatch.setenv('GOOGLE_CLIENT_ID', 'test_client')
        monkeypatch.setenv('GOOGLE_CLIENT_SECRET', 'test_secret')

        # call helper with injected db (tests should pass a real session)
        new_row = refresh_google_token_if_needed(token_row, db=db)
        assert new_row is not None
        assert new_row.access_token != token_row.access_token
    finally:
        db.close()


def test_refresh_with_injected_session(client, monkeypatch):
    # ensure we use the test DB created by the `client` fixture
    import modern.backend.models as models
    importlib.reload(models)
    import modern.backend.oauth as oauth
    importlib.reload(oauth)
    refresh_google_token_if_needed = oauth.refresh_google_token_if_needed

    db = models.SessionLocal()
    try:
        integration = models.Integration(user_id=1, provider='google', external_id='ext2', config='{}')
        db.add(integration)
        db.commit()
        db.refresh(integration)

        token_row = models.OAuthToken(integration_id=integration.id, access_token='old2', refresh_token='enc_refresh2', scope='read', expires_at=1)
        db.add(token_row)
        db.commit()
        db.refresh(token_row)

        def fake_post(url, data=None, timeout=10):
            return DummyResp(200, {'access_token': 'new_access2', 'refresh_token': 'new_refresh2', 'expires_in': 3600, 'scope': 'read'})

        monkeypatch.setattr('modern.backend.oauth.requests.post', fake_post)
        monkeypatch.setenv('GOOGLE_CLIENT_ID', 'test_client')
        monkeypatch.setenv('GOOGLE_CLIENT_SECRET', 'test_secret')

        new_row = refresh_google_token_if_needed(token_row, db=db)
        assert new_row is not None
        assert new_row.access_token != token_row.access_token
    finally:
        db.close()
