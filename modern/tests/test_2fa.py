import importlib

def test_totp_setup_enable_and_login_with_totp(client):
    # Sign up a user with password
    r = client.post('/api/v1/auth/signup', json={'email': '2fa@example.com', 'password': 'pw'} )
    assert r.status_code == 200

    # Begin setup
    r = client.post('/api/v1/auth/2fa/setup')
    assert r.status_code == 200
    data = r.json()
    assert 'otpauth_uri' in data and 'recovery_codes' in data
    assert len(data['recovery_codes']) >= 8

    # Extract current TOTP from secret by reading from DB
    import modern.backend.models as models
    db = models.SessionLocal()
    u = db.query(models.User).filter_by(email='2fa@example.com').first()
    assert u and u.totp_secret

    # compute a valid code
    import pyotp
    code = pyotp.TOTP(u.totp_secret).now()

    # Enable 2FA
    r2 = client.post('/api/v1/auth/2fa/enable', json={'code': code})
    assert r2.status_code == 200

    # Logout to clear session
    client.post('/api/v1/auth/logout')

    # Login must now include totp_code
    r3 = client.post('/api/v1/auth/login', json={'email': '2fa@example.com', 'password': 'pw'})
    assert r3.status_code == 401
    r4 = client.post('/api/v1/auth/login', json={'email': '2fa@example.com', 'password': 'pw', 'totp_code': code})
    assert r4.status_code == 200


def test_login_with_recovery_code(client):
    # new user
    r = client.post('/api/v1/auth/signup', json={'email': '2fa2@example.com', 'password': 'pw'} )
    assert r.status_code == 200

    # setup 2fa to generate recovery codes
    r = client.post('/api/v1/auth/2fa/setup')
    codes = r.json()['recovery_codes']

    # enable 2fa
    import modern.backend.models as models
    db = models.SessionLocal()
    u = db.query(models.User).filter_by(email='2fa2@example.com').first()
    import pyotp
    code = pyotp.TOTP(u.totp_secret).now()
    client.post('/api/v1/auth/2fa/enable', json={'code': code})

    # logout
    client.post('/api/v1/auth/logout')

    # login using one recovery code
    r2 = client.post('/api/v1/auth/login', json={'email': '2fa2@example.com', 'password': 'pw', 'recovery_code': codes[0]})
    assert r2.status_code == 200

    # recovery code should be consumed; using again should fail
    client.post('/api/v1/auth/logout')
    r3 = client.post('/api/v1/auth/login', json={'email': '2fa2@example.com', 'password': 'pw', 'recovery_code': codes[0]})
    assert r3.status_code == 401
