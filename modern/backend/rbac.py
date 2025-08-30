from fastapi import HTTPException, Depends, Request
from auth import get_current_user
from db import get_db
from sqlalchemy.orm import Session


# Role hierarchy for comparisons
HIERARCHY = {'user': 1, 'moderator': 2, 'admin': 3}


def require_role(min_role: str):
    """FastAPI dependency that enforces a minimum role on the calling user.

    This dependency requires the `get_current_user` dependency which in turn
    requires an injected DB session via `get_db` to enforce strict session usage.
    """
    def _dep(request: Request, db: Session = Depends(get_db)):
        user = get_current_user(request, db=db)
        if HIERARCHY.get(user.role or 'user', 0) < HIERARCHY.get(min_role, 0):
            raise HTTPException(status_code=403, detail='insufficient role')
        return user
    return _dep


def require_admin(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db=db)
    if HIERARCHY.get(user.role or 'user', 0) < HIERARCHY.get('admin', 0):
        raise HTTPException(status_code=403, detail='admin required')
    return user


def require_owner_or_admin(resource_user_id: int):
    """Return a callable that can be used inline to check ownership/admin status.

    The returned callable expects a `Request` and an injected `db` (via Depends)
    so that `get_current_user` is always called with a proper session.
    """
    def _inner(request: Request = None, db: Session = Depends(get_db)):
        user = get_current_user(request, db=db)
        if user.id == resource_user_id or user.role == 'admin':
            return user
        raise HTTPException(status_code=403, detail='must be owner or admin')
    return _inner
