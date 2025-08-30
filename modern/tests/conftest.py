import os
import tempfile
import pytest
from fastapi.testclient import TestClient
import importlib

# Do not import app or models at module import time; tests will set DATABASE_URL per-fixture

@pytest.fixture(scope='function')
def client():
    # create a secure temporary sqlite file per test
    tf = tempfile.NamedTemporaryFile(prefix='liferpg_test_', suffix='.db', delete=False)
    tf.close()
    dbpath = tf.name
    os.environ['DATABASE_URL'] = f'sqlite:///{dbpath}'
    # import models after DATABASE_URL is set so engine binds to the test DB
    import modern.backend.models as models
    importlib.reload(models)
    # initialize DB
    models.init_db()
    # import app after models so app uses the correct models/engine
    import modern.backend.app as app
    importlib.reload(app)
    client = TestClient(app.app)
    # create admin user
    resp = client.post('/api/v1/auth/signup', json={'email':'admin@test','password':'pass'})
    # promote to admin directly in DB for tests
    db = models.SessionLocal()
    u = db.query(models.User).filter_by(email='admin@test').first()
    u.role = 'admin'
    db.commit()
    db.close()
    yield client
    # cleanup
    try:
        os.remove(dbpath)
    except Exception:
        pass
