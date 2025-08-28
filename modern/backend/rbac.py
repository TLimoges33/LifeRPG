from fastapi import HTTPException
from .auth import get_current_user
from . import models


def require_role(min_role: str):
    # Simple role hierarchy
    hierarchy = {'user': 1, 'moderator': 2, 'admin': 3}
    def _inner(request=None):
        user = get_current_user(request)
        if hierarchy.get(user.role, 0) < hierarchy.get(min_role, 0):
            raise HTTPException(status_code=403, detail='insufficient role')
        return user
    return _inner


def require_owner_or_admin(resource_user_id: int):
    def _inner(request=None):
        user = get_current_user(request)
        if user.id == resource_user_id or user.role == 'admin':
            return user
        raise HTTPException(status_code=403, detail='must be owner or admin')
    return _inner
