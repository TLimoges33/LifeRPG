from modern.backend import models
import json


def test_sync_to_habits_creates_changelog(client, monkeypatch):
    # prepare a user and an integration with a fake oauth token
    resp = client.post('/api/v1/auth/signup', json={'email': 'syncuser@test', 'password': 'p'})
    assert resp.status_code == 200

    db = models.SessionLocal()
    try:
        user = db.query(models.User).filter_by(email='syncuser@test').first()
        integ = models.Integration(user_id=user.id, provider='google', external_id='s1', config='{}')
        db.add(integ); db.commit(); db.refresh(integ)
        integ_id = integ.id
        # add a fake OAuthToken with an encrypted dummy access token
        from modern.backend.crypto import encrypt_text
        tok = models.OAuthToken(integration_id=integ_id, access_token=encrypt_text('dummy'), refresh_token=encrypt_text('dummy'))
        db.add(tok); db.commit(); db.refresh(tok)
        tok_id = tok.id
    finally:
        db.close()

    # monkeypatch requests.get to return a fake events payload
    class FakeResp:
        def __init__(self, data):
            self._data = data
            self.status_code = 200
        def json(self):
            return self._data

    def fake_get(url, headers=None, params=None, timeout=None):
        return FakeResp({'items': [{'id': 'e1', 'summary': 'Test Event', 'start': {'dateTime': '2025-01-01T10:00:00Z'}}]})

    monkeypatch.setattr('requests.get', fake_get)

    # ensure refresh logic is bypassed by monkeypatching refresh function to return same
    # call sync endpoint
    # make sure the client is acting as admin (fixture created admin user with session)
    client.post('/api/v1/auth/login', json={'email': 'admin@test', 'password': 'pass'})

    r = client.post(f'/api/v1/integrations/{integ_id}/sync_to_habits')
    assert r.status_code == 200

    # check changelog
    db = models.SessionLocal()
    try:
        cl = db.query(models.ChangeLog).filter_by(entity='integration', entity_id=integ_id, action='sync_to_habits').first()
        assert cl is not None
        payload = json.loads(cl.payload or '{}')
        assert payload.get('count') == 1
    finally:
        db.close()
