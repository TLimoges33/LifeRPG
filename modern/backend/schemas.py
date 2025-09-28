"""
Pydantic models for request validation and security
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
import re

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    totp_code: Optional[str] = Field(None, pattern=r'^\d{6}$')
    recovery_code: Optional[str] = Field(None, min_length=8, max_length=64)

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: Optional[str] = Field(None, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        """Enhanced NIST password guidelines with entropy checking"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password must be less than 128 characters')
            
        # Check for common weak passwords
        weak_patterns = [
            r'^password\d*$', r'^123456\d*$', r'^qwerty\d*$', 
            r'^admin\d*$', r'^letmein\d*$', r'^welcome\d*$',
            r'^football\d*$', r'^master\d*$', r'^guest\d*$'
        ]
        for pattern in weak_patterns:
            if re.match(pattern, v.lower()):
                raise ValueError('Password is too common and easily guessable')
        
        # Check for repeated characters (e.g., "aaaaaaaa")
        if len(set(v)) < 4:
            raise ValueError('Password must contain at least 4 unique characters')
        
        # Check for sequential patterns
        sequences = ['012345', '123456', '234567', '345678', '456789', 
                    'abcdef', 'bcdefg', 'cdefgh', 'defghi']
        for seq in sequences:
            if seq in v.lower() or seq[::-1] in v.lower():
                raise ValueError('Password cannot contain sequential patterns')
        
        # Encourage complexity for shorter passwords
        if len(v) < 12:
            char_types = 0
            if re.search(r'[a-z]', v): char_types += 1
            if re.search(r'[A-Z]', v): char_types += 1
            if re.search(r'[0-9]', v): char_types += 1
            if re.search(r'[!@#$%^&*(),.?":{}|<>]', v): char_types += 1
            
            if char_types < 3:
                raise ValueError('Passwords under 12 characters must contain at least 3 character types (uppercase, lowercase, numbers, symbols)')
        
        return v

class TwoFAEnableRequest(BaseModel):
    code: str = Field(..., pattern=r'^\d{6}$')

class TwoFADisableRequest(BaseModel):
    password: str = Field(..., min_length=8, max_length=128)
    code: Optional[str] = Field(None, pattern=r'^\d{6}$')

class HabitCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=50)
    difficulty: Optional[int] = Field(1, ge=1, le=5)
    
    @validator('title')
    def validate_title(cls, v):
        # Prevent XSS in titles
        if '<' in v or '>' in v or 'script' in v.lower():
            raise ValueError('Invalid characters in title')
        return v.strip()

class HabitUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=50)
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    completed: Optional[bool] = None
    
    @validator('title')
    def validate_title(cls, v):
        if v is not None:
            if '<' in v or '>' in v or 'script' in v.lower():
                raise ValueError('Invalid characters in title')
            return v.strip()
        return v

class ProjectCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    
    @validator('title')
    def validate_title(cls, v):
        if '<' in v or '>' in v or 'script' in v.lower():
            raise ValueError('Invalid characters in title')
        return v.strip()

class ProjectUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    
    @validator('title')
    def validate_title(cls, v):
        if v is not None:
            if '<' in v or '>' in v or 'script' in v.lower():
                raise ValueError('Invalid characters in title')
            return v.strip()
        return v

class TokenCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    permissions: List[str] = Field(default_factory=list)
    expires_in_days: Optional[int] = Field(30, ge=1, le=365)
    
    @validator('permissions')
    def validate_permissions(cls, v):
        allowed_permissions = ['read:habits', 'read:projects', 'read:analytics']
        for perm in v:
            if perm not in allowed_permissions:
                raise ValueError(f'Invalid permission: {perm}')
        return v
