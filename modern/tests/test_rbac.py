from modern.backend import models


def test_require_owner_or_admin_blocks_other_users(client):
    # create two users
    client.post('/api/v1/auth/signup', json={'email': 'owner@test', 'password': 'p'})
    client.post('/api/v1/auth/signup', json={'email': 'other@test', 'password': 'p'})

    db = models.SessionLocal()
    try:
        owner = db.query(models.User).filter_by(email='owner@test').first()
        other = db.query(models.User).filter_by(email='other@test').first()
        # create integration for owner
        integ = models.Integration(user_id=owner.id, provider='google', external_id='o1', config='{}')
        db.add(integ)
        db.commit(); db.refresh(integ)
        integ_id = integ.id
    finally:
        db.close()

    # login as 'other' and try to delete integration (should be 403)
    client.post('/api/v1/auth/login', json={'email': 'other@test', 'password': 'p'})
    resp = client.delete(f'/api/v1/integrations/{integ_id}')
    assert resp.status_code in (401, 403)

