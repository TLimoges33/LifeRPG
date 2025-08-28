Token encryption notes

This project includes a small helper (`crypto.py`) that uses Fernet (symmetric AES-GCM via cryptography) to encrypt OAuth tokens at rest.

Development behavior
- If `LIFERPG_DATA_KEY` env var is not set, the helper will create a key in `modern/backend/.dev_liferpg_key` with restrictive permissions (0600). This is intended for local development only.

Production guidance
- Provide a stable, secure encryption key via environment variable `LIFERPG_DATA_KEY` from a secrets manager (Vault, AWS KMS, GCP KMS, etc).
- Rotate keys using envelope encryption: encrypt tokens with a data key and wrap the data key with KMS.
- Consider using a separate secrets store (HashiCorp Vault) and avoid storing ciphertext in the primary DB if required.

Notes
- If the key changes, stored tokens cannot be decrypted. Provide migration/rotation paths through KMS envelope encryption.
- This helper is intentionally small and pragmatic — replace with a hardened secrets management path in production.
