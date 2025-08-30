import json


class FakeResp:
    def __init__(self, status=200, data=None, headers=None):
        self.status_code = status
        self._data = data if data is not None else []
        self.headers = headers or {}

    def json(self):
        return self._data


def test_adapters_store_utc_z_suffix(client, monkeypatch):
    import modern.backend.models as models
    from modern.backend.adapters import ADAPTERS
    import requests
    db = models.SessionLocal()
    try:
        # Setup Todoist integration with token
        integ = models.Integration(user_id=1, provider='todoist', external_id=None, config=json.dumps({'todoist_full_fetch': False}))
        db.add(integ); db.flush()
        from modern.backend.crypto import encrypt_text
        db.add(models.OAuthToken(integration_id=integ.id, access_token=encrypt_text('tok')))
        db.flush()
        monkeypatch.setattr(requests, 'get', lambda *a, **k: FakeResp(200, []))
        ADAPTERS['todoist'].sync(db=db, integration_id=integ.id)
        db.refresh(integ)
        cfg = json.loads(integ.config or '{}')
        v = cfg.get('last_sync_at')
        assert v and isinstance(v, str) and v.endswith('Z')
        # parseable when replacing Z with +00:00
        from datetime import datetime
        datetime.fromisoformat(v.replace('Z','+00:00'))

        # Setup GitHub integration
        g = models.Integration(user_id=1, provider='github', external_id=None, config=json.dumps({}))
        db.add(g); db.flush()
        db.add(models.OAuthToken(integration_id=g.id, access_token=encrypt_text('pat')))
        db.flush()
        monkeypatch.setattr(requests, 'get', lambda *a, **k: FakeResp(200, [], headers={}))
        ADAPTERS['github'].sync(db=db, integration_id=g.id)
        db.refresh(g)
        cfg2 = json.loads(g.config or '{}')
        v2 = cfg2.get('github_since')
        assert v2 and isinstance(v2, str) and v2.endswith('Z')
        from datetime import datetime
        datetime.fromisoformat(v2.replace('Z','+00:00'))
    finally:
        db.close()
