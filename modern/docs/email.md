# Email transport

The notifier supports three transports controlled by environment variables:

- LIFERPG_EMAIL_TRANSPORT: `console` (default), `smtp`, or `disabled`.
- SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_USE_TLS, SMTP_FROM

Behavior:
- console: logs an `email_console` event (no email sent).
- smtp: sends via SMTP with optional STARTTLS and auth.
- disabled: logs an `email_disabled` event and does nothing.

Example `.env`:
```
LIFERPG_EMAIL_TRANSPORT=smtp
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=smtp-user
SMTP_PASSWORD=s3cr3t
SMTP_USE_TLS=true
SMTP_FROM=LifeRPG <noreply@example.com>
```

Troubleshooting:
- If SMTP_HOST is missing, it falls back to console behavior.
- Errors are logged as `email_fail` job events; they don’t raise to the caller.
