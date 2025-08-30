import os
import json
import types


class FakeJob:
    def __init__(self, id='job-1'):
        self.id = id


class FakeQueue:
    def enqueue(self, fn, *args, **kwargs):
        return FakeJob()


def test_todoist_connect_and_sync_inline(client, monkeypatch):
    # Ensure no queue so it runs inline
    import modern.backend.app as app
    monkeypatch.setattr(app, 'enqueue_adapter_sync', lambda provider, integration_id: None)
    # stub run_adapter_sync to avoid network
    monkeypatch.setattr(app, 'run_adapter_sync', lambda provider, integration_id: {"ok": True, "count": 2})

    # create user (id assumed 1 by default DB state; but ensure)
    r = client.post('/api/v1/users', json={'email': 'u@example.com'})
    uid = r.json()['id']

    # login to get a token cookie
    client.post('/api/v1/auth/signup', json={'email': 'u@example.com', 'password': 'pw'})
    # connect todoist (store token)
    r = client.post('/api/v1/integrations/todoist/connect', json={'user_id': uid, 'api_token': 'x'})
    assert r.status_code == 200
    integ_id = r.json()['id']
    # trigger sync (inline)
    r = client.post(f'/api/v1/integrations/{integ_id}/sync')
    assert r.status_code == 200
    data = r.json()
    assert data['queued'] is False and data['result']['ok'] is True


def test_github_connect_and_sync_enqueued(client, monkeypatch):
    # Patch queue to simulate enqueue
    import modern.backend.app as app
    monkeypatch.setattr(app, 'enqueue_adapter_sync', lambda provider, integration_id: types.SimpleNamespace(id='job-123'))

    # create user and login
    client.post('/api/v1/users', json={'email': 'g@example.com'})
    client.post('/api/v1/auth/signup', json={'email': 'g@example.com', 'password': 'pw'})

    # connect github
    r = client.post('/api/v1/integrations/github/connect', json={'user_id': 1, 'token': 'pat'})
    assert r.status_code == 200
    integ_id = r.json()['id']

    # trigger sync -> should be queued
    r = client.post(f'/api/v1/integrations/{integ_id}/sync')
    assert r.status_code == 200
    j = r.json()
    assert j['queued'] is True and 'job_id' in j
