OAuth notes

This scaffold uses `authlib`'s Starlette integration to provide OAuth flows.

How to test Google OAuth locally:
- Create OAuth credentials in Google Cloud Console (OAuth 2.0 Client IDs)
- Set Authorized redirect URI to: http://localhost:8000/api/v1/oauth/google/callback
- Copy credentials into `.env` or environment and start the backend:

  export GOOGLE_CLIENT_ID=...\n  export GOOGLE_CLIENT_SECRET=...\n  export BASE_URL=http://localhost:8000
  uvicorn modern.backend.app:app --reload --port 8000

- Visit: http://localhost:8000/api/v1/oauth/google/login

Security note: Never commit client secrets to source control. Use a secrets manager in production.
