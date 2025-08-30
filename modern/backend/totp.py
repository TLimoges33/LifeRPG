import os
import base64
import secrets
from typing import List, Tuple

import pyotp
from passlib.hash import bcrypt

ISSUER = os.getenv('TOTP_ISSUER', 'LifeRPG')


def generate_totp_secret() -> str:
    # 32 bytes -> base32
    return pyotp.random_base32()


def provisioning_uri(secret: str, email: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=ISSUER)


def verify_totp(secret: str, code: str) -> bool:
    try:
        totp = pyotp.TOTP(secret)
        return bool(totp.verify(code, valid_window=1))
    except Exception:
        return False


def generate_recovery_codes(count: int = 10) -> List[str]:
    return [secrets.token_urlsafe(10) for _ in range(count)]


def hash_recovery_codes(codes: List[str]) -> List[str]:
    return [bcrypt.hash(c) for c in codes]


def verify_and_consume_recovery_code(stored_hashes: List[str], code: str) -> Tuple[bool, List[str]]:
    remaining = []
    used = False
    for h in stored_hashes:
        if not used and bcrypt.verify(code, h):
            used = True
            continue
        remaining.append(h)
    return used, remaining
