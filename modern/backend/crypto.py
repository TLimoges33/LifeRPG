import os
from cryptography.fernet import Fernet, InvalidToken

KEY_ENV = 'LIFERPG_DATA_KEY'
FALLBACK_KEY_PATH = os.path.join(os.path.dirname(__file__), '.dev_liferpg_key')


def _load_key_from_env():
    v = os.getenv(KEY_ENV)
    if v:
        return v.encode()
    return None


def _load_or_create_fallback_key():
    # Try to read an existing key file (dev convenience). Create with restrictive perms if missing.
    try:
        if os.path.exists(FALLBACK_KEY_PATH):
            with open(FALLBACK_KEY_PATH, 'rb') as f:
                return f.read().strip()
        # generate and persist locally (dev only)
        key = Fernet.generate_key()
        # write file with 0600 perms
        fd = os.open(FALLBACK_KEY_PATH, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as f:
            f.write(key)
        return key
    except Exception:
        return None


def get_fernet():
    key = _load_key_from_env() or _load_or_create_fallback_key()
    if not key:
        raise RuntimeError('Encryption key not available. Set env var LIFERPG_DATA_KEY or allow creating a dev key file.')
    return Fernet(key)


def encrypt_text(plaintext: str) -> str:
    if plaintext is None:
        return ''
    f = get_fernet()
    token = f.encrypt(plaintext.encode('utf-8'))
    return token.decode('utf-8')


def decrypt_text(token_text: str) -> str:
    if not token_text:
        return ''
    f = get_fernet()
    try:
        out = f.decrypt(token_text.encode('utf-8'))
        return out.decode('utf-8')
    except InvalidToken:
        # Token can't be decrypted — likely different key; surface empty
        return ''
