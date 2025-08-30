import json
from modern.backend import models


def test_admin_set_role_creates_changelog(client):
    # create a user to modify
    r = client.post('/api/v1/auth/signup', json={'email': 'audituser@test', 'password': 'p'})
    assert r.status_code == 200

    # as admin (fixture provides admin session), set role
    resp = client.post('/api/v1/admin/users/2/role', json={'role': 'moderator'})
    assert resp.status_code == 200

    # check change log was created
    db = models.SessionLocal()
    try:
        row = db.query(models.ChangeLog).order_by(models.ChangeLog.id.desc()).first()
        assert row is not None
        assert row.entity == 'user'
        assert row.action == 'set_role'
        payload = json.loads(row.payload or '{}')
        assert payload.get('role') == 'moderator'
    finally:
        db.close()
