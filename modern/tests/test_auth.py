import pytest
from fastapi.testclient import TestClient
from modern.backend.app import app

client = TestClient(app)

def test_signup_and_login():
    resp = client.post('/api/v1/auth/signup', json={'email':'test@example.com','password':'secret'})
    assert resp.status_code == 200
    resp = client.post('/api/v1/auth/login', json={'email':'test@example.com','password':'secret'})
    assert resp.status_code == 200
    assert 'session' in resp.cookies
*** End Patch
