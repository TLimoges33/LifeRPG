from contextlib import contextmanager
from sqlalchemy.orm import Session


@contextmanager
def transactional(session: Session, nested: bool = True):
    """
    Context manager for a transactional unit-of-work.

    If nested is True, uses session.begin_nested() to create a SAVEPOINT when
    needed; otherwise uses session.begin(). Caller is responsible for providing
    a session (e.g. from `get_db`).
    """
    if nested:
        tx = session.begin_nested()
    else:
        tx = session.begin()
    try:
        with tx:
            yield session
    except Exception:
        # ensure the session is rolled back explicitly
        try:
            session.rollback()
        except Exception:
            pass
        raise
