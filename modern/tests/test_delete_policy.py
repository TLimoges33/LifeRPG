import json


class FakeResp:
    def __init__(self, status=200, data=None, headers=None):
        self.status_code = status
        self._data = data if data is not None else []
        self.headers = headers or {}

    def json(self):
        return self._data


def _setup_integration(db, user_id: int, provider: str, token: str, config: dict = None):
    import modern.backend.models as models
    integ = models.Integration(user_id=user_id, provider=provider, external_id=None, config=json.dumps(config or {}))
    db.add(integ)
    db.flush()
    from modern.backend.crypto import encrypt_text
    db.add(models.OAuthToken(integration_id=integ.id, access_token=encrypt_text(token)))
    db.flush()
    return integ


def _create_mapped_habit(db, integration_id: int, external_id: str = 'ext-1', title='Old Title'):
    import modern.backend.models as models
    h = models.Habit(user_id=1, title=title, cadence='once', notes='test', status='active')
    db.add(h)
    db.flush()
    db.add(models.IntegrationItemMap(integration_id=integration_id, external_id=external_id, entity_type='habit', entity_id=h.id))
    db.flush()
    return h


def test_todoist_archive_vs_delete_full_sync(client, monkeypatch):
    import modern.backend.models as models
    import requests
    from modern.backend.adapters import ADAPTERS
    from modern.backend.config import settings
    db = models.SessionLocal()
    try:
        # Archive policy
        integ = _setup_integration(db, 1, 'todoist', 'tok', config={'todoist_full_fetch': True})
        h = _create_mapped_habit(db, integ.id, external_id='gone', title='Goner')
        monkeypatch.setattr(requests, 'get', lambda *a, **k: FakeResp(200, []))
        settings.INTEGRATION_CLOSE_MODE = 'archive'
        ADAPTERS['todoist'].sync(db=db, integration_id=integ.id)
        db.refresh(h)
        assert h.status == 'archived'

        # Delete policy
        integ2 = _setup_integration(db, 1, 'todoist', 'tok', config={'todoist_full_fetch': True})
        h2 = _create_mapped_habit(db, integ2.id, external_id='gone2', title='Goner2')
        settings.INTEGRATION_CLOSE_MODE = 'delete'
        ADAPTERS['todoist'].sync(db=db, integration_id=integ2.id)
        assert db.query(models.Habit).filter_by(id=h2.id).first() is None
    finally:
        db.close()


def test_todoist_no_delete_on_incremental(client, monkeypatch):
    import modern.backend.models as models
    import requests
    from modern.backend.adapters import ADAPTERS
    from modern.backend.config import settings
    db = models.SessionLocal()
    try:
        integ = _setup_integration(db, 1, 'todoist', 'tok', config={'todoist_full_fetch': False})
        h = _create_mapped_habit(db, integ.id, external_id='stay', title='Stay Put')
        monkeypatch.setattr(requests, 'get', lambda *a, **k: FakeResp(200, []))
        settings.INTEGRATION_CLOSE_MODE = 'delete'
        ADAPTERS['todoist'].sync(db=db, integration_id=integ.id)
        db.refresh(h)
        assert h.status == 'active'
    finally:
        db.close()


def test_github_delete_only_on_full_vs_incremental(client, monkeypatch):
    import modern.backend.models as models
    import requests
    from modern.backend.adapters import ADAPTERS
    from modern.backend.config import settings
    db = models.SessionLocal()
    try:
        # Incremental: since set -> no delete
        integ_inc = _setup_integration(db, 1, 'github', 'pat', config={'github_since': '2025-08-28T00:00:00Z'})
        h_inc = _create_mapped_habit(db, integ_inc.id, external_id='999', title='GH Stay')
        def fake_get(url, headers=None, params=None, timeout=10):
            return FakeResp(200, [], headers={})
        monkeypatch.setattr(requests, 'get', fake_get)
        settings.INTEGRATION_CLOSE_MODE = 'delete'
        ADAPTERS['github'].sync(db=db, integration_id=integ_inc.id)
        assert db.query(models.Habit).filter_by(id=h_inc.id).first() is not None

        # Full: since not set -> delete
        integ_full = _setup_integration(db, 1, 'github', 'pat', config={})
        h_full = _create_mapped_habit(db, integ_full.id, external_id='1000', title='GH Gone')
        ADAPTERS['github'].sync(db=db, integration_id=integ_full.id)
        assert db.query(models.Habit).filter_by(id=h_full.id).first() is None
    finally:
        db.close()
