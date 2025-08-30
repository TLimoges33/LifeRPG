import os
import hmac
import hashlib


class FakeJob:
    def __init__(self, id='job-1'):
        self.id = id


class FakeQueue:
    def enqueue(self, fn, payload):
        return FakeJob()


def test_todoist_webhook_enqueues_with_valid_signature(client, monkeypatch):
    os.environ['TODOIST_WEBHOOK_SECRET'] = 'secret'
    # Patch get_queue in app to return fake queue
    import modern.backend.app as app
    monkeypatch.setattr(app, 'get_queue', lambda: FakeQueue())

    body = b'{"event_name":"item:added"}'
    sig = hmac.new(b'secret', body, hashlib.sha256).hexdigest()
    r = client.post('/api/v1/webhooks/todoist', data=body, headers={'X-Todoist-Hmac-SHA256': sig, 'content-type': 'application/json'})
    assert r.status_code == 200
    j = r.json()
    assert j.get('ok') is True and j.get('queued') is True and j.get('verified') is True


def test_todoist_webhook_rejects_bad_signature(client):
    os.environ['TODOIST_WEBHOOK_SECRET'] = 'secret'
    r = client.post('/api/v1/webhooks/todoist', data=b'{}', headers={'X-Todoist-Hmac-SHA256': 'bad'})
    assert r.status_code == 403
