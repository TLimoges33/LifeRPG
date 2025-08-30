import os
import json
import importlib
from modern.backend import models


def test_export_import_roundtrip(client):
    # Login as admin
    r = client.post('/api/v1/auth/login', json={'email': 'admin@test', 'password': 'pass'})
    assert r.status_code == 200

    # Create some data directly in DB
    db = models.SessionLocal()
    try:
        u = models.User(email='u@test')
        db.add(u)
        db.flush()
        p = models.Project(user_id=u.id, title='P1')
        db.add(p)
        db.flush()
        h = models.Habit(user_id=u.id, project_id=p.id, title='H1')
        db.add(h)
        db.commit()
    finally:
        db.close()

    # Export
    exp = client.get('/api/v1/admin/export')
    assert exp.status_code == 200
    ciphertext = exp.json().get('ciphertext')
    assert ciphertext

    # Drop and recreate schema
    import modern.backend.models as m
    importlib.reload(m)
    m.Base.metadata.drop_all(bind=m.engine)
    m.Base.metadata.create_all(bind=m.engine)

    # Import
    imp = client.post('/api/v1/admin/import', json={'ciphertext': ciphertext})
    assert imp.status_code == 200

    # Verify user restored
    db2 = models.SessionLocal()
    try:
        assert db2.query(models.User).filter_by(email='u@test').first() is not None
    finally:
        db2.close()
