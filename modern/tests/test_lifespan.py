from modern.tests.conftest import client as _c

# Basic sanity: the client fixture creates a test DB and app startup should
# initialize tables; this test simply uses the client to create a user.

def test_startup_initializes_db(client):
    r = client.post('/api/v1/auth/signup', json={'email': 'life@test', 'password': 'p'})
    assert r.status_code == 200
