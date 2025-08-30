import os
import secrets
import hashlib
from datetime import datetime, timezone
from typing import Optional

from .models import PublicToken, SessionLocal

PEPPER = os.getenv('LIFERPG_TOKEN_PEPPER', 'dev_pepper_change_me')


def _hash_token(token: str) -> str:
    return hashlib.sha256((token + PEPPER).encode('utf-8')).hexdigest()


def create_public_token(db, user_id: int, name: str, scope: str = 'read:widgets') -> str:
    """Create a new public token for the user and return the plaintext token value once.
    The token is prefixed for readability and stored hashed in DB.
    """
    raw = f"lpt_{secrets.token_urlsafe(24)}"
    h = _hash_token(raw)
    pt = PublicToken(user_id=user_id, name=name or 'token', scope=scope or 'read:widgets', token_hash=h)
    db.add(pt)
    db.flush()
    return raw


def verify_public_token(db, token: str) -> Optional[int]:
    if not token:
        return None
    h = _hash_token(token)
    row = db.query(PublicToken).filter_by(token_hash=h).first()
    if not row:
        return None
    row.last_used_at = datetime.now(timezone.utc)
    db.flush()
    return row.user_id
