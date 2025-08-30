Backend README

FastAPI backend for LifeRPG with SQLAlchemy, Alembic, JWT auth, and security middleware.

Run (dev):

- Use the app module: uvicorn modern.backend.app:app --reload
- Or via docker-compose: see modern/docker-compose.yml

Security configuration (env):

- FRONTEND_ORIGINS or FRONTEND_ORIGIN: Allowed CORS origins
- FORCE_HTTPS=true: Redirect http->https when behind a reverse proxy
- HSTS_ENABLE=true: Add Strict-Transport-Security header (TLS-only deployments)
- COOKIE_SECURE=true and COOKIE_SAMESITE=none|lax|strict: Configure session cookie
- MAX_BODY_BYTES=1048576: Request body size limit (bytes)
- REQUESTS_PER_MINUTE=120: Naive per-IP rate limit
 - CSRF_ENABLE=false: Enable CSRF protection for cookie-based state-changing requests
 - CSRF_HEADER_NAME=x-csrf-token and CSRF_COOKIE_NAME=csrf_token

Reverse proxy notes (production):

- Terminate TLS at your proxy (nginx/Traefik/ALB) and forward to the app over HTTP
- Set and trust X-Forwarded-Proto to preserve original scheme; enable FORCE_HTTPS for redirects
- Forward client IP via X-Forwarded-For; the app’s rate limiter reads the first address
- Configure CORS at the proxy if you prefer, or rely on the app’s CORS middleware

CSRF guidance:

- If you rely on cookie-based auth for state-changing requests, enable CSRF (double-submit cookie pattern)
- For pure Bearer token APIs from JS, CSRF is not required if cookies aren’t used


Two-Factor Auth (2FA) and session_alt
-------------------------------------

Flows that create users while an admin is already logged in need to configure 2FA for the new user without replacing the admin’s session. To support this, the backend issues an alternate cookie named `session_alt` on signup when a session already exists.

- Signup:
	- If no existing session is present, the normal `session` cookie is set for the newly created user.
	- If an admin (or any logged-in user) creates a new user, the backend preserves the admin’s `session` and additionally sets `session_alt` for the newly created user.

- 2FA endpoints:
	- `/api/v1/auth/2fa/setup`, `/api/v1/auth/2fa/enable`, `/api/v1/auth/2fa/disable` prefer `session_alt` when present. This lets admins guide users through TOTP setup immediately after signup in admin-driven flows.

- Logout:
	- `/api/v1/auth/logout` clears both `session` and `session_alt`.

TOTP setup and recovery codes
-----------------------------

Endpoints:

- `POST /api/v1/auth/2fa/setup`
	- Requires an authenticated session (or `session_alt`).
	- Generates a new TOTP secret and a set of plaintext recovery codes.
	- Returns `{ otpauth_uri, recovery_codes }`. Only bcrypt hashes of recovery codes are stored server-side.

- `POST /api/v1/auth/2fa/enable` with body `{ code }`
	- Verifies the current TOTP code and enables 2FA for the account.

- `POST /api/v1/auth/2fa/disable` with body `{ password, code? }`
	- Validates password and (if enabled) optionally validates a TOTP code.
	- Disables 2FA and clears the TOTP secret and recovery codes.

- `POST /api/v1/auth/login` with body `{ email, password, totp_code? | recovery_code? }`
	- If 2FA is enabled on the account, a valid `totp_code` or a one-time `recovery_code` is required.
	- Recovery codes are consumed on use and cannot be reused.

Frontend UX tips:

- After admin-driven signup, read `session_alt` to complete TOTP setup for the new account in the same browser without disrupting the admin session.
- Display the recovery codes exactly once at the end of setup and prompt the user to store them securely. The server cannot show them again.

