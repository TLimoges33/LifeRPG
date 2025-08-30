import json
import os

def test_email_hook_console_transport(client, monkeypatch):
    # Force console transport
    monkeypatch.setenv('LIFERPG_EMAIL_TRANSPORT', 'console')
    # Force inline execution (no RQ)
    monkeypatch.setattr('modern.backend.app.get_queue', lambda: None, raising=False)
    # Import models after client fixture initialized DB
    from modern.backend import models
    # Create a dummy integration with an EmailHook in post_sync
    db = models.SessionLocal()
    try:
        integ = models.Integration(user_id=1, provider='slack', external_id=None, config=json.dumps({
            'hooks': {
                'pre_sync': [],
                'post_sync': [
                    { 'type': 'email', 'to': 'ops@example.com', 'subject': 'Sync {provider}', 'body': 'count={count}', 'on': 'success' }
                ]
            }
        }))
        db.add(integ)
        db.commit()
        db.refresh(integ)
    finally:
        db.close()
    # Trigger sync enqueue inline path by calling /api/v1/integrations/{id}/sync with no RQ (queue not running in tests)
    resp = client.post(f'/api/v1/integrations/{integ.id}/sync')
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('queued') is False
    # We can't easily assert email delivery; success here is the inline path completed without error
