from fastapi import HTTPException, Depends, Request
from .auth import get_current_user


# Role hierarchy for comparisons
HIERARCHY = {'user': 1, 'moderator': 2, 'admin': 3}


def require_role(min_role: str):
    """FastAPI dependency that enforces a minimum role on the calling user."""
    def _dep(user=Depends(get_current_user)):
        if HIERARCHY.get(user.role or 'user', 0) < HIERARCHY.get(min_role, 0):
            raise HTTPException(status_code=403, detail='insufficient role')
        return user
    return _dep


def require_admin(user=Depends(get_current_user)):
    if HIERARCHY.get(user.role or 'user', 0) < HIERARCHY.get('admin'):
        raise HTTPException(status_code=403, detail='admin required')
    return user


def require_owner_or_admin(resource_user_id: int):
    """Return a callable that can be used inline to check ownership/admin status.

    Note: FastAPI path param injection into dependency factories is complex; for
    simplicity endpoints can call this helper with the resource owner id.
    """
    def _inner(request: Request = None):
        user = get_current_user(request)
        if user.id == resource_user_id or user.role == 'admin':
            return user
        raise HTTPException(status_code=403, detail='must be owner or admin')
    return _inner
