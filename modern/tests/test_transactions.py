import pytest
from modern.backend import models


def test_create_then_fail_rolls_back(client):
    # ensure no user with this email exists
    db = models.SessionLocal()
    try:
        before = db.query(models.User).filter_by(email='rollback@test').first()
        assert before is None
    finally:
        db.close()

    r = client.post('/api/v1/_test/create_then_fail', json={'email': 'rollback@test'})
    assert r.status_code == 500

    db = models.SessionLocal()
    try:
        after = db.query(models.User).filter_by(email='rollback@test').first()
        assert after is None
    finally:
        db.close()


def test_create_commits_when_no_error(client):
    # create via normal endpoint
    r = client.post('/api/v1/users', json={'email': 'commit@test'})
    assert r.status_code == 200
    data = r.json()
    assert data.get('email') == 'commit@test'

    db = models.SessionLocal()
    try:
        user = db.query(models.User).filter_by(email='commit@test').first()
        assert user is not None
    finally:
        db.close()
