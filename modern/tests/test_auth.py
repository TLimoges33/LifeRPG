import pytest
from modern.backend.app import app


def test_signup_and_login(client):
    resp = client.post('/api/v1/auth/signup', json={'email':'user1@test','password':'secret'})
    assert resp.status_code == 200
    resp = client.post('/api/v1/auth/login', json={'email':'user1@test','password':'secret'})
    assert resp.status_code == 200
    assert 'session' in resp.cookies


def test_admin_set_role(client):
    # Login as admin (created in fixture)
    resp = client.post('/api/v1/auth/login', json={'email':'admin@test','password':'pass'})
    assert resp.status_code == 200
    # Set role of a user (create user first)
    r = client.post('/api/v1/auth/signup', json={'email':'tochange@test','password':'p'})
    assert r.status_code == 200
    # As admin, set role
    resp = client.post('/api/v1/admin/users/2/role', json={'role':'moderator'})
    assert resp.status_code == 200
    assert resp.json().get('role') == 'moderator'
