from modern.backend import models


def test_integration_delete_logs_change(client):
    # create a normal user
    r = client.post('/api/v1/auth/signup', json={'email': 'intuser@test', 'password': 'p'})
    assert r.status_code == 200

    # find user id
    db = models.SessionLocal()
    try:
        user = db.query(models.User).filter_by(email='intuser@test').first()
        assert user is not None
        # create integration directly
        integ = models.Integration(user_id=user.id, provider='google', external_id='ext-1', config='{}')
        db.add(integ)
        db.commit()
        db.refresh(integ)
        integ_id = integ.id
    finally:
        db.close()

    # As admin (fixture), delete the integration
    resp = client.delete(f'/api/v1/integrations/{integ_id}')
    assert resp.status_code == 200

    # check changelog
    db = models.SessionLocal()
    try:
        cl = db.query(models.ChangeLog).filter_by(entity='integration', entity_id=integ_id, action='delete').first()
        assert cl is not None
    finally:
        db.close()
