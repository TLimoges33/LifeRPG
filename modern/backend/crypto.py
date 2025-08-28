import os
from cryptography.fernet import Fernet, InvalidToken

KEY_ENV = 'LIFERPG_DATA_KEY'
FALLBACK_KEY_PATH = os.path.join(os.path.dirname(__file__), '.dev_liferpg_key')
KMS_WRAPPED_PATH = os.path.join(os.path.dirname(__file__), '.wrapped_data_key')
KMS_KEY_ID_ENV = 'LIFERPG_KMS_KEY_ID'


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


def _load_key_from_kms():
    """Optional: use AWS KMS to manage a wrapped data key for envelope encryption.

    If env var LIFERPG_KMS_KEY_ID is set and boto3 is available, this will either:
    - read an existing wrapped key from KMS_WRAPPED_PATH and call KMS Decrypt to obtain the plaintext data key,
    - or call KMS GenerateDataKey to produce and persist a wrapped key locally (development convenience).
    """
    key_id = os.getenv(KMS_KEY_ID_ENV)
    if not key_id:
        return None
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
    except Exception:
        return None

    kms = boto3.client('kms')
    # If wrapped key exists, decrypt it
    if os.path.exists(KMS_WRAPPED_PATH):
        try:
            with open(KMS_WRAPPED_PATH, 'rb') as f:
                blob = f.read()
            resp = kms.decrypt(CiphertextBlob=blob)
            return resp['Plaintext']
        except Exception:
            return None

    # Otherwise, generate a new data key and store the wrapped blob
    try:
        resp = kms.generate_data_key(KeyId=key_id, KeySpec='AES_256')
        plaintext = resp['Plaintext']
        ciphertext = resp['CiphertextBlob']
        # persist wrapped key
        with open(KMS_WRAPPED_PATH, 'wb') as f:
            f.write(ciphertext)
        # restrict perms
        try:
            os.chmod(KMS_WRAPPED_PATH, 0o600)
        except Exception:
            pass
        return plaintext
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
