"""
Centralized authorization middleware for API endpoints
"""
from functools import wraps
from fastapi import HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import models
from db import get_db
from auth import get_current_user


class Permission:
    """Permission constants"""
    READ_HABITS = "read:habits"
    WRITE_HABITS = "write:habits"
    READ_PROJECTS = "read:projects"
    WRITE_PROJECTS = "write:projects"
    READ_ANALYTICS = "read:analytics"
    READ_USERS = "read:users"
    WRITE_USERS = "write:users"
    ADMIN = "admin"


class AuthorizationMiddleware:
    """Centralized authorization logic"""
    
    def __init__(self):
        # Role-based permissions
        self.role_permissions = {
            'user': [
                Permission.READ_HABITS,
                Permission.WRITE_HABITS,
                Permission.READ_PROJECTS,
                Permission.WRITE_PROJECTS,
                Permission.READ_ANALYTICS,
            ],
            'admin': [
                Permission.READ_HABITS,
                Permission.WRITE_HABITS,
                Permission.READ_PROJECTS,
                Permission.WRITE_PROJECTS,
                Permission.READ_ANALYTICS,
                Permission.READ_USERS,
                Permission.WRITE_USERS,
                Permission.ADMIN,
            ]
        }
    
    def require_permissions(self, required_permissions: List[str]):
        """Decorator to require specific permissions"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, request: Request = None, db: Session = Depends(get_db), **kwargs):
                user = get_current_user(request, db)
                if not user:
                    raise HTTPException(status_code=401, detail="Authentication required")
                
                user_permissions = self.get_user_permissions(user)
                
                for permission in required_permissions:
                    if permission not in user_permissions:
                        raise HTTPException(
                            status_code=403, 
                            detail=f"Missing required permission: {permission}"
                        )
                
                return await func(*args, request=request, db=db, **kwargs)
            return wrapper
        return decorator
    
    def require_resource_ownership(self, resource_type: str, resource_id_param: str = "id"):
        """Decorator to require ownership of a resource"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                request = kwargs.get('request')
                db = kwargs.get('db')
                
                if not request or not db:
                    raise HTTPException(status_code=500, detail="Authorization middleware misconfigured")
                
                user = get_current_user(request, db)
                if not user:
                    raise HTTPException(status_code=401, detail="Authentication required")
                
                resource_id = kwargs.get(resource_id_param)
                if not resource_id:
                    raise HTTPException(status_code=400, detail=f"Missing {resource_id_param}")
                
                # Check ownership based on resource type
                if resource_type == "habit":
                    resource = db.query(models.Habit).filter_by(id=resource_id).first()
                elif resource_type == "project":
                    resource = db.query(models.Project).filter_by(id=resource_id).first()
                else:
                    raise HTTPException(status_code=500, detail=f"Unknown resource type: {resource_type}")
                
                if not resource:
                    raise HTTPException(status_code=404, detail=f"{resource_type.title()} not found")
                
                if resource.user_id != user.id and user.role != 'admin':
                    raise HTTPException(status_code=403, detail="Access denied")
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def get_user_permissions(self, user) -> List[str]:
        """Get all permissions for a user based on their role"""
        role = getattr(user, 'role', 'user')
        return self.role_permissions.get(role, [])
    
    def check_permission(self, user, permission: str) -> bool:
        """Check if user has a specific permission"""
        user_permissions = self.get_user_permissions(user)
        return permission in user_permissions


# Global authorization instance
auth_middleware = AuthorizationMiddleware()

# Convenience decorators
def require_auth(func):
    """Require authentication"""
    @wraps(func)
    async def wrapper(*args, request: Request = None, db: Session = Depends(get_db), **kwargs):
        user = get_current_user(request, db)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        return await func(*args, request=request, db=db, **kwargs)
    return wrapper

def require_admin(func):
    """Require admin role"""
    return auth_middleware.require_permissions([Permission.ADMIN])(func)

def require_habit_access(func):
    """Require habit read/write permissions"""
    return auth_middleware.require_permissions([Permission.READ_HABITS, Permission.WRITE_HABITS])(func)

def require_project_access(func):
    """Require project read/write permissions"""
    return auth_middleware.require_permissions([Permission.READ_PROJECTS, Permission.WRITE_PROJECTS])(func)

def require_habit_ownership(func):
    """Require ownership of the habit resource"""
    return auth_middleware.require_resource_ownership("habit")(func)

def require_project_ownership(func):
    """Require ownership of the project resource"""
    return auth_middleware.require_resource_ownership("project")(func)