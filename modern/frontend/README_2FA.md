Frontend 2FA UX

This backend supports TOTP-based 2FA and one-time recovery codes.

Key flows:

- Admin-assisted signup + setup
 - After creating a user via the backend while logged in as admin, an alternate cookie `session_alt` will be set.
 - Use this cookie when calling 2FA endpoints to configure TOTP for the new account without logging the admin out.

- TOTP setup
 1) POST /api/v1/auth/2fa/setup
 - Show the `otpauth_uri` QR and the plaintext `recovery_codes` once.
 2) After the user scans the QR in an authenticator, prompt for a 6-digit code.
 3) POST /api/v1/auth/2fa/enable with `{ code }`.

- Login with 2FA
 - If the login response indicates 2FA is required (401 with detail), ask the user for their TOTP code and retry including `totp_code`.
 - Provide an option to use a recovery code; if used successfully, it is consumed and cannot be used again.

Notes

- Recovery codes are displayed only once during setup. Store them securely.
- Logout should clear both `session` and `session_alt`.