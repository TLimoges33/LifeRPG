"""Lightweight notifier for backend events (sync success/failure).

Currently supports Slack via incoming webhook stored as an OAuthToken on a
Slack integration for the same user. Best-effort; failures are logged but do
not raise.
"""
from typing import Dict, Any, List
import requests
import smtplib
from email.message import EmailMessage


def _slack_webhooks_for_user(db, user_id: int) -> List[str]:
    from . import models
    from .crypto import decrypt_text
    out: List[str] = []
    rows = db.query(models.Integration).filter_by(user_id=user_id, provider='slack').all()
    for integ in rows:
        tok = (
            db.query(models.OAuthToken)
            .filter_by(integration_id=integ.id)
            .order_by(models.OAuthToken.id.desc())
            .first()
        )
        if tok and tok.access_token:
            try:
                url = decrypt_text(tok.access_token)
                if url:
                    out.append(url)
            except Exception:
                continue
    return out


def emit_sync_event(db, integration_id: int, event: str, payload: Dict[str, Any]):
    """Emit a sync event notification to configured channels.

    For now, if the owning user has a Slack integration, post a message.
    """
    from . import models
    from .metrics import log_job_event

    integ = db.query(models.Integration).filter_by(id=integration_id).first()
    if not integ:
        return
    user_id = integ.user_id
    text = f"LifeRPG: {event} for {payload.get('provider','?')} (integration {integration_id})"
    try:
        res = payload.get('summary')
        if isinstance(res, dict):
            count = res.get('count')
            if count is not None:
                text += f" — items: {count}"
    except Exception:
        pass

    for hook in _slack_webhooks_for_user(db, user_id):
        try:
            requests.post(hook, json={"text": text}, timeout=5)
        except Exception as e:
            try:
                log_job_event('notify_fail', integration_id=integration_id, channel='slack', error=str(e))
            except Exception:
                pass


def send_webhook(url: str, body: Dict[str, Any], headers: Dict[str, str] | None = None):
    headers = headers or {}
    requests.post(url, json=body, headers=headers, timeout=5)


def send_email(to: str, subject: str, body: str):
    """Send an email via configured transport.

    Transports:
    - console (default): log intent only
    - smtp: use SMTP settings from environment
    - disabled: no-op
    """
    try:
        from .metrics import log_job_event
    except Exception:
        log_job_event = None
    try:
        from .config import settings
    except Exception:
        settings = None

    transport = (settings.EMAIL_TRANSPORT if settings else 'console') if settings else 'console'
    if transport == 'disabled':
        if log_job_event:
            try:
                log_job_event('email_disabled', to=to)
            except Exception:
                pass
        return
    if transport == 'console' or settings is None:
        if log_job_event:
            try:
                log_job_event('email_console', to=to, subject=subject)
            except Exception:
                pass
        return

    # SMTP path
    host = settings.SMTP_HOST
    port = settings.SMTP_PORT
    user = settings.SMTP_USERNAME
    pwd = settings.SMTP_PASSWORD
    use_tls = settings.SMTP_USE_TLS
    sender = settings.SMTP_FROM or user or 'no-reply@liferpg.local'
    if not host:
        # fallback to console if missing configuration
        if log_job_event:
            try:
                log_job_event('email_console', to=to, subject=subject, reason='smtp_not_configured')
            except Exception:
                pass
        return
    msg = EmailMessage()
    msg['From'] = sender
    msg['To'] = to
    msg['Subject'] = subject
    msg.set_content(body)
    try:
        if use_tls:
            server = smtplib.SMTP(host, port, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP(host, port, timeout=10)
        try:
            if user and pwd:
                server.login(user, pwd)
            server.send_message(msg)
        finally:
            try:
                server.quit()
            except Exception:
                pass
        if log_job_event:
            try:
                log_job_event('email_sent', to=to)
            except Exception:
                pass
    except Exception as e:
        if log_job_event:
            try:
                log_job_event('email_fail', to=to, error=str(e))
            except Exception:
                pass