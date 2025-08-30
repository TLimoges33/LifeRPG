# Public API tokens (read-only)

Create lightweight tokens to embed read-only widgets without a full login.

Endpoints:
- POST /api/v1/tokens — create a token (returns plaintext once)
- GET /api/v1/tokens — list your tokens
- DELETE /api/v1/tokens/{id} — revoke
- GET /api/v1/public/widgets/status?token=... — public read-only status JSON

Security notes:
- Tokens are one-way hashed in DB with a server-side pepper; only shown at creation.
- Scope is currently `read:widgets` only.
- Treat tokens like secrets; rotate regularly.