from modern.backend import models
from modern.backend.app import _log_change
import importlib


def test_log_change_requires_db(client):
    # reload models bound to test DB
    import modern.backend.models as models
    importlib.reload(models)
    import modern.backend.app as app
    importlib.reload(app)

    db = models.SessionLocal()
    try:
        # should add a ChangeLog record when passed a real db
        _log_change(None, 'test', None, 'action', {'a':1}, db=db)
        db.commit()
        row = db.query(models.ChangeLog).order_by(models.ChangeLog.id.desc()).first()
        assert row is not None
    finally:
        db.close()
